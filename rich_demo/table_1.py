from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.live import Live
from rich.console import Console
import time

console = Console()


class StatusCell:
    """单元格文本：通过公开 API 原地更新状态，无需碰私有 _cells"""

    def __init__(self, text: str = ""):
        self.text = text

    def set(self, text: str) -> None:
        self.text = text

    def __rich_console__(self, console, options):  # Rich 公开渲染协议
        yield self.text

def progress_with_table_correct():
    """正确做法：每个任务一个独立的 Progress"""
    console.print("[bold cyan]结合表格展示进度（正确版）[/bold cyan]")
    
    # 创建表格
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("文件", style="cyan")
    table.add_column("大小", style="yellow")
    table.add_column("状态", max_width=10)  # 限制宽度，避免被多余空间撑宽
    table.add_column("进度")
    
    files = [
        ("文档.pdf", "10 MB"),
        ("图片.jpg", "5 MB"),
        ("视频.mp4", "100 MB"),
        ("音乐.mp3", "8 MB"),
    ]
    
    # 为每个文件创建独立的单行 Progress
    progresses = []
    status_cells = []
    for filename, size in files:
        # 创建一个只有一行的进度条
        p = Progress(
            TextColumn("{task.fields[filename]}", justify="right"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
        )
        task_id = p.add_task("", filename=filename, total=100)
        progresses.append((p, task_id))
        # 状态列放一个可变单元格（公开 API 原地改）
        status = StatusCell("下载中")
        status_cells.append(status)
        table.add_row(filename, size, status, p)
    
    # 使用 Live 实时更新表格
    with Live(table, console=console, refresh_per_second=10):
        done = set()  # 记录已标记完成的行
        # 模拟不同速度的下载
        for step in range(1000):
            for i, (p, task_id) in enumerate(progresses):
                # 不同的下载速度
                speed = [2, 1, 0.5, 1.5][i]
                p.update(task_id, advance=speed)

                # 若这个 p 的任务完成了，把对应行的"状态"列置为完成
                if i not in done and p.finished:
                    done.add(i)
                    status_cells[i].set("[green]✓ 完成[/green]")
            # 如果全部完成，就退出循环
            if len(done) == len(progresses):
                break
            time.sleep(0.05)
        
    

progress_with_table_correct()