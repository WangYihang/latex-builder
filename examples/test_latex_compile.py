#!/usr/bin/env python3
"""测试改进后的LaTeX编译功能，验证不会卡在交互式提示上。"""

import tempfile
from pathlib import Path
from latex_builder.utils.command import run_latex_command


def test_latex_compile():
    """测试LaTeX编译功能"""
    print("测试改进后的LaTeX编译功能...")
    
    # 创建一个简单的LaTeX文档
    latex_content = r"""\documentclass{article}
\usepackage{amsmath}
\begin{document}
\title{Test Document}
\author{Test Author}
\date{\today}
\maketitle

\section{Introduction}
This is a test document to verify that LaTeX compilation doesn't hang on interactive prompts.

\section{Math Example}
Here's a simple equation:
\begin{equation}
E = mc^2
\end{equation}

\end{document}"""
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 写入LaTeX文件
        tex_file = temp_path / "main.tex"
        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(latex_content)
        
        print(f"创建测试文件: {tex_file}")
        
        try:
            # 测试xelatex编译
            print("\n测试xelatex编译...")
            result = run_latex_command(
                ["xelatex", "-shell-escape", "main.tex"], 
                cwd=temp_path,
                timeout=60  # 1分钟超时
            )
            print("✅ xelatex编译成功")
            print(f"输出长度: {len(result)} 字符")
            
            # 检查是否生成了PDF
            pdf_file = temp_path / "test.pdf"
            if pdf_file.exists():
                print(f"✅ PDF文件已生成: {pdf_file}")
                print(f"PDF文件大小: {pdf_file.stat().st_size} 字节")
            else:
                print("❌ PDF文件未生成")
                
        except Exception as e:
            print(f"❌ xelatex编译失败: {e}")
        
        try:
            # 测试pdflatex编译
            print("\n测试pdflatex编译...")
            result = run_latex_command(
                ["pdflatex", "-shell-escape", "main.tex"], 
                cwd=temp_path,
                timeout=60  # 1分钟超时
            )
            print("✅ pdflatex编译成功")
            print(f"输出长度: {len(result)} 字符")
            
        except Exception as e:
            print(f"❌ pdflatex编译失败: {e}")
        
        try:
            # 测试lualatex编译
            print("\n测试lualatex编译...")
            result = run_latex_command(
                ["lualatex", "-shell-escape", "main.tex"], 
                cwd=temp_path,
                timeout=60  # 1分钟超时
            )
            print("✅ lualatex编译成功")
            print(f"输出长度: {len(result)} 字符")
            
        except Exception as e:
            print(f"❌ lualatex编译失败: {e}")
    
    print("\n测试完成！")


if __name__ == "__main__":
    test_latex_compile()
