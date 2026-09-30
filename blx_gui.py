# -*- coding: utf-8 -*-
"""
Bannerlord 锻造 XML -> XSLT 转换器（图形界面）

把旧式的 crafting_templates.xml / weapon_descriptions.xml
一键转换成新版要求的 XSLT 补丁文件。
"""
import os
import sys
import glob
import traceback

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

import blx_core as C

APP_TITLE = "Bannerlord 锻造 XML → XSLT 转换器"
VERSION = "v1.1"

COMMON_ROOTS = [
    r"C:\Program Files (x86)\Steam\steamapps\common\Mount & Blade II Bannerlord",
    r"C:\Program Files\Steam\steamapps\common\Mount & Blade II Bannerlord",
    r"D:\SteamLibrary\steamapps\common\Mount & Blade II Bannerlord",
    r"E:\SteamLibrary\steamapps\common\Mount & Blade II Bannerlord",
]


HELP_TEXT = """这个工具做什么

  新版霸主不再允许模组自带一整份 crafting_templates.xml / weapon_descriptions.xml，
  必须改成 XSLT 补丁：在 SubModule.xml 里注册一个 .xslt，
  由引擎把它套到 Native 已经加载好的那份 XML 上。
  本工具就是把旧的 XML 自动改写成这种 XSLT。

怎么用

  1. 确认"游戏目录"填的是霸主根目录（通常会自动找到）。
  2. 点"添加文件"，选你模组里旧的 crafting_templates.xml / weapon_descriptions.xml。
     可以一次选多个。
  3. 转换模式保持"自动判断"即可：
       · 输入是只写了新增内容的小文件         -> 按"纯增量插入"处理
       · 输入是从 Native 复制出来再改的大文件  -> 按"与 Native 比对"处理，只抽出你改动的部分
  4. 输出目录默认填"输入文件所在目录 \\ XSLT"，也可以自己改。
  5. 点"开始转换"。日志里会显示每条改动，以及 XSLT 实跑验证的结果。

转换之后还要做两件事（工具不会替你改）

  1. 把"SubModule.xml 片段"页里的内容，粘到你的 SubModule.xml 的 <Xmls> 节点里。
     片段里的 <IncludedGameTypes> 是照抄你自己 SubModule.xml 里那一条的：
     原来写了几种游戏类型，片段里就是几种；原来没写，片段里也不写。
     不用手动补，游戏类型的生效范围跟改动前完全一致。
  2. 把 SubModule.xml 里原来指向旧 .xml 的那个 <XmlNode> 删掉或注释掉，
     否则旧的 .xml 仍然会被加载，还是会崩。
     转换出来的 .xslt 不要求旁边有同名 .xml。

两种输出写法的区别

  · xsl:element（默认）：和官方 DLC 的 xslt 一模一样，最保险，但看着啰嗦。
  · 字面元素：几乎就是原来的 XML 写法，读起来舒服，方便自己再手改。
    两种在游戏里效果完全一样。

关于验证

  工具会在后台真的把生成的 XSLT 跑一遍（用 lxml），
  检查你原文件里的每一个条目是否都被正确注入。
  显示"验证通过"基本就可以放心进游戏了。
"""


def find_game_dir():
    for p in COMMON_ROOTS:
        if os.path.isdir(os.path.join(p, "Modules", "Native", "ModuleData")):
            return p
    # 扫一遍盘符下的 SteamLibrary
    for drive in ["C:\\", "D:\\", "E:\\", "F:\\", "G:\\"]:
        for pat in [drive + "SteamLibrary\\steamapps\\common\\Mount & Blade II Bannerlord",
                    drive + "Steam\\steamapps\\common\\Mount & Blade II Bannerlord",
                    drive + "Games\\Mount & Blade II Bannerlord"]:
            if os.path.isdir(os.path.join(pat, "Modules", "Native", "ModuleData")):
                return pat
    return ""


