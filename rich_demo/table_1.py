from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.live import Live
from rich.console import Console
import time

console = Console()

def progress_with_table_correct():
    """正确做法：每个任务一个独立的 Progress"""
    console.print("[bold cyan]结合表格展示进度（正确版）[/bold cyan]")
    
    # 创建表格
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("文件", style="cyan")
    table.add_column("大小", style="yellow")
    table.add_column("状态")
    table.add_column("进度")
    
    files = [
        ("文档.pdf", "10 MB"),
        ("图片.jpg", "5 MB"),
        ("视频.mp4", "100 MB"),
        ("音乐.mp3", "8 MB"),
    ]
    
    # 为每个文件创建独立的单行 Progress
    progresses = []
    for filename, size in files:
        # 创建一个只有一行的进度条
        p = Progress(
            TextColumn("{task.description}", style="bold cyan"),
            BarColumn(bar_width=20),
            TaskProgressColumn(),
            TextColumn("[green]✓ 完成[/green]"),
        )
        task_id = p.add_task("", total=100)
        progresses.append((p, task_id))
        table.add_row(filename, size, "下载中", p)
    
    # 使用 Live 实时更新表格
    with Live(table, console=console, refresh_per_second=10):
        # 模拟不同速度的下载
        for step in range(100):
            for i, (p, task_id) in enumerate(progresses):
                # 不同的下载速度
                speed = [2, 1, 0.5, 1.5][i]
                p.update(task_id, advance=speed)
            
            # 检查是否所有任务都完成
            if all(p.finished for p, _ in progresses):
                break
            
            time.sleep(0.05)
        
        # 更新状态
        table.rows.clear()
        for filename, size in files:
            table.add_row(filename, size, "[green]✓ 完成[/green]", "")
    
    console.print()

progress_with_table_correct()