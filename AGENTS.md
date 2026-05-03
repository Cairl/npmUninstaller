# AGENTS.md — npmUninstaller 项目总结

## 项目概述

Windows 下的交互式命令行工具，用于卸载和清理多种 AI CLI 工具的残留文件。单文件 Python 项目，无外部依赖。

## 文件结构

| 文件 | 作用 |
|---|---|
| `npm_uninstaller.py` | 主程序，包含所有逻辑 |
| `.gitignore` | Git 忽略规则 |

## 架构

**核心流程**：显示菜单 → 用户选择 → 执行清理 → 等待按键返回菜单

**菜单机制**：
- 菜单列表按名称 a-z 排序（`menu.sort(key=lambda x: x[0].lower())`）
- `[0]` 退出，`[1-9]` 对应清理选项，`Q` 也可退出
- 使用 `msvcrt.getch()` 读取单字符输入（无需回车）
- 光标在程序运行时隐藏，退出时恢复（`atexit` + `try/finally` 双重保障）

## 清理流程（三步走）

每个清理选项遵循统一模式，部分选项省略不需要的步骤：

1. **npm 全局卸载**（`uninstall_npm`）— 调用 `npm uninstall -g` 卸载指定包；Ollama 等非 npm 工具跳过此步
2. **删除已知路径**（`rm_path`）— 逐一删除配置/缓存/快捷方式等已知路径
3. **深度残留扫描**（`find_and_clean_leftovers`）— 在系统目录中搜索关键词匹配的残留文件，需用户确认后删除

## 核心函数

| 函数 | 作用 |
|---|---|
| `set_cursor_visible(visible)` | 通过 Windows API 控制控制台光标可见性 |
| `rm_path(p, tag, silent)` | 删除文件/目录，Python API 优先，失败回退 cmd 强制删除，处理只读属性 |
| `uninstall_npm(packages, tag)` | 查找 npm 可执行文件并执行全局卸载 |
| `find_and_clean_leftovers(keyword, tag)` | 在 `C:\Users\`、`C:\ProgramData\`、`C:\Program Files\`、`C:\Program Files (x86)\` 中递归搜索残留项 |

## 清理选项一览

| 菜单名称 | npm 包 | 特殊处理 |
|---|---|---|
| Claude Code | `@anthropic-ai/claude-code`, `@musistudio/claude-code-router` | 无 |
| Claude Code Router | `@musistudio/claude-code-router` | 无 |
| Gemini CLI | `@google/gemini-cli` | 无 |
| iFlow CLI | `@iflow-ai/iflow-cli` | 清理 npm bin 残留、Bun 缓存 |
| Ollama | 无（非 npm） | 仅清除残余，无 npm 卸载步骤 |
| OpenClaw | `openclaw` | 先调用 `openclaw uninstall`；删除计划任务；清理 Temp/Bun 缓存/通配文件 |
| OpenCode | `opencode-ai` | 清理 Bun 缓存 |

## 编程哲学与约定

- **单文件项目**：所有逻辑集中在 `npm_uninstaller.py`，不拆分模块
- **无外部依赖**：仅使用 Python 标准库
- **Windows 专用**：依赖 `msvcrt`、`ctypes.windll`、`cmd /c` 等 Windows API
- **异常处理**：使用 `except Exception:` 而非裸 `except:`，避免吞掉 `KeyboardInterrupt`
- **删除策略**：Python API 优先 → cmd 命令兜底 → 处理只读属性
- **深度扫描排序**：去重后按路径长度降序排列，确保子目录先于父目录被删除
- **0 项提示**：深度搜索发现 0 项时直接显示"未发现明显残留"，不显示冗余的"发现 0 项"
- **终端状态恢复**：程序退出时必须恢复光标可见性并清屏，通过 `atexit` + `try/finally` 双重保障
