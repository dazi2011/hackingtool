#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
from pathlib import Path

# ── Python version check (must be before any other local import) ──────────────
if sys.version_info < (3, 10):
    print(
        f"[错误] 需要 Python 3.10 或更高版本。\n"
        f"当前版本：Python {sys.version_info.major}.{sys.version_info.minor}\n"
        f"可使用以下命令安装：sudo apt install python3.10"
    )
    sys.exit(1)

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich import box

from constants import (
    REPO_URL, APP_INSTALL_DIR, APP_BIN_PATH,
    VERSION, VERSION_DISPLAY,
    USER_CONFIG_DIR, USER_TOOLS_DIR, USER_CONFIG_FILE,
    DEFAULT_CONFIG,
)
from os_detect import CURRENT_OS, REQUIRED_PACKAGES, PACKAGE_UPDATE_CMDS, PACKAGE_INSTALL_CMDS

console = Console()

VENV_DIR_NAME = "venv"
REQUIREMENTS   = "requirements.txt"
BOOTSTRAP_PYTHON = os.environ.get("HACKINGTOOL_BOOTSTRAP_PYTHON") or shutil.which("python3") or sys.executable


PACKAGE_BINARIES: dict[str, dict[str, str]] = {
    "brew": {
        "git": "git",
        "python3": "python3",
        "curl": "curl",
        "wget": "wget",
        "ruby": "ruby",
        "go": "go",
        "php": "php",
    }
}


# ── Privilege check ────────────────────────────────────────────────────────────

def _can_write_install_targets() -> bool:
    targets = [APP_INSTALL_DIR.parent, APP_BIN_PATH.parent]
    for target in targets:
        if not os.access(target, os.W_OK):
            return False
    for existing in (APP_INSTALL_DIR, APP_BIN_PATH):
        if existing.exists() and not os.access(existing, os.W_OK):
            return False
    return True


def check_privileges():
    if os.geteuid() == 0:
        return

    # On macOS, Homebrew-style paths may already be user-writable.
    if CURRENT_OS.system == "macos" and _can_write_install_targets():
        console.print("[dim]检测到 macOS 且安装目标可写，将以当前用户身份继续安装。[/dim]")
        return

    install_hint = "sudo python3 install.py"
    if CURRENT_OS.system == "macos":
        install_hint = "sudo python3 install.py 或确保 /usr/local/share 与 /usr/local/bin 可写"

    if os.geteuid() != 0:
        console.print(Panel(
            "[error]此安装器必须以 root 身份运行。\n"
            f"请使用：[bold]{install_hint}[/bold][/error]",
            border_style="red",
        ))
        sys.exit(1)


# ── OS compatibility check ─────────────────────────────────────────────────────

def check_os_compatibility():
    """Print detected OS info and exit on unsupported systems."""
    info = CURRENT_OS
    console.print(
        f"[dim]检测结果：OS={info.system} | 发行版={info.distro_id or 'n/a'} | "
        f"包管理器={info.pkg_manager or 'none'} | 架构={info.arch}[/dim]"
    )

    if info.system == "windows":
        console.print(Panel(
            "[error]暂不原生支持 Windows。[/error]\n"
            "请使用带 Kali 或 Ubuntu 镜像的 WSL2。",
            border_style="red",
        ))
        sys.exit(1)

    if info.is_wsl:
        console.print("[warning]检测到 WSL。无线类工具无法在 WSL 中正常工作。[/warning]")

    if info.system == "macos":
        console.print(Panel(
            "[warning]macOS 仅提供部分支持。[/warning]\n"
            "网络 / 无线类工具通常需要 Linux；OSINT 和 Web 类工具基本可用。",
            border_style="yellow",
        ))
        if not shutil.which("brew"):
            console.print("[error]未找到 Homebrew。请先安装：https://brew.sh[/error]")
            sys.exit(1)

    if not info.pkg_manager:
        console.print("[warning]未找到受支持的包管理器。[/warning]")
        console.print("[dim]当前支持：apt-get、pacman、dnf、zypper、apk、brew[/dim]")


# ── Internet check ─────────────────────────────────────────────────────────────

def check_internet() -> bool:
    console.print("[dim]正在检查网络连接...[/dim]")
    for host in ("https://github.com", "https://www.google.com"):
        r = subprocess.run(
            ["curl", "-sSf", "--max-time", "8", host],
            capture_output=True,
        )
        if r.returncode == 0:
            console.print("[success]网络连接正常。[/success]")
            return True
    console.print("[error]网络连接不可用。[/error]")
    return False


# ── System packages ────────────────────────────────────────────────────────────

def install_system_packages():
    mgr = CURRENT_OS.pkg_manager
    if not mgr:
        console.print("[warning]未找到包管理器，跳过系统依赖安装。[/warning]")
        return

    # Use sudo only when not already root (uid != 0).
    # Inside Docker we run as root and sudo is not installed.
    priv = "" if os.geteuid() == 0 else "sudo "

    # Update index first (skip for brew — not needed)
    if mgr != "brew":
        update_cmd = PACKAGE_UPDATE_CMDS.get(mgr, "")
        if update_cmd:
            console.print(f"[dim]正在更新包索引（{mgr}）...[/dim]")
            subprocess.run(f"{priv}{update_cmd}", shell=True, check=False)

    packages = REQUIRED_PACKAGES.get(mgr, [])
    if not packages:
        return

    # On macOS/Homebrew, avoid reinstalling formulas when the required
    # command is already available. This prevents unnecessary privilege prompts.
    if mgr in PACKAGE_BINARIES:
        binary_map = PACKAGE_BINARIES[mgr]
        missing = [pkg for pkg in packages if not shutil.which(binary_map.get(pkg, pkg))]
        if not missing:
            console.print("[dim]系统依赖已齐全，跳过安装。[/dim]")
            return
        packages = missing

    install_tpl = PACKAGE_INSTALL_CMDS[mgr]
    cmd = install_tpl.format(packages=" ".join(packages))
    console.print(f"[dim]正在安装系统依赖（{mgr}）...[/dim]")
    result = subprocess.run(f"{priv}{cmd}", shell=True, check=False)
    if result.returncode != 0:
        console.print("[warning]部分软件包安装失败，你可能需要手动安装。[/warning]")


