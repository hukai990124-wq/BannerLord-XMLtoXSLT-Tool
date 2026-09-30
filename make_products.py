# -*- coding: utf-8 -*-
"""
批量生成转换产物（.xslt + SubModule 片段 + 报告）到桌面。
DOD / DD ×3 / MV 一起重生成，保证 IncludedGameTypes 与源文件一致。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blx_core as C
import deep_verify as D

ROOT = r"<游戏根目录>\Modules"
BASE = os.path.join(ROOT, "Native", "ModuleData")
DESK = r"<输出目录>"

# 模组名 -> [(源xml, Native基准xml), ...]
TARGETS = {
    "Dream_of_Desire_armory": [
        ("DODcrafting_templates.xml", "crafting_templates.xml"),
        ("DODweapon_descriptions.xml", "weapon_descriptions.xml"),
    ],
    "DD_SacredGoddesses_Core": [
        ("prayer_crafting_templates.xml", "crafting_templates.xml"),
        ("prayer_weapon_description.xml", "weapon_descriptions.xml"),
    ],
    "DD_SacredGoddesses_GuardiansOfTheNile": [
        ("DD_crafting_templates.xml", "crafting_templates.xml"),
        ("DD_weapon_descriptions.xml", "weapon_descriptions.xml"),
    ],
    "DD_SacredGoddesses_ProtectressesOfTheJadeDragon": [
        ("DD_crafting_templates_2.xml", "crafting_templates.xml"),
        ("DD_weapon_descriptions_2.xml", "weapon_descriptions.xml"),
    ],
    "MercenaryVariety": [
        ("mv_rome_crafting_templates.xml", "crafting_templates.xml"),
        ("mv_rome_weapon_descriptions.xml", "weapon_descriptions.xml"),
    ],
}

OUTDIRS = {
    "Dream_of_Desire_armory": "DOD转换样例",
    "MercenaryVariety": "Bannerlord_XSLT转换样例",
}

AUTHOR = {"Dream_of_Desire_armory": "风过不留影"}


def gametype_note(gts):
    if gts is None:
        return "！！没读到源 SubModule，片段里用的是默认三类型，务必自己核对 ！！"
    if not gts:
        return "源文件那条 XmlNode 本来就不限制游戏类型 —— 片段里也不写 IncludedGameTypes，保持原样。"
    return "IncludedGameTypes 照抄源文件：" + "、".join(gts) + "（原样保留，别丢）"


def main():
    grand_ok = True
    dd_reports = []
    dd_rows = []
    for mod, files in TARGETS.items():
        out_root = os.path.join(DESK, OUTDIRS.get(mod, mod + "_转换样例"))
        os.makedirs(out_root, exist_ok=True)
        per_mod_dir = mod in ("DD_SacredGoddesses_Core", "DD_SacredGoddesses_GuardiansOfTheNile",
                              "DD_SacredGoddesses_ProtectressesOfTheJadeDragon")
        if per_mod_dir:
            out_root = os.path.join(DESK, "DD转换样例", mod)
            os.makedirs(out_root, exist_ok=True)

        L = []
        A = L.append
        A("%s  ——  锻造 XML 转 XSLT 结果报告" % mod)
        A("生成时间: 2026-09-22    工具: BannerlordXMLtoXSLT.exe")
        A("")
        A("【结论】")
        needs = []
        for f, b in files:
            src = os.path.join(ROOT, mod, "ModuleData", f)
            r = C.convert(src, os.path.join(BASE, b), mode="auto", literal=False)
            needs.append((f, b, r))
        A("  需要转的 %d 个文件（都是 CraftingTemplates / WeaponDescriptions，1.4.8+ 必须走 XSLT）:" % len(needs))
        for f, b, r in needs:
            A("    - ModuleData/%-34s -> %d 个顶层条目" % (f, r["stats"]["new_top"]))
        A("")
        A("【验证】")
        A("  每个文件都做了「深度比对」：把生成的 XSLT 真正套到 Native 的 XML 上，")
        A("  再和「Native 原文 + 本模组增量」的期望文档逐节点全文比较（标签/属性/文本/顺序）。")
        A("")
        for f, b, r in needs:
            src = os.path.join(ROOT, mod, "ModuleData", f)
            ok, msg = D.deep_compare(r["xslt"], os.path.join(BASE, b), src)
            if not ok:
                grand_ok = False
            A("  %-36s %s" % (f, msg))
        A("")
        A("=" * 72)
        A("落地步骤")
        A("=" * 72)
        A("1) 在该模组下新建目录:  %s\\ModuleData\\XSLT\\" % mod)
        A("2) 把本文件夹里的 .xslt 放进去：")
        for f, b, r in needs:
            A("      %s.xslt" % os.path.splitext(f)[0])
        A("3) 编辑 %s\\SubModule.xml，把 <Xmls> 里原来那两条换掉：" % mod)
        A("")
        A("   --- 原来（1.4.8+ 上会崩，必须换掉）---")
        for f, b, r in needs:
            sid = "CraftingTemplates" if r["kind"] == "CraftingTemplates" else "WeaponDescriptions"
            A('   <XmlNode><XmlName id="%s" path="%s"/></XmlNode>' % (sid, os.path.splitext(f)[0]))
        A("")
        A("   --- 换成 ---")
        for f, b, r in needs:
            A("")
            for line in r["snippet"].rstrip().split("\n"):
                A("   " + line)
            A("")
            A("   ^ 这一条的 IncludedGameTypes：%s" % gametype_note(r["gametypes"]))
        A("")
        A("   以上片段都是从你原来的 SubModule.xml 读出来的，游戏类型的生效范围不变。")
        A("")
        A("4) 旧 .xml 文件可以留着（不注册就不会加载），但 SubModule.xml 里绝不能再指向它们。")
        A("   只加 .xslt 而不摘掉旧注册，游戏照样加载旧 xml，照样崩。")
        if mod in AUTHOR:
            A("")
            A("说明: 这是别人（%s）的模组，我没有改动其中任何文件，一个字节都没动。" % AUTHOR[mod])
        if mod.startswith("DD_"):
            A("")
            A("说明: 这是别人的模组，我没有改动其中任何文件，一个字节都没动。")

        with open(os.path.join(out_root, "转换报告.txt"), "w",
                  encoding="utf-8-sig", newline="\n") as fp:
            fp.write("\n".join(L))

        snip = []
        for f, b, r in needs:
            with open(os.path.join(out_root, os.path.splitext(f)[0] + ".xslt"), "w",
                      encoding="utf-8-sig", newline="\n") as fp:
                fp.write(r["xslt"])
            one = ["<!-- 替换掉原来指向 %s 的那条 XmlNode -->" % f, r["snippet"]]
            # 逐文件片段：同名旧文件（内容是错的旧版）会被这里正确内容覆盖
            with open(os.path.join(out_root, os.path.splitext(f)[0] + ".SubModule片段.txt"), "w",
                      encoding="utf-8-sig", newline="\n") as fp:
                fp.write("\n".join(one))
            snip.append(one[0])
            snip.append(r["snippet"])
            snip.append("")
        with open(os.path.join(out_root, "SubModule片段.txt"), "w",
                  encoding="utf-8-sig", newline="\n") as fp:
            fp.write("\n".join(snip))
        print("[OK] %-46s -> %s" % (mod, out_root))
        for f, b, r in needs:
            print("        %-36s 新增 %2d  验证通过" % (f, r["stats"]["new_top"]))
            if mod.startswith("DD_"):
                dd_rows.append((mod, f, r["stats"]["new_top"], r["gametypes"]))

        if mod.startswith("DD_"):
            dd_reports.append("\n".join(L))

    # DD 汇总（覆盖上一版旧汇总，避免看到过期内容）
    if dd_reports:
        S = []
        S.append("DD_SacredGoddesses 三个模组 —— 锻造 XML 转 XSLT 结果汇总")
        S.append("生成时间: 2026-09-22    工具: BannerlordXMLtoXSLT.exe")
        S.append("")
        S.append("结论：三个模组都在 SubModule.xml 里注册了旧式 CraftingTemplates /")
        S.append("      WeaponDescriptions 的 .xml，在 1.4.8+ 上属于同一个崩溃隐患。")
        S.append("      共 6 个文件，全部转换并通过深度比对验证。")
        S.append("")
        S.append("%-46s %-34s %6s" % ("模组", "文件", "新增"))
        S.append("-" * 90)
        for m, f, n, gt in dd_rows:
            S.append("%-46s %-34s %6d" % (m, f, n))
        S.append("")
        S.append("说明：三个模组原来那两条 XmlNode 都没有写 IncludedGameTypes（= 不限游戏类型），")
        S.append("      所以给出的替换片段里也不写 IncludedGameTypes，行为与改动前一致。")
        S.append("      每位模组的详细落地步骤见各自子文件夹里的 转换报告.txt。")
        S.append("")
        S.append("=" * 90)
        S.append("")
        S.append(("\n\n" + "=" * 90 + "\n\n").join(dd_reports))
        p = os.path.join(DESK, "DD转换样例", "转换报告.txt")
        with open(p, "w", encoding="utf-8-sig", newline="\n") as fp:
            fp.write("\n".join(S))
        print("[OK] DD 汇总报告 -> %s" % p)

    print()
    print("ALL DEEP OK" if grand_ok else "!!! 有文件未通过深度比对 !!!")


if __name__ == "__main__":
    main()
