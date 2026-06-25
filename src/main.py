from __future__ import annotations

import json
import sys

from src.core.config import bootstrap_filesystem, diagnostics, load_config
from src.core.exceptions import PipelineError
from src.core.instrumentation import setup_opentelemetry, setup_sentry
from src.core.logging import configure_logging, get_logger
from src.services.pipeline_runner import build_runner


def main() -> int:
    run_id = "bootstrap"
    try:
        config, warnings = load_config()
        bootstrap_filesystem(config)

        run_id = "init"
        configure_logging(config, run_id=run_id)
        logger = get_logger("etl.main", run_id=run_id)
        setup_sentry(config, logger)
        setup_opentelemetry(config, logger)

        startup_diagnostics = diagnostics(config, warnings)
        logger.info("Startup diagnostics.", extra={"stage": "startup", "diagnostics": startup_diagnostics})
        for warning in warnings:
            logger.warning(warning, extra={"stage": "startup"})

        runner = build_runner(config)
        # Reconfigure run-scoped logger context.
        configure_logging(config, run_id=runner.run_id)
        logger = get_logger("etl.main", run_id=runner.run_id)

        result = runner.run()
        logger.info("Pipeline succeeded.", extra={"stage": "complete", "result": result})
        print(json.dumps(result, ensure_ascii=True))
        return 0
    except PipelineError as exc:
        print(json.dumps(exc.to_dict(), ensure_ascii=True), file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - final safety net
        print(f"[UNHANDLED] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
