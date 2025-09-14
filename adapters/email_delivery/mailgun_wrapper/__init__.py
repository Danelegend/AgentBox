from adapters.email_delivery.mailgun_wrapper.domain import (
    create_subdomain_on_eds, 
    delete_subdomain_on_eds,
    subdomain_exists_on_eds,
    get_domains_on_eds,
    get_subdomains_on_eds,
    verify_domain_on_eds
)
from adapters.email_delivery.mailgun_wrapper.user import (
    create_user_on_eds,
    delete_user_on_eds,
    get_users_on_eds
)
from adapters.email_delivery.mailgun_wrapper.email import (
    send_email_on_eds
)
from adapters.email_delivery.mailgun_wrapper.webhook import (
    set_inbound_email_webhook,
    delete_routes
)


__all__ = [
    "create_subdomain_on_eds",
    "delete_subdomain_on_eds",
    "subdomain_exists_on_eds",
    "get_domains_on_eds",
    "get_subdomains_on_eds",
    "verify_domain_on_eds",
    "create_user_on_eds",
    "delete_user_on_eds",
    "send_email_on_eds",
    "get_users_on_eds",
    "set_inbound_email_webhook",
    "delete_routes"
]
