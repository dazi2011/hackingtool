import os
import shutil
import sys
import webbrowser
from collections.abc import Callable
from platform import system

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich.traceback import install

from constants import (
    THEME_PRIMARY, THEME_BORDER, THEME_ACCENT,
    THEME_SUCCESS, THEME_ERROR, THEME_WARNING,
    THEME_DIM, THEME_ARCHIVED, THEME_URL, THEME_TEXT,
)
from localization import patch_console, patch_interaction, tr

# Enable rich tracebacks globally
install()

_theme = Theme({
    "primary":  THEME_PRIMARY,
    "accent":   THEME_ACCENT,
    "text":     THEME_TEXT,
    "purple":   THEME_BORDER,
    "success":  THEME_SUCCESS,
    "error":    THEME_ERROR,
    "warning":  THEME_WARNING,
    "archived": THEME_ARCHIVED,
    "url":      THEME_URL,
    "dim":      THEME_DIM,
})

# Single shared console — all tool files do: from core import console
console = Console(theme=_theme)
patch_interaction()
patch_console(console)


def clear_screen():
    os.system("cls" if system() == "Windows" else "clear")


def validate_input(ip, val_range: list) -> int | None:
    """Return the integer if it is in val_range, else None."""
    if not val_range:
        return None
    try:
        ip = int(ip)
        if ip in val_range:
            return ip
    except (TypeError, ValueError):
        pass
    return None


def _show_inline_help():
    """Quick help available from any menu level."""
    console.print(Panel(
        Text.assemble(
            ("  导航说明\n", "bold"),
            ("  ─────────────────────────────────\n", "dim"),
            ("  1–N    ", "accent"), ("选择条目\n", "text"),
            ("  97     ", "accent"), ("安装当前分类中的全部工具\n", "text"),
            ("\n  工具菜单：安装 / 运行 / 更新 / 打开目录\n", "dim"),
            ("  99     ", "accent"), ("返回上一级\n", "text"),
            ("  98     ", "accent"), ("打开项目主页 / 查看已归档工具\n", "text"),
            ("  ?      ", "accent"), ("显示帮助\n", "text"),
            ("  q      ", "accent"), ("退出 Hackingtool\n", "text"),
        ),
        title="[primary] 帮助 [/primary]",
        border_style="primary",
        box=box.ROUNDED,
        padding=(0, 2),
    ))
    Prompt.ask("[dim]按回车返回[/dim]", default="")


