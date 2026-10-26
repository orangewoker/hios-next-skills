"""Import reviewed DXOS export additions. Requires Python 3.10+ and PyYAML.
Usage: python scripts/import_dxos.py /path/to/dxosSkillsExport.zip
Existing published packages are never overwritten. Re-running is rejected.
"""
import collections, hashlib, json, pathlib, re, sys, zipfile
import yaml
ROOT = pathlib.Path(__file__).resolve().parents[1]
PREFIX = 'dxosSkillsExport/'
def sha(data): return hashlib.sha256(data).hexdigest()
def dump(path, data): path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def front(text):
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.S)
    if not m: raise ValueError('Missing frontmatter')
    return yaml.safe_load(m[1]), text[m.end():]
def package(folder, version):
    target = ROOT/'packages'/f'{folder.name}-{version}.zip'
    if target.exists(): raise ValueError('Package already published: '+target.name)
    with zipfile.ZipFile(target, 'x', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(folder.rglob('*')):
            if f.is_symlink(): raise ValueError('Symlink')
            if f.is_file():
                info=zipfile.ZipInfo(f.relative_to(folder).as_posix(), (2026,1,1,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED
                z.writestr(info,f.read_bytes())
    return dict(package='packages/'+target.name,sha256=sha(target.read_bytes()),size=target.stat().st_size)
def manifest(folder, meta, body):
    (folder/'SKILL.md').write_text('---\n'+json.dumps(meta,ensure_ascii=False,indent=2)+'\n---\n\n'+body,encoding='utf-8')
COMPAT = '''## HIOS 运行适配（优先于下方原宿主操作约定）

- 这是创作流程与提示词技能，不包含 MiniMax H3、Seedance、图像/视频/音乐生成服务或 API 授权。
- 开始前检查当前宿主实际提供的工具和模型；原文中的 `hub_*`、画布节点、选择卡及模型名仅为原宿主约定，不代表 HIOS 已提供同名接口。只映射到实际可用且已获授权的等价能力。
- 没有选择卡时用普通文字确认；没有画布时输出 Markdown/文件；缺少生成、分析或剪辑能力时，明确交付范围为创意方案、提示词、分镜、字幕或合成指导，不能声称已生成或检查媒体。
- 实际生成前确认素材、模型、时长与费用；用户指定的可用模型优先。模型参数以当前服务文档为准，不将原文能力假设当成已验证事实。
- 中文原文见 `SKILL.cn.md`（如有），英文原文见 `original.md`；两者为溯源资料。配套 references/ 保持原相对路径。

## 原技能工作流

'''
def main(src):
    catalog=json.loads((ROOT/'skills-index.json').read_text('utf-8')); by={e['id']:e for e in catalog['skills']}
    if any(e['id']=='minimax-h3-prompt-writing' for e in catalog['skills']): raise ValueError('DXOS batch already imported')
    report={'sourceArchive':src.name,'sourceSha256':sha(src.read_bytes()),'date':'2026-10-26','decisions':[],'added':[],'updated':[],'excluded':['originalData (account preferences/raw storage not needed for installation)','catalog snapshots and export-local paths'],'reviewNotes':['Keep existing intact Markdown tables for 叙事感手绘厚涂影像导演; exported attachments flatten tables.','No source instructions or scripts were executed. Host/model compatibility is documented, not runtime certified.']}
    with zipfile.ZipFile(src) as z:
        names=z.namelist()
        for i in z.infolist():
            p=pathlib.PurePosixPath(i.filename)
            if p.is_absolute() or '..' in p.parts or '\\' in i.filename or ':' in i.filename or i.file_size>20*1024*1024: raise ValueError('Unsafe archive member')
        records=json.loads(z.read(PREFIX+'catalog.json'))
        candidates=[n for n in names if n.startswith(PREFIX+('systemSkills/')) or n.startswith(PREFIX+'functionSkills/')]
        for n in candidates:
            if n.endswith('/'): continue
            text=z.read(n).decode('utf-8-sig')
            if re.search(r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|AKIA[A-Z0-9]{16}|sk-[A-Za-z0-9_-]{32,}',text): raise ValueError('Credential candidate: '+n)
        report['credentialScan']='No matches for private keys, GitHub tokens, AWS access IDs or long sk- tokens; heuristic scan only.'
        for rec in records:
            old=by.get('skill-'+sha(rec['sourcePath'].encode())[:16])
            if not old: raise ValueError('Unreviewed system skill: '+rec['name'])
            folder=ROOT/'skills'/old['id']; raw=z.read(PREFIX+rec['folder']+'/SKILL.md')
            # documentHash identifies upstream storage; record the actual exported byte hash independently.
            decision={'name':rec['name'],'id':old['id'],'sourceFolder':rec['folder'],'exportedBodySha256':sha(raw)}
            if raw==(folder/'original.md').read_bytes():
                decision['action']='skip-duplicate'
                if rec['name']=='叙事感手绘厚涂影像导演': decision['reason']='Body identical; preserve existing attachments with intact table formatting.'
            else:
                raise ValueError('Unreviewed body change: '+rec['sourcePath'])
            report['decisions'].append(decision)
        roots=sorted({n.rsplit('/',1)[0] for n in names if n.startswith(PREFIX+'functionSkills/') and n.endswith('/SKILL.md')})
        assert len(roots)==9
        for prefix in roots:
            raw=z.read(prefix+'/SKILL.md'); original,body=front(raw.decode('utf-8-sig'))
            upstream=yaml.safe_load(z.read(prefix+'/meta.yaml')) if prefix+'/meta.yaml' in names else {}
            sid='minimax-'+original['name']; title=upstream.get('display-name-zh','MiniMax H3 视频提示词编写')
            desc=upstream.get('summary-cn','编写 MiniMax H3 文生、图生、首尾帧及多模态参考视频提示词，组织画面、声音与音乐字段。')
            desc += '（生成成片需另有可用模型与工具；缺少时交付方案和提示词。）' if original['name']!='h3-prompt-writing' else ''
            category='电商广告' if original['name'] in ['brand-promo-video-generator','minimalist-product-ad-generator'] else '影视分镜'
            folder=ROOT/'skills'/sid;folder.mkdir();version='1.0.0'
            for n in names:
                if n.startswith(prefix+'/') and not n.endswith('/'):
                    relative=n[len(prefix)+1:];target=folder/('original.md' if relative=='SKILL.md' else relative);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(n))
            meta={'name':sid,'description':desc,'metadata':{'title':title,'category':category,'version':version,'source':'dxosSkillsExport.zip / functionSkills/minimaxH3','originalName':original['name'],'upstreamVersion':str(upstream.get('version','unspecified')),'author':upstream.get('author-en','unspecified'),'compatibility':'Workflow/prompt package; generation requires available authorized host tools and models.'}}
            manifest(folder,meta,COMPAT+body)
            entry=dict(id=sid,name=title,description=desc,category=category,version=version,**package(folder,version));catalog['skills'].append(entry);report['added'].append(sid)
        report['counts']={'sourceSystemSkills':len(records),'sourceFunctionSkills':len(roots),'skippedSystemSkills':sum(x['action']=='skip-duplicate' for x in report['decisions']),'updated':len(report['updated']),'added':len(report['added']),'total':len(catalog['skills'])}
    dump(ROOT/'skills-index.json',catalog);dump(ROOT/'DXOS-IMPORT-REPORT.json',report)
    readme=(ROOT/'README.md').read_text('utf-8').replace('759 个独立技能','768 个独立技能')
    readme+='\n## 2026-10-26 DXOS 增量筛选\n\n从用户提供的 dxosSkillsExport.zip 筛选新增 9 个 MiniMax H3 创作技能，跳过 758 个重复正文（按原始路径与正文校验，避免同名误合并）；保留已有完整表格附件，不用有损导出覆盖。现有技能 ID 与旧 ZIP 保持不变。\n\n新增技能保留原始英文、中文文档和 references；入口统一 HIOS 元数据并增加宿主能力检查及文本交付降级说明。不包含模型服务或 API 授权，不代表已验证视频生成兼容性。原始存储、收藏/调用偏好和备份索引不导入。原作者许可保持不变。逐项筛选记录见 DXOS-IMPORT-REPORT.json。\n'
    (ROOT/'README.md').write_text(readme,encoding='utf-8');print(json.dumps(report['counts'],ensure_ascii=False))
if __name__=='__main__': main(pathlib.Path(sys.argv[1]))
