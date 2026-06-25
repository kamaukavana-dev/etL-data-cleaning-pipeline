import sys
import smtplib
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.core.config import load_config
from src.services.notification_service import NotificationService

def audit_reliability():
    """
    Audit reliability claims by injecting failures into the SMTP stack.
    Verifies retry counts and backoff logic.
    """
    print("--- RELIABILITY AUDIT: SMTP Failure Injection ---")
    
    config, _ = load_config()
    service = NotificationService(config)
    
    attempts = 0
    def side_effect(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        print(f"SMTP Attempt {attempts} at {time.time():.2f}")
        raise ConnectionError("Simulated network outage")

    # Mock smtplib.SMTP or smtplib.SMTP_SSL depending on config
    # For audit, we'll patch the send_email internal logic that uses smtplib
    
    with patch("smtplib.SMTP") as mock_smtp, patch("smtplib.SMTP_SSL") as mock_ssl:
        mock_smtp.return_value.__enter__.return_value.send_message.side_effect = side_effect
        mock_ssl.return_value.__enter__.return_value.send_message.side_effect = side_effect
        
        start_time = time.time()
        try:
            service.send_email(subject="Audit", body="Test", recipient="test@example.com")
        except Exception as e:
            print(f"Final failure after retries: {e}")
            
        end_time = time.time()
        total_duration = end_time - start_time
        
        print("\n=== RELIABILITY RESULTS ===")
        print(f"Total Attempts Recorded: {attempts}")
        print(f"Total Test Duration:     {total_duration:.2f}s")
        
        if attempts == 3:
            print("[VERIFIED] Retry count is exactly 3.")
        else:
            print(f"[FAIL] Expected 3 attempts, got {attempts}.")
            
        if total_duration >= 4: # Min wait is 4s in policy
             print("[VERIFIED] Backoff delay observed.")
        else:
             print(f"[FAIL] Insufficient delay between retries ({total_duration:.2f}s).")
        print("==========================\n")

if __name__ == "__main__":
    audit_reliability()
