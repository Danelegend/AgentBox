import requests as req
import os
from typing import Optional, Literal, List
from pydantic import BaseModel

import logging
logger = logging.getLogger(__name__)

DNS_CREATE_URI = "https://api.porkbun.com/api/json/v3/dns/create/{domain}"
DNS_UPDATE_URI = "https://api.porkbun.com/api/json/v3/dns/editByNameType/{domain}/{type}/{subdomain}"
DNS_DELETE_URI = "https://api.porkbun.com/api/json/v3/dns/deleteByNameType/{domain}/{type}/{subdomain}"
DNS_DELETE_BY_ID_URI = "https://api.porkbun.com/api/json/v3/dns/delete/{domain}/{id}"

DNS_GET_URI = "https://api.porkbun.com/api/json/v3/dns/retrieve/{domain}"

RECORD_TYPES = Literal["A", "MX", "CNAME", "ALIAS", "TXT", "NS", "AAAA", "SRV", "TLSA", "CAA"]

class DNSRecord(BaseModel):
    id: str
    name: str
    type: RECORD_TYPES
    content: str
    ttl: str
    prio: str | None
    notes: str | None

class PorkbunClient:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        
    def create_dns_record(
        self,
        domain: str,
        record_type: RECORD_TYPES,
        value: str,
        name: Optional[str] = None,
        ttl: Optional[int] = None,
        priority: Optional[int] = None
    ) -> bool:
        payload = {
            "secretapikey": self.api_secret,
            "apikey": self.api_key,
            "name": name,
            "type": record_type,
            "content": value,
        }
        
        if ttl is not None:
            payload["ttl"] = ttl
        if priority is not None:
            payload["priority"] = priority

        response = req.post(
            DNS_CREATE_URI.format(domain=domain),
            json=payload
        )
        
        return response.status_code == 200
    
    def get_dns_records(
        self,
        domain: str,
    ) -> List[DNSRecord]:
        """
        Retrieves the DNS records for the given domain.
        """
        payload = {
            "secretapikey": self.api_secret,
            "apikey": self.api_key,
        }
        
        response = req.post(
            DNS_GET_URI.format(domain=domain),
            json=payload
        )
        
        response_json = response.json()
        
        if response.status_code != 200:
            return []
        
        return [DNSRecord(**record) for record in response_json["records"]]
    
    def delete_dns_record(
        self,
        domain: str,
        record_id: str,
    ):
        payload = {
            "secretapikey": self.api_secret,
            "apikey": self.api_key,
        }
        
        response = req.post(
            DNS_DELETE_BY_ID_URI.format(domain=domain, id=record_id),
            json=payload
        )
        
        return response.status_code == 200
    

client = PorkbunClient(
    api_key=os.getenv("PORKBUN_API_KEY"), 
    api_secret=os.getenv("PORKBUN_API_SECRET")
)

def get_client() -> PorkbunClient:
    return client