from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TaskProgressColumn, TimeRemainingColumn
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
import time
import random

console = Console()

def create_single_line_progress(description="", bar_width=30):
    """
    创建一个单行进度条
    
    Args:
        description: 进度条描述文本
        bar_width: 进度条宽度
    
    Returns:
        tuple: (Progress对象, task_id)
    """
    p = Progress(
        TextColumn("{task.description}", style="bold cyan", justify="left"),
        BarColumn(bar_width=bar_width),
        TaskProgressColumn(),
        TimeRemainingColumn(),
    )
    task_id = p.add_task(description, total=100)
    return p, task_id


def progress_with_table_v2():
    """使用独立的单行 Progress 对象嵌入表格"""
    
    console.print()
    console.print(Panel.fit(
        "[bold yellow]📊 文件下载管理器[/bold yellow]\n"
        "[dim]每个任务使用独立的单行进度条[/dim]",
        border_style="cyan"
    ))
    console.print()
    
    # 创建表格
    table = Table(
        show_header=True,
        header_style="bold magenta",
        title="[bold]下载任务列表[/bold]",
        caption="[dim]实时更新中...[/dim]",
        border_style="blue",
        padding=(0, 1),
    )
    
    # 添加列
    table.add_column("序号", style="dim", width=6, justify="center")
    table.add_column("文件名", style="bold cyan", min_width=15)
    table.add_column("大小", style="yellow", justify="right")
    table.add_column("进度", min_width=40)
    table.add_column("状态", justify="center")
    
    # 模拟文件信息
    files = [
        {"name": "项目报告.pdf", "size": "12.5 MB", "speed": 2.0},
        {"name": "设计图.psd", "size": "45.8 MB", "speed": 1.2},
        {"name": "视频素材.mp4", "size": "230 MB", "speed": 0.8},
        {"name": "源代码.zip", "size": "8.3 MB", "speed": 3.0},
    ]
    
    # 为每个文件创建独立的单行进度条
    progress_items = []
    
    for i, file_info in enumerate(files, 1):
        # 创建单行进度条（每个 Progress 只包含一个任务）
        p, task_id = create_single_line_progress(bar_width=25)
        progress_items.append({
            'progress': p,
            'task_id': task_id,
            'file': file_info,
            'completed': False,
            'row_index': i - 1,  # 记录行索引
        })
        
        # 添加到表格
        table.add_row(
            str(i),
            file_info['name'],
            file_info['size'],
            p,  # 单行 Progress 对象，可以安全放入单元格
            "[bold yellow]⏳ 等待中...[/bold yellow]"
        )
    
    console.print("[dim]开始下载...[/dim]\n")
    
    # 使用 Live 实时更新表格
    with Live(table, console=console, refresh_per_second=15, vertical_overflow="visible") as live:
        
        # 模拟下载过程
        max_steps = 150  # 最大步数，防止无限循环
        step = 0
        
        while step < max_steps:
            all_completed = True
            
            # 更新每个任务的进度
            for item in progress_items:
                if not item['completed']:
                    # 随机增加进度
                    advance = random.uniform(0.5, item['file']['speed'] * 2)
                    item['progress'].update(item['task_id'], advance=advance)
                    
                    # 检查是否完成
                    if item['progress'].tasks[item['task_id']].completed:
                        item['completed'] = True
                        all_completed = False
                else:
                    all_completed = all_completed and True
            
            # 如果所有任务都完成，退出循环
            if all(item['completed'] for item in progress_items):
                break
            
            step += 1
            time.sleep(0.05)
        
        # 最后更新：确保所有任务都标记为完成
        console.print("\n[bold green]🎉 所有文件下载完成！[/bold green]")
        console.print(f"[dim]总耗时：{step * 0.05:.2f} 秒（模拟）[/dim]")




def progress_with_table_v2_alternative():
    """
    替代方案：使用 Rich 的 update 方法更新单元格
    """
    console.print()
    console.print("[bold cyan]📥 使用 update 方法更新单元格[/bold cyan]\n")
    
    # 创建表格
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("文件", style="cyan")
    table.add_column("进度", min_width=40)
    table.add_column("状态", justify="center")
    
    # 文件列表
    filenames = ["文档.pdf", "图片.jpg", "视频.mp4", "音乐.mp3"]
    
    # 创建独立的单行进度条
    progress_bars = []
    for filename in filenames:
        # 每个文件一个独立的 Progress（单行）
        p = Progress(
            BarColumn(bar_width=25),
            TaskProgressColumn(),
        )
        task_id = p.add_task("", total=100)
        progress_bars.append({
            'progress': p,
            'task_id': task_id,
            'filename': filename,
            'done': False,
        })
        
        table.add_row(
            filename,
            p,  # 单行对象
            "[yellow]⏳ 下载中[/yellow]"
        )
    
    # 实时更新
    with Live(table, console=console, refresh_per_second=10) as live:
        # 模拟下载，不同文件不同速度
        speeds = [3, 2, 1, 2.5]
        
        while True:
            for i, item in enumerate(progress_bars):
                if not item['done']:
                    # 更新进度
                    item['progress'].update(item['task_id'], advance=speeds[i])
                    
                    # 检查完成（finished 为达到 total 后自动置位的布尔标志）
                    task = item['progress'].tasks[item['task_id']]
                    if task.finished:
                        item['done'] = True
                        # 使用 update_cell 更新状态
                        table.columns[2]._cells[i] = "[green]✓ 完成[/green]"
            
            # 所有任务完成则立即退出，避免多余的一次循环
            if all(item['done'] for item in progress_bars):
                break
            time.sleep(0.1)
    
    console.print("\n[bold green]✅ 所有文件下载完成！[/bold green]\n")


# 运行演示
if __name__ == "__main__":

    # 运行替代方案
    progress_with_table_v2_alternative()