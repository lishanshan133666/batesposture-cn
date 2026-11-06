# batesposture-cn · Windows 中文坐姿提醒

基于开源项目 [`wtbates99/batesposture`](https://github.com/wtbates99/batesposture)（GitHub 26 ★，MIT，PyPI 包名 `batesposture` 1.1.1）的 **Windows 本机适配 + 中文化** 版本。

用普通 USB 摄像头实时检测坐姿，给出 0–100 的姿势评分；姿势变差时在屏幕右下角弹出中文提醒卡片并播放提示音，全程系统托盘后台运行。

> 上游项目本身很好，但它的代码按 `mediapipe` 旧版 `solutions` API 写、依赖 PyQt6 最新版，在 2026 年的 Windows + Python 3.12 环境里装完直接启动会连续报错。本仓库记录并自动化了让它跑起来、并且用起来顺手的全部改动。

---

## ✨ 功能

- **实时评分**：MediaPipe Pose 33 个关键点 → 头/颈/肩/脊柱相对位置 → 0–100 分
- **实时面板**：摄像头画面 + 骨架叠加 + 中文评分浮字 + 分数曲线 + 当前/平均/最低/最高/最佳保持/时长
- **中文提醒**：低于阈值时右下角置顶卡片「坐姿提醒 — 坐直一点！…」+ 系统提示音（不依赖 Windows 原生 toast）
- **中文基础设置**：开机自启、提醒开关、专注模式、历史记录、提醒阈值、提醒最短间隔、摄像头编号、检测频率
- **托盘常驻**：开始/停止检测、显示面板、检测频率、导出 CSV、退出；离开座位自动暂停
- **本地记录**：分数历史存 SQLite，可导出 CSV
- **开机自启 + 启动即检测**：登录后自动后台运行；默认连续监测（摄像头常开）

## 🖥 环境

- Windows 11（Windows 10 也可以），Python 3.12
- 任意 USB / 笔记本摄像头（推荐能拍到「头 + 双肩 + 上半身」的取景）
- 屏幕 1280×720 以上

## 📦 安装

默认安装位置 `D:\Apps\PostureGuard`（本仓库的补丁里有几个绝对路径常量指向这里，见下文「安装路径」）。

```powershell
# 1. 准备目录和虚拟环境
New-Item -ItemType Directory -Force D:\Apps\PostureGuard
cd D:\Apps\PostureGuard
python -m venv venv

# 2. 安装依赖（国内用清华镜像）
.\venv\Scripts\python.exe -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple `
    batesposture==1.1.1 mediapipe==0.10.35 pyqt6==6.9.1

# 3. 把本仓库的文件放到 D:\Apps\PostureGuard（repair.py、patches\、shim\、scripts\、app.ico）
#    这一步也可以直接 git clone 到该目录后执行
.\venv\Scripts\python.exe repair.py

# 4. 启动
.\venv\Scripts\pythonw.exe -m batesposture
```

`repair.py` 是幂等的，会依次完成：

1. 固定版本：`mediapipe==0.10.35`、`pyqt6==6.9.1`
2. 安装 MediaPipe 旧 API 兼容层（`mediapipe/python/solutions/`）
3. 补 `camera_service.py` 的 DirectShow 后端
4. 替换通知模块（本地提醒卡片 + 声音）
5. 安装中文界面补丁（托盘 / 面板 / 设置窗口）
6. 面板快捷入口 + 托盘自动开始检测
7. 自检：mediapipe 版本 / 35 条骨架连线 / 摄像头抓帧

装完托盘出现图标，约 1.5 秒后自动开始检测。

## 🚀 使用（界面已全部中文）

| 入口 | 说明 |
| --- | --- |
| 托盘右键 | 开始检测 / 显示监控面板 / 姿势提醒 / 历史记录 / 专注模式 / 设置… / 导出历史数据 (CSV)… / 检测频率 / 退出 |
| 托盘「显示监控面板」 | 实时画面 + 骨架 + 中文评分 + 曲线 + 统计 + 快捷开关（开机自启、姿势提醒） |
| 托盘「设置…」 | 中文设置窗口：开机自启、提醒开关、专注模式、历史记录、阈值、最短间隔、摄像头编号、检测频率 |
| 桌面「坐姿实时监控」 | 一键唤醒面板（程序未运行会先自动启动） |

评分 **低于 60 分**触发提醒，默认 **5 分钟**内不重复；阈值和间隔都能在设置里改。

**摄像头摆放**：正对自己、高度约在眼睛/胸口水平，画面里能看到完整的头、双肩和上半身；纯侧面/背后拍不到肩高差，分数会不准。

**火绒等安全软件**：首次启用摄像头会弹「发现软件启用摄像头」，请点「允许」并记住，否则摄像头调用会被拦截。

## 🗂 目录结构

```
batesposture-cn/
├─ repair.py                 # 一键应用全部适配（幂等）
├─ install.ps1               # 可选的安装脚本（建 venv、装依赖、跑 repair、建快捷方式）
├─ 使用说明.md                # 面向使用者的详细中文说明
├─ patches/
│  ├─ ui_zh.py               # 中文设置窗口 + 开机自启读写
│  ├─ ui_patch.py            # 托盘/面板汉化、快捷开关、评分浮字中文化
│  └─ util__send_notification.py  # Windows 本地提醒卡片 + 声音
├─ shim/
│  ├─ install_shim.py        # 把兼容层装进 mediapipe 包目录
│  └─ python/                # mediapipe.python.solutions 兼容实现（pose / drawing_utils）
├─ scripts/
│  ├─ posture_alert.pyw      # 右下角中文提醒卡片
│  ├─ open_dashboard.py      # 唤醒运行中的实例并打开面板
│  └─ test_pipeline.py       # 摄像头 + 打分/绘图冒烟测试
├─ app.ico / app_icon_64.png # 图标
└─ requirements.txt
```

## 🔧 相对上游做了哪些改动

上游 `batesposture` 1.1.1 的原始代码一行没改地保留在 `venv\Lib\site-packages\batesposture`，本仓库的改动都通过 `repair.py` 以「补丁/替换/兼容层」的方式注入，升级后重跑一次即可恢复。

1. **PyQt6 降到 6.9.1**
   最新 6.12.0 在这台机器上 `import PyQt6.QtCore` 直接 `DLL load failed while importing QtCore: 找不到指定的程序`；6.9.1 正常。
2. **MediaPipe 旧 API 兼容层（`shim/`）**
   当前 pip 能装到的 mediapipe（1.2.2 / 0.10.35）都已经没有 `mediapipe.python.solutions`，只剩 `mediapipe.tasks`。兼容层用新版 `PoseLandmarker` 重新实现 `mp.solutions.pose.Pose`（33 个关键点、35 条连线、`POSE_CONNECTIONS`、`drawing_utils.draw_landmarks`），模型自动下载到 `models\` 并缓存。上游 `mediapipe_compat.py` 原样可用。
3. **摄像头后端改用 DirectShow（`patches` 注入到 `camera_service.py`）**
   默认 MSMF 后端在这台机器上读一帧后报 `CvCapture_MSMF::grabFrame ... Error: -2147483638`；改为 `cv2.CAP_DSHOW` 优先、缓冲 1 帧后稳定出帧。同时修复了上游补丁方式引入的 `NameError: os`。
4. **提醒通道重写（`patches/util__send_notification.py`）**
   原生 Windows toast 在本机完全不显示（非专注助手/通知设置问题），于是 Windows 分支改为拉起 `scripts\posture_alert.pyw` 画一个置顶深色中文卡片 + `winsound` 提示音；动态文案（定时抽查、久坐提醒）也翻译成中文。macOS/Linux 分支保持原逻辑。
5. **默认连续监测 + 启动即检测**
   上游默认每 30 分钟才扫 2 分钟、首次启动弹校准向导。这里把间隔默认改为 0（连续），启动 1.5 秒后自动开始跟踪，并写入校准基线（可随时重新校准）。
6. **全中文界面 + 基础设置（`patches/ui_zh.py`、`patches/ui_patch.py`）**
   托盘菜单 34 处、实时面板 24 处文案汉化；面板底部新增「开机自启 / 姿势提醒」快捷开关和「更多设置…」；新增中文设置窗口（`BasicSettingsDialog`），开机自启写入注册表 `HKCU\...\CurrentVersion\Run`。设置窗口入口通过 `open_settings_zh` 接管托盘「设置…」。
7. **画面评分浮字中文化**
   OpenCV 自带字体画不出中文，改成 PIL + 微软雅黑绘制「坐姿评分：xx 分」，并保留低分时的中文提醒文案。
8. **面板快捷入口（`scripts/open_dashboard.py`）**
   托盘里加了一个标志文件监听：已运行时写 `open_dashboard.flag` 即打开面板；未运行时先启动再打开。

## ⚠️ 已知限制

- **安装路径**：`patches/ui_zh.py`（`RUN_COMMAND`）、`patches/util__send_notification.py`（`_ALERT_SCRIPT`）、`patches/ui_patch.py`（`_DASHBOARD_FLAG`）、`shim/python/solutions/pose.py`（模型目录）里有 `D:\Apps\PostureGuard` 绝对路径常量；装到别的目录需要同步修改这些常量后重跑 `repair.py`。
- **摄像头角度**：本机实测摄像头偏低偏侧时只能拍到后脑/桌面，会一直「无姿势」；摆正后才能稳定打分。
- **Python 3.12 + mediapipe 0.10.35** 是当前验证过的组合；升级 mediapipe / PyQt6 / batesposture 后请重跑 `repair.py`。
- Windows 原生系统通知在本机不可用是环境问题（已用自绘卡片规避），不是代码问题。
- 本项目只做本机适配与汉化，**不是上游项目的分支替代**；上游功能、算法、数据结构均归上游作者。

## 📄 许可

- 上游 [`wtbates99/batesposture`](https://github.com/wtbates99/batesposture)：MIT License，Copyright (c) the batesposture upstream authors
- 本仓库新增的补丁/脚本/文档：MIT License，Copyright (c) 2026 lishanshan133666

详见 [LICENSE](LICENSE)。
