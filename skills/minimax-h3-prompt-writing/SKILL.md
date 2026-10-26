---
{
  "name": "minimax-h3-prompt-writing",
  "description": "编写 MiniMax H3 文生、图生、首尾帧及多模态参考视频提示词，组织画面、声音与音乐字段。",
  "metadata": {
    "title": "MiniMax H3 视频提示词编写",
    "category": "影视分镜",
    "version": "1.0.0",
    "source": "dxosSkillsExport.zip / functionSkills/minimaxH3",
    "originalName": "h3-prompt-writing",
    "upstreamVersion": "unspecified",
    "author": "unspecified",
    "compatibility": "Workflow/prompt package; generation requires available authorized host tools and models."
  }
}
---

## HIOS 运行适配（优先于下方原宿主操作约定）

- 这是创作流程与提示词技能，不包含 MiniMax H3、Seedance、图像/视频/音乐生成服务或 API 授权。
- 开始前检查当前宿主实际提供的工具和模型；原文中的 `hub_*`、画布节点、选择卡及模型名仅为原宿主约定，不代表 HIOS 已提供同名接口。只映射到实际可用且已获授权的等价能力。
- 没有选择卡时用普通文字确认；没有画布时输出 Markdown/文件；缺少生成、分析或剪辑能力时，明确交付范围为创意方案、提示词、分镜、字幕或合成指导，不能声称已生成或检查媒体。
- 实际生成前确认素材、模型、时长与费用；用户指定的可用模型优先。模型参数以当前服务文档为准，不将原文能力假设当成已验证事实。
- 中文原文见 `SKILL.cn.md`（如有），英文原文见 `original.md`；两者为溯源资料。配套 references/ 保持原相对路径。

## 原技能工作流

# H3 Prompt Writing

## Workflow

1. Identify the input mode: T2VA, I2VA, FL2VA, L2VA, or full-reference Ref2VA.
2. For base text/keyframe modes, read `references/base-en.txt` and follow its final prompt structure.
3. For full-reference mode, read `references/ref-en.txt` and follow its six-section rewrite format.
4. Preserve the exact field names, section order, labels, and timing notation from the selected guide.

## Base Modes

- T2VA: build the full audiovisual timeline from text.
- I2VA: start from the first frame and develop forward from it.
- FL2VA: describe the continuous path between the first and last frames.
- L2VA: infer a plausible opening and converge to the supplied last frame.

Use `integrated_multimodal_description`, `overall_soundscape`, and `non_diegetic_music` in the order shown in `references/base-en.txt`.

## Full-Reference Mode

Ref2VA rewrites use `subject_definitions`, `summary`, `retention_analysis`, `detailed_description`, `overall_soundscape`, and `non_diegetic_music` in that order. Reference labels stay consistent across all sections.

Read `references/ref-en.txt` for label rules, retention analysis, and complete examples.

## Output Rules

- Write rewrite sections in English; preserve dialogue, lyrics, and visible scene text in their original language.
- Describe each shot by composition, subjects, environment, actions, camera, sound, and the exact point where referenced content appears.
- Avoid plot summaries, unresolved reference labels, and timing that does not match the requested duration.
