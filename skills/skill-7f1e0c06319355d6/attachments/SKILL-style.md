# 故事板 Skill · 画面风格与电影级词库分册

> 📁 **文件说明**：本文件是故事板 Skill 的**画面风格参考词库分册**，承载步骤4「电影级增强」的**完整可抄英文词块**。配套 `SKILL.md`（流程主干）使用；当用户明确要求「电影感」、需叠加五变量技术词块时，**执行前先加载本文件取词，逐字复用，不得凭印象复述**。

---

## 电影级增强（完整词库）

> 本块由 `SKILL.md` 步骤4 拆分而来，原文未删、只搬位置。

> 🔴 **先纠正一个误读（记死）**：**「纪实」本身就是电影风格的一种**（纪录片、新现实主义、日常凝视这一路），它**不是「不写光、不写焦段」**。纪实风同样要写死「光源＋方向＋色温＋焦段」，只是它的**调色克制、光质自然、不做戏剧化**——所以「默认纪实」与「电影级镜头指令」**不矛盾**：纪实是**调性**（克制平实），镜头指令是**技术底座**（光/焦段/景深照写）。别再把「纪实」误当成「不用写光」。

**🔴 核心结论（一句话记死）**：「电影感」不是写「高级/史诗/电影感」这类形容词，而是写 **5 个可控变量：镜头（lens）→ 灯光（lighting）→ 调色（grade）→ 胶片（stock/纹理）→ 运镜（movement）**。五变量写成一段技术词块，效果远超堆十句情绪形容词。多来源一致：**「密度＞长度」「具名光源＞具名情绪」「报导演名只占 20%，技术簇占 80%」**。

**一、五变量具体英文词（可直接抄，来源：domer.io 七层 + Veo3 五层 + sureprompts 导演拆解）**

变量怎么写关键英文词**镜头/焦段**写焦段+景深+光学签名`35mm anamorphic`（变形宽银幕，椭圆光斑/横光晕）、`85mm`（压缩肖像）、`shallow depth of field`（浅景深）、`oval bokeh`、`vintage spherical prime`**灯光**写「光源+方向+质量+色温」，不写「明亮/戏剧」光源 `practical lamp`/`window`/`neon sign`/`overcast sky`；方向 `camera-left`/`back`/`top`；质量 `hard`/`soft`；色温 `warm tungsten`/`cool moonlight`/`sodium vapor`。例：`warm tungsten work lamp from camera left, hard shadow`**调色**写具体分级名，不写「好看的颜色」`teal-and-orange`（青橙）、`bleach bypass`（漂白留银）、`desaturated`、`lifted blacks`、`day-for-night`、`cross-processed`**胶片/纹理**写胶片型号+颗粒+光晕`Kodak Vision3 500T`、`Kodak Portra 400`、`Fujifilm Eterna`、`CineStill 800T`、`fine 35mm film grain`、`halation around highlights`、`gate weave`**运镜**写具体运动+速度词`slow push-in`、`handheld drift`、`slow dolly-in`、`crane up`、`orbit`

**二、🔴 本厂铁律：Seedance 吃「技术词」，不吃「导演名」**

来源 invideo 官方 FAQ 明确：**Kling、Seedance 2.0 对「报导演名」响应差，对「技术簇」响应好**——写 `Roger Deakins 风格` 不如写 `motivated practical key, warm shadow fill, 2.40:1, shallow depth of field`。**所以本厂视频侧（Seedance）画面风格一律写技术词簇，不写导演名**。**图片侧（img2 / Lib Image 2.5 Pro / Seedream 等图像模型）则相反——图像模型吃导演名/摄影师名/胶片型号这类实体锚点**（LiblibAI 官方口径：AI 不认识「风/感」抽象词，只认导演名、摄影师名、设备型号、出版物封面等实体锚点），所以三视图模板里的「是枝裕和电影质感」是对的、保留。**一句话记死：视频用技术簇、图片用导演名锚。**

**三、导演风格 → 技术簇拆解表（要用某导演的感觉，就抄右边，不写名字）**

