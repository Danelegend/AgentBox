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

