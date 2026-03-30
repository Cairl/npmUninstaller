import os
import shutil
import stat
import subprocess
import sys
import msvcrt
import warnings
from pathlib import Path

# 获取常用路径
ENV = os.environ
APPDATA = Path(ENV.get("APPDATA", ""))
LOCAL = Path(ENV.get("LOCALAPPDATA", ""))
HOME = Path(ENV.get("USERPROFILE", ""))

def remove_readonly(func, path, _):
    """清除只读属性并重试删除"""
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
    
    roots = ["C:\\Users\\", "C:\\ProgramData\\", "C:\\\"Program Files\"\\", "C:\\\"Program Files (x86)\"\\"]
    found = []
    
    for root in roots:
        try:
            cmd = f'dir /s /b /a {root}*{keyword}* 2>nul'
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
    
    print(f"[{tag}] 深度搜索完成，发现 {len(found)} 项")
    
    if found:
        unique_found = sorted(list(set(found)), key=len, reverse=True)
        for p in unique_found: print(f"  - {p}")
        
        print(f"\n是否删除? (Y/n): ", end="", flush=True)
        char = msvcrt.getch()
        if char == b'\r':
            choice = 'Y'
        else:
            try:
                choice = char.decode('utf-8').upper()
            except:
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
    except: pass

    uninstall_npm(["openclaw"], tag)
    
    try:
        subprocess.run(["schtasks", "/Delete", "/TN", "OpenClaw Gateway", "/F"], check=False, capture_output=True)
    except: pass

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

def main():
    menu = [
        ("Claude Code", cleanup_claude),
        ("Claude Code Router", cleanup_claude_router),
        ("Gemini CLI", cleanup_gemini),
        ("iFlow CLI", cleanup_iflow),
        ("OpenClaw", cleanup_openclaw),
        ("OpenCode", cleanup_opencode),
    ]

    while True:
        clear_screen()
        for i, (name, _) in enumerate(menu, 1):
            print(f" [{i}] 卸载 {name}")
        print("\n> ", end="", flush=True)

        try:
            char = msvcrt.getch().decode('utf-8').upper()
        except: continue
        
        print(char)

        if char.isdigit():
            idx = int(char) - 1
            if 0 <= idx < len(menu):
                name, func = menu[idx]
                print()  # 换行美化
                func()
                print("\n任务已完成！按任意键返回菜单...")
                msvcrt.getch()

if __name__ == "__main__":
    main()
