# 本地连接与安装

在 HIOS「插件管理 → 技能 → 探索」安装 **Blender 家具与空间** 后，DSH 通过 HIOS 已安装技能 provider 加载整个资源目录，不需要再复制到 DSH_HOME。首次使用选择 `/blender-furniture-spaces`；已打开的会话需要重新加载技能列表或新建会话。

也支持独立 DSH 的原生技能目录。执行工具是 DSH 的 PowerShell/终端，不需要注册虚构的 `blender_*` MCP 工具。Node 只用标准库，HIOS 启动 DSH 时已将其管理的 Node 加入 PATH；Blender 插件使用 Blender 自带 Python。Windows 自动检测优先使用 PowerShell 7，未安装时回退系统自带 Windows PowerShell。

## 第一次安装

市场安装只解压技能，不会自动运行脚本或启用 Blender 插件。首次需要执行下面的安装命令，并在 Blender 启用插件；不要求安装旧 HIOS Blender MCP 或 BlenderHub。

```powershell
node "<技能目录>/scripts/blender.mjs" doctor
node "<技能目录>/scripts/blender.mjs" install --blender "实际/blender.exe"
```

安装器根据真实 Blender `--version` 选择用户配置目录，仅安装独立 `dsh_blender_bridge.py`，不会更改 BlenderHub 或其他插件。首次会建立 `~/.dsh-blender/settings.json`，默认输出 `~/Documents/DSH-Blender`；可以通过安装参数 `--workspace "绝对路径"` 选择目录。更新已有插件文件会保留时间戳备份。

安装后有两种启用方式：

- Blender 首选项 → 插件 → 刷新，启用 **DSH Local Modeling Bridge**。或者在 Blender Python 控制台执行安装器返回的 `enableCommand`。
- 若当前 Blender 已运行 BlenderHub Bridge，可显式执行 `install --blender "..." --enable-via-blenderhub --pid 实际PID`。控制器会核对本机端口 8877 的 `/ping` PID，再请求启用新插件；不修改原插件代码。

没有 BlenderHub 时只安装，不尝试 UI 键盘注入，也不自动重启。启用后重跑 `doctor`。

技能升级后，如果安装器返回 `restartRequiredForAlreadyLoadedUpdate: true`，已加载的桥接插件仍是旧代码。保存用户工作后，在 Blender 首选项停用再启用该插件（或由用户自行重启 Blender），再继续建模；不要将“文件已复制”当作“运行代码已更新”。

## 命令

所有命令用 `node "<技能目录>/scripts/blender.mjs" 命令 ...`：

| 命令 | 参数 | 意义 |
| --- | --- | --- |
| `doctor` | `--pid PID` 可选 | 自动检测 Blender、连接及工作区 |
| `install` | `--blender 路径`、`--workspace 路径`、`--enable-via-blenderhub --pid PID` | 安装到对应 Blender 用户目录 |
| `inspect` | `--scene 场景名` 可选 | 查询 scene、几何、位置、修改器、材质与范围 |
| `checkpoint` | `--label 标签` | 保存版本化副本，不切换原文件路径 |
| `exec` | `--file Python文件`、`--request-id 稳定ID`、`--no-checkpoint` | 主线程执行，默认先检查点 |
| `render` | `--output PNG`、`--scene`、`--camera`、`--width`、`--height`、`--engine keep/eevee/cycles`、`--samples` | 渲染，之后恢复原渲染配置 |
| `save` | `--output BLEND` | 保存副本；拒绝覆盖 |
| `job` | `--id ID` | 查询之前的调用；不会重放 |

所有连接命令可加 `--pid`。`--timeout` 为轮询等待的秒数，默认 180；超时返回 job ID，Blender 内运行不会被强行终止。请求 ID 去重在单次插件进程生命期内有效，重启后旧 ID 不可作为跨进程完成证据。`exec` 参数与文件内容改变后必须用新 request ID。

插件只监听 `127.0.0.1` 随机端口，令牌保存在本账户 `~/.dsh-blender/sessions/bridge-PID.json`，控制器不打印它。拒绝带浏览器 Origin 的请求；所有 `bpy` 调用由 `bpy.app.timers` 主线程执行，HTTP 线程只排队与查询。不要把会话文件放入技能 ZIP、日志或版本库。

技能安装目录保持只读：任务脚本、模型、渲染、配置和会话都放在任务工作区或 `~/.dsh-blender`，不写回技能目录。工具库由桥接直接编译源码，不生成 `lib/__pycache__`，以免影响市场的本地修改保护和后续升级。

## 故障定位

- 没有连接：确认启用的是当前版本 Blender 的插件，而不是只装进旧版本目录。
- 多进程：用 `doctor` 查实际 PID，再指定 `--pid`。
- job 失败：查看返回的 Python traceback；脚本可能有部分修改。先 `inspect` 再最小修正，不把整个文件盲目重跑。
- 超时：查询原 job。长时间渲染期间界面可能暂时不可交互，不据此自动重启 Blender。
- 外部贴图：核对文件路径与材质图像节点，最终打包进 `.blend`；本技能的程序材质无需外部贴图。

## 安装给 DSH

```powershell
node "<技能目录>/scripts/install-dsh.mjs" --home "实际DSH_HOME"
# 已安装时，显式加 --update，旧版会保存到该 home 的 skill-backups/
```

也可把整个 `blender-furniture-spaces` 文件夹（不能只有 SKILL.md）放进目标 `DSH_HOME/skills/`，或者用 HIOS 的本地技能/ZIP 导入入口安装。原生 DSH 的技能目录与 HIOS 扩展中心目录是不同入口；同一运行环境选一个入口，避免重复安装同名技能。新会话或重新加载技能列表后选择 `/blender-furniture-spaces`。
