"""Backward-compatible entrypoint for the V2.6 performance learning store."""
try:
    from .performance_store_v26 import *  # type: ignore # noqa: F401,F403
except ImportError:
    from performance_store_v26 import *  # type: ignore # noqa: F401,F403

if __name__ == "__main__":
    raise SystemExit(main())
