from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TaskProgressColumn
from rich.layout import Layout
from rich.live import Live
import time

console = Console()

def progress_with_layout():
    """使用 Layout 组织多个进度条"""
    console.print("[bold cyan]使用 Layout 展示多个进度条[/bold cyan]")
    
    # 创建布局
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
    )
    
    # 为每个任务创建独立的单行进度条
    progress_bars = []
    for i in range(4):
        p = Progress(
            TextColumn(f"[bold cyan]任务 {i+1}[/bold cyan]", justify="left"),
            BarColumn(bar_width=30),
            TaskProgressColumn(),
        )
        task_id = p.add_task("", total=100)
        progress_bars.append((p, task_id))
    
    with Live(layout, console=console, refresh_per_second=10):
        # 更新布局
        layout["header"].update(Panel("[bold yellow]文件下载进度[/bold yellow]"))
        
        # 将进度条组合在一起
        from rich.console import Group
        progress_group = Group(*[p for p, _ in progress_bars])
        layout["body"].update(Panel(progress_group))
        
        # 模拟下载
        for step in range(100):
            for p, task_id in progress_bars:
                p.update(task_id, advance=1)
            time.sleep(0.03)
    
    console.print("[green]✓ 所有任务完成！[/green]")

progress_with_layout()