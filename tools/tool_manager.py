import os
import sys
import subprocess
from time import sleep

from rich.prompt import Confirm

from core import HackingTool, HackingToolsCollection, console
from constants import APP_INSTALL_DIR, APP_BIN_PATH, USER_CONFIG_DIR, REPO_URL


class UpdateTool(HackingTool):
    TITLE = "Update Tool or System"
    DESCRIPTION = "Update system packages or pull the latest hackingtool code"

    def __init__(self):
        super().__init__([
            ("Update System", self.update_sys),
            ("Update Hackingtool", self.update_ht),
        ], installable=False, runnable=False)

    def update_sys(self):
        from os_detect import CURRENT_OS, PACKAGE_UPDATE_CMDS
        mgr = CURRENT_OS.pkg_manager
        cmd = PACKAGE_UPDATE_CMDS.get(mgr)
        if cmd:
            priv = "" if (CURRENT_OS.system == "macos" or os.geteuid() == 0) else "sudo "
            # shell=True needed — cmd contains && chains; strings are hardcoded, not user input
            subprocess.run(f"{priv}{cmd}", shell=True, check=False)
        else:
            console.print("[warning]未知包管理器，请手动更新。[/warning]")

    def update_ht(self):
        if not APP_INSTALL_DIR.exists():
            console.print(f"[error]未找到安装目录：{APP_INSTALL_DIR}[/error]")
            console.print("[dim]请先运行 install.py。[/dim]")
            return
        console.print(f"[bold cyan]正在从 {REPO_URL} 拉取最新代码...[/bold cyan]")
        result = subprocess.run(
            ["git", "pull", "--rebase"],
            cwd=str(APP_INSTALL_DIR),
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            console.print(f"[error]git pull 失败：\n{result.stderr}[/error]")
            return
        pip = str(APP_INSTALL_DIR / "venv" / "bin" / "pip")
        if (APP_INSTALL_DIR / "venv" / "bin" / "pip").exists():
            subprocess.run([pip, "install", "-q", "-r",
                            str(APP_INSTALL_DIR / "requirements.txt")])
        console.print("[success]Hackingtool 已更新。[/success]")


class UninstallTool(HackingTool):
    TITLE = "Uninstall HackingTool"
    DESCRIPTION = "Remove hackingtool from system"

    def __init__(self):
        super().__init__([
            ("Uninstall", self.uninstall),
        ], installable=False, runnable=False)

    def uninstall(self):
        import shutil
        console.print("[warning]这将从你的系统中移除 hackingtool。[/warning]")
        if not Confirm.ask("是否继续？", default=False):
            return

        if APP_INSTALL_DIR.exists():
            shutil.rmtree(str(APP_INSTALL_DIR))
            console.print(f"[success]已删除 {APP_INSTALL_DIR}[/success]")
        else:
            console.print(f"[dim]未找到 {APP_INSTALL_DIR}，可能已经删除。[/dim]")

        if APP_BIN_PATH.exists():
            APP_BIN_PATH.unlink()
            console.print(f"[success]已删除启动器 {APP_BIN_PATH}[/success]")

        if Confirm.ask(f"是否同时删除用户数据目录 {USER_CONFIG_DIR}？", default=False):
            shutil.rmtree(str(USER_CONFIG_DIR), ignore_errors=True)
            console.print(f"[success]已删除 {USER_CONFIG_DIR}[/success]")

        console.print("[bold green]Hackingtool 已卸载。[/bold green]")
        sleep(1)
        sys.exit(0)


class ToolManager(HackingToolsCollection):
    TITLE = "Update or Uninstall | Hackingtool"
    TOOLS = [
        UpdateTool(),
        UninstallTool(),
    ]


if __name__ == "__main__":
    manager = ToolManager()
    manager.show_options()
