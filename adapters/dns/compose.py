from .dns import DnsPort
from .dns_porkbun import PorkbunDnsAdapter

from typing import Literal

DNS_OPTIONS = Literal["PORKBUN"]

def build_dns(dns_type: DNS_OPTIONS) -> DnsPort:
    if dns_type == "PORKBUN":
        return PorkbunDnsAdapter()
    else:
        raise ValueError(f"Invalid DNS type: {dns_type}")
