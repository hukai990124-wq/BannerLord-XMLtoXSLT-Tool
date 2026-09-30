# Bannerlord 锻造 XML → XSLT 转换器

一个把《骑马与砍杀 II：霸主》旧式锻造数据文件一键转成 XSLT 补丁的小工具。

```
gui.py  ·  blx_core.py  ·  deep_verify.py  ·  examples/
```

---

## 这个工具解决什么问题

从 **游戏版本 1.4.8** 开始，Bannerlord 修改了 crafting 数据的加载方式：

- **不允许**模组自带一整份 `crafting_templates.xml` / `weapon_descriptions.xml`
- **只能**提供一份 XSLT 补丁，由引擎套用到 Native 已加载的 XML 上

结果就是：**所有还挂着旧式 XML 的模组，在 1.4.8+ 上启动即崩**。

崩溃现场很难定位 —— 没有堆栈指向你的模组，游戏只是在主菜单之前就退出了。
排查方向通常是错的（以为是 C# 的 `SubModule` 问题、以为是排序问题、以为是版本不匹配）。

这个工具做的事，就是把这个机械改写自动化。

```
旧模组                              转换后
ModuleData/                         ModuleData/
  crafting_templates.xml     →        XSLT/
  weapon_descriptions.xml    →          crafting_templates.xslt
                                        weapon_descriptions.xslt
SubModule.xml                       SubModule.xml
  id="CraftingTemplates"              id="CraftingTemplates"
  path="crafting_templates"           path="XSLT/crafting_templates"
```

---

## 先说清楚：哪些文件需要转，哪些不需要

**这是最容易搞错的一点。** 只有两类数据走 XSLT：

| 数据类型（`<XmlName id="...">`） | 需要转? | 说明 |
|---|:---:|---|
| `CraftingTemplates` | ✅ **必须转** | 改的是原生模板 → 必须 XSLT |
| `WeaponDescriptions` | ✅ **必须转** | 改的是原生描述 → 必须 XSLT |
| `CraftingPieces` | ❌ 不用 | 自建数据，仍是普通 XML |
| `Items` | ❌ 不用 | 自建数据，仍是普通 XML |
| `GameText` / `NPCCharacters` / … | ❌ 不用 | 与本次改动无关 |

**别把 `crafting_pieces.xml` 也转掉。** 它经常是整个模组里最大的文件（几十上百 KB），
但它的注册方式从头到尾没变过。判断依据：`id` 是不是 `CraftingTemplates` 或 `WeaponDescriptions`。

官方参照物 —— `Modules\NavalDLC\SubModule.xml` 逐字如此：

```xml
<XmlName id="CraftingPieces"     path="naval_crafting_pieces" />                    <!-- 普通 XML -->
<XmlName id="CraftingTemplates"  path="XSLT/NavalDLC_Native_CraftingTemplates" />    <!-- XSLT -->
<XmlName id="WeaponDescriptions" path="XSLT/NavalDLC_Native_WeaponDescriptions" />   <!-- XSLT -->
```

NavalDLC 的 `ModuleData\` 根目录里**没有** `crafting_templates.xml`，它只靠 XSLT 改原生。

---

## 用法

### 图形界面

双击 `BannerlordXMLtoXSLT.exe`（Releases 里下载）。

1. **游戏目录** —— 大部分情况会自动找到。找不到手动指定游戏根目录
   （即包含 `Modules\Native` 的那一层）。
2. **添加文件** —— 选模组里旧的 `crafting_templates.xml` / `weapon_descriptions.xml`，可多选。
3. **转换模式** —— 保持「自动判断」。
4. **输出目录** —— 默认填 `输入文件所在目录\XSLT`。
5. **开始转换** —— 日志里会逐条列出改动，并给出实跑验证结果。

### 命令行 / 脚本调用

```python
import blx_core as C

res = C.convert(
    r"你的模组\ModuleData\crafting_templates.xml",
    r"游戏\Modules\Native\ModuleData\crafting_templates.xml",   # 基准，可省略
    mode="auto",
)

print(res["report"])        # 改动清单
open("out.xslt", "w", encoding="utf-8").write(res["xslt"])
print(res["snippet"])       # 贴进 SubModule.xml 的片段
```

---

## 两种源文件形态，它都能处理

`mode="auto"` 会自动判断：

**① 纯增量小文件** —— 文件里只写了你自己新增的 id。

```xml
<CraftingTemplates>
    <CraftingTemplate id="My_Custom_Sword" item_type="OneHandedWeapon" ...>
        ...
    </CraftingTemplate>
