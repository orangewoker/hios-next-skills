# HIOS 社区技能库

768 个独立技能。每项有独立目录、版本、ZIP 和 SHA-256。内容来自用户提供的 skill(1).zip，原文及附件保留；初始分类根据标题关键词生成，可在 HIOS 中调整。

索引：skills-index.json。安装仅下载所选技能，不会自动安装全部。

原技能中的作者及许可声明以原文为准，本仓库未统一授予额外许可。

更新时修改对应 skills/<id>/SKILL.md 和附件，运行 python scripts/rebuild.py <id> <新版本>，再提交 skills、packages 和 skills-index.json。旧包保留，索引指向新版本。

## 2026-10-26 DXOS 增量筛选

从用户提供的 dxosSkillsExport.zip 筛选新增 9 个 MiniMax H3 创作技能，跳过 758 个重复正文（按原始路径与正文校验，避免同名误合并）；保留已有完整表格附件，不用有损导出覆盖。现有技能 ID 与旧 ZIP 保持不变。

新增技能保留原始英文、中文文档和 references；入口统一 HIOS 元数据并增加宿主能力检查及文本交付降级说明。不包含模型服务或 API 授权，不代表已验证视频生成兼容性。原始存储、收藏/调用偏好和备份索引不导入。原作者许可保持不变。逐项筛选记录见 DXOS-IMPORT-REPORT.json。
