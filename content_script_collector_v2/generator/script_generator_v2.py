"""Backward-compatible entrypoint for Script Generator V2.

V2.7 is the active implementation. Existing BAT files and imports can keep using
`script_generator_v2.py` without changing their command or import path.
"""
try:
    from .script_generator_v27 import *  # type: ignore # noqa: F401,F403
except ImportError:
    from script_generator_v27 import *  # type: ignore # noqa: F401,F403

if __name__ == "__main__":
    raise SystemExit(main())
