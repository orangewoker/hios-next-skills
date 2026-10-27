"""Shared manifest and publication-file rules; not a skill runtime dependency."""
import json
import re
from pathlib import Path

import yaml

ID_PATTERN = r'[a-z0-9][a-z0-9._-]{1,95}'
VERSION_PATTERN = r'\d+\.\d+\.\d+'
IGNORED_DIRS = {'__pycache__', '.git', '.pytest_cache', 'node_modules'}
IGNORED_FILES = {'.DS_Store', 'Thumbs.db', 'desktop.ini'}


def manifest(text):
    match = re.match(r'\A\ufeff?---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)', text, re.S)
    if not match:
        raise ValueError('SKILL.md requires YAML or JSON frontmatter')
    meta = yaml.safe_load(match[1])
    if not isinstance(meta, dict) or not isinstance(meta.get('metadata', {}), dict):
        raise ValueError('Skill metadata must be an object')
    if not isinstance(meta.get('metadata', {}).get('hios', {}), dict):
        raise ValueError('metadata.hios must be an object')
    return meta, match, match[1].lstrip().startswith('{')


def version_of(meta):
    metadata = meta.get('metadata', {})
    return str(metadata.get('hios', {}).get('version') or metadata.get('version') or '1.0.0')


def with_version(text, version):
    meta, match, is_json = manifest(text)
    if version_of(meta) == version:
        return text, meta
    metadata = meta.setdefault('metadata', {})
    if isinstance(metadata.get('hios'), dict) and 'version' in metadata['hios']:
        metadata['hios']['version'] = version
    else:
        metadata['version'] = version
    front = json.dumps(meta, ensure_ascii=False, indent=2) if is_json else yaml.safe_dump(
        meta, allow_unicode=True, sort_keys=False, width=2000).rstrip()
    return '---\n' + front + '\n---\n' + text[match.end():], meta


def publication_files(folder):
    """Never include generated caches, and never follow symlinks."""
    folder = Path(folder)
    files = []

    def visit(directory):
        for path in sorted(directory.iterdir()):
            if path.name in IGNORED_DIRS or path.name in IGNORED_FILES or path.suffix in {'.pyc', '.pyo'}:
                continue
            if path.is_symlink():
                raise ValueError('Symlinks not supported: ' + str(path))
            relative = path.relative_to(folder).as_posix()
            if any(c in relative for c in ('\\', ':')):
                raise ValueError('Unsupported package path: ' + relative)
            if path.is_dir():
                visit(path)
            elif path.is_file():
                files.append(path)
            else:
                raise ValueError('Only regular files supported: ' + relative)

    visit(folder)
    return sorted(files, key=lambda p: p.relative_to(folder).as_posix())
