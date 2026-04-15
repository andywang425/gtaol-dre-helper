# 代码贡献指南

欢迎参与本项目的开发！

## 项目结构

```
gtaol-dre-helper
├─gtaol_dre_helper/
│  ├─models/          数据模型
│  ├─screens/         界面
│  ├─services/        服务
│  ├─utils/           工具
│  ├─widgets/         组件
│  └─app.py           Textual App
├─tests/              测试用例
└─main.py             程序入口
```

## 基本环境要求

- Windows 11 (x64)
- Windows Terminal
- Powershell 5.1
- Python 3.14
- [uv](https://docs.astral.sh/uv/)

## 从源代码运行

1. 克隆仓库到本地

   ```powershell
   git clone https://github.com/andywang425/gtaol-dre-helper
   ```

2. 进入项目根目录

   ```powershell
   cd gtaol-dre-helper
   ```

3. 创建虚拟环境

   ```powershell
   uv venv --python 3.14
   ```

4. 安装依赖

   ```powershell
   uv sync --group dev
   ```

5. 准备 OCR 所需的 [Tesseract](https://github.com/UB-Mannheim/tesseract/releases/latest)

   建议从[Release 包](https://github.com/andywang425/gtaol-dre-helper/releases/latest)中把整个 `tesseract` 目录复制过来，这是精简后的版本，去掉了非必要文件。

6. 启动程序

   ```powershell
   uv run python main.py
   ```

### 开发调试

建议先在 IDE 的终端中运行 `.\console` 打开 Textual 控制台，方便观察日志。

然后打开 Windows Terminal (PowerShell)，运行 `.\dev` 以开发模式启动程序。

## 测试

运行全部测试用例：

```powershell
uv run pytest
```

### 测试约定

- 为新功能添加对应的测试用例
- 每个测试函数都应带中文注释，简要说明这个用例在验证什么
- 提交代码前，确保所有测试通过

## 构建与发版

### 额外环境要求

在[基本环境要求](#基本环境要求)的基础上，你还需要：

- [7-Zip](https://www.7-zip.org/)
- [Visual Studio Build Tools 2022](https://visualstudio.microsoft.com/zh-hans/downloads/)

说明：

- `7z.exe` 需要在 PATH 上
- Build Tools 不需要安装完整 IDE，但需要可用的 MSVC 工具链

如果你使用 VS Code，又不想改系统 PATH，可以在 `.vscode/settings.json` 中加：

```json
"terminal.integrated.env.windows": {
  "PATH": "你的7-Zip安装路径;${env:PATH}"
}
```

### 构建前自检

```powershell
# 检查是否有 7z 命令
where.exe 7z

# 检查构建脚本能否探测到安装的 Visual Studio Build Tools 2022 且 MSVC 工具链可用
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'; & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64

# 检查 Nuitka 能否检测到 MSVC
uv run python -m nuitka --version
```

如果 `uv run python -m nuitka --version` 的输出里能看到类似 `Version C compiler: cl (cl 14.3).` 的东西，说明 Nuitka 已找到可用的编译器。

### 开始构建

默认使用 `Nuitka` 构建正式包：

```powershell
.\build.ps1
```

也可以显式指定后端：

```powershell
.\build.ps1 -Backend nuitka
.\build.ps1 -Backend pyinstaller
```

如果正式包构建失败，可以用 `PyInstaller` 构建兼容性回退包。

### 构建产物

构建完成后，产物位于 `dist` 目录，常见内容包括：

- `dist\gtaol-dre-helper`
- `dist\gtaol-dre-helper.7z`
- `dist\gtaol-dre-helper-pyinstaller`
- `dist\gtaol-dre-helper-pyinstaller.7z`

正式发版时优先使用 `gtaol-dre-helper.7z`。

### 冒烟检查

构建完成后请手动运行编译得到的 `gtaol-dre-helper.exe`，在游戏中实际测试一下，确保软件能否正常工作。
