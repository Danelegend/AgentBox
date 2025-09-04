import logging

from typing import List

from common_types import DNSRecord
from adapters.dns.porkbun_wrapper.client import get_client

logger = logging.getLogger(__name__)

def create_dns_records(
    domain: str,
    subdomain: str,
    dns_records: List[DNSRecord],
) -> bool:
    logger.info(f"Creating DNS records for {domain} under {subdomain}")
    client = get_client()
    
    records_created = 0
    
    for dns_record in dns_records:
        name = _extract_subdomain(dns_record.name, domain)
        
        success = client.create_dns_record(
            domain=domain,
            record_type=dns_record.record_type,
            value=dns_record.value,
            name=name,
            priority=dns_record.priority,
        )
        
        if not success:
            logger.error(f"Failed to create DNS record={dns_record} for domain={domain} under {subdomain}")
        else:
            records_created += 1
            
    return records_created == len(dns_records)
    
def delete_dns_records(
    domain: str,
    subdomain: str
) -> bool:
    """
    Deletes the DNS records for the given subdomain under the domain
    """
    client = get_client()
    
    records = client.get_dns_records(domain)
    
    failure_recorded = False
    
    for record in records:
        if record.name.endswith(subdomain + "." + domain):
            success = client.delete_dns_record(domain, record.id)
            if not success:
                logger.error(f"Failed to delete DNS record={record} for domain={domain} under {subdomain}")
                failure_recorded = True
                
    return not failure_recorded

def exists_dns_records(
    domain: str,
    subdomain: str
) -> bool:
    client = get_client()
    
    records = client.get_dns_records(domain)
    
    for record in records:
        if record.name == subdomain + "." + domain:
            return True
    
    return False

def _extract_subdomain(full_name: str, domain: str) -> str:
    if not full_name.endswith(domain):
        return full_name
    
    remaining = full_name[:-len(domain)]
    
    return remaining.rstrip(".")
