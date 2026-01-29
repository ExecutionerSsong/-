import sys
import os
import random
import ctypes
import pygame
import pyautogui
import tkinter as tk
from tkinter.font import Font
from PIL import Image, ImageTk
import winreg as reg
import threading
import simpleaudio as sa

# -------------------------- 桌宠核心配置（可微调） --------------------------
GIF_NAME = "Blade.gif"  # GIF文件名
AUDIO_NAMES = [f"line{i}.wav" for i in range(1, 6)]  # WAV音频
TEXT_FILE = "lines.txt"  # 台词文本文件
PET_WIDTH = 320  # 桌宠宽
PET_HEIGHT = 320  # 桌宠高
OFFSET_X = 50  # 初始位置右偏移
OFFSET_Y = 50  # 初始位置下偏移
GIF_PLAY_SPEED = 100  # GIF播放速度（越小越快）
BUBBLE_FONT = ("微软雅黑", 12)  # 气泡字体/大小
BUBBLE_PAD = 10  # 气泡内边距
BUBBLE_GAP = 10  # 气泡与桌宠的间距
LINE_BREAK_NUM = 8  # 按8字自动换行
PRUSSIAN_BLUE = "#003153"  # 普鲁士蓝标准十六进制色码
# -----------------------------------------------------------------------------

# 忽略无关警告+隐藏控制台黑框
import warnings
warnings.filterwarnings("ignore")
pygame.init()
if sys.platform == "win32":
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass

# 打包路径适配：EXE/py运行均能找到resource文件夹
def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# 资源绝对路径（兼容中文/打包/直接运行）
RESOURCE_PATH = get_resource_path("resource")
GIF_PATH = os.path.join(RESOURCE_PATH, GIF_NAME)
AUDIO_PATHS = [os.path.join(RESOURCE_PATH, name) for name in AUDIO_NAMES]
TEXT_PATH = os.path.join(RESOURCE_PATH, TEXT_FILE)

# 全局音频播放实例（秒切核心）
global_play_obj = None

