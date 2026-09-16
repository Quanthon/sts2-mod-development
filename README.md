# STS2 Mod Development Skill

面向 Agent 的《杀戮尖塔 2》Mod 开发技能。使用者负责设计，Agent 按项目实际情况实现、验证并维护工作流。

支持角色与卡牌内容、皮肤、特效和其他玩法改动。当前工具面向 Windows；文档中的工具与实现方式是默认建议，按实际游戏版本和工程适配。

## 使用

将整个仓库作为名为 sts2-mod-development 的技能目录，放入 Agent 支持的技能位置。Codex 本地技能目录可使用 ~/.codex/skills/sts2-mod-development。

在对话中调用：

    $sts2-mod-development
    我想制作一个 STS2 Mod，请先根据我的需求检查环境并引导开发。

从 [SKILL.md](SKILL.md) 开始。Agent 会先准备可运行的最小 Mod，再按需求补齐开发工具；玩家无需安装 IDE。

## 内容

- 公共环境准备、实现验证与发布流程。
- 独立的角色内容流程，以及皮肤、特效和其他需求入口。
- 卡牌、关键词、状态、遗物四类 [设计工作簿](assets/mod-design.xlsx)。
- 环境检查、项目初始化、设计差异与快照管理、素材同步和图标生成工具。

详细命令见 [工具接口](references/tools.md)。模板和 PNG 工具需要安装 scripts/requirements.txt 中的依赖；公共初始化和检查只需 Python 标准库。

## 验证

开发工具要求 Python 3.10+。安装工具依赖后运行：

    python -m unittest discover -s tests -v

测试在临时项目中运行，不启动游戏。工具测试不代替具体 Mod 的编译、加载和游戏行为验证。

本仓库不包含游戏程序集、反编译源码、第三方工具安装包或示例项目的角色素材。
