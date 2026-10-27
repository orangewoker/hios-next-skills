"""Validate every catalog entry, archive hash, metadata and source tree."""
import hashlib,json,pathlib,re,zipfile
from catalog_lib import manifest, publication_files, version_of
root=pathlib.Path(__file__).resolve().parents[1]
index=json.loads((root/'skills-index.json').read_text('utf-8')); seen=set()
for e in index['skills']:
    sid=e['id']; assert sid not in seen;seen.add(sid)
    assert re.fullmatch(r'[a-z0-9][a-z0-9._-]{1,95}',sid)
    assert re.fullmatch(r'\d+\.\d+\.\d+',e['version'])
    path=root/e['package'];data=path.read_bytes()
    assert len(data)==e['size'] and hashlib.sha256(data).hexdigest()==e['sha256'],sid
    folder=root/'skills'/sid
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(set(z.namelist()))
        assert set(z.namelist())=={p.relative_to(folder).as_posix() for p in publication_files(folder)},sid
        for n in z.namelist():
            p=pathlib.PurePosixPath(n);assert not p.is_absolute() and '..' not in p.parts and '\\' not in n and ':' not in n
            packed,source=z.read(n),(folder/n).read_bytes()
            if packed!=source:
                # Older imported text was normalized by Git before byte-preserving
                # attributes existed. Archive SHA-256 remains checked verbatim.
                assert packed.decode('utf-8-sig').replace('\r\n','\n')==source.decode('utf-8-sig').replace('\r\n','\n'),(sid,n)
        text=z.read('SKILL.md').decode('utf-8-sig').replace('\r\n','\n');meta=manifest(text)[0]
        assert meta['name']==sid and version_of(meta)==e['version'],sid
        assert meta['description']==e['description']
        if sid.startswith('minimax-'):
            for f in folder.rglob('*'):
                if f.is_file() and f.suffix in ['.md','.txt']:
                    for ref in re.findall(r'`(references/[^`\s]+\.(?:md|txt))`',f.read_text('utf-8')):
                        assert (folder/ref).is_file(),(sid,ref)
print(f'PASS: {len(seen)} catalog entries, ZIPs, SHA-256, sizes, manifests and source trees; new reference paths resolved.')
