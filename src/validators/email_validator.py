import re
from typing import Optional

def validate_email(email: Optional[str]) -> bool:
    """Return True if email looks valid, else False."""
    if not isinstance(email, str):
        return False
    email = email.strip().lower()
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return bool(re.match(pattern, email))

def fix_email(email: Optional[str]) -> Optional[str]:
    """Normalize and return email if valid, else None."""
    if not isinstance(email, str):
        return None
    email = email.strip().lower()
    return email if validate_email(email) else None
