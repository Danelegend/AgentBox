from adapters.email_delivery.mailgun_wrapper.client import get_client
from util.password_generator import generate_password
from typing import List
from pydantic import BaseModel

import logging
logger = logging.getLogger(__name__)

def create_user_on_eds(local_part: str, domain: str) -> str:
    """
    Create a user on the given domain.
    
    Returns the password for the user.
    """
    client = get_client()
    
    password = generate_password(32)
    
    data = {
        "login": f"{local_part}@{domain}",
        "password": password
    }
    
    response = client.domains_credentials.create(
        domain=domain,
        data=data
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to create user on domain={domain}, local_part={local_part}")
        return ""
    
    return password

def delete_user_on_eds(local_part: str, domain: str) -> bool:
    client = get_client()
    
    response = client.domains_credentials.delete(
        domain=domain,
        login=f"{local_part}@{domain}"
    )
    
    # User not found -> Success
    if response.status_code == 404:
        return True
    
    return response.status_code == 200

def get_users_on_eds(domain: str) -> List[str]:
    class UserItem(BaseModel):
        mailbox: str
        login: str
        created_at: str
        size_bytes: int | None
    
    client = get_client()
    
    logger.info(f"Getting users on domain={domain}")
    
    response = client.domains_credentials.get(
        domain=domain
    )
    
    response_json = response.json()
    
    items = response_json["items"]
    
    users = []
    
    for item in items:
        item = UserItem.model_validate(item)
        users.append(item.mailbox)
    
    return users
    
    