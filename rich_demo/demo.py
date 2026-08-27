import time
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    MofNCompleteColumn,
    TaskProgressColumn,
    DownloadColumn,
    TransferSpeedColumn,
)
from rich.console import Console
from rich.table import Table
from rich.live import Live

console = Console()

def basic_progress():
    """基础进度条"""
    console.print("[bold cyan]1. 基础进度条[/bold cyan]")
    with Progress() as progress:
        task = progress.add_task("[green]处理中...", total=100)
        while not progress.finished:
            progress.update(task, advance=1) # 每次+1
            time.sleep(0.02)
    console.print()

def custom_columns_progress():
    """自定义列进度条"""
    console.print("[bold cyan]2. 自定义列进度条[/bold cyan]")
    # 这里把"动画、描述、横条、百分比、数字、耗时、剩余时间"拼成一个更丰富的进度条
    with Progress(
        SpinnerColumn(), # 加载动画
        TextColumn("[bold]{task.fields[filename]}", justify="right"), # 文件名
        TextColumn("[progress.description] ==> {task.description}"), # 任务描述
        BarColumn(), # 进度条
        TaskProgressColumn(), # 任务百分比
        MofNCompleteColumn(), # 已完成进度数
        TimeElapsedColumn(), # 已用时间
        TimeRemainingColumn(), # 剩余时间
    ) as progress:
        task = progress.add_task("[red]下载中...",filename="movie.mp4", total=100)
        while not progress.finished:
            progress.update(task, advance=0.5)
            time.sleep(0.1)
    console.print()

def multiple_tasks():
    """多任务并行进度条"""
    console.print("[bold cyan]3. 多任务并行进度条[/bold cyan]")
    with Progress() as progress:
        task1 = progress.add_task("[red]任务1", total=100)
        task2 = progress.add_task("[green]任务2", total=200)
        task3 = progress.add_task("[blue]任务3", total=150)
        
        while not progress.finished:
            progress.update(task1, advance=2)
            progress.update(task2, advance=1.5)
            progress.update(task3, advance=1)
            time.sleep(0.01)
    console.print()

def download_simulation():
    """模拟下载进度条"""
    console.print("[bold cyan]4. 模拟下载进度条[/bold cyan]")
    with Progress(
        TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
        BarColumn(bar_width=None), # 不限制宽度，让横条自动撑满剩余可用空间
        "[progress.percentage]{task.percentage:>3.1f}%", # 任务百分比
        "•",
        DownloadColumn(), # 下载速度
        "•",
        TransferSpeedColumn(), # 传输速度
        "•",
        TimeRemainingColumn(), # 剩余时间
        "•",
        TimeElapsedColumn(), # 已用时间
    ) as progress:
        for i in range(3):
            filename = f"file_{i+1}.zip"
            task = progress.add_task("下载", filename=filename, total=1000)
            while not progress.finished:
                progress.update(task, advance=5)
                time.sleep(0.01)
    console.print()

def indeterminate_progress():
    """不确定进度（加载动画）"""
    console.print("[bold cyan]5. 不确定进度（加载动画）[/bold cyan]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,  # 完成后清除进度条
    ) as progress:
        task = progress.add_task("正在连接服务器...", total=None)
        time.sleep(3)
    
    console.print("[green]✓ 连接成功！[/green]\n")

def progress_with_table():
    """结合表格展示进度"""
    console.print("[bold cyan]6. 结合表格展示进度[/bold cyan]")
    
    # 创建表格
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("文件")
    table.add_column("大小")
    table.add_column("状态")
    table.add_column("进度")
    
    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=20),
        TaskProgressColumn(),
    )
    
    with Live(table, console=console, refresh_per_second=10):
        files = ["文档.pdf", "图片.jpg", "视频.mp4", "音乐.mp3"]
        tasks = []
        
        # 初始化表格
        for f in files:
            task_id = progress.add_task(f, total=100)
            tasks.append(task_id)
            table.add_row(f, "10 MB", "下载中", progress)
        
        # 模拟下载
        while not progress.finished:
            for task_id in tasks:
                progress.update(task_id, advance=1)
            time.sleep(0.05)
        
        # 更新状态为完成
        table.rows.clear()
        for f in files:
            table.add_row(f, "10 MB", "[green]✓ 完成[/green]", "")
    
    console.print()

def main():
    console.print("[bold yellow]Rich 进度条演示[/bold yellow]\n", justify="center")
    
    # basic_progress()
    # custom_columns_progress()
    # multiple_tasks()
    download_simulation()
    # indeterminate_progress()
    # progress_with_table()
    
    console.print("[bold green]所有演示完成！[/bold green]")

if __name__ == "__main__":
    main()