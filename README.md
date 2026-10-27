# HIOS 社区技能库

769 个独立技能。每项有独立目录、版本、ZIP 和 SHA-256。包含用户提供的 skill(1).zip、DXOS 导入内容与独立开发技能，原文及附件保留；初始分类根据标题关键词生成，可在 HIOS 中调整。

索引：skills-index.json。安装仅下载所选技能，不会自动安装全部。

原技能中的作者及许可声明以原文为准，本仓库未统一授予额外许可。

发布前安装工具依赖：`python -m pip install -r scripts/requirements.txt`（仅仓库维护者需要）。
首次上架：`python scripts/rebuild.py <id> 1.0.0 --new`，入口提供 `metadata.title`、`metadata.category`、`metadata.version`。
更新时修改对应 skills/<id>/SKILL.md 和附件，运行 `python scripts/rebuild.py <id> <新版本>`，再提交 skills、packages 和 skills-index.json。支持 YAML / JSON frontmatter，旧包保留，索引指向新版本。包内直接放 SKILL.md 和附件，不包含外层文件夹或运行缓存。
验证：`python scripts/validate.py`、`python -m unittest discover -s tests -p "test_*.py"`。

## Blender 家具与空间（DSH）

`blender-furniture-spaces`，分类「空间建筑」，独立版本 `1.0.0`。
在 HIOS「插件管理 → 技能 → 探索」刷新并安装，然后在 DSH 选择 `/blender-furniture-spaces`。
无需旧 Blender MCP，也不需要复制到 DSH_HOME；首次需按技能的 `references/connection.md` 安装并启用本地 Blender 桥接插件。
支持软包曲面、程序布料/木材、家具与空间建模、检查点、渲染和可编辑 .blend 保存；参考图分析取决于当前 DSH 模型/图像工具是否支持视觉，不额外配置视觉 API。
HIOS 主程序不内置此技能。旧版如残留同名内置技能，应更新主程序的退役技能过滤，不能覆盖用户或插件提供的技能。
公开包只含技能源码与说明，不含个人配置、会话令牌、用户参考图或建模工程。

## 2026-10-26 DXOS 增量筛选

从用户提供的 dxosSkillsExport.zip 筛选新增 9 个 MiniMax H3 创作技能，跳过 758 个重复正文（按原始路径与正文校验，避免同名误合并）；保留已有完整表格附件，不用有损导出覆盖。现有技能 ID 与旧 ZIP 保持不变。

新增技能保留原始英文、中文文档和 references；入口统一 HIOS 元数据并增加宿主能力检查及文本交付降级说明。不包含模型服务或 API 授权，不代表已验证视频生成兼容性。原始存储、收藏/调用偏好和备份索引不导入。原作者许可保持不变。逐项筛选记录见 DXOS-IMPORT-REPORT.json。
