"""Run all tests in the tests package.

Usage:
    .venv/bin/python -m tests
"""

from __future__ import annotations

import importlib
import pkgutil
import traceback
from pathlib import Path


def _iter_test_modules() -> list[str]:
    package_dir = Path(__file__).parent
    names = [
        name
        for _, name, ispkg in pkgutil.iter_modules([str(package_dir)])
        if not ispkg and name.startswith("test_")
    ]
    return sorted(names)


def _iter_test_callables(module):
    seen = set()

    # Support the existing convention in this repo.
    maybe_test = getattr(module, "test", None)
    if callable(maybe_test):
        seen.add("test")
        yield "test", maybe_test

    # Also support multiple test functions in one module.
    for name in sorted(dir(module)):
        if not name.startswith("test_"):
            continue
        if name in seen:
            continue
        fn = getattr(module, name, None)
        if callable(fn):
            yield name, fn


def main() -> int:
    """Run all tests in the tests package."""
    package_name = __package__ or "tests"
    modules = _iter_test_modules()

    if not modules:
        print("No test modules found in tests/.")
        return 0

    failures = 0
    ran = 0

    for module_name in modules:
        fqmn = f"{package_name}.{module_name}"
        print(f"[module] {fqmn}")
        module = importlib.import_module(fqmn)

        found_callable = False
        for test_name, test_fn in _iter_test_callables(module):
            found_callable = True
            label = f"{fqmn}.{test_name}"
            try:
                test_fn()
                print(f"PASS {label}")
                ran += 1
            except Exception: # pylint: disable=broad-except
                failures += 1
                print(f"FAIL {label}")
                traceback.print_exc()

        if not found_callable:
            print(f"SKIP {fqmn} (no callable test entrypoints found)")

    print(f"\nSummary: ran={ran}, failed={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
