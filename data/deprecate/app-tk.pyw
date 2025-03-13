"""
图形界面版本（tkinter实现）：智慧教育平台资源下载工具
"""

import argparse
import logging
import time
import tkinter as tk
import tkinter.font as tkFont
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from tools.downloader import download_files_tk, fetch_all_data
from tools.parser import extract_resource_url, parse_urls
from tools.utils import base64_to_image
from tools.theme import set_theme, set_dpi_scale
from tools.parser import RESOURCE_DICT
from tools.logo import DESCRIBES, LOGO_TEXT
from tools.icons import ICON_LARGE, ICON_SMALL


RESOURCE_FORMATS = ["pdf", "mp3", "ogg", "jpg", "m3u8", "superboard"]
RESOURCE_NAMES = ["文档", "音频", "音频", "图片", "视频", "白板"]


def display_results(results: list, elapsed_time: float):
    """展示下载结果统计"""
    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = len(results) - success_count

    messages = [
        ["总计文件", str(len(results))],
        ["成功下载", f"{success_count}"],
        ["下载失败", f"{failed_count}"],
        ["总用时", f"{elapsed_time:.1f}秒"],
    ]
    return "\n".join([": ".join(v) for v in messages])


def update_labels_wraplength(event, labels, scale=1.0, delta=20, frame=None):
    # 更新标签的wraplength
    if not labels:
        return
    if frame:
        width = frame.winfo_width()
    elif event:
        width = event.width
    else:
        width = labels[0].winfo_toplevel().winfo_width()
    wraplength = int(width - delta * scale)

    for label in labels:
        label.configure(wraplength=wraplength)


class InputURLAreaFrame(ttk.Frame):
    """手动输入面板"""

    def __init__(self, parent, fonts, font_size, scale=1.0, os_name=None):
        super().__init__(parent)
        self.fonts = fonts
        self.font_size = font_size
        self.scale = scale
        self.padx = int(5 * scale)
        self.pady = int(5 * scale)

        self.setup_ui()

    def setup_ui(self):
        """初始化UI"""

        # 创建输入区域
        input_frame = ttk.LabelFrame(self, text="输入URL（每行一个）", padding=self.padx * 2)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=self.padx, pady=self.pady)

        # 创建文本框和滚动条
        text_frame = ttk.Frame(input_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=self.pady)

        self.text = tk.Text(
            text_frame, height=5, width=20, font=(self.fonts["sans_serif"], self.font_size)
        )
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)

        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 添加清空按钮
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill=tk.X, pady=self.pady)
        clean_btn = ttk.Button(
            btn_frame, text="清空", command=lambda: self.text.delete("1.0", tk.END)
        )
        clean_btn.pack(side=tk.RIGHT)

        # 创建说明区域
        help_frame = ttk.LabelFrame(self, text="格式说明", padding=self.padx * 2)
        help_frame.pack(fill=tk.BOTH, expand=True, padx=self.padx, pady=self.pady)

        keys = ["/tchMaterial", "/syncClassroom"]
        texts = ""
        for i, key in enumerate(keys, 1):
            config = RESOURCE_DICT[key]
            texts += f"{i}. {config['name'][:2]}URL：" + str(config["resources"]["detail"]) + "\n"

        help_text = f"支持的URL格式示例：\n{texts}\n可以直接从浏览器地址复制URL。"
        help_label = ttk.Label(
            help_frame, text=help_text, justify=tk.LEFT, font=(self.fonts["kaiti"], self.font_size)
        )
        help_label.pack(fill=tk.X, padx=self.padx, pady=self.pady)
        help_frame.bind(
            "<Configure>", lambda e: update_labels_wraplength(e, [help_label], self.scale)
        )

    def get_urls(self) -> list:
        """获取输入的URL列表"""
        text = self.text.get("1.0", tk.END).strip()
        urls = [url.strip() for url in text.split("\n") if url.strip()] if text else []
        return urls


