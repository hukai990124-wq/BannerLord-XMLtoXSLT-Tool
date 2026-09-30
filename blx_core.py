# -*- coding: utf-8 -*-
"""
Bannerlord 锻造 XML -> XSLT 转换核心
把旧式的 crafting_templates.xml / weapon_descriptions.xml
改写成新版要求的 XSLT 补丁文件。

只依赖标准库。
"""
import xml.etree.ElementTree as ET
import os
import re
import copy

# ---------------------------------------------------------------- 类型定义

# child_keys: 容器标签 -> (子元素标签, 用于识别子元素的属性名或属性名元组)
KIND_SPECS = {
    "CraftingTemplates": {
        "root": "CraftingTemplates",
        "child": "CraftingTemplate",
        "submodule_id": "CraftingTemplates",
        "native_file": "crafting_templates.xml",
        "child_keys": {
            "PieceDatas": ("PieceData", ("piece_type",)),
            "WeaponDescriptions": ("WeaponDescription", ("id",)),
            "StatsData": ("StatData", ("stat_type",)),
            "UsablePieces": ("UsablePiece", ("piece_id",)),
        },
    },
    "WeaponDescriptions": {
        "root": "WeaponDescriptions",
        "child": "WeaponDescription",
        "submodule_id": "WeaponDescriptions",
        "native_file": "weapon_descriptions.xml",
        "child_keys": {
            "WeaponFlags": ("WeaponFlag", ("value",)),
            "AvailablePieces": ("AvailablePiece", ("id",)),
        },
    },
}

HEADER = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns="">\n'
    '  <xsl:output omit-xml-declaration="no" indent="yes" />\n'
    '  <xsl:template match="@*|node()">\n'
    '    <xsl:copy>\n'
    '      <xsl:apply-templates select="@*|node()" />\n'
    '    </xsl:copy>\n'
    '  </xsl:template>\n'
)

FOOTER = "</xsl:stylesheet>\n"


class ConvertError(Exception):
    pass


# ---------------------------------------------------------------- 工具函数

def load_xml(path):
    if not os.path.exists(path):
        raise ConvertError("文件不存在: %s" % path)
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as e:
        raise ConvertError("XML 解析失败 %s: %s" % (os.path.basename(path), e))


def detect_kind(root):
    tag = root.tag
    if tag in KIND_SPECS:
        return tag
    for k, spec in KIND_SPECS.items():
        if tag == spec["root"]:
            return k
    raise ConvertError(
        "无法识别的 XML 类型，根元素是 <%s>。只支持 <%s> 和 <%s>。"
        % (tag, "CraftingTemplates", "WeaponDescriptions")
    )


def _q(s):
    """XPath 字符串转义"""
    if "'" not in s:
        return "'%s'" % s
    if '"' not in s:
        return '"%s"' % s
    # 两边都有引号，用 concat 拼
    parts = re.split(r"(')", s)
    return "concat(%s)" % ",".join("\"%s\"" % p if p != "'" else "\"'\"" for p in parts if p != "")


def elem_key(elem, key_attrs):
    for a in key_attrs:
        if a in elem.attrib:
            return (a, elem.attrib[a])
    return None


def child_signature(elem):
    """子元素的完整签名，用于判断两个子元素是否完全相同"""
    return (elem.tag, tuple(sorted(elem.attrib.items())),
            tuple(child_signature(c) for c in elem))


# ---------------------------------------------------------------- diff 计算

class Patch(object):
    def __init__(self, kind):
        self.kind = kind
        self.spec = KIND_SPECS[kind]
        self.new_top = []              # 新增的顶层节点（Element）
        self.append_ops = {}           # 容器 xpath -> [Element,...]  往容器追加
        self.attr_ops = {}             # 节点 xpath -> {attr: value}  改/加属性
        self.delete_ops = []           # 需要删除的 xpath
        self.warnings = []

    def add_append(self, xpath, elem):
        self.append_ops.setdefault(xpath, []).append(elem)

    def add_attr(self, xpath, attr, value):
        self.attr_ops.setdefault(xpath, {})[attr] = value


