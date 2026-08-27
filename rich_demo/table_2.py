from rich.console import Console, Group
from rich.progress import Progress, BarColumn, TextColumn, TaskProgressColumn
from rich.table import Table
from rich.live import Live
from rich.text import Text
import time

console = Console()

def create_single_line_progress():
    """创建一个单行进度条"""
    return Progress(
        TextColumn("{task.description}"),
        BarColumn(bar_width=20),
        TaskProgressColumn(),
    )

def progress_with_table_v2():
    """使用单行 Progress 对象"""
    console.print("[bold cyan]表格中的独立进度条[/bold cyan]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("任务")
    table.add_column("进度")
    table.add_column("状态")
    
    # 创建4个独立的单行进度条
    progress_bars = []
    task_info = []
    
    for i in range(4):
        # 每个进度条只有一个任务
        p = Progress(
            BarColumn(bar_width=30),
            TaskProgressColumn(),
        )
        task_id = p.add_task("", total=100)
        progress_bars.append((p, task_id))
        
        table.add_row(
            f"[cyan]任务 {i+1}[/cyan]",
            p,  # 这是单行对象，可以放入单元格
            "[yellow]进行中...[/yellow]"
        )
    
    with Live(table, console=console, refresh_per_second=10):
        for step in range(100):
            for i, (p, task_id) in enumerate(progress_bars):
                p.update(task_id, advance=1)
            time.sleep(0.03)
        
        # 完成后更新状态
        table.rows.clear()
        for i in range(4):
            table.add_row(
                f"[cyan]任务 {i+1}[/cyan]",
                "",
                "[green]✓ 完成[/green]"
            )
    
    console.print()

progress_with_table_v2()