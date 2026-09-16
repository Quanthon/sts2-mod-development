# 配套工具接口

Python 3.10+。公共 init/doctor 只用标准库，内容模板、表格和图片命令需要 scripts/requirements.txt。<工具> 指 scripts/moddev.py。
CLI 输出 JSON：0 表示本次操作成功，2 表示检查发现待处理项，1 表示命令失败。具体结论看报告，命令成功不等于 Mod 已完成。

## 配置

moddev.json 使用 schema_version=1，project_root 相对配置文件目录。workbook、state_dir、asset_manifest、csproj、asset_roots 是项目内路径；environment 可指向外部工具；environment.dotnet 可指定 SDK 启动程序，未设置时从 PATH 查找。
languages 指定同步语言；pools 对应遗物池类型；keyword_ids 对应关键词稳定实现 ID；preferences 保存素材选择和测试范围，versions 记录核对过的版本。

项目相对路径使用 /；读取时兼容既有反斜杠路径，验证和占位图记录的新路径统一为 /。更换系统时重新配置机器相关绝对路径和虚拟环境。
这些字段和下面的表格/PNG 要求属于当前脚本接口。已有项目的其他格式可通过适配接入，无需为了使用工具改变设计。

## 初始化与检查

    python <工具> init --project <工程>
    python <工具> doctor --config <工程>/moddev.json

init 创建通用配置、需求文档和进度，已有目标文件保持不变并报冲突。通常在最小 Mod 加载成功、Python 准备好后使用。
required_checks 指定当前任务必需项，默认 python、game、dotnet、godot；Python 用于后段配套工具，IDE 不在检查范围。其他可选项为 openpyxl、Pillow、tutorials、official_reference、sts2_agent、mcp_server、project、ritsulib。旧配置未设置该字段时检查全部。
doctor 区分 missing 和 optional_missing。doctor 返回系统和架构。Godot 探测支持 Windows .exe、Linux/macOS 原生可执行文件和 macOS .app 应用包，核对执行权限及 Mono 版本标记；识别失败时保留原始输出，按 [环境准备](environment.md) 核对实际能力再适配检测，版本兼容与导出仍需工程验证。

## 内容模板

    python <工具> init --project <新工程> --profile character
    python <工具> add-content --config <已有工程>/moddev.json

角色 profile 一次创建公共文件和四类内容模板。add-content 只补缺少的工作簿、机制/角色说明、填写指南及素材清单，返回 created 和 preserved，可重复执行。
已有工作簿先配置真实路径，其格式由 diff 检查。公共 init 默认不创建工作簿；需要完整模板的调用使用 character profile。

## 差异与接受

    python <工具> diff --config moddev.json --kind cards --key SparkStrike

类别为 cards、keywords、powers、relics。省略筛选时检查全部；--key 可重复，关键词使用显示名称。
差异包含新增、修改、删除及疑似改名。快照按类别独立保存，首次全部待核验。删除和标识迁移单独处理，不由接受命令自动删除。

实际检查完成后，记录对应实现文件与报告：

    python <工具> record --config moddev.json --kind cards --key SparkStrike --artifact Mod/Cards/SparkStrike.cs --check .moddev/checks/spark-strike.json --behavior passed
    python <工具> accept --config moddev.json --kind cards --key SparkStrike

--artifact 和 --check 可重复，指向项目内非空文件；纳入相关代码、本地化、注册、共享机制和必要素材。报告记录真实命令、结果及证据。
--behavior 为 passed、reused 或 skipped，后两项提供 --reason；关键词另传 --implementation-id 并与 keyword_ids 一致。
record 不执行测试，accept 核对设计、配置和文件哈希，只接受记录仍有效的条目。共享文件改变后重新审查相关记录；整批修改完成后再记录可减少重复。
省略 --key 接受该类全部变化；存在删除时选择已完成的具体 key。接受前基线与证据保存在 history 中。

## 四类内容素材

    python <工具> placeholder --config moddev.json --key SparkStrike --name 火花打击 --type 攻击
    python <工具> sync-art --config moddev.json
    python <工具> sync-art --config moddev.json --apply
    python <工具> icons --config moddev.json --key Momentum --apply

placeholder 自动尝试本机系统字体；中文缺字或需指定字体时使用 --font <字体文件>，相对路径按项目根目录解析，也支持绝对路径。
适用于显式清单中的 PNG。匹配、占位图保护、备份与生成规则见 [素材处理](art.md)。这些命令处理资源文件，导出 PCK 和游戏加载由项目流程完成。
