import os
import shutil
import stat
import subprocess
import msvcrt
import warnings
import ctypes
import atexit
from ctypes import wintypes
from pathlib import Path

class CONSOLE_CURSOR_INFO(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("bVisible", wintypes.BOOL)]

def set_cursor_visible(visible):
    handle = ctypes.windll.kernel32.GetStdHandle(-11)
    info = CONSOLE_CURSOR_INFO()
    ctypes.windll.kernel32.GetConsoleCursorInfo(handle, ctypes.byref(info))
    info.bVisible = visible
    ctypes.windll.kernel32.SetConsoleCursorInfo(handle, ctypes.byref(info))

def move_cursor_up(lines):
    handle = ctypes.windll.kernel32.GetStdHandle(-11)
    info = ctypes.wintypes.CONSOLE_SCREEN_BUFFER_INFO()
    ctypes.windll.kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(info))
    pos = info.dwCursorPosition
    pos.Y -= lines
    ctypes.windll.kernel32.SetConsoleCursorPosition(handle, pos)

ENV = os.environ
APPDATA = Path(ENV.get("APPDATA", ""))
LOCAL = Path(ENV.get("LOCALAPPDATA", ""))
HOME = Path(ENV.get("USERPROFILE", ""))

def remove_readonly(func, path, _):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass

def rm_path(p: Path, tag="清理", silent=False):
    if not p.exists():
        return False
    try:
        p = p.resolve()
        if p.is_dir():
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                shutil.rmtree(p, onerror=remove_readonly)
            if p.exists():
                subprocess.run(["cmd", "/c", "rmdir", "/s", "/q", f'"{p}"'], check=False, capture_output=True)
        else:
            try:
                os.chmod(p, stat.S_IWRITE)
                p.unlink()
            except Exception:
                subprocess.run(["cmd", "/c", "del", "/f", "/q", f'"{p}"'], check=False, capture_output=True)
        
        success = not p.exists()
        if success and not silent:
            print(f"[{tag}] 已删除: {p.name}")
        return success
    except Exception:
        return False

def uninstall_npm(packages, tag="清理"):
    npm_exe = shutil.which("npm.cmd") or shutil.which("npm.exe") or shutil.which("npm")
    if not npm_exe: return
    
    print(f"[{tag}] 正在卸载全局包...")
    try:
        args = ["uninstall", "-g"] + packages + ["--force", "--loglevel=silent"]
        if npm_exe.lower().endswith(".ps1"):
            cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", npm_exe] + args
        else:
            cmd = [npm_exe] + args
        
        subprocess.run(cmd, check=False, capture_output=True)
        print(f"[{tag}] 卸载全局包完成")
    except Exception:
        print(f"[{tag}] 卸载全局包失败 (已跳过)")

def find_and_clean_leftovers(keyword, tag="扫描"):
    print(f"[{tag}] 正在深度搜索残留项...")
    
    roots = ["C:\\Users\\", "C:\\ProgramData\\", "C:\\Program Files\\", "C:\\Program Files (x86)\\"]
    found = []
    
    for root in roots:
        try:
            cmd = f'dir /s /b /a "{root}*{keyword}*" 2>nul'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='gbk', errors='ignore')
            if result.stdout:
                lines = result.stdout.strip().splitlines()
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    if "ForceUninstall" in line or "$Recycle.Bin" in line or "System32" in line or "SysWOW64" in line:
                        continue
                    found.append(line)
        except Exception: pass
    
    if found:
        print(f"[{tag}] 深度搜索完成，发现 {len(found)} 项")
        unique_found = sorted(list(set(found)), key=len, reverse=True)
        for p in unique_found: print(f"  - {p}")
        
        print(f"\n是否删除? (Y/n): ", end="", flush=True)
        char = msvcrt.getch()
        if char == b'\r':
            choice = 'Y'
        else:
            try:
                choice = char.decode('utf-8').upper()
            except Exception:
                choice = 'N'
        print(choice)
        
        if choice == 'Y':
            print(f"[{tag}] 正在执行深度清理...")
            count = 0
            for p_str in unique_found:
                if rm_path(Path(p_str), tag, silent=True): count += 1
            print(f"[{tag}] 深度清理完成 (删除了 {count} 个残留项)")
    else:
        print(f"[{tag}] 未发现明显残留。")

def cleanup_claude():
    tag = "Claude Code"
    uninstall_npm(["@anthropic-ai/claude-code", "@musistudio/claude-code-router"], tag)
    paths = [
        APPDATA / "claude-code", LOCAL / "claude-code", HOME / ".claude",
        HOME / ".claude.json", HOME / ".claude-code-router",
        HOME / ".config" / "claude-code", HOME / "Desktop" / "Claude Code.lnk",
        HOME / ".local" / "bin" / "claude.exe",
        HOME / ".local" / "share" / "claude", HOME / ".local" / "state" / "claude"
    ]
    for p in paths: rm_path(p, tag, silent=True)
    find_and_clean_leftovers("claude", tag)

