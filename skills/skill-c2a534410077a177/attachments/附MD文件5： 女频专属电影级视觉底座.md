# 附MD文件5： 女频专属电影级视觉底座

## #做什么

本模块为女频短剧漫剧的专属电影级视觉底座附MD。

解决女频短剧在AI生成时“非专业塑料质感强、光影层次不足、角色面部一致性不足”的痛点。

在保留【提示词 | 电影级物理参数底座】物理光学底座的前提下，强制替换为“唯美通透系”数字摄影机参数。

## #需要什么输入

**最少提供：**

- 主MD下发的分镜剧本：古装女频 / 现代女频 / 情感女频。
- 主角三视图与关键道具。
- 情绪基调与场景上下文。
- 目标画面比例：9:16竖屏。

**可选提供：**

- 是否需要输出视频脚本、Prompt清单、视觉方案。
- 上下游分镜、提示词、视觉方案结果。
- 目标时长与制作规格。
- 是否需要中日双语字幕。

## #怎么做

### 一、强制调用提示词Skill

必须优先调用以下父级/元认知 Skill：

**【提示词**】英文 slugID：libtv-user-generated/award-winning-cinematic-prompter-074be3667ece41bc8993cea11c99240e\
对应显示名：提示词 | 电影级物理参数底座

若未调用提示词Skill，禁止输出任何女频专属电影级视觉底座参数。

### 二、女频化参数替换

在生成任何Prompt时，严禁使用【提示词】Skill默认的胶片颗粒参数。必须强制替换为女频唯美数字电影参数：

`Shot on Arri Alexa Mini LF, Zeiss Supreme Prime lenses, soft diffused lighting, cinematic warm glow, shallow depth of field, creamy bokeh, hyper-realistic but flawless skin texture, soft pastel color palette, no film grain, no harsh shadows, no neon, no cheap CGI.`

### 【帧率与曝光规范】

统一锁定全片帧率，标准电影感为 24fps，短剧强节奏可为 30fps（需提前确认）。\
曝光参数必须形成模板：如 `ISO 400, f/2.8, 1/50s`（胶片感）或 `f/1.8, 1/60s`（柔光人像）。严禁出现高光过曝和死黑阴影。

### 【全局色彩LUT校准铁律】

多镜头拼合时，严禁画面色彩各自为政（如一段冷蓝、一段暖黄）。

- 必须在视觉底座中设定专属的“色彩LUT参数”（如：青橙分离、低饱和度胶片感、黑位压暗）。
- 每一镜的Prompt必须强制包含统一的光影色彩描述，如：`Cinematic color grading, consistent LUT, unified contrast and saturation.`
- 交付物中必须明确包含一份《全片色彩统一性规范报告》。

### 三、关键防崩校验

- 必须包含 `flawless skin texture`，保证皮肤细腻通透。
- 必须包含 `no film grain`，女频要的是高清唯美，不能加颗粒。
- 必须包含 `soft diffused lighting`，柔光，营造梦幻氛围。
- 必须包含 `no harsh shadows`，面部不允许有死黑阴影。
- 必须包含 `no cheap CGI`，防止非专业塑料质感。

### 四、执行原则

- 女频专属视觉底座必须与【顶级大导演思维】的戏剧张力分析保持一致。
- 如剧本出现激烈动作或情绪高点戏，导致画面需要强对比度时，必须停下来询问用户优先保唯美还是保冲突张力。
- 任何下游分镜、Prompt转写、视频生成环节均不得违反本模块规则。

## #产出什么

最终交付：

- 带有女频唯美数字电影参数的分镜Prompt
- 视频脚本
- Prompt清单
- 视觉方案
- 女频专属电影级视觉底座参数清单
- 负面Prompt禁则清单
- 适配AI视频工具生成链路

## #什么时候问你

出现以下情况时，必须停下来问用户：

- 剧本出现激烈动作或情绪高点戏，需要强对比度时，询问优先保唯美还是保冲突张力。
- 用户要求使用非女频唯美参数。
- 用户要求输出视频脚本、Prompt清单、视觉方案，但缺少关键输入。
- 本模块与上游主SKILL、提示词Skill或其他附MD规则冲突。