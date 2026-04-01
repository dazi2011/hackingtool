#!/usr/bin/env python3
import sys

# ── Python version guard (must be before any other local import) ───────────────
if sys.version_info < (3, 10):
    print(
        f"[ERROR] Python 3.10 or newer is required.\n"
        f"You are running Python {sys.version_info.major}.{sys.version_info.minor}.\n"
        f"Upgrade with: sudo apt install python3.10"
    )
    sys.exit(1)

import os
import platform
import socket
import datetime
import random
import webbrowser
import getpass
from itertools import zip_longest

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.align import Align
from rich.text import Text
from rich import box
from rich.rule import Rule
from rich.columns import Columns

from core import HackingToolsCollection, clear_screen, console
from constants import VERSION_DISPLAY, REPO_WEB_URL
from config import get_tools_dir
from localization import localize_tool_tree, original_text
from tools.anonsurf import AnonSurfTools
from tools.ddos import DDOSTools
from tools.exploit_frameworks import ExploitFrameworkTools
from tools.forensics import ForensicTools
from tools.information_gathering import InformationGatheringTools
from tools.other_tools import OtherTools
from tools.payload_creator import PayloadCreatorTools
from tools.phishing_attack import PhishingAttackTools
from tools.post_exploitation import PostExploitationTools
from tools.remote_administration import RemoteAdministrationTools
from tools.reverse_engineering import ReverseEngineeringTools
from tools.sql_injection import SqlInjectionTools
from tools.steganography import SteganographyTools
from tools.tool_manager import ToolManager
from tools.web_attack import WebAttackTools
from tools.wireless_attack import WirelessAttackTools
from tools.wordlist_generator import WordlistGeneratorTools
from tools.xss_attack import XSSAttackTools
from tools.active_directory import ActiveDirectoryTools
from tools.cloud_security import CloudSecurityTools
from tools.mobile_security import MobileSecurityTools

# ── Tool registry ──────────────────────────────────────────────────────────────

# (full_title, icon, menu_label)
# menu_label is the concise name shown in the 2-column main menu grid.
# full_title is shown when entering the category.
tool_definitions = [
    ("匿名隐藏工具",             "", "匿名隐藏"),
    ("信息收集工具",             "", "信息收集"),
    ("字典生成工具",             "", "字典生成"),
    ("无线攻击工具",             "", "无线攻击"),
    ("SQL 注入工具",            "", "SQL 注入"),
    ("钓鱼攻击工具",             "", "钓鱼攻击"),
    ("Web 攻击工具",            "", "Web 攻击"),
    ("后渗透工具",               "", "后渗透"),
    ("取证工具",                 "", "取证分析"),
    ("载荷生成工具",             "", "载荷生成"),
    ("利用框架",                 "", "利用框架"),
    ("逆向工程工具",             "", "逆向工程"),
    ("DDoS 攻击工具",           "", "DDoS 攻击"),
    ("远程管理工具（RAT）",      "", "远程管理"),
    ("XSS 攻击工具",            "", "XSS 攻击"),
    ("隐写工具",                 "", "隐写分析"),
    ("活动目录工具",             "", "活动目录"),
    ("云安全工具",               "", "云安全"),
    ("移动安全工具",             "", "移动安全"),
    ("其他工具",                 "", "其他工具"),
    ("更新或卸载 | Hackingtool", "", "更新 / 卸载"),
]

all_tools = [
    AnonSurfTools(),
    InformationGatheringTools(),
    WordlistGeneratorTools(),
    WirelessAttackTools(),
    SqlInjectionTools(),
    PhishingAttackTools(),
    WebAttackTools(),
    PostExploitationTools(),
    ForensicTools(),
    PayloadCreatorTools(),
    ExploitFrameworkTools(),
    ReverseEngineeringTools(),
    DDOSTools(),
    RemoteAdministrationTools(),
    XSSAttackTools(),
    SteganographyTools(),
    ActiveDirectoryTools(),
    CloudSecurityTools(),
    MobileSecurityTools(),
    OtherTools(),
    ToolManager(),
]
localize_tool_tree(all_tools)

# Used by generate_readme.py
class AllTools(HackingToolsCollection):
    TITLE = "全部工具"
    TOOLS = all_tools


# ── Help overlay ───────────────────────────────────────────────────────────────

