from mailgun.client import Client

import os

auth = ("api", os.getenv("MAILGUN_API_KEY"))

mg = Client(auth=auth)

def get_client() -> Client:
    return mg