class HackingTool:
    TITLE: str              = ""
    DESCRIPTION: str        = ""
    INSTALL_COMMANDS: list[str]  = []
    UNINSTALL_COMMANDS: list[str] = []
    RUN_COMMANDS: list[str]      = []
    OPTIONS: list[tuple[str, Callable]] = []
    PROJECT_URL: str        = ""

    # OS / capability metadata
    SUPPORTED_OS: list[str] = ["linux", "macos"]
    REQUIRES_ROOT: bool     = False
    REQUIRES_WIFI: bool     = False
    REQUIRES_GO: bool       = False
    REQUIRES_RUBY: bool     = False
    REQUIRES_JAVA: bool     = False
    REQUIRES_DOCKER: bool   = False

    # Tags for search/filter (e.g. ["osint", "web", "recon", "scanner"])
    TAGS: list[str]         = []

    # Archived tool flags
    ARCHIVED: bool          = False
    ARCHIVED_REASON: str    = ""

    def __init__(self, options=None, installable=True, runnable=True):
        options = options or []
        if not isinstance(options, list):
            raise TypeError("options must be a list of (option_name, option_fn) tuples")
        self.OPTIONS = []
        if installable:
            self.OPTIONS.append(("Install", self.install))
        if runnable:
            self.OPTIONS.append(("Run", self.run))
        self.OPTIONS.append(("Update", self.update))
        self.OPTIONS.append(("Open Folder", self.open_folder))
        self.OPTIONS.extend(options)

    @property
    def is_installed(self) -> bool:
        """Check if the tool's binary is on PATH or its clone dir exists."""
        if self.RUN_COMMANDS:
            cmd = self.RUN_COMMANDS[0]
            # Handle "cd foo && binary --help" pattern
            if "&&" in cmd:
                cmd = cmd.split("&&")[-1].strip()
            if cmd.startswith("sudo "):
                cmd = cmd[5:].strip()
            binary = cmd.split()[0] if cmd else ""
            if binary and binary not in (".", "echo", "cd"):
                if shutil.which(binary):
                    return True
        # Check if git clone target dir exists
        if self.INSTALL_COMMANDS:
            for ic in self.INSTALL_COMMANDS:
                if "git clone" in ic:
                    parts = ic.split()
                    repo_url = [p for p in parts if p.startswith("http")]
                    if repo_url:
                        dirname = repo_url[0].rstrip("/").rsplit("/", 1)[-1].replace(".git", "")
                        if os.path.isdir(dirname):
                            return True
        return False

    def show_info(self):
        desc = f"[text]{self.DESCRIPTION}[/text]"
        if self.PROJECT_URL:
            desc += f"\n[url]项目主页：{self.PROJECT_URL}[/url]"
        if self.ARCHIVED:
            desc += f"\n[archived]已归档：{self.ARCHIVED_REASON}[/archived]"
        console.print(Panel(
            desc,
            title=f"[primary]{self.TITLE}[/primary]",
            border_style="purple",
            box=box.DOUBLE,
        ))

    def show_options(self, parent=None):
        """Iterative menu loop — no recursion, no stack growth."""
        while True:
            clear_screen()
            self.show_info()

            table = Table(title="操作", box=box.SIMPLE_HEAVY)
            table.add_column("编号", style="accent", justify="center")
            table.add_column("动作", style="bold")

            for index, option in enumerate(self.OPTIONS):
                table.add_row(str(index + 1), tr(option[0]))

            if self.PROJECT_URL:
                table.add_row("98", "打开项目主页")
            table.add_row("99", f"返回到 {parent.TITLE if parent else '主菜单'}")
            console.print(table)
            console.print(
                "  [accent]?[/accent] [dim]帮助[/dim]  "
                "[accent]q[/accent] [dim]退出[/dim]  "
                "[accent]99[/accent] [dim]返回[/dim]"
            )

            raw = Prompt.ask("[accent]╰─>[/accent]", default="").strip().lower()
            if not raw:
                continue
            if raw in ("?", "help", "帮助"):
                _show_inline_help()
                continue
            if raw in ("q", "quit", "exit", "退出"):
                raise SystemExit(0)

            try:
                choice = int(raw)
            except ValueError:
                console.print("[error]请输入数字，或输入 ? 查看帮助、q 退出。[/error]")
                Prompt.ask("[dim]按回车继续[/dim]", default="")
                continue

            if choice == 99:
                return
            elif choice == 98 and self.PROJECT_URL:
                self.show_project_page()
            elif 1 <= choice <= len(self.OPTIONS):
                try:
                    self.OPTIONS[choice - 1][1]()
                except Exception:
                    console.print_exception(show_locals=True)
                Prompt.ask("[dim]按回车继续[/dim]", default="")
            else:
                console.print("[error]无效选项。[/error]")

    def before_install(self): pass

    def install(self):
        self.before_install()
        if isinstance(self.INSTALL_COMMANDS, (list, tuple)):
            for cmd in self.INSTALL_COMMANDS:
                console.print(f"[warning]执行安装命令：{cmd}[/warning]")
                os.system(cmd)
        self.after_install()

    def after_install(self):
        console.print("[success]安装完成。[/success]")

    def before_uninstall(self) -> bool:
        return True

    def uninstall(self):
        if self.before_uninstall():
            if isinstance(self.UNINSTALL_COMMANDS, (list, tuple)):
                for cmd in self.UNINSTALL_COMMANDS:
                    console.print(f"[error]执行卸载命令：{cmd}[/error]")
                    os.system(cmd)
        self.after_uninstall()

    def after_uninstall(self): pass

    def update(self):
        """Smart update — detects install method and runs the right update command."""
        if not self.is_installed:
            console.print("[warning]该工具尚未安装，请先安装。[/warning]")
            return

        updated = False
        for ic in (self.INSTALL_COMMANDS or []):
            if "git clone" in ic:
                # Extract repo dir name from clone command
                parts = ic.split()
                repo_urls = [p for p in parts if p.startswith("http")]
                if repo_urls:
                    dirname = repo_urls[0].rstrip("/").rsplit("/", 1)[-1].replace(".git", "")
                    if os.path.isdir(dirname):
                        console.print(f"[accent]执行更新命令：git -C {dirname} pull[/accent]")
                        os.system(f"git -C {dirname} pull")
                        updated = True
            elif "pip install" in ic:
                # Re-run pip install (--upgrade)
                upgrade_cmd = ic.replace("pip install", "pip install --upgrade")
                console.print(f"[accent]执行更新命令：{upgrade_cmd}[/accent]")
                os.system(upgrade_cmd)
                updated = True
            elif "go install" in ic:
                # Re-run go install (fetches latest)
                console.print(f"[accent]执行更新命令：{ic}[/accent]")
                os.system(ic)
                updated = True
            elif "gem install" in ic:
                upgrade_cmd = ic.replace("gem install", "gem update")
                console.print(f"[accent]执行更新命令：{upgrade_cmd}[/accent]")
                os.system(upgrade_cmd)
                updated = True

        if updated:
            console.print("[success]更新完成。[/success]")
        else:
            console.print("[dim]该工具暂不支持自动更新。[/dim]")

    def _get_tool_dir(self) -> str | None:
        """Find the tool's local directory — clone target, pip location, or binary path."""
        # 1. Check git clone target dir
        for ic in (self.INSTALL_COMMANDS or []):
            if "git clone" in ic:
                parts = ic.split()
                # If last arg is not a URL, it's a custom dir name
                repo_urls = [p for p in parts if p.startswith("http")]
                if repo_urls:
                    dirname = repo_urls[0].rstrip("/").rsplit("/", 1)[-1].replace(".git", "")
                    # Check custom target dir (arg after URL)
                    url_idx = parts.index(repo_urls[0])
                    if url_idx + 1 < len(parts):
                        dirname = parts[url_idx + 1]
                    if os.path.isdir(dirname):
                        return os.path.abspath(dirname)

        # 2. Check binary location via which
        if self.RUN_COMMANDS:
            cmd = self.RUN_COMMANDS[0]
            if "&&" in cmd:
                # "cd foo && bar" → check "foo"
                cd_part = cmd.split("&&")[0].strip()
                if cd_part.startswith("cd "):
                    d = cd_part[3:].strip()
                    if os.path.isdir(d):
                        return os.path.abspath(d)
            binary = cmd.split()[0] if cmd else ""
            if binary.startswith("sudo"):
                binary = cmd.split()[1] if len(cmd.split()) > 1 else ""
            path = shutil.which(binary) if binary else None
            if path:
                return os.path.dirname(os.path.realpath(path))

        return None

    def open_folder(self):
        """Open the tool's directory in a new shell so the user can work manually."""
        tool_dir = self._get_tool_dir()
        if tool_dir:
            console.print(f"[success]正在打开目录：{tool_dir}[/success]")
            console.print("[dim]输入 'exit' 可返回 Hackingtool。[/dim]")
            os.system(f'cd "{tool_dir}" && $SHELL')
        else:
            console.print("[warning]未找到工具目录。[/warning]")
            if self.PROJECT_URL:
                console.print("[dim]你也可以手动克隆：[/dim]")
                console.print(f"[accent]  git clone {self.PROJECT_URL}.git[/accent]")

    def before_run(self): pass

    def run(self):
        self.before_run()
        if isinstance(self.RUN_COMMANDS, (list, tuple)):
            for cmd in self.RUN_COMMANDS:
                console.print(f"[accent]正在执行：[/accent] [bold]{cmd}[/bold]")
                os.system(cmd)
        self.after_run()

    def after_run(self): pass

    def show_project_page(self):
        console.print(f"[url]正在打开项目主页：{self.PROJECT_URL}[/url]")
        webbrowser.open_new_tab(self.PROJECT_URL)


