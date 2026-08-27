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


def make_progress(name: str, total: int = 100):
    """创建一个只有一行任务的 Progress，返回 (Progress, task_id)"""
    p = Progress(
        TextColumn("{task.fields[name]}", justify="right"),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
    )
    task_id = p.add_task("", name=name, total=total)
    return p, task_id


def progress_with_subtasks():
    """每个 task 下嵌套一层 sub-task：父行显示整体状态，子行显示各 sub-task 进度"""
    console.print("[bold cyan]嵌套 sub-task 进度（每个 task 下多个 sub-task）[/bold cyan]")

    # (任务名, 大小, 子模块列表)
    tasks = [
        ("任务1", "10 MB", ["sub1", "sub2", "sub3"]),
        ("任务2", "5 MB", ["sub1", "sub2"]),
        ("任务3", "100 MB", ["sub1", "sub2", "sub3", "sub4"]),
        ("任务4", "8 MB", ["sub1"]),
    ]

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("任务", style="cyan")
    table.add_column("子模块", width=8)
    table.add_column("大小", style="yellow")
    table.add_column("状态", max_width=12)
    table.add_column("进度")

    task_bars = []  # (Progress, task_id) 
    task_done = [0] * len(tasks) 
    task_total = []  # 每个任务总共的 sub-task 数
    task_status = [] 
    sub_tasks = []  # (task_index, sub_index, Progress, task_id, StatusCell)

    for task_idx, (taskname, size, subs) in enumerate(tasks):
        # 主任务
        status = StatusCell("进行中")
        task_p, task_id = make_progress("", total=len(subs))
        table.add_row(taskname, "", size, status, task_p)
        
        task_status.append(status)
        task_total.append(len(subs))
        task_bars.append((task_p, task_id))

        # 子任务
        for sub_idx, subname in enumerate(subs):
            sub_p, sub_id = make_progress(f"T{task_idx}-{sub_idx}")
            status = StatusCell("待开始")
            table.add_row("", subname, "", status, sub_p)

            sub_tasks.append((task_idx, sub_idx, sub_p, sub_id, status))

        # 在任务之间加横分格线（最后一行任务不加）
        if task_idx != len(tasks) - 1:
            table.add_section()

    remaining = len(sub_tasks)
    with Live(table, console=console, refresh_per_second=10):
        while remaining > 0:
            for task_idx, sub_idx, sub_p, sub_id, status in sub_tasks:
                if sub_p.finished: # 
                    continue
                # 不同的下载速度
                speed = [2, 1, 0.5, 1.5][(task_idx + sub_idx) % 4]
                sub_p.update(sub_id, advance=speed)
                status.set("[cyan]下载中[/cyan]")

                if sub_p.finished:
                    status.set("[green]✓ 完成[/green]")
                    task_done[task_idx] += 1
                    remaining -= 1
                    # 父行进度条：每个子模块完成时前进 1 格（total = 子模块总数）
                    task_p, task_id = task_bars[task_idx]
                    task_p.update(task_id, advance=1)
                    # 若该任务的子模块全部完成，更新父行状态
                    if task_done[task_idx] == task_total[task_idx]:
                        task_status[task_idx].set("[green]✓ 全部完成[/green]")
            time.sleep(0.05)


progress_with_subtasks()