def build_patch(mod_root, base_root, kind, ignore_deletes=True):
    """
    mod_root: 模组旧 xml 的根
    base_root: 基准（Native）xml 的根，None 表示纯增量模式
    """
    spec = KIND_SPECS[kind]
    child_tag = spec["child"]
    patch = Patch(kind)

    base_index = {}
    if base_root is not None:
        for b in base_root:
            if b.tag == child_tag and "id" in b.attrib:
                base_index[b.attrib["id"]] = b

    for m in mod_root:
        if m.tag != child_tag:
            patch.warnings.append("跳过无法处理的顶层节点 <%s>" % m.tag)
            continue
        mid = m.attrib.get("id")
        if mid is None:
            patch.warnings.append("顶层 <%s> 缺少 id 属性，已按新增处理" % child_tag)
        b = base_index.get(mid) if mid is not None else None
        if b is None:
            patch.new_top.append(m)
        else:
            _diff_top(m, b, patch, mid)

    if base_root is not None and not ignore_deletes:
        mod_ids = set()
        for m in mod_root:
            if m.tag == child_tag and "id" in m.attrib:
                mod_ids.add(m.attrib["id"])
        for bid in base_index:
            if bid not in mod_ids:
                patch.delete_ops.append(
                    "/%s[1]/%s[@id=%s]" % (spec["root"], child_tag, _q(bid))
                )
    elif base_root is not None:
        mod_ids = set()
        for m in mod_root:
            if m.tag == child_tag and "id" in m.attrib:
                mod_ids.add(m.attrib["id"])
        missing = [i for i in base_index if i not in mod_ids]
        if missing:
            patch.warnings.append(
                "基准里有 %d 个条目在你的 xml 中不存在（默认不删除）：%s"
                % (len(missing), ", ".join(sorted(missing)[:5]) + (" ..." if len(missing) > 5 else ""))
            )

    return patch


def _diff_top(m, b, patch, mid):
    spec = patch.spec
    child_tag = spec["child"]
    base_xpath = "/%s[1]/%s[@id=%s]" % (spec["root"], child_tag, _q(mid))

    # 属性差异
    for a, v in m.attrib.items():
        if b.attrib.get(a) != v:
            patch.add_attr(base_xpath, a, v)
    dropped = [a for a in b.attrib if a not in m.attrib]
    if dropped:
        patch.warnings.append(
            "%s: 基准有但你的 xml 没有的属性（已忽略，未生成删除）: %s" % (mid, ", ".join(dropped))
        )

    # 子元素容器
    for container_tag, (item_tag, key_attrs) in spec["child_keys"].items():
        m_cont = _find_containers(m, container_tag)
        b_cont = _find_containers(b, container_tag)
        for mc in m_cont:
            cpath = base_xpath + "/" + container_tag + _container_pred(mc) + "[1]"
            bc = _match_container(b_cont, mc)
            if bc is None:
                # 整个容器都是新增的
                for item in mc:
                    if item.tag == item_tag:
                        patch.add_append(cpath, item)
                    else:
                        patch.warnings.append("%s/%s: 未知子元素 <%s>" % (mid, container_tag, item.tag))
                continue
            b_items = {}
            for bi in bc:
                k = elem_key(bi, key_attrs)
                if k is not None:
                    b_items[k[1]] = bi
            for mi in mc:
                if mi.tag != item_tag:
                    patch.warnings.append("%s/%s: 未知子元素 <%s>" % (mid, container_tag, mi.tag))
                    continue
                k = elem_key(mi, key_attrs)
                if k is None:
                    patch.add_append(cpath, mi)
                    continue
                bi = b_items.get(k[1])
                if bi is None:
                    patch.add_append(cpath, mi)
                elif child_signature(bi) != child_signature(mi):
                    # 同 id 但内容不同：整条替换做不到，退化为属性覆盖 + 警告
                    for a, v in mi.attrib.items():
                        if bi.attrib.get(a) != v:
                            patch.add_attr(
                                cpath + "/%s[@%s=%s]" % (item_tag, k[0], _q(k[1])), a, v
                            )


def _find_containers(parent, tag):
    return [c for c in parent if c.tag == tag]


def _container_pred(container):
    """容器自身的属性谓词（例如 StatsData 上的 weapon_description）"""
    preds = ""
    for a, v in container.attrib.items():
        preds += "[@%s=%s]" % (a, _q(v))
    return preds


def _match_container(base_containers, mc):
    """在基准里找到属性完全相同的同名容器"""
    sig = tuple(sorted(mc.attrib.items()))
    for bc in base_containers:
        if tuple(sorted(bc.attrib.items())) == sig:
            return bc
    return None


# ---------------------------------------------------------------- XSLT 生成

