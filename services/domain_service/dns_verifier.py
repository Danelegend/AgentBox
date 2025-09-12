import datetime
import threading
import time

from pydantic import BaseModel, Field
from typing import Dict, Callable, Optional, List, Literal
from enum import Enum

from adapters import EmailDeliveryPort

import logging
logger = logging.getLogger(__name__)

class VerificationStatus(Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"
    

class PendingDomain(BaseModel):
    domain: str
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    last_attempt: datetime.datetime = Field(default_factory=datetime.datetime.now)
    attempts: int = 1
    max_completion_time: datetime.timedelta = Field(default=datetime.timedelta(minutes=10))
    completion_function: Optional[Callable[[str], None]] = None
    error_function: Optional[Callable[[str, str], None]] = None
    status: VerificationStatus = VerificationStatus.PENDING
    last_error: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
        use_enum_values = True

    def should_retry(self) -> bool:
        """Check if domain should still be retried"""
        if self.status != VerificationStatus.PENDING:
            return False
        
        # Check that the last attempt was after the max_completion_time
        age = datetime.datetime.now() - self.last_attempt
        if age > self.max_completion_time:
            self.status = VerificationStatus.EXPIRED
            return False
        
        return True
    
    def get_next_delay(self, base_delay: int = 30, max_delay: int = 300) -> int:
        """Calculate exponential backoff delay"""
        # Exponential backoff: base_delay * (1.5 ^ (attempts - 1))
        delay = min(base_delay * (1.5 ** (self.attempts - 1)), max_delay)
        return int(delay)

class DnsVerifier:
    def __init__(
        self,
        email_delivery: EmailDeliveryPort,
        check_interval: int = 10
    ):
        self.email_delivery = email_delivery
        self.check_interval = check_interval
    
        self.pending_domains: Dict[str, PendingDomain] = {}
        self._verification_timer: Optional[threading.Timer] = None
        self._timer_lock = threading.Lock()
        self._shutdown = threading.Event()
    
    def get_domain_status(self, domain: str) -> Optional[Literal["verified", "pending"]]:
        if domain in self.pending_domains:
            status = self.pending_domains[domain].status
            return "verified" if status == VerificationStatus.VERIFIED else "pending"
        return None
    
    def add_pending_dns_verification(
        self, 
        domain: str, 
        completion_function: Optional[Callable[[str], None]] = None,
        error_function: Optional[Callable[[str, str], None]] = None
    ) -> bool:
        with self._timer_lock:
            # Check if domain already exists
            if domain in self.pending_domains:
                existing = self.pending_domains[domain]
                
                if existing.status in [VerificationStatus.VERIFIED, VerificationStatus.FAILED]:
                    logger.warning(f"Domain {domain} already processed with status {existing.status}")
                    return False
                
                # Update callbacks for existing pending domain
                if completion_function:
                    existing.completion_function = completion_function
                if error_function:
                    existing.error_function = error_function
                return True
            
            # Add new domain
            self.pending_domains[domain] = PendingDomain(
                domain=domain,
                completion_function=completion_function,
                error_function=error_function,
            )
            
            logger.info(f"Added domain {domain} for DNS verification")
            
            # Start time if this is the first domain
            self._ensure_verification_timer_running()
        
        return True
    
    def remove_domain(self, domain: str) -> bool:
        """Remove a domain from verification (eg. if user cancels)"""
        with self._timer_lock:
            if domain in self.pending_domains:
                del self.pending_domains[domain]
                logger.info(f"Removed domain {domain} from verification")
                return True
            return False
    
    def _ensure_verification_timer_running(self):
        """Ensure the verification timer is running"""
        if self._verification_timer is None or not self._verification_timer.is_alive():
            self._start_verification_timer()
            
    def _start_verification_timer(self):
        """Start the verification timer"""
        if self._shutdown.is_set():
            return
        
        self._verification_timer = threading.Timer(
            self.check_interval,
            self._verification_cycle
        )
        
        self._verification_timer.daemon = True
        self._verification_timer.start()
        logger.info(f"Started DNS verification timer (interval={self.check_interval}s)")
    
    def _verification_cycle(self):
        """Main verification cycle - runs periodically"""
        try:
            self._verify_domains()
            
            # Schedule next cycle if we still have pending domains
            with self._timer_lock:
                pending_count = len([
                    p for p in self.pending_domains.values()
                    if p.status == VerificationStatus.PENDING
                ])
                
                if pending_count > 0 and not self._shutdown.is_set():
                    self._start_verification_timer()
                else:
                    self._verification_timer = None
                    logger.info("Stopped DNS verification timer (no pending domains)")
        except Exception as e:
            logger.error(f"Error in verification cycle: {e}", exc_info=True)
            # Restart timer even on error
            if not self._shutdown.is_set():
                self._start_verification_timer()
    
    def _verify_domains(self):
        """Verify all pending domains"""
        now = datetime.datetime.now()
        logger.info(f"Verifying domains at {now}")
        domains_to_process = []
        
        # Collect domains that need processing
        with self._timer_lock:
            for domain, pending_domain in self.pending_domains.items():
                if not pending_domain.should_retry():
                    continue
                
                # Check if enough time has passed since last attempt
                time_since_last = (now - pending_domain.last_attempt).total_seconds()
                required_delay = pending_domain.get_next_delay()
                
                if time_since_last >= required_delay:
                    domains_to_process.append(domain)
        
        # Process domains (outside lock to avoid blocking)
        completed_domains = []
        failed_domains = []
        
        for domain in domains_to_process:
            pending_domain = self.pending_domains.get(domain)
            if not pending_domain:
                continue
            
            try:
                pending_domain.last_attempt = now
                pending_domain.attempts += 1
                
                logger.debug(f"Verifying domain {domain} (attempt {pending_domain.attempts})")
                
                if self._verify_dns_domain(domain):
                    pending_domain.status = VerificationStatus.VERIFIED
                    completed_domains.append(domain)
                    logger.info(f"Domain {domain} verified successfully")
                else:
                    pending_domain.last_error = "Domain verification failed"
                    if not pending_domain.should_retry():
                        failed_domains.append(domain)
                        logger.warning(f"Domain {domain} verification failed permanently")
            
            except Exception as e:
                pending_domain.last_error = str(e)
                logger.error(f"Error verifying domain {domain}: {e}")
                
                if not pending_domain.should_retry():
                    failed_domains.append(domain)
        
        # Handle completed and failed domains
        self._handle_completed_domains(completed_domains)
        self._handle_failed_domains(failed_domains)
        
    def _handle_completed_domains(self, domains: List[str]):
        """Handle successfully verified domains"""
        for domain in domains:
            pending_domain = self.pending_domains.get(domain)
            if not pending_domain:
                continue
            
            # Call completion function
            if pending_domain.completion_function:
                try:
                    pending_domain.completion_function(
                        pending_domain.domain
                    )
                except Exception as e:
                    logger.error(f"Error in completion function for {domain}: {e}")

    def _handle_failed_domains(self, domains: List[str]):
        """Handle failed/expired domains"""
        for domain in domains:
            pending_domain = self.pending_domains.get(domain)
            if not pending_domain:
                continue
            
            if pending_domain.status == VerificationStatus.EXPIRED:
                error_msg = f"Domain verification expired for {domain}"
            else:
                error_msg = f"Domain verification failed for {domain}: {pending_domain.last_error}"

            # Call error function
            if pending_domain.error_function:
                try:
                    pending_domain.error_function(
                        pending_domain.domain,
                        error_msg
                    )
                except Exception as e:
                    logger.error(f"Error in error function for {domain}: {e}")
            
            logger.warning(error_msg)
    
    def _verify_dns_domain(self, domain: str) -> bool:
        """Verify a single domain"""
        try:
            return self.email_delivery.verify_domain(domain)
        except Exception as e:
            logger.error(f"Exception during domain verification for {domain}: {e}")
            return False
        
    def shutdown(self, timeout: int = 30):
        """Gracefully shutdown the verifier"""
        logger.info("Shutting down DNS verifier...")
        self._shutdown.set()
        
        with self._timer_lock:
            if self._verification_timer and self._verification_timer.is_alive():
                self._verification_timer.cancel()
        
        # Wait for any ongoing verification to complete
        time.sleep(min(timeout, 5))
        
        # Call error functions for remaining pending domains
        for domain, pending in self.pending_domains.items():
            if pending.status == VerificationStatus.PENDING and pending.error_function:
                try:
                    pending.error_function("DNS verifier shutting down")
                except Exception as e:
                    logger.error(f"Error calling error function during shutdown for {domain}: {e}")
        
        logger.info("DNS verifier shutdown complete")
