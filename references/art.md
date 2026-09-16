# 素材同步与关联图标

工具只处理 PNG，不改源工作簿，不生成机制或注册，不自动修改任意 C# 路径。

## 素材选择

preferences.missing_art = ask / placeholder / defer。
仅在用户选择 placeholder 或明确请求时运行 placeholder；选择 defer 时不运行生成器，按当版框架查明允许缺图的方式。
临时图是带类型和文字的程序绘制占位图，不是 AI 创作图片。正式素材由使用者提供，其他生成请求另按对应工具处理。

    python <工具> placeholder --config moddev.json --key SparkStrike --name 火花打击 --type 攻击

写入配置中的 cards 原始素材目录。已有图片默认拒绝覆盖；--refresh 仅能重生成 registry 哈希仍匹配的原占位图，不能覆盖已被正式图替换的文件。

## 显式接入清单

.moddev/assets.json：

    {
      "schema_version": 1,
      "entries": [
        {
          "kind": "cards",
          "key": "SparkStrike",
          "implementation": "Mod/Cards/SparkStrike.cs",
          "target": "Mod/Example/images/cards/SparkStrike.png"
        }
      ]
    }

kind 支持 cards、powers、relics；implementation 填真实类型文件，必须先存在。target 是已在工程中接入的 PNG 路径，限项目内部，不能指向原始素材目录。路径示例需要按目标项目替换。
一条内容可以有多个明确的目标引用，但各目标必须唯一。目标可以是既有正式图片，素材同步的职责就是按用户提交的源图更新它；这与占位图“不覆盖正式图”不同。

来源按 key 文件名、当前名称、已接受基线名称依次精确匹配。卡牌图片若在 placeholders.json 中有登记且当前内容哈希仍吻合，视为工具生成的未修改占位图：优先选取匹配到的非占位图片，仅无其他候选时回退到占位图。因此 Spark.png 是已登记占位图时，新提交的火花.png 可以接入；原始占位图保持不变。未登记或内容已改变的图片不推断为占位图，仍按正常 key 优先级处理。同一级别多个非占位候选报歧义，一个来源被不同条目争用也报错，不做模糊匹配。历史更久的别名可由使用者改名为 key，不静默推断。
卡牌和遗物标注弃用时跳过。缺图、损坏、缺类型和重名不删除旧资源，有效项仍可继续。
图片按字节内容比较，不依赖时间戳；原图尺寸和透明度不变。此核心工具不生成遗物轮廓等专用派生资产，Agent 按框架资源要求另行适配并验证。

    python <工具> sync-art --config moddev.json
    python <工具> sync-art --config moddev.json --kind cards --apply

预览只读；apply 对变化项备份，再写入。普通写入异常回滚本批，断电等情况可按 .moddev/backups 下 manifest.json 手工恢复。备份应保留到导出和加载通过。
needs_export=true 表示本次有资源变化；另在项目进度记录 PCK 待导出状态，导出失败后不能因下次图片无变化就跳过重试。核心同步工具本身不导出 PCK。

## 从关联卡牌生成状态图标

    python <工具> icons --config moddev.json
    python <工具> icons --config moddev.json --key Momentum --apply

指定 --key 时只报告所选状态及其关联卡牌的问题；状态表头等影响整个输入的错误仍保留。不指定 --key 时检查全部状态。只处理状态表中有关联的条目；支持 key、唯一当前名称、名称（Key）。无关联跳过，未知/歧义关联报告。
读取 cards 源图，居中裁成正方形，再等比缩放为 256×256 RGBA PNG，写入 powers 原始素材目录。
已有成品默认保留；明确重裁时使用 --overwrite，写入前备份。生成后检查构图，再将该状态列入素材清单并执行 sync-art 接入工程。

