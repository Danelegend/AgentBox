from typing import List
from common_types import DNSRecord
from adapters.dns.dns import DnsPort
from adapters.dns.porkbun_wrapper import create_dns_records, delete_dns_records, exists_dns_records

class PorkbunDnsAdapter(DnsPort):
    def create_records(self, domain: str, subdomain: str, records: List[DNSRecord]) -> bool:
        return create_dns_records(domain, subdomain, records)

    def delete_records(self, domain: str, subdomain: str) -> bool:
        return delete_dns_records(domain, subdomain)

    def exists_records(self, domain: str, subdomain: str) -> bool:
        return exists_dns_records(domain, subdomain)