# batesposture-cn 安装脚本（PowerShell 5.1+ / Windows 10/11）
#
# 用法（在仓库根目录）：
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -InstallDir "E:\Apps\PostureGuard" -SkipShortcuts
#
# 注意：补丁里有几个指向 D:\Apps\PostureGuard 的绝对路径常量，
# 换成其他安装目录时请先修改 patches\ 与 shim\ 中对应常量（见 README「已知限制」）。

param(
    [string]$InstallDir = "D:\Apps\PostureGuard",
    [switch]$SkipShortcuts
)

$ErrorActionPreference = "Stop"
$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Mirror = "https://pypi.tuna.tsinghua.edu.cn/simple"

Write-Host "[1/5] 安装目录: $InstallDir"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

Write-Host "[2/5] 复制程序文件"
foreach ($item in @("repair.py", "requirements.txt", "使用说明.md", "app.ico", "app_icon_64.png")) {
    Copy-Item (Join-Path $RepoDir $item) (Join-Path $InstallDir $item) -Force
}
foreach ($dir in @("patches", "shim", "scripts")) {
    $dest = Join-Path $InstallDir $dir
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Copy-Item (Join-Path $RepoDir "$dir\*") $dest -Recurse -Force
}

Write-Host "[3/5] 创建虚拟环境并安装依赖（媒体步可能较慢，约 300 MB）"
$Venv = Join-Path $InstallDir "venv"
if (-not (Test-Path (Join-Path $Venv "Scripts\python.exe"))) {
    python -m venv $Venv
}
& (Join-Path $Venv "Scripts\python.exe") -m pip install --upgrade pip -q
& (Join-Path $Venv "Scripts\python.exe") -m pip install -q -i $Mirror -r (Join-Path $InstallDir "requirements.txt")

Write-Host "[4/5] 应用本机适配补丁"
& (Join-Path $Venv "Scripts\python.exe") (Join-Path $InstallDir "repair.py")

if (-not $SkipShortcuts) {
    Write-Host "[5/5] 创建快捷方式"
    $pythonw = Join-Path $Venv "Scripts\pythonw.exe"
    $shell = New-Object -ComObject WScript.Shell
    $icon = Join-Path $InstallDir "app.ico"

    $targets = @(
        [IO.Path]::Combine([Environment]::GetFolderPath("Desktop"), "BatesPosture 坐姿提醒.lnk"),
        [IO.Path]::Combine([Environment]::GetFolderPath("Programs"), "BatesPosture 坐姿提醒.lnk")
    )
    foreach ($lnkPath in $targets) {
        $lnk = $shell.CreateShortcut($lnkPath)
        $lnk.TargetPath = $pythonw
        $lnk.Arguments = "-m batesposture"
        $lnk.WorkingDirectory = $InstallDir
        $lnk.IconLocation = $icon
        $lnk.WindowStyle = 7
        $lnk.Save()
    }

    $dashLnk = $shell.CreateShortcut([IO.Path]::Combine([Environment]::GetFolderPath("Desktop"), "坐姿实时监控.lnk"))
    $dashLnk.TargetPath = $pythonw
    $dashLnk.Arguments = '"' + (Join-Path $InstallDir "scripts\open_dashboard.py") + '"'
    $dashLnk.WorkingDirectory = $InstallDir
    $dashLnk.IconLocation = $icon
    $dashLnk.WindowStyle = 7
    $dashLnk.Save()
} else {
    Write-Host "[5/5] 跳过快捷方式"
}

Write-Host ""
Write-Host "完成。启动命令："
Write-Host "  `"$InstallDir\venv\Scripts\pythonw.exe`" -m batesposture"
Write-Host "首次使用请把摄像头摆正（头+双肩+上半身入镜），并允许安全软件访问摄像头。"
