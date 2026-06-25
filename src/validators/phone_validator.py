import re
from typing import Optional

def validate_phone(phone: Optional[str]) -> bool:
    """Return True if phone looks valid (7-15 digits), else False."""
    if not isinstance(phone, str):
        return False
    phone = re.sub(r"[^\d+]", "", phone.strip())
    digits = phone[1:] if phone.startswith("+") else phone
    return digits.isdigit() and 7 <= len(digits) <= 15

def normalize_phone(phone: Optional[str]) -> Optional[str]:
    """Normalize and return phone if valid, else None."""
    if not isinstance(phone, str):
        return None
    phone = re.sub(r"[^\d+]", "", phone.strip())
    digits = phone[1:] if phone.startswith("+") else phone
    return phone if digits.isdigit() and 7 <= len(digits) <= 15 else None