def show_help():
    console.print(Panel(
        Text.assemble(
            ("  主菜单\n", "bold white"),
            ("  ─────────────────────────────────────\n", "dim"),
            ("  1–20   ", "bold cyan"), ("进入某个分类\n", "white"),
            ("  21     ", "bold cyan"), ("更新 / 卸载 Hackingtool\n", "white"),
            ("  / 或 s ", "bold cyan"), ("按名称或关键词搜索工具\n", "white"),
            ("  t      ", "bold cyan"), ("按标签筛选工具（osint、web、c2 等）\n", "white"),
            ("  r      ", "bold cyan"), ("按任务推荐工具\n", "white"),
            ("  ?      ", "bold cyan"), ("显示帮助\n", "white"),
            ("  q      ", "bold cyan"), ("退出 Hackingtool\n\n", "white"),
            ("  分类内\n", "bold white"),
            ("  ─────────────────────────────────────\n", "dim"),
            ("  1–N    ", "bold cyan"), ("选择工具\n", "white"),
            ("  99     ", "bold cyan"), ("返回主菜单\n", "white"),
            ("  98     ", "bold cyan"), ("打开项目主页（若可用）\n\n", "white"),
            ("  工具页内\n", "bold white"),
            ("  ─────────────────────────────────────\n", "dim"),
            ("  1      ", "bold cyan"), ("安装工具\n", "white"),
            ("  2      ", "bold cyan"), ("运行工具\n", "white"),
            ("  99     ", "bold cyan"), ("返回分类\n", "white"),
        ),
        title="[bold magenta] 帮助 [/bold magenta]",
        border_style="magenta",
        box=box.ROUNDED,
        padding=(0, 2),
    ))
    Prompt.ask("[dim]按回车返回[/dim]", default="")


# ── Header: ASCII art + live system info ──────────────────────────────────────

# Full "HACKING TOOL" block-letter art — 12 lines, split layout with stats
_BANNER_ART = [
    " ██╗  ██╗ █████╗  ██████╗██╗  ██╗██╗███╗   ██╗ ██████╗ ",
    " ██║  ██║██╔══██╗██╔════╝██║ ██╔╝██║████╗  ██║██╔════╝ ",
    " ███████║███████║██║     █████╔╝ ██║██╔██╗ ██║██║  ███╗",
    " ██╔══██║██╔══██║██║     ██╔═██╗ ██║██║╚██╗██║██║   ██║",
    " ██║  ██║██║  ██║╚██████╗██║  ██╗██║██║ ╚████║╚██████╔╝",
    " ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ",
    "        ████████╗ ██████╗  ██████╗ ██╗",
    "        ╚══██╔══╝██╔═══██╗██╔═══██╗██║",
    "           ██║   ██║   ██║██║   ██║██║",
    "           ██║   ██║   ██║██║   ██║██║",
    "           ██║   ╚██████╔╝╚██████╔╝███████╗",
    "           ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝",
]

_QUOTES = [
    '"越安静，越能听见更多细节。"',
    '"进攻是防守最好的老师。"',
    '"对人的愚蠢，没有补丁可打。"',
    '"先清点，再利用。"',
    '"范围定义了你的战场。"',
    '"训练时多流汗，实战时少流血。"',
    '"安全是一种持续过程，不是单一产品。"',
]


def _sys_info() -> dict:
    """Collect live system info for the header panel."""
    info: dict = {}

    # OS pretty name
    try:
        info["os"] = platform.freedesktop_os_release().get("PRETTY_NAME", "")
    except Exception:
        info["os"] = ""
    if not info["os"]:
        info["os"] = f"{platform.system()} {platform.release()}"

    info["kernel"] = platform.release()

    # Current user
    try:
        info["user"] = os.environ.get("USER") or os.environ.get("LOGNAME") or getpass.getuser()
    except Exception:
        info["user"] = getpass.getuser()

    info["host"] = socket.gethostname()

    # Local IP — connect to a routable address without sending data
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(("10.254.254.254", 1))
        info["ip"] = s.getsockname()[0]
        s.close()
    except Exception:
        info["ip"] = "127.0.0.1"

    info["time"] = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M")
    return info


