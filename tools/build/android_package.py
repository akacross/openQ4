#!/usr/bin/env python3
"""Canonical content manifest shared by Android APK verification and fixtures."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re


def package_manifest(directory: Path) -> bytes:
    entries = {}
    for path in directory.rglob('*'):
        if path.is_symlink():
            raise ValueError(f'Package assets may not be links: {path}')
        if path.is_file():
            name = path.relative_to(directory).as_posix()
            if (len(name) > 240 or not re.fullmatch(r'[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*', name)
                    or len(name.split('/')) > 16 or any(part in ('.', '..') for part in name.split('/'))):
                raise ValueError(f'Invalid package path: {name}')
            entries[name] = path
    if len(entries) > 4096 or not {'mod.json', 'pak0.pk4', 'pak1.pk4'} <= entries.keys():
        raise ValueError('Invalid package manifest file count or missing required file')
    lines = ['openQ4-package-v1\n']
    total = 0
    for name, path in sorted(entries.items()):
        size = path.stat().st_size
        total += size
        if size > 2 * 1024**3 or total > 4 * 1024**3:
            raise ValueError('Package size exceeds limit')
        digest = hashlib.sha256()
        count = 0
        with path.open('rb') as stream:
            while chunk := stream.read(65536):
                count += len(chunk)
                if count > size:
                    raise ValueError(f'Package file changed during staging: {name}')
                digest.update(chunk)
        if count != size:
            raise ValueError(f'Package file changed during staging: {name}')
        lines.append(f'{digest.hexdigest()}\t{size}\t{name}\n')
    result = ''.join(lines).encode('ascii')
    if len(result) > 1024 * 1024:
        raise ValueError('Package manifest exceeds limit')
    return result
