# 项目概述

- 项目名称：`gtaol-dre-helper`
- 项目定位：辅助 GTA Online 玩家执行“卡 CEO”和“卡单人战局”操作的 Windows 小工具
- 当前形态：基于 `Textual` 的 TUI 应用，入口为 `main.py`，主应用类为 `gtaol_dre_helper.app.DreHelperApp`
- 核心业务：
  - 卡 CEO：截图指定区域 -> OCR 识别玩家人数 -> 满足“已加入人数 >= 2”时执行按键序列
  - 卡单：截图指定区域 -> 记录/比对菜单颜色 -> 菜单消失时执行按键序列
- 运行时主链路：加载配置 -> 初始化 Tesseract -> 轮询监控开关键 -> 按方案执行 CEO/卡单检测 -> 触发键盘模拟输入

# 运行环境

- 操作系统：Windows 11 (x64)
- Python：`>=3.14`
- 包管理与虚拟环境：`uv`
- 主要依赖：
  - `textual`：TUI 界面
  - `pydantic`：配置模型与校验
  - `pytesseract` + 内置 `tesseract.exe`：OCR
  - `mss` + `Pillow`：截图与图像处理
  - `PyYAML`：读取 `config.yaml`

# 项目结构

- `main.py`：程序入口
- `gtaol_dre_helper/app.py`：Textual 应用入口
- `gtaol_dre_helper/screens/dashboard.py`：当前主界面
- `gtaol_dre_helper/services/monitor.py`：监控主循环核心
- `gtaol_dre_helper/models/`：数据模型与校验
- `gtaol_dre_helper/utils/`：OCR、截图、热键、输入、路径、配置等工具
- `tests/`：测试

# 开发与验证

## 测试

- 测试框架：`pytest`
- 测试命令：`uv run pytest`

每个测试用例函数都要有中文注释，对用例做简要说明

## 常用脚本

- 打包：`.\build.ps1`
  - 默认后端是 `Nuitka`，会执行依赖同步、主程序打包、使用 Visual Studio Build Tools 编译 `RegionLocator.exe`、复制 `config.example.yaml` 与 `tesseract` 资源，并生成 `7z` 压缩包
  - 可通过 `.\build.ps1 -Backend nuitka` 或 `.\build.ps1 -Backend pyinstaller` 显式指定后端
  - 具体后端脚本：`.\build-nuitka.ps1`、`.\build-pyinstaller.ps1`

## 代码质量命令

- 当前项目未配置 lint、typecheck 或 format 命令
- 目前可用的验证方式以测试为主，即执行 `uv run pytest`
