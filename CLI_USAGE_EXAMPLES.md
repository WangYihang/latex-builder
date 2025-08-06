# LaTeX Builder - 新的命令行界面使用示例

## 概述

重新设计的 LaTeX Builder 工具现在提供了更直观的命令行界面，支持指定 Git 仓库路径、LaTeX 编译器选择，以及灵活的版本比较选项。

## 基本用法

### 1. 在当前目录构建 LaTeX 项目

```bash
# 最简单的用法 - 使用当前目录，默认设置
uv run latex-builder

# 等同于
uv run latex-builder . -f main.tex -c xelatex
```

### 2. 指定 Git 仓库路径

```bash
# 指定项目路径
uv run latex-builder /path/to/your/latex/project

# 指定相对路径
uv run latex-builder ../my-thesis
```

### 3. 指定 LaTeX 文件和编译器

```bash
# 使用不同的主文件和编译器
uv run latex-builder . -f thesis.tex -c pdflatex

# 使用 lualatex 编译器
uv run latex-builder . -c lualatex
```

## 版本比较选项

### 1. 自动选择比较目标（默认行为）

```bash
# 自动选择：优先使用最新标签，否则使用上一个提交
uv run latex-builder
```

### 2. 与指定标签比较

```bash
# 与特定标签比较
uv run latex-builder --compare-with v1.0.0

# 与特定标签比较，使用不同编译器
uv run latex-builder --compare-with v2.1.0 -c pdflatex
```

### 3. 与指定提交比较

```bash
# 与特定提交哈希比较
uv run latex-builder --compare-with abc1234

# 与特定分支比较
uv run latex-builder --compare-with feature/new-chapter
```

## 构建模式

### 1. 完整模式（默认）

```bash
# 构建当前版本和差异文档
uv run latex-builder
```

### 2. 仅构建当前版本

```bash
# 跳过差异生成，只构建当前版本
uv run latex-builder --no-diff
```

### 3. 仅生成差异

```bash
# 只生成差异文件，不构建 PDF
uv run latex-builder --diff-only
```

## 输出控制

### 1. 自定义输出目录

```bash
# 指定输出和构建目录
uv run latex-builder -o my-output -b my-build
```

### 2. 自定义版本文件路径

```bash
# 指定版本信息文件位置
uv run latex-builder --revision-file version/revision.tex
```

## 日志级别

### 1. 详细输出

```bash
# 启用详细日志
uv run latex-builder -v
```

### 2. 静默模式

```bash
# 只显示错误信息
uv run latex-builder -q
```

## 实际使用场景示例

### 场景 1: 学术论文版本管理

```bash
# 构建论文并与上一个发布版本比较
uv run latex-builder ~/papers/my-paper --compare-with submitted-version -c xelatex

# 只构建当前版本用于预览
uv run latex-builder ~/papers/my-paper --no-diff -q
```

### 场景 2: 书籍/文档项目

```bash
# 使用自定义文件名和输出目录
uv run latex-builder ~/books/my-book \
  -f book.tex \
  -c lualatex \
  -o releases \
  --revision-file meta/version.tex
```

### 场景 3: 持续集成环境

```bash
# CI 环境中的静默构建
uv run latex-builder . --compare-with origin/main -q

# 只生成差异用于代码审查
uv run latex-builder . --diff-only --compare-with develop
```

## 完整选项参考

```
positional arguments:
  repo_path             Git 仓库路径（默认：当前目录）

options:
  -h, --help            显示帮助信息
  -f TEX_FILE, --tex-file TEX_FILE
                        主 LaTeX 文件（默认：main.tex）
  -c {xelatex,pdflatex,lualatex}, --compiler {xelatex,pdflatex,lualatex}
                        LaTeX 编译器（默认：xelatex）
  --compare-with COMPARE_WITH
                        比较目标（标签或提交哈希）
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        输出目录（默认：output）
  -b BUILD_DIR, --build-dir BUILD_DIR
                        构建目录（默认：build）
  --revision-file REVISION_FILE
                        版本信息文件路径（默认：miscellaneous/revision.tex）
  --no-diff             只构建当前版本，跳过差异生成
  --diff-only           只生成差异，不构建 PDF
  -v, --verbose         启用详细日志
  -q, --quiet           只显示错误信息
```

## 输出文件说明

### 生成的文件

1. **当前版本 PDF**: `output/{当前版本名称}.pdf`
2. **差异 PDF**: `output/diff-{比较版本}-to-{当前版本}.pdf`
3. **差异 LaTeX 文件**: `build/compare/diff-{比较版本哈希}-{当前版本哈希}.tex`
4. **元数据文件**: `output/metadata.json`
5. **版本信息文件**: `{--revision-file 指定的路径}/revision.tex`

### 版本信息文件内容

生成的 `revision.tex` 文件包含以下 LaTeX 命令：

```latex
\newcommand{\GitCommit}{abc1234}
\newcommand{\GitTag}{v1.2.0}
\newcommand{\GitBranch}{main}
\newcommand{\GitRevision}{v1.2.0}
\newcommand{\CompiledDate}{2025-01-06T13:57:58.123456}
```

## 错误处理

### 常见错误和解决方案

1. **LaTeX 文件不存在**
   ```
   错误: LaTeX file not found: /path/to/main.tex
   解决: 检查文件路径或使用 -f 指定正确的文件名
   ```

2. **比较目标不存在**
   ```
   错误: Comparison target not found: non-existent-tag
   解决: 检查标签/提交是否存在，或让工具自动选择比较目标
   ```

3. **不是 Git 仓库**
   ```
   错误: /path is not a valid Git repository
   解决: 确保指定的路径包含 .git 目录
   ```

4. **编译器不可用**
   ```
   错误: Command 'xelatex' not found
   解决: 安装相应的 LaTeX 发行版 (TeX Live, MiKTeX)
   ```
