"""Advanced progress indicators and tracking components.

This module provides sophisticated progress tracking including multi-step
operations, cancellable progress, and detailed status reporting.
"""

import time
import threading
from typing import List, Optional, Dict, Any, Callable, Iterator
from dataclasses import dataclass, field
from contextlib import contextmanager
from enum import Enum

from rich.console import Console
from rich.progress import (
    Progress, 
    SpinnerColumn, 
    TextColumn, 
    BarColumn, 
    TaskProgressColumn, 
    TimeRemainingColumn,
    MofNCompleteColumn,
)
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.align import Align
import select

console = Console()


class StepStatus(Enum):
    """Status of a progress step."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ProgressStep:
    """Represents a step in a multi-step progress operation."""
    id: str
    title: str
    description: Optional[str] = None
    status: StepStatus = StepStatus.PENDING
    progress: float = 0.0
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AdvancedProgress:
    """Enhanced progress indicator with detailed status and customization."""
    
    def __init__(
        self,
        show_spinner: bool = True,
        show_bar: bool = True,
        show_percentage: bool = True,
        show_time: bool = True,
        show_speed: bool = False,
        console_obj: Optional[Console] = None,
    ) -> None:
        """Initialize advanced progress indicator.
        
        Args:
            show_spinner: Whether to show spinner
            show_bar: Whether to show progress bar
            show_percentage: Whether to show percentage
            show_time: Whether to show time remaining
            show_speed: Whether to show processing speed
            console_obj: Console instance to use
        """
        self.console = console_obj or console
        
        # Build columns based on options
        columns = []
        
        if show_spinner:
            columns.append(SpinnerColumn())
        
        columns.append(TextColumn("[progress.description]{task.description}"))
        
        if show_bar:
            columns.append(BarColumn())
        
        if show_percentage:
            columns.append(TaskProgressColumn())
        
        if show_time:
            columns.append(TimeRemainingColumn())
        
        self.progress = Progress(*columns, console=self.console)
        self.tasks: Dict[str, int] = {}
    
    @contextmanager
    def track(self, description: str, total: Optional[float] = None):
        """Context manager for tracking a single operation.
        
        Args:
            description: Operation description
            total: Total units of work (None for indeterminate)
        """
        with self.progress:
            task_id = self.progress.add_task(description, total=total)
            try:
                yield ProgressTracker(self.progress, task_id)
            finally:
                pass  # Progress context manager handles cleanup


class ProgressTracker:
    """Helper class for updating progress within a context."""
    
    def __init__(self, progress: Progress, task_id: int) -> None:
        self.progress = progress
        self.task_id = task_id
    
    def update(self, advance: Optional[float] = None, description: Optional[str] = None) -> None:
        """Update progress.
        
        Args:
            advance: Amount to advance progress
            description: New description
        """
        kwargs = {}
        if advance is not None:
            kwargs['advance'] = advance
        if description is not None:
            kwargs['description'] = description
        
        if kwargs:
            self.progress.update(self.task_id, **kwargs)
    
    def set_total(self, total: float) -> None:
        """Set total amount of work."""
        self.progress.update(self.task_id, total=total)
    
    def complete(self, description: Optional[str] = None) -> None:
        """Mark progress as complete."""
        if description:
            self.progress.update(self.task_id, description=description)
        self.progress.update(self.task_id, completed=self.progress.tasks[self.task_id].total or 100)


class MultiStepProgress:
    """Progress tracker for multi-step operations with detailed status."""
    
    def __init__(
        self,
        title: str,
        steps: List[ProgressStep],
        show_details: bool = True,
        console_obj: Optional[Console] = None,
    ) -> None:
        """Initialize multi-step progress tracker.
        
        Args:
            title: Overall operation title
            steps: List of steps to track
            show_details: Whether to show detailed step information
            console_obj: Console instance to use
        """
        self.title = title
        self.steps = {step.id: step for step in steps}
        self.step_order = [step.id for step in steps]
        self.show_details = show_details
        self.console = console_obj or console
        self.current_step: Optional[str] = None
        self._cancelled = threading.Event()
    
    def get_step(self, step_id: str) -> ProgressStep:
        """Get step by ID."""
        if step_id not in self.steps:
            raise ValueError(f"Step '{step_id}' not found")
        return self.steps[step_id]
    
    def start_step(self, step_id: str) -> None:
        """Start a step."""
        step = self.get_step(step_id)
        step.status = StepStatus.IN_PROGRESS
        step.start_time = time.time()
        self.current_step = step_id
    
    def complete_step(self, step_id: str, success: bool = True, error_message: Optional[str] = None) -> None:
        """Complete a step."""
        step = self.get_step(step_id)
        step.status = StepStatus.COMPLETED if success else StepStatus.FAILED
        step.end_time = time.time()
        step.progress = 100.0
        
        if error_message:
            step.error_message = error_message
        
        if self.current_step == step_id:
            self.current_step = None
    
    def skip_step(self, step_id: str, reason: Optional[str] = None) -> None:
        """Skip a step."""
        step = self.get_step(step_id)
        step.status = StepStatus.SKIPPED
        step.end_time = time.time()
        
        if reason:
            step.metadata['skip_reason'] = reason
    
    def update_step_progress(self, step_id: str, progress: float, description: Optional[str] = None) -> None:
        """Update step progress."""
        step = self.get_step(step_id)
        step.progress = max(0.0, min(100.0, progress))
        
        if description:
            step.description = description
    
    def cancel(self) -> None:
        """Cancel the operation."""
        self._cancelled.set()
    
    def is_cancelled(self) -> bool:
        """Check if operation is cancelled."""
        return self._cancelled.is_set()
    
    def get_overall_progress(self) -> float:
        """Get overall progress percentage."""
        if not self.steps:
            return 0.0
        
        total_progress = sum(
            step.progress for step in self.steps.values()
            if step.status != StepStatus.SKIPPED
        )
        
        active_steps = len([
            step for step in self.steps.values()
            if step.status != StepStatus.SKIPPED
        ])
        
        return total_progress / max(1, active_steps)
    
    def _get_status_display(self, status: StepStatus) -> tuple[str, str]:
        """Get status icon and color."""
        status_displays = {
            StepStatus.PENDING: ("⏳", "dim"),
            StepStatus.IN_PROGRESS: ("⚡", "yellow"),
            StepStatus.COMPLETED: ("✅", "green"),
            StepStatus.FAILED: ("❌", "red"),
            StepStatus.SKIPPED: ("⏭️", "dim"),
        }
        return status_displays.get(status, ("?", "white"))
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"
    
    def create_status_table(self) -> Table:
        """Create an enhanced table showing step status with visual progress bars."""
        table = Table(
            title=self.title,
            show_header=True,
            header_style="bold cyan",
            border_style="cyan",
            title_style="bold cyan",
            title_justify="center",
            expand=True,
        )
        table.add_column("Step", style="white", ratio=3)
        table.add_column("Status", width=15, justify="center")
        table.add_column("Progress", width=25, justify="center")
        table.add_column("Time", width=10, justify="right")
        
        for step_id in self.step_order:
            step = self.steps[step_id]
            
            # Status with icon
            status_icons = {
                StepStatus.PENDING: ("⏳", "dim"),
                StepStatus.IN_PROGRESS: ("⚡", "yellow"),
                StepStatus.COMPLETED: ("✅", "green"),
                StepStatus.FAILED: ("❌", "red"),
                StepStatus.SKIPPED: ("⏭️", "blue"),
            }
            
            # Step number and title with description
            step_text = f"{self.step_order.index(step_id)+1}. {step.title}"
            if step.description and self.show_details:
                step_text += f"\n   [dim]{step.description}[/dim]"
            
            # Status with icon
            icon, color = self._get_status_display(step.status)
            status_text = Text(f"{icon} {step.status.value.title()}", style=color)
            
            # Progress bar visualization
            if step.status in (StepStatus.IN_PROGRESS, StepStatus.COMPLETED):
                bar_width = 15
                filled = int((step.progress / 100.0) * bar_width)
                empty = bar_width - filled
                
                if step.status == StepStatus.IN_PROGRESS:
                    bar = f"[cyan]{'█' * filled}{'░' * empty}[/cyan]"
                else:
                    bar = f"[green]{'█' * bar_width}[/green]"
                
                progress_text = f"{bar} {step.progress:.0f}%"
            elif step.status == StepStatus.FAILED:
                progress_text = Text("Failed", style="red")
            elif step.status == StepStatus.SKIPPED:
                progress_text = Text("Skipped", style="dim")
            else:
                progress_text = Text("Waiting...", style="dim")
            
            # Time calculation
            if step.start_time and step.end_time:
                duration = step.end_time - step.start_time
                time_text = self._format_duration(duration)
            elif step.start_time:
                duration = time.time() - step.start_time
                time_text = f"[yellow]{self._format_duration(duration)}[/yellow]"
            else:
                time_text = "-"
            
            # Add error message as separate row if failed
            if step.status == StepStatus.FAILED and step.error_message:
                step_text += f"\n   [red]❗ {step.error_message}[/red]"
            
            # Add skip reason if skipped
            if step.status == StepStatus.SKIPPED and 'skip_reason' in step.metadata:
                step_text += f"\n   [dim]↳ {step.metadata['skip_reason']}[/dim]"
            
            table.add_row(
                step_text,
                status_text,
                progress_text,
                time_text,
            )
        
        # Add overall progress footer
        overall = self.get_overall_progress()
        completed_steps = len([s for s in self.steps.values() if s.status == StepStatus.COMPLETED])
        total_steps = len([s for s in self.steps.values() if s.status != StepStatus.SKIPPED])
        
        if total_steps > 0:
            table.caption = f"[bold cyan]Overall Progress: {overall:.0f}% ({completed_steps}/{total_steps} steps)[/bold cyan]"
        
        return table
    
    @contextmanager
    def live_display(self, refresh_rate: float = 0.1):
        """Context manager for live-updating display."""
        def create_panel() -> Panel:
            content = []
            
            # Overall progress
            overall = self.get_overall_progress()
            content.append(f"Overall Progress: {overall:.1f}%")
            
            if self.show_details:
                content.append("")
                content.append(self.create_status_table())
            
            return Panel(
                "\n".join(str(item) for item in content),
                title=f"🔄 {self.title}",
                border_style="cyan",
                padding=(1, 2),
            )
        
        with Live(
            create_panel(),
            console=self.console,
            refresh_per_second=1.0 / refresh_rate,
        ) as live:
            yield live, lambda: live.update(create_panel())


    def create_installation_report(self, items_type: str = "items") -> Panel:
        """Create a detailed installation report panel.
        
        Args:
            items_type: Type of items being installed (e.g., "templates", "hooks")
            
        Returns:
            Panel with installation summary
        """
        lines = []
        
        # Header
        lines.append(f"[bold cyan]📦 {self.title}[/bold cyan]")
        lines.append("")
        
        # Summary statistics
        completed = [s for s in self.steps.values() if s.status == StepStatus.COMPLETED]
        failed = [s for s in self.steps.values() if s.status == StepStatus.FAILED]
        skipped = [s for s in self.steps.values() if s.status == StepStatus.SKIPPED]
        
        if completed:
            lines.append(f"[green]✅ Successfully installed: {len(completed)} {items_type}[/green]")
            for step in completed:
                lines.append(f"   • {step.title}")
        
        if failed:
            lines.append("")
            lines.append(f"[red]❌ Failed to install: {len(failed)} {items_type}[/red]")
            for step in failed:
                lines.append(f"   • {step.title}")
                if step.error_message:
                    lines.append(f"     [dim]Error: {step.error_message}[/dim]")
        
        if skipped:
            lines.append("")
            lines.append(f"[yellow]⏭️  Skipped: {len(skipped)} {items_type}[/yellow]")
            for step in skipped:
                reason = step.metadata.get('skip_reason', 'No reason provided')
                lines.append(f"   • {step.title} - [dim]{reason}[/dim]")
        
        # Total time
        start_times = [s.start_time for s in self.steps.values() if s.start_time]
        end_times = [s.end_time for s in self.steps.values() if s.end_time]
        
        if start_times and end_times:
            total_time = max(end_times) - min(start_times)
            lines.append("")
            lines.append(f"[dim]Total time: {self._format_duration(total_time)}[/dim]")
        
        return Panel(
            "\n".join(lines),
            title="Installation Summary",
            border_style="green" if not failed else "red",
            expand=False,
        )


class CancellableProgress:
    """Progress indicator that can be cancelled by user input."""
    
    def __init__(
        self,
        title: str,
        console_obj: Optional[Console] = None,
        cancel_key: str = "q",
    ) -> None:
        """Initialize cancellable progress.
        
        Args:
            title: Progress title
            console_obj: Console instance to use
            cancel_key: Key to press for cancellation
        """
        self.title = title
        self.console = console_obj or console
        self.cancel_key = cancel_key
        self._cancelled = threading.Event()
        self._cancel_thread: Optional[threading.Thread] = None
    
    def _monitor_input(self) -> None:
        """Monitor for cancellation input in a separate thread."""
        try:
            import sys
            
            # Try Unix-like terminal control first
            try:
                import tty
                import termios
                
                if hasattr(sys.stdin, 'fileno'):
                    old_settings = termios.tcgetattr(sys.stdin)
                    try:
                        tty.cbreak(sys.stdin.fileno())
                        while not self._cancelled.is_set():
                            if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                                key = sys.stdin.read(1)
                                if key.lower() == self.cancel_key.lower():
                                    self._cancelled.set()
                                    break
                    finally:
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            except (ImportError, OSError):
                # Fallback for Windows or when terminal control not available
                # Note: This is a simplified approach
                if sys.platform == 'win32':
                    import msvcrt
                    
                    while not self._cancelled.is_set():
                        if msvcrt.kbhit():
                            key = msvcrt.getch().decode('utf-8', errors='ignore')
                            if key.lower() == self.cancel_key.lower():
                                self._cancelled.set()
                                break
                        time.sleep(0.1)
        except Exception:
            # Silently ignore any errors in cancellation monitoring
            pass
    
    @contextmanager
    def track(self, description: str, total: Optional[float] = None, show_cancel_hint: bool = True):
        """Context manager for cancellable progress tracking.
        
        Args:
            description: Operation description
            total: Total units of work
            show_cancel_hint: Whether to show cancellation hint
        """
        if show_cancel_hint:
            hint = f"[dim]Press '{self.cancel_key}' to cancel[/dim]"
            self.console.print(hint)
        
        # Start input monitoring thread
        self._cancel_thread = threading.Thread(target=self._monitor_input, daemon=True)
        self._cancel_thread.start()
        
        columns = [
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        ]
        
        try:
            with Progress(*columns, console=self.console) as progress:
                task_id = progress.add_task(description, total=total)
                yield CancellableTracker(progress, task_id, self._cancelled)
        finally:
            self._cancelled.set()  # Ensure monitoring thread stops
    
    def is_cancelled(self) -> bool:
        """Check if operation was cancelled."""
        return self._cancelled.is_set()


class CancellableTracker:
    """Tracker for cancellable progress operations."""
    
    def __init__(self, progress: Progress, task_id: int, cancel_event: threading.Event) -> None:
        self.progress = progress
        self.task_id = task_id
        self.cancel_event = cancel_event
    
    def update(self, advance: Optional[float] = None, description: Optional[str] = None) -> None:
        """Update progress."""
        if self.cancel_event.is_set():
            raise KeyboardInterrupt("Operation cancelled by user")
        
        kwargs = {}
        if advance is not None:
            kwargs['advance'] = advance
        if description is not None:
            kwargs['description'] = description
        
        if kwargs:
            self.progress.update(self.task_id, **kwargs)
    
    def is_cancelled(self) -> bool:
        """Check if operation is cancelled."""
        return self.cancel_event.is_set()
    
    def check_cancelled(self) -> None:
        """Raise KeyboardInterrupt if cancelled."""
        if self.cancel_event.is_set():
            raise KeyboardInterrupt("Operation cancelled by user")
    
    def complete(self, description: Optional[str] = None) -> None:
        """Mark progress as complete."""
        if description:
            self.progress.update(self.task_id, description=description)
        task = self.progress.tasks.get(self.task_id)
        if task:
            self.progress.update(self.task_id, completed=task.total or 100)


# Alias for backward compatibility
SimpleTracker = ProgressTracker


# Import select for input monitoring (Unix-like systems only)
try:
    import select
except ImportError:
    select = None