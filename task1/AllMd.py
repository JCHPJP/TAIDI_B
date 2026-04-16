
from pathlib import Path
def getAllMarkdownFiles(path= Path.cwd().parent / "processed" /"财务报告" )->list:
    print(f"正在扫描目录 {path} 下的所有 Markdown 文件...")
    md_files = Path(path).rglob("*.md")
    return  [ str(file) for file in md_files]

if __name__ == "__main__":
    print(len(getAllMarkdownFiles()))