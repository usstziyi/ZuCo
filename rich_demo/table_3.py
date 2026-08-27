from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich.style import Style
import time

console = Console()

def custom_progress_bar(percentage, width=20):
    """创建自定义进度条文本"""
    filled = int(width * percentage / 100)
    bar = "█" * filled + "░" * (width - filled)
    return Text(f"{bar} {percentage:3.0f}%", style="bold cyan")

def progress_with_custom_bars():
    """使用自定义进度条"""
    console.print("[bold cyan]自定义进度条表格[/bold cyan]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("文件")
    table.add_column("进度")
    table.add_column("速度")
    table.add_column("状态")
    
    files = [
        ("文档.pdf", "10 MB/s"),
        ("图片.jpg", "8 MB/s"),
        ("视频.mp4", "15 MB/s"),
        ("音乐.mp3", "5 MB/s"),
    ]
    
    # 初始化进度
    progress_values = [0, 0, 0, 0]
    speeds = [2, 1.5, 3, 1]  # 不同速度
    
    with Live(table, console=console, refresh_per_second=10) as live:
        # 初始表格
        for i, (filename, speed) in enumerate(files):
            table.add_row(
                f"[cyan]{filename}[/cyan]",
                custom_progress_bar(0),
                f"[yellow]{speed}[/yellow]",
                "[bold yellow]下载中...[/bold yellow]"
            )
        
        # 模拟下载
        while any(v < 100 for v in progress_values):
            # 更新进度
            for i in range(len(progress_values)):
                progress_values[i] = min(100, progress_values[i] + speeds[i])
            
            # 重建表格
            table.rows.clear()
            for i, (filename, speed) in enumerate(files):
                status = "[green]✓ 完成[/green]" if progress_values[i] >= 100 else "[bold yellow]下载中...[/bold yellow]"
                table.add_row(
                    f"[cyan]{filename}[/cyan]",
                    custom_progress_bar(progress_values[i]),
                    f"[yellow]{speed}[/yellow]",
                    status
                )
            
            time.sleep(0.05)
    
    console.print()

progress_with_custom_bars()