def cleanup_gemini():
    tag = "Gemini CLI"
    uninstall_npm(["@google/gemini-cli"], tag)
    paths = [
        APPDATA / "gemini-cli", LOCAL / "gemini-cli", HOME / ".gemini",
        HOME / ".config" / "gemini-cli", HOME / "Desktop" / "Gemini CLI.lnk",
        HOME / ".local" / "bin" / "gemini.exe"
    ]
    for p in paths: rm_path(p, tag, silent=True)
    find_and_clean_leftovers("gemini", tag)

def cleanup_hermes_agent():
    tag = "Hermes Agent"
    uninstall_npm(["hermes-agent"], tag)
    paths = [
        APPDATA / "hermes-agent", LOCAL / "hermes-agent", HOME / ".hermes-agent",
        HOME / ".hermes", HOME / ".config" / "hermes-agent",
        HOME / "Desktop" / "Hermes Agent.lnk"
    ]
    for p in paths: rm_path(p, tag, silent=True)
    find_and_clean_leftovers("hermes", tag)

def cleanup_iflow():
    tag = "iFlow CLI"
    uninstall_npm(["@iflow-ai/iflow-cli"], tag)
    paths = [
        APPDATA / "iflow-cli", LOCAL / "iflow-cli", HOME / ".iflow-cli",
        HOME / ".iflow", LOCAL / "oh-my-iflow", HOME / "Desktop" / "iFlow CLI.lnk",
        HOME / ".config" / "iflow-cli", HOME / ".config" / "configstore" / "update-notifier-@iflow-ai",
        APPDATA / "npm" / "iflow", APPDATA / "npm" / "iflow.cmd", APPDATA / "npm" / "iflow.ps1"
    ]
    for p in paths: rm_path(p, tag, silent=True)
    for p in (HOME / ".bun" / "install" / "cache").glob("*iflow*"): rm_path(p, tag, silent=True)
    find_and_clean_leftovers("iflow", tag)

def cleanup_opencode():
    tag = "OpenCode"
    uninstall_npm(["opencode-ai"], tag)
    paths = [
        APPDATA / "opencode", LOCAL / "opencode", HOME / ".opencode",
        HOME / ".config" / "opencode", LOCAL / "oh-my-opencode", 
        HOME / "Desktop" / "OpenCode.lnk"
    ]
    for p in paths: rm_path(p, tag, silent=True)
    for p in (HOME / ".bun" / "install" / "cache").glob("*opencode*"): rm_path(p, tag, silent=True)
    find_and_clean_leftovers("opencode", tag)

def cleanup_openclaw():
    tag = "OpenClaw"
    try:
        subprocess.run(["openclaw", "uninstall", "--all", "--yes", "--non-interactive"], check=False, capture_output=True)
    except Exception: pass

    uninstall_npm(["openclaw"], tag)
    
    try:
        subprocess.run(["schtasks", "/Delete", "/TN", "OpenClaw Gateway", "/F"], check=False, capture_output=True)
    except Exception: pass

    paths = [
        HOME / ".openclaw",
        APPDATA / "openclaw", LOCAL / "openclaw", 
        HOME / ".config" / "openclaw", LOCAL / "oh-my-openclaw", 
        HOME / "Desktop" / "OpenClaw.lnk",
        LOCAL / "Temp" / "openclaw",
        LOCAL / "Temp" / "agency-agents" / "integrations" / "openclaw"
    ]
    for p in paths: rm_path(p, tag, silent=True)
    
    for p in (LOCAL / "Temp").glob("skills-*"):
        for test_file in (p / "tests").glob("openclaw*"):
            rm_path(test_file, tag, silent=True)
    
    for p in HOME.glob(".openclaw-*"):
        rm_path(p, tag, silent=True)
        
    for p in (HOME / ".bun" / "install" / "cache").glob("*openclaw*"): rm_path(p, tag, silent=True)
    find_and_clean_leftovers("openclaw", tag)

def cleanup_ollama():
    tag = "Ollama"
    paths = [
        HOME / ".ollama",
        LOCAL / "Ollama",
        APPDATA / "Ollama",
        LOCAL / "Programs" / "Ollama",
        HOME / ".config" / "ollama",
        HOME / "Desktop" / "Ollama.lnk",
    ]
    for p in paths: rm_path(p, tag, silent=True)
    find_and_clean_leftovers("ollama", tag)

