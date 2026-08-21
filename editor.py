import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

# 以编辑器所在目录作为博客根目录，避免从不同工作目录启动时扫描失败。
SCAN_ROOT = os.path.dirname(os.path.abspath(__file__))

class BlogEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("博客JSON编辑器（Tkinter桌面版）")
        self.root.geometry("1000x700")

        # 数据变量
        self.file_path_list = []    # 扫描出来全部text.json路径
        self.current_file = None    # 当前打开的文件路径
        self.blog_data = []         # 当前文件的博客数组
        self.selected_article_idx = None  # 当前选中文章下标

        # ---------- 顶部：文件选择区域 ----------
        frame_top = ttk.LabelFrame(root, text="文件选择")
        frame_top.pack(fill=tk.X, padx=8, pady=4)

        ttk.Button(frame_top, text="🔄 扫描文件夹", command=self.scan_folder).grid(row=0, column=0, padx=5, pady=6)
        self.combo_file = ttk.Combobox(frame_top, width=80, state="readonly")
        self.combo_file.grid(row=0, column=1, padx=5, pady=6)
        ttk.Button(frame_top, text="📂打开选中文件", command=self.open_selected_file).grid(row=0, column=2, padx=5, pady=6)
        ttk.Button(frame_top, text="💾保存回原文件", command=self.save_to_original_file).grid(row=0, column=3, padx=5, pady=6)

        # ---------- 主体左右分割 ----------
        main_pane = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # 左侧：文章列表
        frame_left = ttk.LabelFrame(main_pane, text="文章列表")
        main_pane.add(frame_left, weight=1)

        self.listbox_articles = tk.Listbox(frame_left)
        self.listbox_articles.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.listbox_articles.bind("<<ListboxSelect>>", self.on_select_article)

        frame_btn_left = ttk.Frame(frame_left)
        frame_btn_left.pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(frame_btn_left, text="➕新增文章", command=self.add_new_article).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(frame_btn_left, text="🗑删除文章", command=self.delete_article).pack(side=tk.LEFT, expand=True, fill=tk.X)

        frame_order = ttk.Frame(frame_left)
        frame_order.pack(fill=tk.X, padx=4, pady=(0, 4))
        ttk.Button(frame_order, text="⬆上移", command=lambda: self.move_article(-1)).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(frame_order, text="⬇下移", command=lambda: self.move_article(1)).pack(side=tk.LEFT, expand=True, fill=tk.X)

        # 右侧编辑区
        frame_right = ttk.LabelFrame(main_pane, text="编辑文章")
        main_pane.add(frame_right, weight=2)

        ttk.Label(frame_right, text="标题：").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        self.var_title = tk.StringVar()
        ttk.Entry(frame_right, textvariable=self.var_title).grid(row=0, column=1, sticky="ew", padx=6, pady=4)

        ttk.Label(frame_right, text="日期：").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        self.var_date = tk.StringVar()
        ttk.Entry(frame_right, textvariable=self.var_date).grid(row=1, column=1, sticky="ew", padx=6, pady=4)

        ttk.Label(frame_right, text="正文（换行分割body数组）：").grid(row=2, column=0, sticky="nw", padx=6, pady=4)
        self.text_body = tk.Text(frame_right)
        self.text_body.grid(row=2, column=1, sticky="nsew", padx=6, pady=4)

        ttk.Button(frame_right, text="✅应用修改到内存", command=self.apply_change).grid(row=3, column=1, sticky="ew", padx=6, pady=6)

        frame_right.grid_columnconfigure(1, weight=1)
        frame_right.grid_rowconfigure(2, weight=1)

        # 底部json预览
        frame_preview = ttk.LabelFrame(root, text="JSON预览")
        frame_preview.pack(fill=tk.BOTH, padx=8, pady=4)
        self.text_preview = tk.Text(frame_preview, height=10)
        self.text_preview.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # 启动自动扫描
        self.scan_folder()

    def scan_folder(self):
        """递归扫描目录下所有text.json"""
        self.file_path_list = []
        if not os.path.exists(SCAN_ROOT):
            messagebox.showwarning("警告", f"目录不存在：{SCAN_ROOT}，请修改代码中SCAN_ROOT路径")
            self.combo_file["values"] = []
            return

        for dirpath, _, filenames in os.walk(SCAN_ROOT):
            for fname in filenames:
                if fname == "text.json":
                    fullpath = os.path.abspath(os.path.join(dirpath, fname))
                    self.file_path_list.append(fullpath)

        self.file_path_list.sort()
        self.combo_file["values"] = self.file_path_list
        if self.file_path_list:
            self.combo_file.current(0)
            messagebox.showinfo("扫描完成", f"找到 {len(self.file_path_list)} 个 text.json")
        else:
            messagebox.showwarning("扫描完成", f"在目录中没有找到 text.json：\n{SCAN_ROOT}")

    def open_selected_file(self):
        idx = self.combo_file.current()
        if idx <0:
            return
        fp = self.file_path_list[idx]
        try:
            with open(fp, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
            if isinstance(loaded_data, dict):
                loaded_data = [loaded_data]
            if not isinstance(loaded_data, list):
                raise ValueError("JSON 根内容必须是文章对象或文章数组")
            self.blog_data = [self.normalize_article(article) for article in loaded_data]
        except Exception as e:
            messagebox.showerror("读取失败", str(e))
            return
        self.current_file = fp
        self.selected_article_idx = None
        self.clear_editor()
        self.refresh_article_list()
        self.refresh_preview()

    def save_to_original_file(self):
        if not self.current_file:
            messagebox.showwarning("提示", "请先打开一个text.json文件")
            return
        try:
            with open(self.current_file, "w", encoding="utf-8") as f:
                json.dump(self.blog_data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("保存成功", f"已写入磁盘：\n{self.current_file}")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    def refresh_article_list(self):
        self.listbox_articles.delete(0, tk.END)
        for i, art in enumerate(self.blog_data):
            display = f"[{art.get('date', '')}] {art.get('title', '未命名文章')}"
            self.listbox_articles.insert(tk.END, display)

    def refresh_preview(self):
        self.text_preview.delete("1.0", tk.END)
        pretty = json.dumps(self.blog_data, ensure_ascii=False, indent=2)
        self.text_preview.insert(tk.END, pretty)

    def on_select_article(self, event):
        sel = self.listbox_articles.curselection()
        if not sel:
            return
        i = sel[0]
        self.selected_article_idx = i
        art = self.blog_data[i]
        self.var_title.set(art.get("title", ""))
        self.var_date.set(art.get("date", ""))
        self.text_body.delete("1.0", tk.END)
        self.text_body.insert(tk.END, "\n".join(art.get("body", [])))

    def add_new_article(self):
        from datetime import date
        today = date.today().isoformat()
        new_art = {"title":"新文章", "date": today, "body":[""]}
        self.blog_data.append(new_art)
        self.refresh_article_list()
        self.refresh_preview()
        # 自动选中新增的
        new_idx = len(self.blog_data)-1
        self.listbox_articles.select_set(new_idx)
        self.selected_article_idx = new_idx
        self.on_select_article(None)

    def delete_article(self):
        if self.selected_article_idx is None:
            messagebox.showwarning("提示","请先选中一篇文章")
            return
        if not messagebox.askyesno("确认删除","确定删除这篇文章？"):
            return
        self.blog_data.pop(self.selected_article_idx)
        self.selected_article_idx = None
        self.clear_editor()
        self.refresh_article_list()
        self.refresh_preview()

    def move_article(self, offset):
        if self.selected_article_idx is None:
            messagebox.showwarning("提示", "请先选中一篇文章")
            return

        old_idx = self.selected_article_idx
        new_idx = old_idx + offset
        if new_idx < 0 or new_idx >= len(self.blog_data):
            return

        self.blog_data[old_idx], self.blog_data[new_idx] = (
            self.blog_data[new_idx], self.blog_data[old_idx]
        )
        self.selected_article_idx = new_idx
        self.refresh_article_list()
        self.refresh_preview()
        self.listbox_articles.select_set(new_idx)
        self.listbox_articles.activate(new_idx)
        self.listbox_articles.see(new_idx)
        self.on_select_article(None)

    def apply_change(self):
        if self.selected_article_idx is None:
            messagebox.showwarning("提示","请先选中一篇文章")
            return
        art = self.blog_data[self.selected_article_idx]
        art["title"] = self.var_title.get()
        art["date"] = self.var_date.get()
        body_text = self.text_body.get("1.0", tk.END).rstrip("\n")
        art["body"] = body_text.splitlines() if body_text else []
        self.refresh_article_list()
        self.refresh_preview()
        messagebox.showinfo("完成", "修改已经更新到内存，记得点【保存回原文件】写入硬盘！")

    def clear_editor(self):
        self.var_title.set("")
        self.var_date.set("")
        self.text_body.delete("1.0", tk.END)

    @staticmethod
    def normalize_article(article):
        if not isinstance(article, dict):
            raise ValueError("每篇文章必须是 JSON 对象")
        body = article.get("body", [])
        if isinstance(body, str):
            body = body.splitlines()
        if not isinstance(body, list):
            body = []
        return {
            "title": str(article.get("title", "")),
            "date": str(article.get("date", "")),
            "body": [str(paragraph) for paragraph in body],
        }


if __name__ == "__main__":
    root = tk.Tk()
    app = BlogEditorApp(root)
    root.mainloop()