# 加载台词：按行读取，与音频一一对应，UTF-8防中文乱码
def load_lines():
    lines = []
    try:
        with open(TEXT_PATH, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        # 台词数不足音频数时补空，避免索引错误
        if len(lines) < len(AUDIO_PATHS):
            lines += [""] * (len(AUDIO_PATHS) - len(lines))
    except:
        lines = [""] * len(AUDIO_PATHS)
    return lines
LINE_TEXTS = load_lines()

# 音频秒切播放：停止当前音频→播放新音频，无延迟
def play_audio(audio_idx):
    global global_play_obj
    if global_play_obj and global_play_obj.is_playing():
        global_play_obj.stop()
    try:
        wave_obj = sa.WaveObject.from_wave_file(AUDIO_PATHS[audio_idx])
        global_play_obj = wave_obj.play()
    except:
        pass

# 工具函数：按指定字数自动换行，返回带\n的字符串
def split_text_by_num(text, num=LINE_BREAK_NUM):
    if not text:
        return ""
    return "\n".join([text[i:i + num] for i in range(0, len(text), num)])

# 桌宠主类：集成所有功能，气泡强覆盖纯白底色+普鲁士蓝文字
class RenPet:
    def __init__(self):
        # 主窗口：桌宠（无框/置顶/透明无白框，原有逻辑不变）
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "white")
        self.root.config(bg="white")
        self.root.geometry(f"{PET_WIDTH}x{PET_HEIGHT}")

        # 初始化气泡字体（tkinter原生，100%兼容）
        self.bubble_font = Font(family=BUBBLE_FONT[0], size=BUBBLE_FONT[1])

        # 核心设置：气泡窗口取消透明，强覆盖纯白底色
        self.bubble_win = tk.Toplevel(self.root)
        self.bubble_win.overrideredirect(True)  # 无框
        self.bubble_win.wm_attributes("-topmost", True)  # 始终顶层显示
        self.bubble_win.config(bg="#FFFFFF")  # 气泡窗口纯白背景，强覆盖
        self.bubble_win.withdraw()  # 初始隐藏

        # 气泡画布：纯白背景，无高亮边框，和窗口底色一致
        self.bubble_cvs = tk.Canvas(self.bubble_win, bg="#FFFFFF", highlightthickness=0, bd=0)
        self.bubble_cvs.pack()

        # 拖动功能核心变量
        self.is_dragging = False
        self.drag_x0 = 0
        self.drag_y0 = 0
        self.mouse_x0 = 0
        self.mouse_y0 = 0

        # 初始位置：屏幕右下角，气泡随桌宠定位
        self.set_init_pos()

        # 加载GIF帧并循环播放
        self.gif_frames = self.load_gif_frames()
        self.cur_frame = 0
        self.gif_label = tk.Label(self.root, bg="white", borderwidth=0)
        self.gif_label.pack(fill=tk.BOTH, expand=True)
        self.play_gif_loop()

        # 绑定所有鼠标交互事件
        self.bind_mouse_events()

        # 自动设置开机自启
        self.set_auto_start()

    def load_gif_frames(self):
        """加载GIF所有帧，防文件缺失崩溃"""
        frames = []
        try:
            gif = Image.open(GIF_PATH)
            while True:
                frame = gif.copy().resize((PET_WIDTH, PET_HEIGHT), Image.Resampling.LANCZOS)
                frames.append(ImageTk.PhotoImage(frame))
                gif.seek(gif.tell() + 1)
        except:
            pass
        return frames

    def play_gif_loop(self):
        """GIF无限循环播放，无卡顿"""
        if self.gif_frames:
            self.cur_frame = (self.cur_frame + 1) % len(self.gif_frames)
            self.gif_label.config(image=self.gif_frames[self.cur_frame])
        self.root.after(GIF_PLAY_SPEED, self.play_gif_loop)

    def set_init_pos(self):
        """设置桌宠初始位置：屏幕右下角"""
        screen_w, screen_h = pyautogui.size()
        win_x = screen_w - PET_WIDTH - OFFSET_X
        win_y = screen_h - PET_HEIGHT - OFFSET_Y
        self.root.geometry(f"+{win_x}+{win_y}")

    def update_bubble_pos(self):
        """更新气泡位置：桌宠左侧垂直居中，拖动同步跟随"""
        if self.bubble_win.winfo_ismapped():
            pet_x = self.root.winfo_x()
            pet_y = self.root.winfo_y()
            bub_w = self.bubble_win.winfo_width()
            bub_h = self.bubble_win.winfo_height()
            bub_x = pet_x - bub_w - BUBBLE_GAP
            bub_y = pet_y + (PET_HEIGHT - bub_h) // 2
            self.bubble_win.geometry(f"+{bub_x}+{bub_y}")

    def draw_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        """tkinter原生兼容的圆角矩形，无轮廓"""
        points = [
            x1 + r, y1,  # 左上圆角起点
            x2 - r, y1,  # 右上圆角起点
            x2, y1 + r,  # 右上圆角终点
            x2, y2 - r,  # 右下圆角起点
            x2 - r, y2,  # 右下圆角终点
            x1 + r, y2,  # 左下圆角终点
            x1, y2 - r,  # 左下圆角起点
            x1, y1 + r,  # 左上圆角终点
            x1 + r, y1  # 回到起点，原生闭合
        ]
        return self.bubble_cvs.create_polygon(points, **kwargs, smooth=True)

    def show_bubble(self, text):
        """气泡秒切+8字换行+强覆盖纯白+无轮廓+普鲁士蓝文字"""
        self.bubble_cvs.delete("all")
        if not text:
            self.bubble_win.withdraw()
            return

        # 1. 按8字自动换行处理文本
        wrapped_text = split_text_by_num(text)
        lines = wrapped_text.split("\n")
        # 2. 计算多行文字的宽高（适配任意行数）
        line_h = self.bubble_font.metrics("linespace")
        max_line_w = max([self.bubble_font.measure(line) for line in lines])
        total_text_w = max_line_w
        total_text_h = line_h * len(lines)
        # 3. 计算气泡整体尺寸（文字+内边距）
        bub_w = total_text_w + 2 * BUBBLE_PAD
        bub_h = total_text_h + 2 * BUBBLE_PAD
        r = 8  # 圆角半径

        # 纯空白泡主体：无轮廓，纯白填充（强覆盖）
        self.draw_rounded_rect(0, 0, bub_w, bub_h, r, fill="#FFFFFF")
        # 气泡小三角：纯白无轮廓，和主体统一
        tri_x = bub_w
        tri_y = bub_h // 2
        self.bubble_cvs.create_polygon(tri_x, tri_y - 5, tri_x + 8, tri_y, tri_x, tri_y + 5, fill="#FFFFFF")
        # 绘制普鲁士蓝文字，经典正蓝，对比度拉满
        for i, line in enumerate(lines):
            y_pos = BUBBLE_PAD + line_h * i
            self.bubble_cvs.create_text(BUBBLE_PAD, y_pos, text=line,
                                        font=self.bubble_font, fill=PRUSSIAN_BLUE, anchor="nw")

        # 刷新气泡窗口并更新位置
        self.bubble_win.geometry(f"{bub_w + 8}x{bub_h}")
        self.bubble_win.deiconify()
        self.bubble_win.update_idletasks()
        self.update_bubble_pos()

    def bind_mouse_events(self):
        """绑定所有鼠标事件：拖动/秒切/右键退出"""
        # 桌宠区域事件绑定
        for widget in [self.root, self.gif_label]:
            widget.bind("<ButtonPress-1>", self.on_mouse_press)
            widget.bind("<B1-Motion>", self.on_mouse_drag)
            widget.bind("<ButtonRelease-1>", self.on_mouse_release)
            widget.bind("<Button-3>", self.quit_pet)
        # 气泡区域右键退出绑定
        for widget in [self.bubble_win, self.bubble_cvs]:
            widget.bind("<Button-3>", self.quit_pet)

    def on_mouse_press(self, event):
        """左键按下：标记开始拖动"""
        self.is_dragging = True
        self.drag_x0 = self.root.winfo_x()
        self.drag_y0 = self.root.winfo_y()
        self.mouse_x0 = event.x_root
        self.mouse_y0 = event.y_root

    def on_mouse_drag(self, event):
        """左键拖动：移动桌宠+同步气泡位置"""
        if self.is_dragging:
            dx = event.x_root - self.mouse_x0
            dy = event.y_root - self.mouse_y0
            screen_w, screen_h = pyautogui.size()
            # 限制桌宠不超出屏幕边界
            new_x = max(0, min(self.drag_x0 + dx, screen_w - PET_WIDTH))
            new_y = max(0, min(self.drag_y0 + dy, screen_h - PET_HEIGHT))
            self.root.geometry(f"+{new_x}+{new_y}")
            self.update_bubble_pos()

    def on_mouse_release(self, event):
        """左键松开：拖动结束/音频+气泡同步秒切"""
        if self.is_dragging:
            self.is_dragging = False
        else:
            if AUDIO_PATHS and LINE_TEXTS:
                # 随机选音频/台词索引
                idx = random.randint(0, len(AUDIO_PATHS) - 1)
                # 主线程更新气泡（瞬间响应，无延迟）
                self.show_bubble(LINE_TEXTS[idx])
                # 子线程播放音频（避免GIF卡顿）
                threading.Thread(target=lambda: play_audio(idx), daemon=True).start()

    def set_auto_start(self):
        """设置开机自启，兼容py/EXE运行"""
        try:
            app_path = os.path.abspath(__file__)
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_WRITE)
            reg.SetValueEx(key, "刃桌宠", 0, reg.REG_SZ, app_path)
            reg.CloseKey(key)
        except:
            pass

    def quit_pet(self, event=None):
        """右键退出：停止音频+关闭所有窗口，无残留"""
        try:
            global global_play_obj
            if global_play_obj and global_play_obj.is_playing():
                global_play_obj.stop()
            self.bubble_win.destroy()
            self.root.destroy()
            pygame.quit()
            sys.exit(0)
        except:
            pass

    def run(self):
        """启动桌宠主循环"""
        self.root.mainloop()

# 程序入口：无任何额外绑定，直接启动
if __name__ == "__main__":
    pet = RenPet()
    pet.run()