#!/usr/bin/env python3
"""
Introspect the installed `wandas` package and print a JSON schema
containing classes, their public methods (args and docstrings),
module-level functions (args and docstrings), and package version.

This script is intended to be used by agent/skill tooling to discover
the `wandas` API surface.
"""

import json
import sys
import inspect

try:
    import wandas
except ImportError:
    print(json.dumps({"error": "wandas library not found"}))
    sys.exit(1)


def get_class_info(cls):
    methods = {}

    # Public methods
    for name, member in inspect.getmembers(cls, predicate=inspect.isfunction):
        if name.startswith('_'):
            continue
        try:
            spec = inspect.getfullargspec(member)
            methods[name] = {
                "args": spec.args,
                "doc": inspect.getdoc(member)
            }
        except Exception:
            continue

    # Include constructor docs/signature hints
    try:
        init = getattr(cls, "__init__", None)
        if init is not None:
            spec = inspect.getfullargspec(init)
            methods["__init__"] = {
                "args": spec.args,
                "doc": inspect.getdoc(init)
            }
    except Exception:
        pass
    return {
        "methods": methods,
        "doc": inspect.getdoc(cls)
    }


def main():
    schema = {
        "version": getattr(wandas, "__version__", "unknown"),
        "classes": {},
        "functions": {}
    }

    # Inspect main classes in wandas
    for name, obj in inspect.getmembers(wandas, predicate=inspect.isclass):
        if not name.startswith('_'):
            schema["classes"][name] = get_class_info(obj)

    # Inspect module-level functions (e.g., from_numpy)
    for name, obj in inspect.getmembers(wandas, predicate=inspect.isfunction):
        if name.startswith('_'):
            continue
        try:
            spec = inspect.getfullargspec(obj)
            schema["functions"][name] = {
                "args": spec.args,
                "doc": inspect.getdoc(obj)
            }
        except Exception:
            continue

    print(json.dumps(schema))


if __name__ == "__main__":
    main()