class DownloadApp(tk.Tk):
    """主应用窗口"""

    def __init__(self, scale=1.0, os_name=None):
        super().__init__()
        self.frame_names = ["books", "inputs"]
        self.frame_titles = ["教材列表", "手动输入"]
        self.desc_texts = DESCRIBES
        self.download_dir = Path.home() / "Downloads"  # 改为用户目录

        self.scale = scale
        self.os_name = os_name
        width = int(750 * scale)
        height = int(700 * scale)
        self.padx = int(5 * scale)
        self.pady = int(5 * scale)

        # 图形大小
        self.title(self.desc_texts[0])
        self.geometry(f"{width}x{height}")
        self.wm_minsize(width=int(width * 0.8), height=int(height * 0.9))
        # self.resizable(False, False)  # Prevent resizing the window

        # 设置主题
        # style = ttk.Style()
        # style.theme_use('')

        # 设置Icon
        small_icon_file = base64_to_image(ICON_SMALL, "icon_small.png")
        large_icon_file = base64_to_image(ICON_LARGE, "icon_large.png")
        small_icon = tk.PhotoImage(file=small_icon_file)
        large_icon = tk.PhotoImage(file=large_icon_file)
        self.iconphoto(False, large_icon, small_icon)

        self.fonts, default_size = self.setup_fonts()
        self.font_size = int(default_size * min((1.1 + (scale - 1) * 0.3), 1.5))

        self.setup_ui()

    def setup_ui(self):
        """初始化UI: 标题、目录+下载按钮、单选按钮、内容区域、进度条"""

        main_frame = ttk.Frame(self)  # padding=self.padx*2
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.setup_title_frame(main_frame)
        self.setup_mode_frame(main_frame)
        self.setup_control_frame(main_frame)

    def setup_fonts(self):
        font_families = {
            "sans_serif": ["Arial", "Helvetica", "Segoe UI", "Roboto"],
            "serif": ["Georgia", "Times New Roman"],
            "monospace": ["Monaco", "Courier New", "Consolas"],
            "kaiti": ["STKaiti", "SimKai", "楷体"],
        }
        default_font = tkFont.nametofont("TkDefaultFont")
        default_family = default_font.actual("family")
        default_size = default_font.actual("size")
        available_fonts = tkFont.families()

        font_dict = {}
        for key, fonts in font_families.items():
            for font in fonts:
                if font in available_fonts:
                    font_dict[key] = font
                    break
            else:
                font_dict[key] = default_family
        return font_dict, default_size

    def setup_title_frame(self, main_frame):
        # 1. 添加标题和LOGO
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            title_frame, text=LOGO_TEXT, anchor=tk.CENTER, font=(self.fonts["monospace"],)
        ).pack(fill=tk.BOTH, expand=True)
        slogan_label = ttk.Label(
            title_frame,
            text=self.desc_texts[2],
            anchor=tk.CENTER,
            font=(self.fonts["kaiti"], self.font_size),
        )
        slogan_label.pack(fill=tk.BOTH, expand=True, pady=self.pady)
        title_frame.bind(
            "<Configure>", lambda e: update_labels_wraplength(e, [slogan_label], self.scale)
        )

    def setup_mode_frame(self, main_frame):
        # 3. 模式选择：两个单选按钮
        self.mode_var = tk.StringVar(value=self.frame_names[0])
        mode_frame = ttk.Frame(main_frame)
        mode_frame.pack(fill=tk.BOTH, expand=True, pady=self.pady)

        radio1 = ttk.Radiobutton(
            mode_frame,
            text=self.frame_titles[0],
            value=self.frame_names[0],
            variable=self.mode_var,
            command=self.switch_mode,
        )

        radio2 = ttk.Radiobutton(
            mode_frame,
            text=self.frame_titles[1],
            value=self.frame_names[1],
            variable=self.mode_var,
            command=self.switch_mode,
        )
        # radio1.pack(side=tk.LEFT, fill=tk.X, padx=self.padx * 2)
        radio2.pack(side=tk.LEFT, fill=tk.X, padx=self.padx * 2)

        # 4. 内容区域，包括两个面板，单选控制
        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        # self.selector_frame = BookSelectorFrame(
        #     self.content_frame, self.fonts, self.font_size, self.scale, self.os_name
        # )
        self.inputs_frame = InputURLAreaFrame(
            self.content_frame, self.fonts, self.font_size, self.scale, self.os_name
        )

        # 默认显示教材列表面板
        self.inputs_frame.pack(fill=tk.BOTH, expand=True, pady=self.pady * 2)

    def setup_control_frame(self, main_frame):
        # New: 资源类型选项
        formats_frame = ttk.Frame(main_frame)
        formats_frame.pack(fill=tk.X, pady=self.pady)
        ttk.Label(formats_frame, text="资源类型").pack(side=tk.LEFT, padx=self.padx)

        self.formats_vars = {}
        for name, suffix in zip(RESOURCE_NAMES, RESOURCE_FORMATS):
            var = tk.BooleanVar()
            self.formats_vars[suffix] = var
            value, state = False, "enable"
            if suffix == RESOURCE_FORMATS[0]:
                value = True
            if suffix == RESOURCE_FORMATS[-2]:
                state = "disabled"
            var.set(value)
            text = f"{name}({suffix})" if name in ["文档", "音频"] else name
            checkbutton = ttk.Checkbutton(
                formats_frame, text=text, variable=var, onvalue=1, offvalue=0, state=state
            )
            checkbutton.pack(side=tk.LEFT, padx=self.padx)

        # 2. 目录+下载按钮
        download_frame = ttk.Frame(main_frame)
        download_frame.pack(fill=tk.X, pady=self.pady)

        # 目录选择
        dir_frame = ttk.Frame(download_frame)
        dir_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(dir_frame, text="保存目录：").pack(side=tk.LEFT, padx=self.padx)
        self.dir_var = tk.StringVar(value=self.download_dir)
        dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var)
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=self.pady)
        ttk.Button(dir_frame, text="选择目录", command=self.choose_directory).pack(side=tk.LEFT)

        # 下载按钮
        ttk.Button(download_frame, text="开始下载", command=self.start_download).pack(
            side=tk.LEFT, padx=self.padx * 2
        )

        # 底部添加进度条区域
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(fill=tk.X, pady=self.pady)

        # 5. 进度条和标签
        self.progress_var = tk.DoubleVar()
        self.progress_label = ttk.Label(self.progress_frame, text="暂无下载内容")
        self.progress_label.pack(fill=tk.X, padx=self.padx, pady=self.pady)

        self.progress_bar = ttk.Progressbar(
            self.progress_frame, mode="determinate", variable=self.progress_var
        )
        self.progress_bar.pack(fill=tk.X, pady=self.pady)

        # 默认隐藏进度条区域
        # self.progress_frame.pack_forget()

    def choose_directory(self):
        """选择保存目录"""
        directory = filedialog.askdirectory(title="选择保存目录", initialdir=self.dir_var.get())
        if directory:
            self.dir_var.set(directory)

    def switch_mode(self):
        """切换模式"""
        # if self.mode_var.get() == self.frame_names[0]:
        #     self.inputs_frame.pack_forget()
        #     self.selector_frame.pack(fill=tk.BOTH, expand=True)
        # else:
        #     self.selector_frame.pack_forget()
        self.inputs_frame.pack(fill=tk.BOTH, expand=True)
        self.inputs_frame.text.focus_set()  # 聚焦在输入框

    def start_download(self):
        """开始下载"""
        # 获取URL列表
        # if self.mode_var.get() == self.frame_names[0]:
        #     urls = self.selector_frame.get_selected_urls()
        # else:
        urls = self.inputs_frame.get_urls()

        if not urls:
            messagebox.showwarning("警告", "请先选择要下载的资源或输入链接")
            return

        suffix_list = [suffix for suffix, var in self.formats_vars.items() if var.get()]
        if len(suffix_list) == 0:
            messagebox.showwarning("警告", "请至少选择一个下载的资源类型。")
            return

        # 确认下载弹窗
        # save_dir = self.dir_var.get()
        # if not messagebox.askyesno("确认下载", f"将下载 {len(urls)} 个资源到目录：\n{save_dir}\n\n是否继续？"):
        #     return

        try:
            # 显示进度条
            self.progress_var.set(0)
            self.progress_label.configure(text="准备开始下载...")
            self.update()
            result, elapsed_time = self.simple_download(urls, suffix_list)
            self.progress_label.configure(text="下载完成。")

            if result:
                message = display_results(result, elapsed_time)
            else:
                message = "下载列表为空"
            messagebox.showinfo("下载结果", message)

        except Exception as e:
            messagebox.showerror("错误", f"下载失败：{str(e)}")

    def simple_download(self, urls, suffix_list):
        save_path = self.dir_var.get()
        logging.debug(f"\n共选择 {len(urls)} 项目，将保存到 {save_path} 目录，类型 {suffix_list}")

        # 更新进度显示
        self.progress_label.configure(text="正在解析URL...")
        base_progress = 10
        self.progress_var.set(base_progress)
        self.update()

        config_urls = parse_urls(urls, suffix_list)
        resource_dict = fetch_all_data(
            config_urls, lambda data: extract_resource_url(data, suffix_list)
        )

        total = len(resource_dict)
        self.progress_label.configure(
            text=f"共找到配置链接 {len(config_urls)} 项，资源文件 {total} 项"
        )
        base_progress = 20
        self.progress_var.set(base_progress)
        self.update()

        if total == 0:
            logging.warning(f"\n没有找到资源文件（{'/'.join(suffix_list)}等）。结束下载")
            return None, None

        # 开始下载
        start_time = time.time()

        # 更新进度显示
        self.progress_label.configure(text=f"开始下载 {total} 项资源...")
        self.update()
        results = download_files_tk(self, resource_dict, save_path, base_progress=base_progress)

        # 更新进度显示
        self.progress_var.set(100)
        self.update()

        elapsed_time = time.time() - start_time
        return results, elapsed_time


def main(theme=None):
    scale, os_name = set_dpi_scale()
    app = DownloadApp(scale, os_name)
    set_theme(theme=theme, font_scale=scale)
    app.eval("tk::PlaceWindow . center")
    app.mainloop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument(
        "--theme", "-t", default="auto", type=str, choices=["light", "dark", "auto", "raw"]
    )
    args = parser.parse_args()

    # 配置日志
    fmt = "%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s %(message)s"
    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level, format=fmt)
    logging.debug("调试模式已启用")

    main(args.theme)
