# -*- coding: utf-8 -*-
"""
终极交叉验证：把生成的 XSLT 实跑结果，与「Native 原文 + 模组改动」的期望文档
做全量深度比对（标签名 / 属性字典 / 文本 / 子节点顺序）。
比 blx_core.verify 更严：能抓出多余插入、属性丢失、子容器遗漏、顺序错乱。

支持两种补丁形态：
  append  模组文件只含新增顶层节点          -> 期望 = Native + 追加这些节点
  diff    模组文件是 Native 的完整拷贝加料  -> 期望 = 按 id 对齐后，用模组侧覆盖对应节点
                                               （即"以模组文件为准"的最终形态）
"""
import sys
import os
import copy
from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blx_core as C


def norm(e):
    """把元素规范化成可深度比较的结构。"""
    return (
        e.tag,
        dict(e.attrib),
        (e.text or "").strip(),
        [norm(c) for c in e if isinstance(c.tag, str)],
    )


def build_expectation(base_path, mod_path):
    """
    构造期望文档。
    - 模组顶层 id 与 Native 有交集 -> 该 id 一律以模组侧为准（覆盖）
    - 模组独有 id                  -> 追加到末尾
    - Native 独有 id               -> 保留原样
    这就是"老模组 = Native 完整拷贝后加料"的终态。
    """
    base_root = etree.parse(base_path).getroot()
    mod_root = etree.parse(mod_path).getroot()
    spec = C.KIND_SPECS[C.detect_kind(C.load_xml(mod_path))]

    mod_by_id = {}
    for c in mod_root:
        if c.tag == spec["child"] and c.get("id") is not None:
            if c.get("id") in mod_by_id:
                return None, "模组文件里 id=%s 重复，无法构造期望文档" % c.get("id")
            mod_by_id[c.get("id")] = c

    expect = etree.Element(base_root.tag, dict(base_root.attrib))
    replaced = added = 0
    for b in base_root:
        if isinstance(b.tag, str) and b.tag == spec["child"] and b.get("id") in mod_by_id:
            expect.append(copy.deepcopy(mod_by_id[b.get("id")]))
            replaced += 1
        else:
            expect.append(copy.deepcopy(b))

    base_ids = {b.get("id") for b in base_root
                if isinstance(b.tag, str) and b.tag == spec["child"]}
    for mid, m in mod_by_id.items():
        if mid not in base_ids:
            expect.append(copy.deepcopy(m))
            added += 1

    return expect, {"replaced": replaced, "added": added,
                    "native_total": len(base_ids)}


def first_diff(x, y, path=""):
    p = path + "/" + str(x[0])
    if x[0] != y[0]:
        return "%s 标签: %s vs %s" % (p, x[0], y[0])
    if x[1] != y[1]:
        ka = set(x[1]) | set(y[1])
        det = ["%s: %r vs %r" % (k, x[1].get(k), y[1].get(k)) for k in sorted(ka)
               if x[1].get(k) != y[1].get(k)]
        return "%s 属性: %s" % (p, "; ".join(det))
    if x[2] != y[2]:
        return "%s 文本: %r vs %r" % (p, x[2][:40], y[2][:40])
    if len(x[3]) != len(y[3]):
        return "%s 子节点数: 期望 %d，实得 %d" % (p, len(x[3]), len(y[3]))
    for j in range(len(x[3])):
        if x[3][j] != y[3][j]:
            return first_diff(x[3][j], y[3][j], p)
    return p + " 未知差异"


def deep_compare(xslt_text, base_path, mod_path, kind=None):
    base_doc = etree.parse(base_path)
    try:
        xslt_doc = etree.fromstring(xslt_text.encode("utf-8"))
        result = etree.XSLT(xslt_doc)(base_doc).getroot()
    except Exception as e:
        return False, "XSLT 执行失败: %s" % e

    expect, info = build_expectation(base_path, mod_path)
    if expect is None:
        return False, info

    a, b = norm(expect), norm(result)
    if a == b:
        return True, ("深度比对一致：Native %d 个 → 覆盖 %d 个 / 新增 %d 个，全文逐节点相同"
                      % (info["native_total"], info["replaced"], info["added"]))

    diffs = []
    if a[0] != b[0]:
        diffs.append("根标签不同: %s vs %s" % (a[0], b[0]))
    if a[1] != b[1]:
        diffs.append("根属性不同: %s vs %s" % (a[1], b[1]))
    ca, cb = a[3], b[3]
    if len(ca) != len(cb):
        diffs.append("顶层节点数不同: 期望 %d，实得 %d" % (len(ca), len(cb)))
    for i in range(min(len(ca), len(cb))):
        if ca[i] != cb[i]:
            diffs.append("第 %d 个顶层节点(%s): %s"
                         % (i, ca[i][1].get("id", "?"), first_diff(ca[i], cb[i])))
        if len(diffs) >= 8:
            break
    return False, "深度比对不一致：\n    " + "\n    ".join(diffs)
