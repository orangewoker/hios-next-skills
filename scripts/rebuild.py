"""Publish a new skill or rebuild an existing one into an immutable ZIP."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

from catalog_lib import ID_PATTERN, VERSION_PATTERN, publication_files, with_version

ROOT = Path(__file__).resolve().parents[1]


def rebuild(root, sid, version, *, new=False, category=None):
    root = Path(root).resolve()
    if not re.fullmatch(ID_PATTERN, sid) or not re.fullmatch(VERSION_PATTERN, version):
        raise ValueError('Invalid id/version')
    index_path = root / 'skills-index.json'
    original_index = index_path.read_bytes()
    catalog = json.loads(original_index)
    if catalog.get('schemaVersion') != 1 or not isinstance(catalog.get('skills'), list):
        raise ValueError('Invalid catalog')
    matches = [x for x in catalog['skills'] if x['id'] == sid]
    if len(matches) > 1:
        raise ValueError('Duplicate catalog id')
    entry = matches[0] if matches else None
    if new and entry is not None:
        raise ValueError('Skill already registered; omit --new for updates')
    if entry is None and not new:
        raise ValueError('Unknown skill; use --new for first publication')
    if entry and tuple(map(int, version.split('.'))) <= tuple(map(int, entry['version'].split('.'))):
        raise ValueError('New version must increase')
    folder = root / 'skills' / sid
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError('Skill must be a regular directory')
    manifest_path = folder / 'SKILL.md'
    original_manifest = manifest_path.read_bytes()
    text, meta = with_version(original_manifest.decode('utf-8-sig'), version)
    if meta.get('name') != sid:
        raise ValueError('SKILL.md name must match id')
    description = meta.get('description')
    if not isinstance(description, str) or not description.strip() or len(description) > 2000:
        raise ValueError('Skill description must be 1-2000 characters')
    metadata = meta.get('metadata', {})
    title = metadata.get('title') or (entry or {}).get('name') or sid
    category = category or metadata.get('category') or (entry or {}).get('category')
    if not isinstance(title, str) or not title.strip() or len(title) > 200:
        raise ValueError('Invalid skill title')
    if not isinstance(category, str) or not category.strip() or len(category) > 80:
        raise ValueError('Set metadata.category or pass --category')
    package = root / 'packages' / f'{sid}-{version}.zip'
    if package.exists():
        raise ValueError('Published package cannot be overwritten')
    files = publication_files(folder)
    if not any(p.relative_to(folder).as_posix() == 'SKILL.md' for p in files):
        raise ValueError('Package root requires SKILL.md')
    if len(files) > 2000:
        raise ValueError('Package exceeds HIOS file count limit')
    buffer = io.BytesIO()
    total = 0
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for file in files:
            name = file.relative_to(folder).as_posix()
            data = text.encode('utf-8') if name == 'SKILL.md' else file.read_bytes()
            total += len(data)
            if total > 50 * 1024 * 1024:
                raise ValueError('Package exceeds HIOS extracted size limit')
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    data = buffer.getvalue()
    if len(data) > 20 * 1024 * 1024:
        raise ValueError('Package exceeds HIOS download limit')
    updated = dict(entry or {}, id=sid, name=title, description=description, category=category,
                   version=version, package='packages/' + package.name,
                   sha256=hashlib.sha256(data).hexdigest(), size=len(data))
    if entry is None:
        catalog['skills'].append(updated)
    else:
        entry.update(updated)
    index_bytes = (json.dumps(catalog, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    if len(index_bytes) > 8 * 1024 * 1024:
        raise ValueError('Catalog exceeds HIOS index limit')
    # Validate all input before touching the source tree, index, or immutable ZIP.
    package.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        with package.open('xb') as stream:
            created = True
            stream.write(data)
        manifest_path.write_bytes(text.encode('utf-8'))
        index_path.write_bytes(index_bytes)
    except Exception:
        if created:
            manifest_path.write_bytes(original_manifest)
            index_path.write_bytes(original_index)
            package.unlink(missing_ok=True)
        raise
    return updated


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('id')
    parser.add_argument('version')
    parser.add_argument('--new', action='store_true', help='Register a first publication')
    parser.add_argument('--category', help='Override the catalog category')
    args = parser.parse_args()
    result = rebuild(ROOT, args.id, args.version, new=args.new, category=args.category)
    print(f"Built {result['id']} {result['version']} ({result['size']} bytes). Review and commit skills/, packages/, skills-index.json.")
