from adapters.email_delivery.mailgun_wrapper.client import get_client
from common_types import DNSRecord

from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field

import logging

logger = logging.getLogger(__name__)

def create_subdomain_on_eds(subdomain: str, domain: str) -> List[DNSRecord]:
    """
    Create the subdomain upon the given domain.
    """
    domain_name = f"{subdomain}.{domain}"
    
    client = get_client()
    
    logger.info(f"Attempting to create subdomain={subdomain} for domain={domain}")
    
    response = client.domains.create(data={
        "name": domain_name
    })
    
    response_json = response.json()
    
    logger.info(f"Subdomain creation response={response_json}")
    
    receiving_dns_records = response_json["receiving_dns_records"]
    receiving_dns_records = _parse_dns_records(receiving_dns_records)
    
    sending_dns_records = response_json["sending_dns_records"]
    sending_dns_records = _parse_dns_records(sending_dns_records)
    
    logger.info(f"Parsed receiving DNS records={receiving_dns_records}")
    logger.info(f"Parsed sending DNS records={sending_dns_records}")
    
    # Add the DNS records to the DNS provider
    all_records = receiving_dns_records + sending_dns_records
    
    for record in all_records:
        if record.name == "":
            record.name = subdomain
    
    return all_records


def delete_subdomain_on_eds(subdomain: str, domain: str) -> bool:
    client = get_client()
    
    logger.info(f"Attempting to delete subdomain={subdomain} for domain={domain}")
    
    domain_name = f"{subdomain}.{domain}"
    
    response = client.domains.delete(domain=domain_name)
    
    return response.status_code == 200

def subdomain_exists_on_eds(subdomain: str, domain: str) -> bool:
    client = get_client()
    
    domain_name = f"{subdomain}.{domain}"
    
    response = client.domains.get(domain_name=domain_name)

    if response.status_code == 200:
        return True
    elif response.status_code == 404:
        return False
    
    raise Exception(f"Unexpected response code={response.status_code} for domain={domain_name}")

def get_domains_on_eds() -> List[str]:
    client = get_client()
    
    response = client.domains.get()
    
    response_json = response.json()
    
    return [domain["name"] for domain in response_json["items"]]

def get_subdomains_on_eds(domain: str) -> List[str]:
    client = get_client()
    
    response = client.domains.get(domain=domain)
    
    response_json = response.json()
    
    return [subdomain["name"] for subdomain in response_json["items"]]

def verify_domain_on_eds(domain: str) -> bool:
    class DnsRecordVerification(BaseModel):
        is_active: bool
        cached: list
        record_type: str
        valid: Literal['unknown', 'valid']
        value: str
        name: str = Field(default="")
    
    
    client = get_client()
    
    logger.info(f"Attempting to verify domain={domain}")
    
    response = client.domains.put(domain=domain, verify=True)
    
    if response.status_code != 200:
        return False
    
    response_json = response.json()
    
    parsed_sending_records = [
        DnsRecordVerification(**record) for record in response_json["sending_dns_records"]
    ]
    
    parsed_receiving_records = [
        DnsRecordVerification(**record) for record in response_json["receiving_dns_records"]
    ]
    
    all_records = parsed_sending_records + parsed_receiving_records
    
    invalid_record_count = 0
    
    for record in all_records:
        if record.valid != "valid":
            logger.warning(f"Invalid DNS Record, name={record.name}, record_type={record.record_type}")
            invalid_record_count += 1
    
    logger.info(f"Invalid record count={invalid_record_count}")
    
    return invalid_record_count == 0
    


def _parse_dns_records(dns_records: List[Dict]) -> List[DNSRecord]:
    def _parse_dns_record(dns_record: Dict) -> Optional[DNSRecord]:
        try:
            name = dns_record["name"] if "name" in dns_record else ""
            priority = dns_record["priority"] if "priority" in dns_record else None
            record_type = dns_record["record_type"]
            value = dns_record["value"]
        except KeyError as e:
            logger.error(f"Error parsing DNS record={dns_record}: {e}")
            return None
        
        return DNSRecord(name=name, priority=priority, record_type=record_type, value=value)
    
    results = []
    
    for dns_record in dns_records:
        result = _parse_dns_record(dns_record)
        if result is not None:
            results.append(result)
            
    return results
