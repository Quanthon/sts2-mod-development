# 环境准备

先下载并阅读首选教程，据此准备能运行最小 Mod 的环境，再补后续工具。复用已有兼容环境，版本与命令结合教程及当前游戏核对。

## 1. 首先把教程保存到本机

[STS2 Mod 制作教程](https://tutorials.sts2modding.com/) 是环境配置与后续实现的第一参考。先阅读其目录，并将站点链接的 [源码仓库](https://github.com/GlitchedReme/SlayTheSpire2ModdingTutorials) 下载到本机，保存 Markdown、示例和关联资源，例如放在项目的 references/tutorials。

没有 Git 时，使用系统下载与解压能力获取 [源码 ZIP](https://github.com/GlitchedReme/SlayTheSpire2ModdingTutorials/archive/refs/heads/master.zip)；已有 Git 也可浅克隆。此步骤不依赖 Python 或项目初始化脚本。已有有效副本可检查来源与更新情况后复用，记录本地位置和版本或获取日期。

优先阅读本地“环境配置”与所选需求的章节，再决定安装什么及其版本；站点的 [环境配置页](https://tutorials.sts2modding.com/docs/01-env-setup/) 用于对照。站点与副本内容不一致时先核对更新情况。下载或访问受阻时说明具体问题并处理，不把其他教程悄悄当成首选来源。

## 2. 原生初检

用 Windows 自带 PowerShell、注册表和文件读取检查系统、游戏位置、版本及现有工具，无需先有 Python 或项目配置。例如：

    [System.Environment]::OSVersion.VersionString
    [System.Environment]::Is64BitOperatingSystem
    Get-Command -Name python,py,dotnet,git,winget -ErrorAction SilentlyContinue |
        Select-Object Name,Source
    Get-ItemProperty -LiteralPath 'HKCU:\Software\Valve\Steam' -Name SteamPath -ErrorAction SilentlyContinue

从 Steam 路径和 steamapps/libraryfolders.vdf 定位游戏库；找不到或有多个候选时再请玩家协助。命令名和路径只是候选，核对实际可执行文件与版本，注意 Python 应用执行别名、便携工具和未刷新的 PATH。

Agent 负责检查、选版本、安装、配置和验证。玩家只在需要时选择存放位置、登录账户、处理系统权限提示或客户端必须人工执行的操作。给出具体操作后接着检查结果，沿用已确认的选择与授权。

## 3. 按教程跑通最小工程

1. 根据首选教程的环境配置章节和游戏版本，确定最小工程及所需依赖；教程已保存在本机，游戏源码按实际查证需要再提取。
2. 按教程准备所需环境，当前常见首批工具为 **Godot .NET 版和兼容的 .NET SDK**。Agent 编辑代码与配置，无需 IDE；已有可用工具直接复用。
3. 建立包含代码、最小资源和清单的工程，完成编译、PCK 导出、安装及游戏启动。使用本次日志中的加载标识和资源实际表现确认成功，到主菜单即可完成适用检查。

这是当前默认路线。若当前版本或既有项目需要不同构建/加载方式，依据教程、接口与验证结果适配，目标仍是跑通后续会使用的代码和资源链路。

成功后告知玩家已完成什么，以及下一项工具的用途。首段失败先处理相关错误；耗时操作提供实际进展和下一步。

## 4. 按任务补工具

| 用途 | 默认工具 |
| --- | --- |
| 配套脚本 | Python 3.10+；公共 init/doctor 只用标准库 |
| 自动状态读取和行为验证 | STS2-Agent/MCP 及其所需运行时 |
| 四类设计表、PNG 处理 | openpyxl、Pillow |
| 官方源码查证 | ILSpy 或适用的源码查看工具 |
| 参考副本与版本管理 | Git |
| 特定内容、资源与发布 | 对应框架、编辑器、导出工具或上传器 |

按实际任务使用已有可靠替代方案。进入自动场景验证前接通状态读取；最小 Mod 已加载与调试工具已就绪分别记录。

需要 Python 配套工具时，使用确认的解释器建立项目环境。以下变量由 Agent 按实际路径填写：

    & $pythonExe -m venv (Join-Path $projectDir '.venv')
    $projectPython = Join-Path $projectDir '.venv\Scripts\python.exe'
    & $projectPython (Join-Path $skillDir 'scripts\moddev.py') init --project $projectDir

已有项目配置直接复用。init 只生成通用需求、配置和进度；内容模板按 [角色流程](character-mod.md) 添加。填入实际路径后运行 doctor，配置和命令细节见 [工具接口](tools.md)。

## 参考与版本适配

- [首选教程站点](https://tutorials.sts2modding.com/)及其本地副本：优先按环境配置、基础库、相关内容或视觉章节查阅；路径变化时按标题重新定位。所需细节未覆盖时，再补充对应工具官方说明和游戏实现。
- **官方实现**：从本机对应版本的游戏程序集读取。需要时使用 ILSpy CLI 的 --project、--outputdir 等参数，先核对所用版本的帮助。记录游戏版本与来源，参考目录独立于发布产物。
- [STS2-Agent](https://github.com/CharTyr/STS2-Agent)：按所选版本说明安装 Mod 与服务并验证连接，也可沿用项目已验证的调试方式。

教程与实际接口不一致时，查明版本差异，以当前接口、构建和运行结果核实，记录必要适配。查效果时打开完整控制流，确认目标、顺序和取值时机；相同已验证路径直接复用。

doctor 是辅助检查。当前 Godot 检测使用可执行文件与 Mono 构建标记；无法识别时先核对原始输出和当前官方说明，必要时用最小工程验证 C# 与资源导出能力。明确不可执行的路径应修正；未知标记本身不足以证明不兼容。取得可靠证据后适配检测，而不是为迎合旧规则重装环境。