导演/风格拆成的技术词簇（抄这段）**王家卫**`split-toned amber and emerald, slow shutter motion smear, handheld drift, neon signage bokeh, 2.40:1 hard matte`**维伦纽瓦（银翼杀手2049）**`cold desaturated grade, teal-and-orange split, fog haze, slow lateral track, negative space, low-key`**Roger Deakins**`motivated practicals, warm shadow fill, hard side light, subtle lens distortion, tonal restraint`**Wes Anderson**`flat telephoto, centered symmetry, pastel palette, 90-degree angles`**David Fincher / Khondji**`desaturated cold tones, deep shadows, controlled symmetry, 85:15 dark-to-light ratio`

**四、10 个可直接抄的「LUT 风格块」（来源 Veo3 官方调色指南，英文原文，粘贴到提示词末尾即可）**

- **青橙大片**：`Teal-and-orange cinema grade: warm orange skin tones against deep teal-blue shadows, high but smooth contrast, rolled-off highlights, anamorphic 35mm, subtle blue lens flare, fine grain.`
- **怀旧 Super-8**：`Vintage Super-8 home-movie look: warm faded amber grade, lifted milky blacks, low saturation, heavy grain, slight gate weave, soft vignetting, golden afternoon light.`
- **霓虹夜景（CineStill 800T）**：`CineStill 800T tungsten night look: cool blue base with saturated magenta and cyan neon practicals, strong red halation around every light source, crushed shadows, wet reflective streets, 35mm grain.`
- **漂白留银（惊悚/战争）**：`Bleach-bypass grade: desaturated, silver-retained, high contrast with crushed inky blacks and harsh metallic highlights, cold steel-blue cast, gritty texture, hard top light.`
- **日拍夜**：`Day-for-night grade: underexposed two stops, deep blue moonlit cast, cool shadows, a single warm window or streetlamp as the only warm source, soft contrast, subtle grain.`
- **黑白电影**：`High-contrast black-and-white film: rich tonal range, deep blacks with detail, glowing highlights, dramatic side key light, 35mm grain, classic noir chiaroscuro.`
- **柔和独立片（Eterna）**：`Fujifilm Eterna emulation: muted low-contrast pastel grade, gentle desaturated greens, soft natural window light, lifted shadows, delicate skin tones, minimal grain.`
- **黄金时刻浪漫**：`Warm golden-hour grade: honey-amber highlights, long backlit lens flares, atmospheric haze, soft glowing skin, low contrast, Portra-style warmth, 35mm shallow depth of field.`
- **科幻冷峻**：`Cool clinical sci-fi grade: desaturated steel-blue and cyan palette, single warm practical accent, clean high-key fill, sharp anamorphic optics, faint blue halation.`
- **西部/沙漠史诗**：`Sun-baked Western grade: warm dusty ochre and teal sky separation, high overhead sun, hard shadows, slightly faded blacks, fine grain, wide anamorphic vista, heat haze.`

**五、写法顺序（一条画面风格块的标准组装）**

`[镜头] + [灯光源/方向/质量/色温] + [调色名] + [胶片型号+颗粒] + [运镜]`。示例（一句话拼完）：

> `Shot on 35mm anamorphic, shallow depth of field, warm tungsten practical lamp from camera left, teal-and-orange grade with lifted blacks, Kodak Vision3 500T, fine film grain, slow push-in.`

**六、三条避坑（写电影感时最容易踩）**

1. **不要写** `HDR` **/** `ultra-realistic` **/** `vibrant`——这几个词把画面推向「数码塑料感」，正好反着「胶片 filmic curve」走。
2. **不要堆矛盾胶片**：`Portra 400 + bleach bypass + Technicolor` 混在一个提示词里，模型直接糊，一次只选一个风格。
3. **一条只一个主运镜**：`push-in + orbit + whip pan` 叠加必出糊（呼应已有铁律「一镜只取一个方向词」）。

**七、硬约束（叠加时必须遵守，与上文一致）**：① 只写技术词，**不写「高级/史诗/电影感」这类形容词**；② 一次只选一个调色风格，**不堆矛盾胶片**；③ **一镜只一个运镜方向**，不叠加；④ 不写 `HDR / ultra-realistic / vibrant`。