</CraftingTemplates>
```

→ 生成「在根节点末尾追加」的模板。

**② 从 Native 复制后加料的大文件** —— 老模组最常见的形态。整个原生文件被拷进模组，
在中间某几个模板里加了几个 `UsablePiece`。

→ 与 Native 逐节点比对，**只抽真正改动的部分**（新增的子项、改过的属性），
原生内容一律丢弃。生成的补丁很小，也不会覆盖你没碰过的原生数据。

判断标准：模组文件的顶层 id 与 Native 有没有交集。

---

## 转换之后必做的一件事

**把 `SubModule.xml` 里原来指向旧 `.xml` 的那条 `XmlNode` 删掉或注释掉。**

```xml
<!-- 删掉 / 注释掉 -->
<XmlNode>
    <XmlName id="CraftingTemplates" path="crafting_templates" />
</XmlNode>
```

只加 `.xslt` 而不摘掉旧注册 —— 旧 XML 照样会被加载，**照样崩**。
工具会把新片段给你，但不会替你改 `SubModule.xml`。

旧 `.xml` 文件本身可以留在原地，不影响（不注册就不会被读）。想删也行，自己判断。

---

## 关于 `IncludedGameTypes`

工具会**读取你自己 `SubModule.xml` 里那一条的 `IncludedGameTypes`，原样照抄到片段里**：

| 你的源文件 | 生成的片段 |
|---|---|
| 写了 `Campaign` / `CampaignStoryMode` | 逐字照抄这两个 |
| 一个字都没写（= 不限游戏类型） | 片段里也不写 |
| 读不到（目录结构特殊） | 用默认三类型，并在报告里**告警**提醒你核对 |

这一条是刻意做的。曾经踩过：硬编码成三个 `GameType` 会给「本来没写」的条目
凭空加上限制，**缩小了生效范围**，表现为"自建武器在自定义战斗里突然不见了"。

---

## 验证：为什么可以直接信

工具**不会**只告诉你"转换完成"。

**验证层 1 —— 实跑 XSLT。**
用 `lxml`（与游戏同为 XSLT 1.0 实现）把生成的补丁真正套到 Native 的 XML 上，
逐 id 检查你原文件里每一条是否都注入成功、属性是否一致。

**验证层 2 —— 深度比对。**（`deep_verify.py`）
构造「Native 原文 + 你的增量」作为期望文档，与实跑结果**逐节点全文比较**：
标签名、属性字典、文本、子节点顺序。

```python
import blx_core as C, deep_verify as D

res = C.convert(mod_xml, base_xml)
ok, msg = D.deep_compare(res["xslt"], base_xml, mod_xml)
print(ok, msg)
# True  深度比对一致：Native 12 个 + 追加 14 个，全文逐节点相同
```

层 2 能抓出层 1 抓不到的问题：多余插入、属性丢失、嵌套容器遗漏、子节点顺序错乱。

**显示验证通过，就不用靠"进游戏看崩不崩"来试了。**

---

## 输出写法

| 选项 | 生成 | 特点 |
|---|---|---|
| `xsl:element`（默认） | `<xsl:element name="UsablePiece">` | 与官方 DLC 写法完全一致，最保险 |
| 字面元素 | `<UsablePiece piece_id="..."/>` | 接近原始 XML，读起来舒服、方便手改 |

两者在游戏里效果完全相同。

---

## 目录结构

```
blx_core.py       转换引擎（纯标准库，无第三方依赖）
blx_gui.py        tkinter 图形界面
deep_verify.py    深度比对验证
make_products.py  批量转换脚本（一次处理多个模组、生成报告）
examples/         示例输入与对应输出
```

打包成 exe：

```bash
pyinstaller --onefile --windowed --clean --noconfirm \
  --name "BannerlordXMLtoXSLT" blx_gui.py
```

> **注意**：打包用的是系统 Python 3.11（自带 tkinter）。
> Python 3.13 的嵌入式/精简安装通常**不带 tkinter**，打包 GUI 会失败。

---

## 环境要求

- **只转换文件** → 需要 Python 3.8+，**无第三方依赖**
- **实跑验证** → 需要 `lxml`（`pip install lxml`）。没装则跳过验证，转换结果仍可用
- **GUI** → 需要 tkinter（官方 Python 安装包自带）
- **打包 exe** → `pip install pyinstaller`

---

## 已知边界

- 只处理 `CraftingTemplates` 与 `WeaponDescriptions`，其他数据类型原样跳过并提示
- **不修改**任何模组文件。`.xslt` 由你指定输出目录，`SubModule.xml` 需要你自己改
- 不做 XML 格式化美化，输出保持原文件的属性顺序与缩进意图
- 如果模组同时存在「顶层 id 与 Native 有交集」和「只写新增」两种区块，
  会走 diff 模式（更保守，不会漏掉改动）

---

## 许可

MIT
