import dotenv
dotenv.load_dotenv()

import logging
import time
import threading

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

from services import build_inbox_service

inbox_service = build_inbox_service()

domain = "tryfilos.xyz"  # We need API access for this domain
subdomain = "demo"
full_domain = f"{subdomain}.{domain}"
test_email = f"tester@{full_domain}"

# Signal to ensure we only create the inbox once (via callback or polling)
_verified_once = threading.Event()

def _on_verified():
    if _verified_once.is_set():
        return
    logging.info("Domain verified. Creating test inbox...")
    try:
        inbox_service.create_inbox(test_email)
        logging.info("Created inbox: %s", test_email)
        # Do any demo actions here, e.g., send or fetch emails
    finally:
        # Clean up the demo inbox
        inbox_service.delete_inbox(test_email)
        logging.info("Deleted inbox: %s", test_email)
        _verified_once.set()

try:
    result = inbox_service.create_domain(full_domain, verified_callback=_on_verified)
    logging.info("Requested domain creation: %s (status=%s)", full_domain, result.status)

    if result.status == "verified":
        print("Immediately verified")
        _on_verified()
    else:
        # Keep the script alive until verified or timeout
        timeout_seconds = 10 * 60
        poll_interval = 15
        waited = 0
        while not _verified_once.is_set() and waited < timeout_seconds:
            if inbox_service.domain_verified(full_domain):
                _on_verified()
                break
            time.sleep(poll_interval)
            waited += poll_interval

        if not _verified_once.is_set():
            logging.warning("Domain verification timed out after %ss: %s", timeout_seconds, full_domain)
except Exception as e:
    logging.exception("Demo failed: %s", e)

# Delete the domain
inbox_service.delete_subdomain(full_domain)
