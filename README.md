# LaTeX Builder

一个用于构建 LaTeX 文档的 Python 工具，集成了 Git 版本管理和自动差异生成功能。

## 功能特性

- **Git 集成**: 自动检测当前提交、分支和标签信息
- **LaTeX 编译**: 使用 XeLaTeX 和 BibTeX 的完整编译工作流
- **差异生成**: 使用 latexdiff 创建 Git 版本间的可视化差异
- **版本管理**: 为 LaTeX 文档生成版本信息文件
- **清晰日志**: 美观的命令行界面，进度清晰可见

## 安装

```bash
# 使用 pip 安装
pip install -e .

# 或使用 uv 安装
uv pip install -e .
```

## 使用方法

### 命令行使用

```bash
# 基本使用（在包含 main.tex 的 Git 仓库中）
latex-builder

# 指定 LaTeX 文件
latex-builder -t document.tex

# 指定输出目录
latex-builder -o build_output

# 启用详细输出
latex-builder -v

# 完整选项
latex-builder -t main.tex -r misc/revision.tex -o output -b build -v
```

### Python API 使用

```python
from latex_builder import Config, LatexDiffTool
from pathlib import Path

# 创建配置
config = Config(
    tex_file="main.tex",
    revision_path="misc/revision.tex",
    output_folder=Path("output"),
    build_dir=Path("build"),
    verbose=True
)

# 运行工具
tool = LatexDiffTool(config)
exit_code = tool.run()
```

## 包结构

包按功能模块进行组织：

```
latex_builder/
├── cli/                    # 命令行界面
│   ├── main.py            # 主应用程序类
│   └── parser.py          # 命令行参数解析
├── config/                # 配置管理
│   └── settings.py        # 配置数据类
├── diff/                  # 差异生成
│   └── generator.py       # LaTeX 差异操作
├── git/                   # Git 操作
│   ├── repository.py      # Git 仓库处理
│   └── revision.py        # Git 版本数据结构
├── latex/                 # LaTeX 处理
│   └── processor.py       # LaTeX 编译
└── utils/                 # 共享工具
    ├── command.py         # 命令执行
    └── logging.py         # 日志设置
```

## 配置选项

- `tex_file`: 要编译的主 LaTeX 文件（默认："main.tex"）
- `revision_path`: revision.tex 文件路径（默认："miscellaneous/revision.tex"）
- `verbose`: 启用调试日志（默认：False）
- `output_folder`: 输出文件目录（默认："output"）
- `build_dir`: 临时构建文件目录（默认："build"）

## 输出文件

工具会生成以下输出文件：

- **当前版本 PDF**: `{版本名称}.pdf`
- **差异 PDF**: 
  - `diff/since-last-commit-{hash}.pdf`
  - `diff/since-last-tag-{tag}.pdf`
- **元数据**: `metadata.json` 包含版本信息
- **版本文件**: `revision.tex` 包含用于 LaTeX 的版本宏

## 系统要求

- Python 3.11+
- Git 仓库
- LaTeX 安装包括：
  - XeLaTeX
  - BibTeX
  - latexdiff

## 使用示例

```bash
# 在包含 LaTeX 项目的 Git 仓库中
cd my-latex-project

# 安装包
uv pip install -e /path/to/latex-builder

# 构建当前版本并生成差异
uv run latex-builder -v
```

这将：
1. 分析当前 Git 状态
2. 生成版本信息文件
3. 编译当前版本的 PDF
4. 与上一个提交和上一个标签生成差异文档
5. 将所有文件输出到 `output/` 目录

## 开发架构

该包采用模块化架构，职责分离清晰：

- **CLI 层**: 处理命令行交互
- **核心逻辑**: Git 操作、LaTeX 处理、差异生成
- **配置**: 集中化设置管理
- **工具**: 日志和命令执行的共享功能

每个模块都可独立测试，遵循 Python 最佳实践。
