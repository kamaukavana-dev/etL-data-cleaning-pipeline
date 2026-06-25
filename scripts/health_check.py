from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.core.config import load_config, diagnostics, bootstrap_filesystem
from src.core.exceptions import PipelineError

def run_health_check() -> int:
    print("ETL Pipeline Health Check")
    print("="*30)
    
    try:
        # Step 1: Load Configuration
        try:
            config, warnings = load_config()
            print("[OK] Configuration loaded")
        except PipelineError as exc:
            print(f"[FAIL] Configuration load failed: {exc}")
            return 1
            
        # Step 2: Bootstrap Filesystem
        try:
            bootstrap_filesystem(config)
            print("[OK] Filesystem bootstrapped")
        except PipelineError as exc:
            print(f"[FAIL] Filesystem bootstrap failed: {exc}")
            return 1
        
        # Step 3: Run Diagnostics
        results = diagnostics(config, warnings)
        
        print("\nDiagnostic Details:")
        critical_failed = False
        
        # Project Root
        print(f"[OK] Project Root: {results['project_root']}")
        
        # Environment
        env_status = "[OK]" if results['env_file_exists'] else "[WARN]"
        print(f"{env_status} Environment File: {results['env_file']} (Exists: {results['env_file_exists']})")
        
        # Data File
        if results['data_file_exists']:
            print(f"[OK] Data File: {results['data_file']}")
        else:
            print(f"[FAIL] Data File: {results['data_file']} (MISSING)")
            critical_failed = True
            
        # SMTP
        if results['smtp_enabled']:
            print("[OK] SMTP: Enabled")
        else:
            print(f"[INFO] SMTP: Disabled (Reason: {results['smtp_reason']})")
            
        # Warnings
        if results['warnings']:
            print("\nConfiguration Warnings:")
            for warning in results['warnings']:
                print(f"- {warning}")
        
        if critical_failed:
            print("\nResult: UNHEALTHY ❌")
            return 1
            
        print("\nResult: HEALTHY ✅")
        return 0
        
    except Exception as exc:
        print(f"\nCRITICAL ERROR during health check: {exc}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(run_health_check())
