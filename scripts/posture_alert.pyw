"""Posture reminder banner (Windows, tkinter, no console window).

Usage:
    pythonw.exe posture_alert.pyw "<title>" "<message>" [duration_ms]

Shows a topmost card at the bottom-right corner of the primary screen, plays a
short system sound, and closes itself after ``duration_ms`` (default 9000).
Clicking anywhere on the card closes it early.
"""
import sys
import tkinter as tk

TITLE = sys.argv[1] if len(sys.argv) > 1 else "坐姿提醒"
MESSAGE = sys.argv[2] if len(sys.argv) > 2 else "请坐直一点！"
try:
    DURATION_MS = int(sys.argv[3]) if len(sys.argv) > 3 else 9000
except ValueError:
    DURATION_MS = 9000

BG = "#12181f"
FG_TITLE = "#ff8f8f"
FG_TEXT = "#eef3f8"
FG_HINT = "#8596a6"
ACCENT = "#e5484d"

try:
    import winsound

    winsound.PlaySound(
        "SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC
    )
except Exception:
    pass

root = tk.Tk()
root.withdraw()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.configure(bg=BG)
try:
    root.attributes("-alpha", 0.97)
except Exception:
    pass

# Optional app icon (PNG, resized with Pillow when available).
try:
    from PIL import Image, ImageTk

    _img = Image.open(r"D:\Apps\PostureGuard\app_icon_64.png").convert("RGBA")
    _icon = ImageTk.PhotoImage(_img)
    root.iconphoto(True, _icon)
except Exception:
    pass

card = tk.Frame(root, bg=BG, bd=0, highlightthickness=0)
card.pack(fill="both", expand=True)
tk.Frame(card, bg=ACCENT, width=7).pack(side="left", fill="y")
body = tk.Frame(card, bg=BG, padx=20, pady=15)
body.pack(side="left", fill="both", expand=True)

title_label = tk.Label(
    body,
    text=TITLE,
    bg=BG,
    fg=FG_TITLE,
    font=("Microsoft YaHei UI", 15, "bold"),
    anchor="w",
)
title_label.pack(fill="x")
msg_label = tk.Label(
    body,
    text=MESSAGE,
    bg=BG,
    fg=FG_TEXT,
    font=("Microsoft YaHei UI", 12),
    anchor="w",
    justify="left",
    wraplength=430,
)
msg_label.pack(fill="x", pady=(7, 0))
hint_label = tk.Label(
    body,
    text="点击关闭 · 几秒后自动消失",
    bg=BG,
    fg=FG_HINT,
    font=("Microsoft YaHei UI", 9),
    anchor="w",
)
hint_label.pack(fill="x", pady=(11, 0))

root.update_idletasks()
pad = 28
w = max(root.winfo_reqwidth() + 16, 400)
h = root.winfo_reqheight() + 10
sw = root.winfo_screenwidth()
sh = root.winfo_screenheight()
x = sw - w - pad
y = sh - h - 96
root.geometry(f"{w}x{h}+{x}+{y}")


def close(*_args):
    try:
        root.destroy()
    except Exception:
        pass


for widget in (root, card, body, title_label, msg_label, hint_label):
    widget.bind("<Button-1>", close)

root.after(DURATION_MS, close)
root.deiconify()
root.lift()
root.attributes("-topmost", True)
root.mainloop()