def _esc_text(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def emit_element(elem, indent, literal=False):
    """
    生成一个元素。
    literal=False -> xsl:element / xsl:attribute 风格（与官方 DLC 一致）
    literal=True  -> 字面元素，可读性更好
    """
    pad = "  " * indent
    pad1 = "  " * (indent + 1)
    lines = []

    if literal:
        attrs = "".join(
            ' %s="%s"' % (k, _esc_text(v).replace('"', "&quot;")) for k, v in elem.attrib.items()
        )
        kids = [c for c in elem]
        text = (elem.text or "").strip()
        if not kids and not text:
            lines.append("%s<%s%s />" % (pad, elem.tag, attrs))
        else:
            lines.append("%s<%s%s>" % (pad, elem.tag, attrs))
            for c in kids:
                lines.extend(emit_element(c, indent + 1, literal))
            lines.append("%s</%s>" % (pad, elem.tag))
        return lines

    lines.append('%s<xsl:element name="%s">' % (pad, elem.tag))
    for k, v in elem.attrib.items():
        lines.append('%s<xsl:attribute name="%s">%s</xsl:attribute>' % (pad1, k, _esc_text(v)))
    for c in elem:
        lines.extend(emit_element(c, indent + 1, literal))
    if not elem.attrib and not list(elem):
        pass
    lines.append("%s</xsl:element>" % pad)
    return lines


def generate_xslt(patch, literal=False):
    spec = patch.spec
    root_tag = spec["root"]
    out = [HEADER]

    # 1) 新增顶层节点
    if patch.new_top:
        out.append('  <xsl:template match="/%s[1]">\n' % root_tag)
        out.append('    <xsl:copy>\n')
        out.append('      <xsl:copy-of select="@*" />\n')
        out.append('      <xsl:apply-templates select="node()" />\n')
        for e in patch.new_top:
            out.append("\n")
            out.extend(_indent_lines(emit_element(e, 3, literal), 0))
        out.append('    </xsl:copy>\n')
        out.append('  </xsl:template>\n')

    # 2) 往已有容器里追加子元素
    for xpath in sorted(patch.append_ops):
        items = patch.append_ops[xpath]
        out.append('  <xsl:template match="%s">\n' % xpath)
        out.append('    <xsl:copy>\n')
        out.append('      <xsl:copy-of select="@*" />\n')
        out.append('      <xsl:apply-templates select="node()" />\n')
        for e in items:
            out.extend(_indent_lines(emit_element(e, 3, literal), 0))
        out.append('    </xsl:copy>\n')
        out.append('  </xsl:template>\n')

    # 3) 属性覆盖
    for xpath in sorted(patch.attr_ops):
        attrs = patch.attr_ops[xpath]
        out.append('  <xsl:template match="%s">\n' % xpath)
        out.append('    <xsl:copy>\n')
        out.append('      <xsl:copy-of select="@*" />\n')
        for a, v in attrs.items():
            out.append('      <xsl:attribute name="%s">%s</xsl:attribute>\n' % (a, _esc_text(v)))
        out.append('      <xsl:apply-templates select="node()" />\n')
        out.append('    </xsl:copy>\n')
        out.append('  </xsl:template>\n')

    # 4) 删除
    for xpath in patch.delete_ops:
        out.append('  <xsl:template match="%s" />\n' % xpath)

    out.append(FOOTER)
    return "".join(out)


def _indent_lines(lines, extra):
    return [l + "\n" if not l.endswith("\n") else l for l in lines]


# ---------------------------------------------------------------- SubModule 片段

DEFAULT_GAMETYPES = ["Campaign", "CampaignStoryMode", "CustomGame"]


def _module_root_of(xml_path):
    """从 ModuleData/xxx.xml 往上找到含 SubModule.xml 的模组根目录。"""
    d = os.path.dirname(os.path.abspath(xml_path))
    for _ in range(4):
        if os.path.isfile(os.path.join(d, "SubModule.xml")):
            return d
        nd = os.path.dirname(d)
        if nd == d:
            break
        d = nd
    return None


def read_submodule_gametypes(xml_path, submodule_id):
    """
    从源模组自己的 SubModule.xml 里读对应 XmlNode 的 IncludedGameTypes。
    返回值三态：
      None      -> 没找到对应的 XmlNode（无从得知，调用方用默认值并警告）
      []        -> 找到了，但该 XmlNode 本来就没写 IncludedGameTypes（= 不限游戏类型）
      [g1, g2]  -> 原样照抄这些 GameType
    目的：不改变原模组的行为——原本没限制的，转换后也不限制；
          原本只在某些模式生效的，转换后仍只在那些模式生效。
    """
    root = _module_root_of(xml_path)
    if not root:
        return None
    try:
        tree = ET.parse(os.path.join(root, "SubModule.xml"))
    except Exception:
        return None
    stem = os.path.splitext(os.path.basename(xml_path))[0].lower()
    fallback = None
    for node in tree.getroot().iter("XmlNode"):
        xn = node.find("XmlName")
        if xn is None or xn.get("id") != submodule_id:
            continue
        p = (xn.get("path") or "").replace("\\", "/").split("/")[-1]
        gts = [g.get("value") for g in node.iter("GameType") if g.get("value")]
        if os.path.splitext(p)[0].lower() == stem:
            return gts
        if fallback is None:
            fallback = gts
    return fallback


def submodule_snippet(kind, rel_path_without_ext, gametypes=None):
    sid = KIND_SPECS[kind]["submodule_id"]
    path = rel_path_without_ext.replace("\\", "/")
    head = ('  <XmlNode>\n'
            '    <XmlName id="%s" path="%s" />\n' % (sid, path))
    if gametypes is None:
        gts = DEFAULT_GAMETYPES          # 没读到源 SubModule，只能用默认
    else:
        gts = gametypes                  # [] 表示源文件本来就没限制，照旧不写
    if not gts:
        return head + '  </XmlNode>\n'
    body = "\n".join('      <GameType value="%s" />' % g for g in gts)
    return (head +
            '    <IncludedGameTypes>\n'
            '%s\n'
            '    </IncludedGameTypes>\n'
            '  </XmlNode>\n' % body)


# ---------------------------------------------------------------- 主流程

def convert(mod_xml_path, base_xml_path=None, mode="auto", literal=False,
            ignore_deletes=True):
    """
    mode: 'auto'  -> 若能提供基准则按 diff，否则按纯增量
          'append'-> 强制纯增量（所有顶层节点视为新增）
          'diff'  -> 强制与基准比对
    返回 dict: kind, xslt, snippet, report(list), stats(dict)
    """
    mod_root = load_xml(mod_xml_path)
    kind = detect_kind(mod_root)

    base_root = None
    if mode == "diff" and base_xml_path is None:
        raise ConvertError("diff 模式需要提供基准 XML")
    if mode in ("auto", "diff") and base_xml_path:
        base_root = load_xml(base_xml_path)
        bk = detect_kind(base_root)
        if bk != kind:
            raise ConvertError("基准文件是 <%s>，但输入是 <%s>，类型不匹配" % (bk, kind))

    if base_root is None or mode == "append":
        # 纯增量：所有顶层节点都算新增
        spec = KIND_SPECS[kind]
        patch = Patch(kind)
        for m in mod_root:
            if m.tag == spec["child"]:
                patch.new_top.append(m)
            else:
                patch.warnings.append("跳过无法处理的顶层节点 <%s>" % m.tag)
        used_mode = "append"
        if base_root is not None:
            # 仍然检查一下有没有和基准撞 id
            base_ids = {b.attrib.get("id") for b in base_root if b.tag == spec["child"]}
            dup = [e.attrib.get("id") for e in patch.new_top if e.attrib.get("id") in base_ids]
            if dup:
                patch.warnings.append(
                    "这些 id 在基准里已存在，纯增量模式仍会重复插入（建议改用 diff 模式）: %s"
                    % ", ".join(str(d) for d in dup)
                )
    else:
        # 自动判断输入是"增量文件"还是"基准的完整拷贝"
        spec = KIND_SPECS[kind]
        base_ids = {b.attrib.get("id") for b in base_root if b.tag == spec["child"]}
        mod_ids = [m.attrib.get("id") for m in mod_root if m.tag == spec["child"]]
        overlap = [i for i in mod_ids if i in base_ids]
        if overlap:
            patch = build_patch(mod_root, base_root, kind, ignore_deletes=ignore_deletes)
            used_mode = "diff"
        else:
            patch = Patch(kind)
            for m in mod_root:
                if m.tag == spec["child"]:
                    patch.new_top.append(m)
                else:
                    patch.warnings.append("跳过无法处理的顶层节点 <%s>" % m.tag)
            used_mode = "append"

    xslt = generate_xslt(patch, literal=literal)

    report = []
    stats = {
        "kind": kind,
        "mode": used_mode,
        "new_top": len(patch.new_top),
        "append_containers": len(patch.append_ops),
        "append_items": sum(len(v) for v in patch.append_ops.values()),
        "attr_ops": sum(len(v) for v in patch.attr_ops.values()),
        "deletes": len(patch.delete_ops),
    }
    report.append("类型: <%s>  (SubModule id=\"%s\")" % (kind, KIND_SPECS[kind]["submodule_id"]))
    report.append("模式: %s" % ("与基准比对" if used_mode == "diff" else "纯增量插入"))
    report.append("新增顶层节点: %d" % stats["new_top"])
    report.append("往已有节点追加子项: %d 项，分布在 %d 个容器" %
                  (stats["append_items"], stats["append_containers"]))
    report.append("属性修改: %d" % stats["attr_ops"])
    if stats["deletes"]:
        report.append("删除: %d" % stats["deletes"])
    for w in patch.warnings:
        report.append("[注意] " + w)

    gts = read_submodule_gametypes(mod_xml_path, KIND_SPECS[kind]["submodule_id"])
    if gts is None:
        report.append("[注意] 没读到源 SubModule 里对应的 XmlNode，片段里给的是默认三类型，请自行核对")
    elif not gts:
        report.append("源 SubModule 那条 XmlNode 本来就不限制游戏类型，片段里也不写 IncludedGameTypes（保持原样）")
    else:
        report.append("IncludedGameTypes（照抄源文件）: %s" % ", ".join(gts))

    return {
        "kind": kind,
        "mode": used_mode,
        "xslt": xslt,
        "snippet": submodule_snippet(
            kind,
            "XSLT/" + os.path.splitext(os.path.basename(mod_xml_path))[0],
            gametypes=gts,
        ),
        "gametypes": gts,
        "report": report,
        "stats": stats,
        "patch": patch,
    }


# ---------------------------------------------------------------- 自检验证

def verify(xslt_text, base_xml_path, mod_xml_path):
    """
    用 lxml 真正跑一遍 XSLT，验证结果里包含了输入 xml 的全部内容。
    返回 (ok:bool, messages:list)
    """
    msgs = []
    try:
        from lxml import etree
    except ImportError:
        return None, ["未安装 lxml，跳过 XSLT 实跑验证（转换结果仍可正常使用）"]

    try:
        base_doc = etree.parse(base_xml_path)
        xslt_doc = etree.fromstring(xslt_text.encode("utf-8"))
        transform = etree.XSLT(xslt_doc)
        result = transform(base_doc)
    except Exception as e:
        return False, ["XSLT 执行失败: %s" % e]

    mod_root = load_xml(mod_xml_path)
    kind = detect_kind(mod_root)
    spec = KIND_SPECS[kind]
    out_root = result.getroot()

    # 建立结果索引
    idx = {}
    for c in out_root:
        if c.tag == spec["child"] and c.get("id") is not None:
            idx[c.get("id")] = c

    ok = True
    for m in mod_root:
        if m.tag != spec["child"]:
            continue
        mid = m.get("id")
        got = idx.get(mid)
        if got is None:
            ok = False
            msgs.append("[缺失] %s 没有出现在转换结果里" % mid)
            continue
        # 逐容器检查
        for ctag, (itag, keys) in spec["child_keys"].items():
            need = {}
            for mc in _find_containers(m, ctag):
                for mi in mc:
                    if mi.tag == itag:
                        k = elem_key(mi, keys)
                        if k:
                            need[k[1]] = mi
            if not need:
                continue
            have = set()
            for gc in _find_containers_lxml(got, ctag):
                for gi in gc:
                    if gi.tag == itag:
                        for a in keys:
                            if gi.get(a) is not None:
                                have.add(gi.get(a))
                                break
            for k in need:
                if k not in have:
                    ok = False
                    msgs.append("[缺失] %s/%s: %s=%s 未被插入" % (mid, ctag, keys[0], k))
        # 属性检查
        for a, v in m.attrib.items():
            if got.get(a) != v:
                ok = False
                msgs.append("[属性不符] %s 的 %s: 期望 %s，实得 %s" % (mid, a, v, got.get(a)))

    if ok:
        msgs.insert(0, "验证通过：XSLT 实跑后，输入 XML 的全部内容都已正确注入（结果共 %d 个 <%s>）"
                    % (len(idx), spec["child"]))
    return ok, msgs


def _find_containers_lxml(parent, tag):
    return [c for c in parent if _local(c.tag) == tag]


def _local(tag):
    return tag.split("}")[-1] if isinstance(tag, str) else tag