def _build_header() -> Panel:
    info = _sys_info()

    # 12 stat lines paired with the 12 art lines
    stat_lines = [
        ("  系统    ›  ", info["os"][:34]),
        ("  内核    ›  ", info["kernel"][:34]),
        ("  用户    ›  ", f"{info['user']} @ {info['host'][:20]}"),
        ("  地址    ›  ", info["ip"]),
        ("  分类    ›  ", f"{len(all_tools)} 个分类 · 185+ 模块"),
        ("  会话    ›  ", info["time"]),
        ("", ""),
        ("  Python  ›  ", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"),
        ("  架构    ›  ", platform.machine()),
        ("  状态    ›  ", "已就绪"),
        ("", ""),
        ("", ""),
    ]

    grid = Table.grid(padding=0)
    grid.add_column("art", no_wrap=True)
    grid.add_column("sep", no_wrap=True)
    grid.add_column("lbl", no_wrap=True)
    grid.add_column("val", no_wrap=True)

    for art_line, (lbl_text, val_text) in zip(_BANNER_ART, stat_lines):
        grid.add_row(
            Text(art_line, style="bold bright_green"),
            Text("  │ ", style="dim green"),
            Text(lbl_text, style="dim green"),
            Text(val_text, style="bright_green"),
        )

    # Quote + warning below the split row
    quote = random.choice(_QUOTES)
    body = Table.grid(padding=(0, 0))
    body.add_column()
    body.add_row(grid)
    body.add_row(Text(""))
    body.add_row(Text(f"  {quote}", style="italic dim"))
    body.add_row(Text("  仅限经授权的安全测试使用",
                      style="bold dim red"))

    return Panel(
        body,
        title=f"[bold bright_magenta][ HackingTool {VERSION_DISPLAY} ][/bold bright_magenta]",
        title_align="left",
        subtitle=f"[dim][ {info['time']} ][/dim]",
        subtitle_align="right",
        border_style="bright_magenta",
        box=box.HEAVY,
        padding=(0, 1),
    )


# ── Main menu renderer ─────────────────────────────────────────────────────────

def build_menu():
    clear_screen()
    console.print(_build_header())

    # ── 2-column category grid ──
    # Items 1-17 in two columns, item 18 (ToolManager) shown separately
    categories = tool_definitions[:-1]   # 17 items
    update_def = tool_definitions[-1]    # ToolManager

    mid = (len(categories) + 1) // 2    # 9  (left), 8 (right)
    left  = list(enumerate(categories[:mid],  start=1))
    right = list(enumerate(categories[mid:],  start=mid + 1))

    grid = Table.grid(padding=(0, 1), expand=True)
    grid.add_column("ln", justify="right", style="bold magenta", width=5)
    grid.add_column("li", width=3)
    grid.add_column("lt", style="magenta", ratio=1, no_wrap=True)
    grid.add_column("gap", width=3)
    grid.add_column("rn", justify="right", style="bold magenta", width=5)
    grid.add_column("ri", width=3)
    grid.add_column("rt", style="magenta", ratio=1, no_wrap=True)

    for (li, (_, lic, ll)), r in zip_longest(left, right, fillvalue=None):
        if r:
            ri, (_, ric, rl) = r
            grid.add_row(str(li), lic, ll, "", str(ri), ric, rl)
        else:
            grid.add_row(str(li), lic, ll, "", "", "", "")

    console.print(Panel(
        grid,
        title="[bold magenta] 选择分类 [/bold magenta]",
        border_style="bright_magenta",
        box=box.ROUNDED,
        padding=(0, 1),
    ))

    # ── ToolManager row ──
    tm_num = len(categories) + 1
    console.print(
        f"  [bold magenta]  {tm_num}[/bold magenta]  "
        f"[magenta]{update_def[2]}[/magenta]"
    )

    # ── Claude-style dual-line prompt area ──
    console.print(Rule(style="dim magenta"))
    console.print(
        "  [dim cyan]/[/dim cyan][dim]搜索[/dim]  "
        "[dim cyan]t[/dim cyan] [dim]标签[/dim]  "
        "[dim cyan]r[/dim cyan] [dim]推荐[/dim]  "
        "[dim cyan]?[/dim cyan] [dim]帮助[/dim]  "
        "[dim cyan]q[/dim cyan] [dim]退出[/dim]"
    )


# ── Search ─────────────────────────────────────────────────────────────────────

def _collect_all_tools() -> list[tuple]:
    """Walk all collections and return (tool_instance, category_name) pairs."""
    from core import HackingTool, HackingToolsCollection
    results = []

    def _walk(items, parent_title=""):
        for item in items:
            if isinstance(item, HackingToolsCollection):
                _walk(item.TOOLS, item.TITLE)
            elif isinstance(item, HackingTool):
                results.append((item, parent_title))

    _walk(all_tools)
    return results


def _get_all_tags() -> dict[str, list[tuple]]:
    """Build tag → [(tool, category)] index from all tools."""
    import re
    _rules = {
        r'(osint|harvester|maigret|holehe|spiderfoot|sherlock|recon)': 'osint',
        r'(subdomain|subfinder|amass|sublist|subdomainfinder)': 'recon',
        r'(scanner|scan|nmap|masscan|rustscan|nikto|nuclei|trivy)': 'scanner',
        r'(brute|gobuster|ffuf|dirb|dirsearch|ferox|hashcat|john|kerbrute)': 'bruteforce',
        r'(web|http|proxy|zap|xss|sql|wafw00f|arjun|caido|mitmproxy)': 'web',
        r'(wireless|wifi|wlan|airgeddon|bettercap|wifite|fluxion|deauth)': 'wireless',
        r'(phish|social.media|evilginx|setoolkit|social.fish|social.engineer)': 'social-engineering',
        r'(c2|sliver|havoc|mythic|pwncat|reverse.shell|pyshell)': 'c2',
        r'(privesc|peass|linpeas|winpeas)': 'privesc',
        r'(tunnel|pivot|ligolo|chisel|proxy|anon)': 'network',
        r'(password|credential|hash|crack|secret|trufflehog|gitleaks)': 'credentials',
        r'(forensic|memory|volatility|binwalk|autopsy|wireshark|pspy)': 'forensics',
        r'(reverse.eng|ghidra|radare|jadx|androguard|apk)': 'reversing',
        r'(cloud|aws|azure|gcp|kubernetes|prowler|scout|pacu)': 'cloud',
        r'(mobile|android|ios|frida|mobsf|objection|droid)': 'mobile',
        r'(active.directory|bloodhound|netexec|impacket|responder|certipy|kerberos|winrm|smb|ldap)': 'active-directory',
        r'(ddos|dos|slowloris|goldeneye|ufonet)': 'ddos',
        r'(payload|msfvenom|fatrat|venom|stitch|enigma)': 'payload',
        r'(crawler|spider|katana|gospider)': 'crawler',
    }
    tag_index: dict[str, list[tuple]] = {}
    for tool, cat in _collect_all_tools():
        combined = " ".join(
            part for part in [
                tool.TITLE,
                tool.DESCRIPTION,
                original_text(tool, "TITLE"),
                original_text(tool, "DESCRIPTION"),
            ]
            if part
        ).lower()
        # Manual tags first
        tool_tags = set(getattr(tool, "TAGS", []) or [])
        # Auto-derive tags from title/description
        for pattern, tag in _rules.items():
            if re.search(pattern, combined, re.IGNORECASE):
                tool_tags.add(tag)
        for t in tool_tags:
            tag_index.setdefault(t, []).append((tool, cat))
    return tag_index


def filter_by_tag():
    """Show available tags, user picks one, show matching tools."""
    tag_index = _get_all_tags()
    sorted_tags = sorted(tag_index.keys())

    # Show tags in a compact grid
    console.print(Panel(
        "  ".join(f"[bold cyan]{t}[/bold cyan]([dim]{len(tag_index[t])}[/dim])" for t in sorted_tags),
        title="[bold magenta] 可用标签 [/bold magenta]",
        border_style="magenta", box=box.ROUNDED, padding=(0, 2),
    ))

    tag = Prompt.ask("[bold cyan]输入标签[/bold cyan]", default="").strip().lower()
    if not tag or tag not in tag_index:
        if tag:
            console.print(f"[dim]未找到标签 '{tag}'。[/dim]")
            Prompt.ask("[dim]按回车返回[/dim]", default="")
        return

    matches = tag_index[tag]
    table = Table(
        title=f"标签为 '{tag}' 的工具",
        box=box.SIMPLE_HEAD, show_lines=True,
    )
    table.add_column("编号", justify="center", style="bold cyan", width=5)
    table.add_column("状态", width=6)
    table.add_column("工具", style="bold yellow", min_width=20)
    table.add_column("分类", style="magenta", min_width=15)

    for i, (tool, cat) in enumerate(matches, start=1):
        status = "[green]已装[/green]" if tool.is_installed else "[dim]未装[/dim]"
        table.add_row(str(i), status, tool.TITLE, cat)

    table.add_row("99", "", "返回主菜单", "")
    console.print(table)

    raw = Prompt.ask("[bold cyan]>[/bold cyan]", default="").strip()
    if not raw or raw == "99":
        return
    try:
        idx = int(raw)
    except ValueError:
        return
    if 1 <= idx <= len(matches):
        tool, cat = matches[idx - 1]
        tool.show_options()


_RECOMMENDATIONS = {
    "扫描网络":           ["scanner", "port-scanner"],
    "查找子域名":         ["recon"],
    "扫描漏洞":           ["scanner", "web"],
    "破解密码":           ["bruteforce", "credentials"],
    "查找泄露密钥":       ["credentials"],
    "钓鱼演练":           ["social-engineering"],
    "后渗透":             ["c2", "privesc"],
    "网络横向移动":       ["network"],
    "渗透活动目录":       ["active-directory"],
    "渗透 Web 应用":     ["web", "scanner"],
    "云环境渗透":         ["cloud"],
    "移动应用渗透":       ["mobile"],
    "逆向二进制文件":     ["reversing"],
    "抓取 WiFi 握手包": ["wireless"],
    "拦截 HTTP 流量":    ["web", "network"],
    "取证分析":           ["forensics"],
    "DDoS 测试":         ["ddos"],
    "生成载荷":           ["payload"],
    "查找 XSS 漏洞":     ["web"],
    "爆破目录":           ["bruteforce", "web"],
    "对目标做 OSINT / 侦察": ["osint", "recon"],
    "隐藏身份":           ["network"],
}


def recommend_tools():
    """Show common tasks, user picks one, show matching tools."""
    table = Table(
        title="你想做什么？",
        box=box.SIMPLE_HEAD,
    )
    table.add_column("编号", justify="center", style="bold cyan", width=5)
    table.add_column("任务", style="bold yellow")

    tasks = list(_RECOMMENDATIONS.keys())
    for i, task in enumerate(tasks, start=1):
        table.add_row(str(i), task)

    table.add_row("99", "返回主菜单")
    console.print(table)

    raw = Prompt.ask("[bold cyan]>[/bold cyan]", default="").strip()
    if not raw or raw == "99":
        return

    try:
        idx = int(raw)
    except ValueError:
        return

    if 1 <= idx <= len(tasks):
        task = tasks[idx - 1]
        tag_names = _RECOMMENDATIONS[task]
        tag_index = _get_all_tags()

        # Collect unique tools across all matching tags
        seen = set()
        matches = []
        for tag in tag_names:
            for tool, cat in tag_index.get(tag, []):
                if id(tool) not in seen:
                    seen.add(id(tool))
                    matches.append((tool, cat))

        if not matches:
            console.print("[dim]没有找到适合该任务的工具。[/dim]")
            Prompt.ask("[dim]按回车返回[/dim]", default="")
            return

        console.print(Panel(
            f"[bold]推荐工具：{task}[/bold]",
            border_style="green", box=box.ROUNDED,
        ))

        rtable = Table(box=box.SIMPLE_HEAD, show_lines=True)
        rtable.add_column("编号", justify="center", style="bold cyan", width=5)
        rtable.add_column("状态", width=6)
        rtable.add_column("工具", style="bold yellow", min_width=20)
        rtable.add_column("分类", style="magenta")

        for i, (tool, cat) in enumerate(matches, start=1):
            status = "[green]已装[/green]" if tool.is_installed else "[dim]未装[/dim]"
            rtable.add_row(str(i), status, tool.TITLE, cat)

        rtable.add_row("99", "", "返回", "")
        console.print(rtable)

        raw2 = Prompt.ask("[bold cyan]>[/bold cyan]", default="").strip()
        if raw2 and raw2 != "99":
            try:
                ridx = int(raw2)
                if 1 <= ridx <= len(matches):
                    matches[ridx - 1][0].show_options()
            except ValueError:
                pass


def search_tools(query: str | None = None):
    """Search tools — accepts inline query or prompts for one."""
    if query is None:
        query = Prompt.ask("[bold cyan]/ 搜索[/bold cyan]", default="").strip().lower()
    else:
        query = query.lower()
    if not query:
        return

    all_tool_list = _collect_all_tools()

    # Match against title + description + tags
    matches = []
    for tool, category in all_tool_list:
        title = (tool.TITLE or "").lower()
        desc = (tool.DESCRIPTION or "").lower()
        original_title = (original_text(tool, "TITLE") or "").lower()
        original_desc = (original_text(tool, "DESCRIPTION") or "").lower()
        tags = " ".join(getattr(tool, "TAGS", []) or []).lower()
        if query in title or query in desc or query in original_title or query in original_desc or query in tags:
            matches.append((tool, category))

    if not matches:
        console.print(f"[dim]没有找到匹配 '{query}' 的工具。[/dim]")
        Prompt.ask("[dim]按回车返回[/dim]", default="")
        return

    # Display results
    table = Table(
        title=f"搜索结果：'{query}'",
        box=box.SIMPLE_HEAD, show_lines=True,
    )
    table.add_column("编号", justify="center", style="bold cyan", width=5)
    table.add_column("工具", style="bold yellow", min_width=20)
    table.add_column("分类", style="magenta", min_width=15)
    table.add_column("说明", style="white", overflow="fold")

    for i, (tool, cat) in enumerate(matches, start=1):
        desc = (tool.DESCRIPTION or "—").splitlines()[0]
        table.add_row(str(i), tool.TITLE, cat, desc)

    table.add_row("99", "返回主菜单", "", "")
    console.print(table)

    raw = Prompt.ask("[bold cyan]>[/bold cyan]", default="").strip().lower()
    if not raw or raw == "99":
        return

    try:
        idx = int(raw)
    except ValueError:
        return

    if 1 <= idx <= len(matches):
        tool, cat = matches[idx - 1]
        console.print(Panel(
            f"[bold magenta]{tool.TITLE}[/bold magenta]  [dim]({cat})[/dim]",
            border_style="magenta", box=box.ROUNDED,
        ))
        tool.show_options()


# ── Main interaction loop ──────────────────────────────────────────────────────

def interact_menu():
    while True:
        try:
            build_menu()
            raw = Prompt.ask(
                "[bold magenta]╰─>[/bold magenta]", default=""
            ).strip()

            if not raw:
                continue

            raw_lower = raw.lower()

            if raw_lower in ("?", "help", "帮助"):
                show_help()
                continue

            if raw.startswith("/"):
                # Inline search: /subdomain → search immediately
                query = raw[1:].strip()
                search_tools(query=query if query else None)
                continue

            if raw_lower in ("s", "search", "搜索"):
                search_tools()
                continue

            if raw_lower in ("t", "tag", "tags", "filter", "标签"):
                filter_by_tag()
                continue

            if raw_lower in ("r", "rec", "recommend", "推荐"):
                recommend_tools()
                continue

            if raw_lower in ("q", "quit", "exit", "退出"):
                console.print(Panel(
                    "[bold white on magenta]  再见，注意安全  [/bold white on magenta]",
                    box=box.HEAVY, border_style="magenta",
                ))
                break

            try:
                choice = int(raw_lower)
            except ValueError:
                console.print("[red]输入无效，请输入数字、/关键词 搜索，或 q 退出。[/red]")
                Prompt.ask("[dim]按回车继续[/dim]", default="")
                continue

            if 1 <= choice <= len(all_tools):
                title, _, _ = tool_definitions[choice - 1]
                console.print(Panel(
                    f"[bold magenta]{title}[/bold magenta]",
                    border_style="magenta", box=box.ROUNDED,
                ))
                try:
                    all_tools[choice - 1].show_options()
                except Exception as e:
                    console.print(Panel(
                        f"[red]打开 {title} 时出错[/red]\n{e}",
                        border_style="red",
                    ))
                    Prompt.ask("[dim]按回车返回主菜单[/dim]", default="")
            else:
                console.print(f"[red]请输入 1–{len(all_tools)}，或输入 ? 查看帮助、q 退出。[/red]")
                Prompt.ask("[dim]按回车继续[/dim]", default="")

        except KeyboardInterrupt:
            console.print("\n[bold red]已中断，正在退出[/bold red]")
            break


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    try:
        from os_detect import CURRENT_OS

        if CURRENT_OS.system == "windows":
            console.print(Panel("[bold red]请在 Linux 或 macOS 上运行此工具。[/bold red]"))
            if Confirm.ask("Open guidance link in your browser?", default=True):
                webbrowser.open_new_tab(f"{REPO_WEB_URL}#windows")
            return

        if CURRENT_OS.system not in ("linux", "macos"):
            console.print(f"[yellow]当前操作系统 {CURRENT_OS.system} 未正式支持，仍将继续尝试启动。[/yellow]")

        get_tools_dir()   # ensures ~/.hackingtool/tools/ exists
        interact_menu()

    except KeyboardInterrupt:
        console.print("\n[bold red]正在退出...[/bold red]")


if __name__ == "__main__":
    main()
