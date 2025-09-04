import uuid

def generate_password(size: int) -> str:
    password = str(uuid.uuid4())
    return password[:size]