# ── App directory ──────────────────────────────────────────────────────────────

def _is_source_dir() -> bool:
    """Check if install.py is being run from a local clone (hackingtool.py exists alongside it)."""
    return (Path(__file__).resolve().parent / "hackingtool.py").exists()


def prepare_install_dir():
    if APP_INSTALL_DIR.exists():
        console.print(f"[warning]{APP_INSTALL_DIR} 已存在。[/warning]")
        if not Confirm.ask("Replace it? This removes the existing installation.", default=False):
            console.print("[error]安装已取消。[/error]")
            sys.exit(1)
        subprocess.run(["rm", "-rf", str(APP_INSTALL_DIR)], check=True)
    APP_INSTALL_DIR.mkdir(parents=True, exist_ok=True)


def install_source() -> bool:
    """Clone the repo or copy from local source if already in a clone."""
    source_dir = Path(__file__).resolve().parent

    if _is_source_dir() and source_dir != APP_INSTALL_DIR:
        # Already in a local clone — copy instead of re-cloning
        console.print(f"[dim]正在从 {source_dir} 复制源码...[/dim]")
        # Remove first to ensure clean copy (prepare_install_dir may have created it)
        if APP_INSTALL_DIR.exists():
            subprocess.run(["rm", "-rf", str(APP_INSTALL_DIR)], check=True)
        subprocess.run(["cp", "-a", str(source_dir), str(APP_INSTALL_DIR)], check=True)
        # Fix ownership so git doesn't complain about "dubious ownership"
        if os.geteuid() == 0:
            subprocess.run(["chown", "-R", "root:root", str(APP_INSTALL_DIR)], check=False)
        console.print("[success]源码复制完成（无需重新克隆）。[/success]")
        return True

    # Not running from source — clone from GitHub
    console.print(f"[dim]正在克隆 {REPO_URL}...[/dim]")
    r = subprocess.run(["git", "clone", "--depth", "1", REPO_URL, str(APP_INSTALL_DIR)], check=False)
    if r.returncode == 0:
        console.print("[success]仓库克隆完成。[/success]")
        return True
    console.print("[error]仓库克隆失败。[/error]")
    return False


# ── Python venv ────────────────────────────────────────────────────────────────

def create_venv_and_install():
    venv_path = APP_INSTALL_DIR / VENV_DIR_NAME
    console.print("[dim]正在创建虚拟环境...[/dim]")
    subprocess.run([BOOTSTRAP_PYTHON, "-m", "venv", str(venv_path)], check=True)

    pip = str(venv_path / "bin" / "pip")
    req = APP_INSTALL_DIR / REQUIREMENTS
    if req.exists():
        console.print("[dim]正在安装 Python 依赖...[/dim]")
        subprocess.run([pip, "install", "--quiet", "-r", str(req)], check=False)
    else:
        console.print("[warning]未找到 requirements.txt，跳过 pip 安装。[/warning]")


# ── Launcher script ────────────────────────────────────────────────────────────

def create_launcher():
    launcher = APP_INSTALL_DIR / "hackingtool.sh"
    launcher.write_text(
        "#!/bin/bash\n"
        f'source "{APP_INSTALL_DIR / VENV_DIR_NAME}/bin/activate"\n'
        f'python3 "{APP_INSTALL_DIR / "hackingtool.py"}" "$@"\n'
    )
    launcher.chmod(0o755)
    if APP_BIN_PATH.exists():
        APP_BIN_PATH.unlink()
    shutil.move(str(launcher), str(APP_BIN_PATH))
    console.print(f"[success]启动器已安装到 {APP_BIN_PATH}[/success]")


# ── User directories ───────────────────────────────────────────────────────────

def create_user_directories():
    """
    Create ~/.hackingtool/ and write initial config.json.
    Uses Path.home() — always correct regardless of username or OS.
    Safe to run as root (creates /root/.hackingtool/) or as a normal user.
    """
    import json
    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    USER_TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    if not USER_CONFIG_FILE.exists():
        USER_CONFIG_FILE.write_text(json.dumps(DEFAULT_CONFIG, indent=2, sort_keys=True))
        console.print(f"[success]配置文件已创建：{USER_CONFIG_FILE}[/success]")
    console.print(f"[success]工具目录：{USER_TOOLS_DIR}[/success]")


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    check_privileges()
    console.clear()

    console.print(Panel(
        Text(f"HackingTool 安装器  {VERSION_DISPLAY}", style="bold magenta"),
        box=box.DOUBLE, border_style="bright_magenta",
    ))

    check_os_compatibility()

    if not check_internet():
        sys.exit(1)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as p:
        p.add_task("正在安装系统依赖...", total=None)
        install_system_packages()

    prepare_install_dir()

    if not install_source():
        sys.exit(1)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as p:
        p.add_task("正在配置虚拟环境与依赖...", total=None)
        create_venv_and_install()

    create_launcher()
    create_user_directories()

    console.print(Panel(
        "[bold magenta]安装完成！[/bold magenta]\n\n"
        "现在可以在终端中输入 [bold cyan]hackingtool[/bold cyan] 启动。",
        border_style="magenta",
    ))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[error]安装已中断。[/error]")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        console.print(f"[error]命令执行失败：{e}[/error]")
        sys.exit(1)