def cleanup_cc_switch():
    tag = "cc-switch"
    paths = [
        HOME / ".cc-switch",
        LOCAL / "cc-switch",
        APPDATA / "cc-switch",
        HOME / ".config" / "cc-switch",
        HOME / "Desktop" / "cc-switch.lnk",
    ]
    for p in paths: rm_path(p, tag, silent=True)
    find_and_clean_leftovers("cc-switch", tag)

def cleanup_codex_cli():
    tag = "Codex CLI"
    uninstall_npm(["@openai/codex"], tag)
    paths = [
        HOME / ".codex",
        LOCAL / "Codex",
        APPDATA / "Codex",
        HOME / ".config" / "codex",
        HOME / "Desktop" / "Codex.lnk",
    ]
    for p in paths: rm_path(p, tag, silent=True)
    find_and_clean_leftovers("codex", tag)

def cleanup_codex():
    tag = "Codex"
    paths = [
        HOME / ".codex",
        LOCAL / "Codex",
        APPDATA / "Codex",
        HOME / ".config" / "codex",
        HOME / "Desktop" / "Codex.lnk",
    ]
    for p in paths: rm_path(p, tag, silent=True)
    find_and_clean_leftovers("codex", tag)

def cleanup_claude_router():
    tag = "Claude Code Router"
    uninstall_npm(["@musistudio/claude-code-router"], tag)
    paths = [
        HOME / ".claude-code-router",
        LOCAL / "Temp" / "claude-code-router"
    ]
    for p in paths: rm_path(p, tag, silent=True)
    find_and_clean_leftovers("claude-code-router", tag)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_key():
    ch = msvcrt.getch()
    if ch == b'\x00' or ch == b'\xe0':
        ch = msvcrt.getch()
        return ch
    return ch

ARROW_UP = b'H'
ARROW_DOWN = b'P'
ENTER = b'\r'
ESC = b'\x1b'

HIGHLIGHT = "\033[7m"
GRAY_BG = "\033[100m"
RESET = "\033[0m"

def render_menu(uninstall_items, clean_items, selected):
    clear_screen()

    all_names = [name for name, _ in uninstall_items + clean_items]
    max_name = max(len(name) for name in all_names)
    inner = max(max_name + 4, 24)
    bar = "─" * inner

    def section_header(title):
        dw = len(title) * 2
        pad_l = (inner - dw) // 2
        pad_r = inner - dw - pad_l
        body = f"{' ' * pad_l}{title}{' ' * pad_r}"
        print(f"│{GRAY_BG}{body}{RESET}│")

    def item(name, active):
        body = f"  {name}"
        padded = f"{body:<{inner}}"
        if active:
            print(f"│{HIGHLIGHT}{padded}{RESET}│")
        else:
            print(f"│{padded}│")

    print(f"┌{bar}┐")
    section_header("卸载")
    for i, (name, _) in enumerate(uninstall_items):
        item(name, selected == i)

    section_header("清除")
    offset = len(uninstall_items)
    for i, (name, _) in enumerate(clean_items):
        item(name, selected == offset + i)

    print(f"└{bar}┘")

def main():
    uninstall_items = [
        ("Claude Code", cleanup_claude),
        ("Claude Code Router", cleanup_claude_router),
        ("Codex CLI", cleanup_codex_cli),
        ("Gemini CLI", cleanup_gemini),
        ("Hermes Agent", cleanup_hermes_agent),
        ("iFlow CLI", cleanup_iflow),
        ("OpenClaw", cleanup_openclaw),
        ("OpenCode", cleanup_opencode),
    ]
    uninstall_items.sort(key=lambda x: x[0].lower())

    clean_items = [
        ("Codex", cleanup_codex),
        ("Ollama", cleanup_ollama),
    ]
    clean_items.sort(key=lambda x: x[0].lower())

    total_items = len(uninstall_items) + len(clean_items)
    selected = 0

    set_cursor_visible(False)
    atexit.register(set_cursor_visible, True)

    try:
        while True:
            render_menu(uninstall_items, clean_items, selected)

            key = get_key()

            if key == ARROW_UP:
                selected = (selected - 1) % total_items
            elif key == ARROW_DOWN:
                selected = (selected + 1) % total_items
            elif key == ENTER:
                if selected < len(uninstall_items):
                    name, func = uninstall_items[selected]
                else:
                    name, func = clean_items[selected - len(uninstall_items)]
                clear_screen()
                func()
                print("\n任务已完成！按任意键返回菜单...")
                msvcrt.getch()
            elif key == ESC:
                break
    except KeyboardInterrupt:
        pass
    finally:
        set_cursor_visible(True)
        clear_screen()

if __name__ == "__main__":
    main()
