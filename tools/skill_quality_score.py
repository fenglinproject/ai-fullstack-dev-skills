#!/usr/bin/env python3
"""Compatibility entrypoint for the new structural quality audit.

Formerly scored by keyword count; now checks catalog integrity and metadata.
"""
from pathlib import Path
import importlib.util

p=Path(__file__).resolve().with_name('audit_catalog.py')
spec=importlib.util.spec_from_file_location('audit_catalog',p)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.main()