class HackingToolsCollection:
    TITLE: str       = ""
    DESCRIPTION: str = ""
    TOOLS: list      = []

    def __init__(self):
        pass

    def show_info(self):
        console.rule(f"[primary]{self.TITLE}[/primary]", style="primary")
        if self.DESCRIPTION:
            console.print(f"[text]{self.DESCRIPTION}[/text]\n")

    def _active_tools(self) -> list:
        """Return tools that are not archived and are OS-compatible."""
        from os_detect import CURRENT_OS
        return [
            t for t in self.TOOLS
            if not getattr(t, "ARCHIVED", False)
            and CURRENT_OS.system in getattr(t, "SUPPORTED_OS", ["linux", "macos"])
        ]

    def _archived_tools(self) -> list:
        return [t for t in self.TOOLS if getattr(t, "ARCHIVED", False)]

    def _incompatible_tools(self) -> list:
        from os_detect import CURRENT_OS
        return [
            t for t in self.TOOLS
            if not getattr(t, "ARCHIVED", False)
            and CURRENT_OS.system not in getattr(t, "SUPPORTED_OS", ["linux", "macos"])
        ]

    def _show_archived_tools(self):
        """Show archived tools sub-menu (option 98)."""
        archived = self._archived_tools()
        if not archived:
            console.print("[dim]该分类下没有已归档工具。[/dim]")
            Prompt.ask("[dim]按回车返回[/dim]", default="")
            return

        while True:
            clear_screen()
            console.rule(f"[archived]已归档工具 — {self.TITLE}[/archived]", style="yellow")

            table = Table(box=box.MINIMAL_DOUBLE_HEAD, show_lines=True)
            table.add_column("编号", justify="center", style="accent")
            table.add_column("工具", style="archived")
            table.add_column("原因", style="text")

            for i, tool in enumerate(archived):
                reason = getattr(tool, "ARCHIVED_REASON", "未说明原因")
                table.add_row(str(i + 1), tool.TITLE, reason)

            table.add_row("99", "返回", "")
            console.print(table)

            raw = Prompt.ask("[accent][?] 选择[/accent]", default="99")
            try:
                choice = int(raw)
            except ValueError:
                continue

            if choice == 99:
                return
            elif 1 <= choice <= len(archived):
                archived[choice - 1].show_options(parent=self)

    def show_options(self, parent=None):
        """Iterative menu loop — no recursion, no stack growth."""
        while True:
            clear_screen()
            self.show_info()

            active = self._active_tools()
            incompatible = self._incompatible_tools()
            archived = self._archived_tools()

            table = Table(title="可用工具", box=box.SIMPLE_HEAD, show_lines=True)
            table.add_column("编号", justify="center", style="accent", width=6)
            table.add_column("状态", width=6)
            table.add_column("工具", style="bold", min_width=24)
            table.add_column("说明", style="text", overflow="fold")

            for index, tool in enumerate(active, start=1):
                desc = getattr(tool, "DESCRIPTION", "") or "—"
                desc = desc.splitlines()[0] if desc != "—" else "—"
                has_status = hasattr(tool, "is_installed")
                status = ("[green]已装[/green]" if tool.is_installed else "[dim]未装[/dim]") if has_status else ""
                table.add_row(str(index), status, tool.TITLE, desc)

            # Count not-installed tools for "Install All" label (skip sub-collections)
            not_installed = [t for t in active if hasattr(t, "is_installed") and not t.is_installed]
            if not_installed:
                table.add_row(
                    "[success]97[/success]", "",
                    f"[success]安装全部（{len(not_installed)} 个未安装）[/success]", "",
                )
            if archived:
                table.add_row("[accent]98[/accent]", "", f"[archived]已归档工具（{len(archived)}）[/archived]", "")
            if incompatible:
                console.print(f"[dim]（已隐藏 {len(incompatible)} 个当前操作系统不支持的工具）[/dim]")

            table.add_row("99", "", f"返回到 {parent.TITLE if parent else '主菜单'}", "")
            console.print(table)
            console.print(
                "  [accent]?[/accent] [dim]帮助[/dim]  "
                "[accent]q[/accent] [dim]退出[/dim]  "
                "[accent]99[/accent] [dim]返回[/dim]"
            )

            raw = Prompt.ask("[accent]╰─>[/accent]", default="").strip().lower()
            if not raw:
                continue
            if raw in ("?", "help", "帮助"):
                _show_inline_help()
                continue
            if raw in ("q", "quit", "exit", "退出"):
                raise SystemExit(0)

            try:
                choice = int(raw)
            except ValueError:
                console.print("[error]请输入数字，或输入 ? 查看帮助、q 退出。[/error]")
                continue

            if choice == 99:
                return
            elif choice == 97 and not_installed:
                console.print(Panel(
                    f"[bold]正在安装 {len(not_installed)} 个工具...[/bold]",
                    border_style="primary", box=box.ROUNDED,
                ))
                for i, tool in enumerate(not_installed, start=1):
                    console.print(f"\n[accent]({i}/{len(not_installed)})[/accent] {tool.TITLE}")
                    try:
                        tool.install()
                    except Exception:
                        console.print(f"[error]安装失败：{tool.TITLE}[/error]")
                Prompt.ask("\n[dim]按回车继续[/dim]", default="")
            elif choice == 98 and archived:
                self._show_archived_tools()
            elif 1 <= choice <= len(active):
                try:
                    active[choice - 1].show_options(parent=self)
                except Exception:
                    console.print_exception(show_locals=True)
                    Prompt.ask("[dim]按回车继续[/dim]", default="")
            else:
                console.print("[error]无效选项。[/error]")
