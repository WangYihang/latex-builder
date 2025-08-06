import os
import tempfile
import shutil
from pathlib import Path
from git import Repo


a = """\documentclass{article}
\title{Tom Hejda's solution}
\author{me}
\date{May 2024}
\begin{document}
\maketitle
\section{Introduction}
zzz
\end{document}"""

b = r"""\documentclass{article}
\title{latexdiff}
\author{me\and you}
\date{May 2023}

\begin{document}

\maketitle

\section{Introduction}
zzz zzz

\section{Section}
zzz
\end{document}"""


def create_temp_git_repo():
    """创建临时git仓库并提交两个版本"""
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="latex-diff-test-")
    print(f"创建临时目录: {temp_dir}")
    
    try:
        # 初始化git仓库
        repo = Repo.init(temp_dir)
        print("初始化git仓库")
        
        # 创建第一个文件并提交
        file_path = os.path.join(temp_dir, "main.tex")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(a)
        
        repo.index.add(["main.tex"])
        repo.index.commit("Initial commit with version a")
        print("提交版本 a")
        
        # 修改文件并提交第二个版本
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(b)
        
        repo.index.add(["main.tex"])
        repo.index.commit("Update to version b")
        print("提交版本 b")
        
        # 显示提交历史
        print("\n提交历史:")
        for commit in repo.iter_commits():
            print(f"{commit.hexsha[:7]} {commit.message.strip()}")
        
        # 显示两个版本的差异
        print("\n版本差异:")
        diff = repo.head.commit.diff(repo.head.commit.parents[0])
        for change in diff:
            print(f"文件: {change.a_path}")
            print(f"变更类型: {change.change_type}")
            if hasattr(change, 'diff'):
                print("差异内容:")
                print(change.diff)
        
        return temp_dir

    except Exception as e:
        print(f"Git操作失败: {e}")
        return None


def analyze_with_tool(repo_path, skip_latex_build=False):
    """使用工具分析差异"""
    print(f"\n使用工具分析仓库: {repo_path}")
    
    if skip_latex_build:
        print("跳过LaTeX编译，只进行Git分析")
        # 只进行Git分析，不编译LaTeX
        try:
            from latex_builder.git.repository import GitRepository
            
            repo = GitRepository(Path(repo_path))
            current = repo.get_current_revision()
            compare_revision = repo.get_previous_commit()
            
            print(f"当前版本: {current.display_name}")
            print(f"比较版本: {compare_revision.display_name if compare_revision else '无'}")
            
            # 显示文件差异
            if compare_revision:
                print(f"\n文件差异:")
                print(f"  从 {compare_revision.display_name} 到 {current.display_name}")
                # 使用gitpython来获取差异
                git_repo = Repo(repo_path)
                diff = git_repo.head.commit.diff(git_repo.head.commit.parents[0])
                for change in diff:
                    print(f"  - {change.a_path}: {change.change_type}")
            
            print("Git分析完成")
            
        except Exception as e:
            print(f"Git分析过程中出现错误: {e}")
        return
    
    try:
        # 导入latex-builder工具
        from latex_builder.config.settings import Config
        from latex_builder.cli.main import LatexDiffTool
        
        # 创建配置
        config = Config(
            repo_path=Path(repo_path),
            tex_file="main.tex",
            compiler="xelatex",
            compare_with=None,  # 自动选择比较目标
            revision_file="revision.tex",
            output_dir=Path(repo_path) / "output",
            build_dir=Path(repo_path) / "build",
            no_diff=False,
            diff_only=False,
            verbose=True,
            quiet=False,
        )
        
        # 运行latex-builder工具
        tool = LatexDiffTool(config)
        result = tool.run()
        
        if result == 0:
            print("latex-builder工具分析完成")
        else:
            print(f"latex-builder工具分析失败，退出码: {result}")
            
    except ImportError as e:
        print(f"无法导入latex-builder工具: {e}")
        print("请确保已安装latex-builder包")
    except Exception as e:
        print(f"分析过程中出现错误: {e}")


def cleanup_temp_repo(repo_path):
    """清理临时仓库"""
    if repo_path and os.path.exists(repo_path):
        shutil.rmtree(repo_path)
        print(f"清理临时目录: {repo_path}")


if __name__ == "__main__":
    print("开始模拟git仓库操作...")
    
    # 创建临时git仓库
    temp_repo = create_temp_git_repo()
    
    if temp_repo:
        # 使用工具分析，现在可以安全地进行LaTeX编译
        analyze_with_tool(temp_repo, skip_latex_build=False)
        
        # 询问是否清理
        response = input("\n是否清理临时仓库? (y/n): ")
        if response.lower() == 'y':
            cleanup_temp_repo(temp_repo)
        else:
            print(f"临时仓库保留在: {temp_repo}")
    else:
        print("创建临时仓库失败")

