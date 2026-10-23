"""Rebuild one skill into an immutable versioned ZIP and update its catalog."""
import sys,pathlib,json,re,zipfile,hashlib
root=pathlib.Path(__file__).resolve().parents[1]
sid,version=sys.argv[1:3]
if not re.fullmatch(r'[a-z0-9][a-z0-9._-]{1,95}',sid) or not re.fullmatch(r'\d+\.\d+\.\d+',version):raise ValueError('Invalid id/version')
catalog=json.loads((root/'skills-index.json').read_text(encoding='utf-8'))
entry=next(x for x in catalog['skills'] if x['id']==sid)
if tuple(map(int,version.split('.'))) <= tuple(map(int,entry['version'].split('.'))):raise ValueError('New version must increase')
folder=root/'skills'/sid
manifest=folder/'SKILL.md';text=manifest.read_text(encoding='utf-8');match=re.match(r'^---\n(.*?)\n---',text,re.S)
meta=json.loads(match[1]);meta['metadata']['version']=version
package=root/'packages'/f'{sid}-{version}.zip'
if package.exists():raise ValueError('Published package cannot be overwritten')
manifest.write_text('---\n'+json.dumps(meta,ensure_ascii=False,indent=2)+'\n---'+text[match.end():],encoding='utf-8')
with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
 for file in sorted(folder.rglob('*')):
  if file.is_symlink():raise ValueError('Symlinks not supported')
  if file.is_file():z.write(file,file.relative_to(folder).as_posix())
entry.update(version=version,package='packages/'+package.name,sha256=hashlib.sha256(package.read_bytes()).hexdigest(),size=package.stat().st_size,name=meta['metadata']['title'],category=meta['metadata']['category'],description=meta['description'])
(root/'skills-index.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Built {sid} {version}. Review and commit skills/, packages/, skills-index.json.')
