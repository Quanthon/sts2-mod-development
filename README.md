# STS2 Mod Development Skill

面向 Agent 的《杀戮尖塔 2》Mod 开发技能。使用者负责设计，Agent 按项目实际情况实现、验证并维护工作流。

支持角色与卡牌内容、皮肤、特效和其他玩法改动。当前工具面向 Windows；文档中的工具与实现方式是默认建议，按实际游戏版本和工程适配。

## 使用

将整个仓库作为名为 sts2-mod-development 的技能目录，放入 Agent 支持的技能位置。Codex 本地技能目录可使用 ~/.codex/skills/sts2-mod-development。

在对话中调用：

    $sts2-mod-development
    我想制作一个 STS2 Mod，请先根据我的需求检查环境并引导开发。

从 [SKILL.md](SKILL.md) 开始。Agent 首先把 [STS2 Mod 制作教程](https://tutorials.sts2modding.com/) 下载到本机，阅读后决定环境配置，先跑通最小 Mod，再按需求补齐开发工具；玩家无需安装 IDE。

## 内容

- 公共环境准备、实现验证与发布流程。
- 独立的角色内容流程，以及皮肤、特效和其他需求入口。
- 卡牌、关键词、状态、遗物四类 [设计工作簿](assets/mod-design.xlsx)。
- 环境检查、项目初始化、设计差异与快照管理、素材同步和图标生成工具。

详细命令见 [工具接口](references/tools.md)。模板和 PNG 工具需要安装 scripts/requirements.txt 中的依赖；公共初始化和检查只需 Python 标准库。

## 涉及的外部工具

**先下载教程，再决定环境，不用一次安装全部工具。** [STS2 Mod 制作教程](https://tutorials.sts2modding.com/) 是第一参考，可通过站点链接的 [源码仓库](https://github.com/GlitchedReme/SlayTheSpire2ModdingTutorials)下载 ZIP 保存到本机，无需先安装 Git。按教程的环境配置章节结合当前游戏确定工具与版本；常见首批为 Godot .NET 和 .NET SDK。确认最小 Mod 能加载后再补后续工具。

### 首批开发环境

| 工具 | 用途 | 何时需要 |
| --- | --- | --- |
| [Godot .NET 版](https://godotengine.org/download/windows/) | 编辑场景和资源、导出 PCK；使用支持 C# 的版本及所需导出组件 | 默认首批准备 |
| [.NET SDK](https://dotnet.microsoft.com/download) | 编译 C# Mod；仅安装 Runtime 不够 | 默认首批准备 |
| Windows PowerShell | 检查游戏和工具路径、创建文件、调用构建与启动命令 | 使用系统已有能力 |

代码和配置由 Agent 编辑，不要求玩家安装 Rider、VS Code 或其他 IDE。使用本技能还需要支持技能、文件操作和终端执行的 Agent，以及本机已安装的《杀戮尖塔 2》。

### 按后续任务准备

| 工具 / 依赖 | 用途 | 何时需要 |
| --- | --- | --- |
| [Python](https://www.python.org/downloads/)（本工具要求 3.10+） | 运行本技能的初始化、检查、差异和素材脚本 | 开始使用配套脚本时 |
| [RitsuLib](https://github.com/BAKAOLC/STS2-RitsuLib) | 角色与内容开发使用的共享框架，提供相关接口和注册能力 | 项目选择该框架时；不是所有 Mod 的必需依赖 |
| [STS2-Agent / MCP](https://github.com/CharTyr/STS2-Agent) | 将游戏状态与操作连接到 Agent，用于自动读取状态和行为验证 | 接入自动调试时；按所选版本说明配置连接和运行依赖 |
| [ILSpy / ilspycmd](https://github.com/icsharpcode/ILSpy) | 查看本机对应版本的游戏程序集，查证官方实现 | 需要源码参考时 |
| [官方 Mod 上传器](https://github.com/megacrit/sts2-mod-uploader) | 准备并上传 Steam 创意工坊内容 | 发布到工坊时；同时需要可用的 Steam 登录 |

配套脚本依赖见 [requirements.txt](scripts/requirements.txt)，其他工具的运行要求按所选版本说明准备。

### 参考资料与随包工具

- **第一参考：[STS2 Mod 制作教程](https://tutorials.sts2modding.com/)**。先下载其 [源码副本](https://github.com/GlitchedReme/SlayTheSpire2ModdingTutorials)到本机，再根据教程决定环境、内容实现、资源处理与调试方式。
- 官方实现参考从玩家本机对应版本的游戏提取，本仓库不分发游戏源码。
- 本技能自带的 init、doctor、add-content、diff、record、accept、placeholder、sync-art、icons 命令位于 scripts/moddev.py，详细用法见 [工具接口](references/tools.md)。
- 完整准备流程见 [环境准备](references/environment.md)，发布与采集见 [发布与扩展](references/extensions.md)。

上述工具是当前默认选择，可依据项目和游戏版本使用经过核实的替代方案。第三方工具不随本仓库打包。

## 验证

开发工具要求 Python 3.10+。安装工具依赖后运行：

    python -m unittest discover -s tests -v

测试在临时项目中运行，不启动游戏。工具测试不代替具体 Mod 的编译、加载和游戏行为验证。

本仓库不包含游戏程序集、反编译源码、第三方工具安装包或示例项目的角色素材。
