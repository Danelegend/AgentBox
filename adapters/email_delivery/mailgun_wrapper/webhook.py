from typing import List

from .client import get_client

def set_inbound_email_webhook(domain: str, webhook_url: str):
    client = get_client()
    
    forward_action = f"forward('{webhook_url}')"
    stop_action = "stop()"
    
    data = {
        "priority": 0,
        "description": "Inbound email webhook",
        "expression": "catch_all()",
        "action": [forward_action, stop_action],
    }
    
    req = client.routes.create(domain=domain, data=data)
    
    return req.status_code == 200

def get_routes(domain: str) -> List[str]:
    client = get_client()
    
    req = client.routes.get(domain=domain)
    
    if req.status_code != 200:
        return []
    
    data = req.json()
    items = data["items"]
    results = []
    for item in items:
        results.append(item["id"])
    
    return results

def delete_routes(domain: str):
    route_ids = get_routes(domain)
    
    client = get_client()
    
    for route_id in route_ids:
        client.routes.delete(domain=domain, route_id=route_id)
