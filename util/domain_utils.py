from typing import Tuple

def parse_email(email: str) -> Tuple[str, str]:
    # returns (local_part, domain_full)
    local, domain = email.split("@", 1)
    return local, domain

def split_domain(domain_full: str) -> Tuple[str, str]:
    # naive split: subdomain vs apex (example: foo.example.com -> ("foo", "example.com"))
    # replace with tld-extract if you need public suffix handling
    parts = domain_full.split(".")
    if len(parts) < 3:
        return "", domain_full
    return ".".join(parts[:-2]), ".".join(parts[-2:])