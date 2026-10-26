---
{
  "name": "minimax-co-op-game-intro-generator",
  "description": "根据玩家信息、角色参考图和视觉风格，完成首图确认与界面动效设计，输出双人游戏开场视频。（生成成片需另有可用模型与工具；缺少时交付方案和提示词。）",
  "metadata": {
    "title": "双人游戏开场视频生成器",
    "category": "影视分镜",
    "version": "1.0.0",
    "source": "dxosSkillsExport.zip / functionSkills/minimaxH3",
    "originalName": "co-op-game-intro-generator",
    "upstreamVersion": "0.1.5",
    "author": "MiniMax Hub",
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

# Co-op Game Intro Generator

Use this Skill when the user wants a co-op game intro video and wants to confirm the visual direction with one image before generating the final H3 video. The workflow collects style, player names, game title, and optional character refs, then creates a framework-preserving confirmation image before generating the H3 video.

## Required References

These two templates are mandatory runtime inputs, not optional background notes:

- Use `references/h3-confirmation-image-template.md` when building the confirmation-image prompt in STEP 3 and generating the first confirmation image in STEP 4. Fill the template fields in order and do not skip framework, palette, UI, character, typography, layout, or negative-constraint fields.
- Use `references/h3-video-prompt-template.md` when refilling the final Minimax H3 video prompt in STEP 6. Fill the template from the approved confirmation image, player/game data, final UI copy, event timing, motion directions, and negative constraints.

If either template is unavailable, stop and report that the Skill package is incomplete instead of improvising a different prompt structure.

## STEP 1: Ask for visual style
Ask the user to choose a preset style or enter a custom style. This style has top priority and controls supplemental style language, palette language, background texture, character rendering, expression, outfit direction, UI colors, button/icon style, and typography texture.

## STEP 2: Collect player and game info
Collect PLAYER 1 name, PLAYER 2 name, and game title. If the user provides character images, use PLAYER 1 and PLAYER 2 refs only for identity mapping: recognizable face silhouette, hairstyle, glasses, relative facial proportions, and distinctive traits. Do not inherit photographic realism, skin texture, real-world lighting, camera quality, or the original image style; redesign the face into the selected visual style while preserving identity anchors.

## STEP 3: Build the GPT confirmation-image prompt
Load and follow `references/h3-confirmation-image-template.md` as the required prompt skeleton. Use a fixed framework + dynamic style fill + palette-linked prompt structure:

1. **Overall Style**: always preserve game main menu UI, high-quality game promo poster, deep UI-character integration, modern commercial game UI design, strong visual impact, clean composition, and avoid over-decoration. Add other style terms from the selected style.
2. **Color Palette**: always follow: xx as main color, xx as UI body color, xx as text color, xx as functional accent color, red as danger accent, palette within five colors, high-contrast color blocking, fresh modern look, and xx-style color language. All later UI/button/icon/type colors must match this palette.
3. **Composition**: preserve 16:9 landscape, full-frame background, x centered characters, UI around rather than blocking them, upper-left player card, right-side vertical menu, bottom caution tape, a few corner graffiti accents, Z reading path, enough negative space, clear hierarchy, and Continue as the visual focus.
4. **Background**: follow pure xx background, slight xx texture, large solid-color blank space, texture only as detail, avoid heavy dirt/dense scratches/too much ink splash/large paint splatter, a little black spray-paint edge detail, clean modern premium UI-first background. Derive xx and additions from the selected style.
5. **Character Style**: strictly expand according to the selected style. Use source text only as dimension guidance, not fixed style.
6. **Character A**: facial features from character image 1; expression, rendering, and outfit follow selected style; optional compatible outfit dimensions include khaki short jacket, black inner layer, black cargo pants, brown boots, adventurer outfit. Fixed action: cross-legged, hands on floor, slight backward lean, looking up.
7. **Character B**: facial features from character image 2; expression, rendering, and outfit follow selected style; optional compatible outfit dimensions include green thick jacket, burgundy padded lining, white inner shirt, black pants, thick boots. Fixed action: cross-legged, hands in front of legs, slight forward lean, looking at camera.
8. **Lighting**: preserve top main light, upper-left warm/cool fill, soft bottom ambient reflection, soft shadows, contact shadows, rim light, high-quality GI, and natural character-background integration. Choose warm/cool from style.
9. **Game UI**: preserve console game menu, unified button size, rounded rectangles, slight tilt, minimal spray/drip elements, modern clean sticker design, readability, and no over-decoration. Button body, outline, and glow colors must match the palette.
10. **Layout Rules**: preserve horizontal long buttons, unified width/height/radius, width adapted to text, single-line titles only, no wrapping, no two-line titles, centered text, consistent margins and spacing.
11. **Buttons**: adapt colors from palette and icons from selected style. Continue is the large visual-center highlighted button with hover/click state. Start New Game is above Continue. Settings remains visually consistent. Exit Game uses danger/exit cue with red accents allowed.
12. **Player Cards**: preserve upper-left x-player info cards, irregular rectangular card, outline, slight edge damage, left logo/icon, right three-level info (PLAYER label, nickname, READY), bold sans-serif, industrial sticker design. Card colors, outline, READY color, and logo style follow palette and selected style.
13. **Icon System**: derive icon style from selected style, colors from palette, and keep one-row-only, no wrapping, no stacking, at most one row per UI block, minimal quantity, unified size, never stealing focus.
14. **Typography**: preserve bold sans-serif, all caps, Anton/Impact/Burbank/Tungsten-like weight, tight tracking, heavy strokes, clear hierarchy, single-line typography, no wrapping, button width adapts to text, never two-line menu titles. Colors and texture follow palette and selected style.

## STEP 4: Generate the first confirmation image
Generate only one confirmation image from the filled `references/h3-confirmation-image-template.md`. Preserve the framework structure, while making the selected style visibly dominant.

## STEP 5: Wait for approval
Do not generate video until the user approves the image. If the user changes style, names, game title, identity, or image direction, return to the image prompt step.

## STEP 6: Refill video prompt and generate with Minimax H3
After approval, load `references/h3-video-prompt-template.md` and refill the final video prompt with confirmed style, character refs, player names, game title, UI text, event timing, motion directions, and negative constraints. Generate the final video with Minimax H3.

## STEP 7: Repair common failures
If text is unreadable, reduce on-screen text. If identities swap, strengthen names, positions, and colors. If faces drift, reuse uploaded refs and explicitly preserve identity anchors, hairstyle, and outfit anchors while keeping the face rendered in the selected visual style. If the selected style is weak, rewrite Overall Style, Color Palette, Character Style, Background, Game UI, Buttons, Icons, and Typography instead of changing layout framework.