class App(object):
    def __init__(self, root):
        self.root = root
        root.title("%s  %s" % (APP_TITLE, VERSION))
        root.geometry("980x720")
        root.minsize(880, 620)

        self.files = []
        self.last_results = {}

        self._build_ui()

        g = find_game_dir()
        if g:
            self.game_var.set(g)
            self.log("已自动找到游戏目录: %s" % g)

    # ------------------------------------------------------------ UI
    def _build_ui(self):
        st = ttk.Style()
        try:
            st.theme_use("clam")
        except Exception:
            pass

        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=tk.X)

        # 游戏目录
        row = ttk.Frame(top)
        row.pack(fill=tk.X, pady=3)
        ttk.Label(row, text="游戏目录:", width=12).pack(side=tk.LEFT)
        self.game_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.game_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        ttk.Button(row, text="浏览…", command=self.pick_game, width=8).pack(side=tk.LEFT)

        # 文件列表
        frm = ttk.LabelFrame(self.root, text="待转换的旧 XML 文件", padding=8)
        frm.pack(fill=tk.BOTH, expand=False, padx=10, pady=6)

        self.listbox = tk.Listbox(frm, height=5, font=("Consolas", 9))
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(frm, orient=tk.VERTICAL, command=self.listbox.yview)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        self.listbox.config(yscrollcommand=sb.set)

        btns = ttk.Frame(frm)
        btns.pack(side=tk.LEFT, fill=tk.Y, padx=6)
        ttk.Button(btns, text="添加文件", command=self.add_files).pack(fill=tk.X, pady=2)
        ttk.Button(btns, text="移除选中", command=self.remove_sel).pack(fill=tk.X, pady=2)
        ttk.Button(btns, text="清空", command=self.clear_files).pack(fill=tk.X, pady=2)

        # 选项
        opt = ttk.LabelFrame(self.root, text="选项", padding=8)
        opt.pack(fill=tk.X, padx=10, pady=4)

        r1 = ttk.Frame(opt)
        r1.pack(fill=tk.X, pady=2)
        ttk.Label(r1, text="转换模式:", width=12).pack(side=tk.LEFT)
        self.mode_var = tk.StringVar(value="auto")
        ttk.Radiobutton(r1, text="自动判断（推荐）", value="auto",
                        variable=self.mode_var).pack(side=tk.LEFT, padx=6)
        ttk.Radiobutton(r1, text="纯增量插入", value="append",
                        variable=self.mode_var).pack(side=tk.LEFT, padx=6)
        ttk.Radiobutton(r1, text="与 Native 比对（diff）", value="diff",
                        variable=self.mode_var).pack(side=tk.LEFT, padx=6)

        r2 = ttk.Frame(opt)
        r2.pack(fill=tk.X, pady=2)
        ttk.Label(r2, text="输出写法:", width=12).pack(side=tk.LEFT)
        self.lit_var = tk.BooleanVar(value=False)
        ttk.Radiobutton(r2, text="xsl:element（与官方 DLC 一致，最稳）", value=False,
                        variable=self.lit_var).pack(side=tk.LEFT, padx=6)
        ttk.Radiobutton(r2, text="字面元素（更接近原 XML，好手改）", value=True,
                        variable=self.lit_var).pack(side=tk.LEFT, padx=6)

        r3 = ttk.Frame(opt)
        r3.pack(fill=tk.X, pady=2)
        ttk.Label(r3, text="输出目录:", width=12).pack(side=tk.LEFT)
        self.out_var = tk.StringVar(value="")
        ttk.Entry(r3, textvariable=self.out_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        ttk.Button(r3, text="浏览…", command=self.pick_out, width=8).pack(side=tk.LEFT)

        # 动作
        act = ttk.Frame(self.root, padding=(10, 4))
        act.pack(fill=tk.X)
        self.btn_run = ttk.Button(act, text="开始转换", command=self.run)
        self.btn_run.pack(side=tk.LEFT)
        ttk.Button(act, text="保存当前预览", command=self.save_current).pack(side=tk.LEFT, padx=6)
        ttk.Button(act, text="复制 SubModule 片段", command=self.copy_snippet).pack(side=tk.LEFT)
        self.lbl_status = ttk.Label(act, text="")
        self.lbl_status.pack(side=tk.LEFT, padx=12)

        # 结果
        nb = ttk.Notebook(self.root)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
        self.nb = nb

        self.txt_log = scrolledtext.ScrolledText(nb, font=("Consolas", 9), wrap=tk.WORD)
        nb.add(self.txt_log, text="  日志  ")

        self.txt_xslt = scrolledtext.ScrolledText(nb, font=("Consolas", 9), wrap=tk.NONE)
        nb.add(self.txt_xslt, text="  XSLT 预览  ")

        self.txt_snip = scrolledtext.ScrolledText(nb, font=("Consolas", 9), wrap=tk.NONE)
        nb.add(self.txt_snip, text="  SubModule.xml 片段  ")

        self.txt_help = scrolledtext.ScrolledText(nb, font=("Microsoft YaHei UI", 10), wrap=tk.WORD)
        nb.add(self.txt_help, text="  怎么用  ")
        self.txt_help.insert(tk.END, HELP_TEXT)
        self.txt_help.config(state=tk.DISABLED)

    # ------------------------------------------------------------ 事件
    def log(self, msg):
        self.txt_log.insert(tk.END, msg + "\n")
        self.txt_log.see(tk.END)
        self.root.update_idletasks()

    def pick_game(self):
        d = filedialog.askdirectory(title="选择 Mount & Blade II Bannerlord 根目录")
        if d:
            self.game_var.set(d)

    def pick_out(self):
        d = filedialog.askdirectory(title="选择输出目录")
        if d:
            self.out_var.set(d)

    def add_files(self):
        ps = filedialog.askopenfilenames(
            title="选择旧格式的 XML 文件",
            filetypes=[("XML 文件", "*.xml"), ("所有文件", "*.*")])
        for p in ps:
            if p not in self.files:
                self.files.append(p)
                self.listbox.insert(tk.END, p)
        if self.files and not self.out_var.get():
            self.out_var.set(os.path.join(os.path.dirname(self.files[0]), "XSLT"))

    def remove_sel(self):
        sel = list(self.listbox.curselection())
        for i in reversed(sel):
            self.listbox.delete(i)
            del self.files[i]

    def clear_files(self):
        self.listbox.delete(0, tk.END)
        self.files = []

    def _base_path(self, kind):
        g = self.game_var.get().strip()
        if not g:
            return None
        p = os.path.join(g, "Modules", "Native", "ModuleData", C.KIND_SPECS[kind]["native_file"])
        return p if os.path.exists(p) else None

    def run(self):
        self.txt_log.delete(1.0, tk.END)
        self.txt_xslt.delete(1.0, tk.END)
        self.txt_snip.delete(1.0, tk.END)
        self.last_results = {}

        if not self.files:
            messagebox.showwarning("没有文件", "请先添加要转换的 XML 文件。")
            return

        mode = self.mode_var.get()
        literal = self.lit_var.get()
        outdir = self.out_var.get().strip()

        ok_all = True
        for path in self.files:
            self.log("=" * 60)
            self.log("输入: %s" % path)
            try:
                # 先探测类型以决定基准文件
                kind = C.detect_kind(C.load_xml(path))
                base = None
                if mode in ("auto", "diff"):
                    base = self._base_path(kind)
                    if base is None and mode == "diff":
                        raise C.ConvertError(
                            "找不到 Native 的 %s，请检查游戏目录设置"
                            % C.KIND_SPECS[kind]["native_file"])
                    if base:
                        self.log("基准: %s" % base)

                res = C.convert(path, base, mode=mode, literal=literal)
                for line in res["report"]:
                    self.log("  " + line)

                # 验证
                if base:
                    vok, vmsgs = C.verify(res["xslt"], base, path)
                    if vok is None:
                        self.log("  [验证] " + vmsgs[0])
                    elif vok:
                        self.log("  [验证] " + vmsgs[0])
                    else:
                        ok_all = False
                        for m in vmsgs:
                            self.log("  [验证失败] " + m)
                else:
                    self.log("  [验证] 未提供基准文件，跳过实跑验证")

                self.last_results[path] = res

                # 写文件
                if outdir:
                    os.makedirs(outdir, exist_ok=True)
                    name = os.path.splitext(os.path.basename(path))[0] + ".xslt"
                    op = os.path.join(outdir, name)
                else:
                    op = os.path.splitext(path)[0] + ".xslt"
                with open(op, "w", encoding="utf-8-sig", newline="\n") as f:
                    f.write(res["xslt"])
                self.log("  已写出: %s" % op)
                res["out_path"] = op

                self.txt_snip.insert(
                    tk.END, "<!-- 由 %s 转换而来 -->\n%s\n" % (os.path.basename(path), res["snippet"]))

            except C.ConvertError as e:
                ok_all = False
                self.log("  [错误] %s" % e)
            except Exception:
                ok_all = False
                self.log("  [异常] " + traceback.format_exc())

        # 预览第一个结果
        if self.last_results:
            first = self.last_results[self.files[0] if self.files[0] in self.last_results
                                      else list(self.last_results)[0]]
            self.txt_xslt.insert(tk.END, first["xslt"])
            self.txt_xslt.mark_set(tk.INSERT, "1.0")

        self.lbl_status.config(
            text=("全部完成" if ok_all else "完成，但有需要注意的项"),
            foreground=("#0a7d28" if ok_all else "#b06000"))
        self.log("=" * 60)
        self.log("完毕。")

    def save_current(self):
        if not self.last_results:
            messagebox.showinfo("没有内容", "请先执行转换。")
            return
        key = list(self.last_results)[0]
        res = self.last_results[key]
        p = filedialog.asksaveasfilename(
            title="保存 XSLT",
            defaultextension=".xslt",
            initialfile=os.path.basename(res.get("out_path", "output.xslt")),
            filetypes=[("XSLT 文件", "*.xslt"), ("所有文件", "*.*")])
        if p:
            with open(p, "w", encoding="utf-8-sig", newline="\n") as f:
                f.write(res["xslt"])
            self.log("已保存到: %s" % p)

    def copy_snippet(self):
        if not self.last_results:
            messagebox.showinfo("没有内容", "请先执行转换。")
            return
        txt = self.txt_snip.get(1.0, tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(txt)
        messagebox.showinfo("已复制", "SubModule.xml 片段已复制到剪贴板。")


def main():
    root = tk.Tk()
    try:
        root.call("tk", "scaling", 1.0)
    except Exception:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
