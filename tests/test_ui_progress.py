"""Tests for advanced progress indicators."""

import time
import threading
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from claude_code_setup.ui.progress import (
    StepStatus,
    ProgressStep,
    AdvancedProgress,
    MultiStepProgress,
    CancellableProgress,
)


class TestProgressStep:
    """Test ProgressStep dataclass."""
    
    def test_progress_step_creation(self) -> None:
        """Test creating a progress step."""
        step = ProgressStep(
            id="test",
            title="Test Step",
            description="This is a test step",
        )
        
        assert step.id == "test"
        assert step.title == "Test Step"
        assert step.description == "This is a test step"
        assert step.status == StepStatus.PENDING
        assert step.progress == 0.0
        assert step.error_message is None
        assert step.start_time is None
        assert step.end_time is None
        assert step.metadata == {}
    
    def test_progress_step_with_metadata(self) -> None:
        """Test progress step with metadata."""
        metadata = {"key": "value", "count": 42}
        step = ProgressStep(
            id="test",
            title="Test Step",
            metadata=metadata,
        )
        
        assert step.metadata == metadata


class TestMultiStepProgress:
    """Test MultiStepProgress class."""
    
    def test_multi_step_progress_creation(self) -> None:
        """Test creating multi-step progress."""
        steps = [
            ProgressStep("step1", "Step 1"),
            ProgressStep("step2", "Step 2"),
            ProgressStep("step3", "Step 3"),
        ]
        
        progress = MultiStepProgress(
            title="Test Operation",
            steps=steps,
        )
        
        assert progress.title == "Test Operation"
        assert len(progress.steps) == 3
        assert progress.step_order == ["step1", "step2", "step3"]
        assert progress.current_step is None
    
    def test_get_step(self) -> None:
        """Test getting a step by ID."""
        steps = [
            ProgressStep("step1", "Step 1"),
            ProgressStep("step2", "Step 2"),
        ]
        
        progress = MultiStepProgress("Test", steps)
        
        step1 = progress.get_step("step1")
        assert step1.title == "Step 1"
        
        with pytest.raises(ValueError, match="Step 'invalid' not found"):
            progress.get_step("invalid")
    
    def test_start_step(self) -> None:
        """Test starting a step."""
        step = ProgressStep("test", "Test Step")
        progress = MultiStepProgress("Test", [step])
        
        progress.start_step("test")
        
        updated_step = progress.get_step("test")
        assert updated_step.status == StepStatus.IN_PROGRESS
        assert updated_step.start_time is not None
        assert progress.current_step == "test"
    
    def test_complete_step_success(self) -> None:
        """Test completing a step successfully."""
        step = ProgressStep("test", "Test Step")
        progress = MultiStepProgress("Test", [step])
        
        progress.start_step("test")
        time.sleep(0.01)  # Ensure some time passes
        progress.complete_step("test", success=True)
        
        updated_step = progress.get_step("test")
        assert updated_step.status == StepStatus.COMPLETED
        assert updated_step.end_time is not None
        assert updated_step.progress == 100.0
        assert updated_step.error_message is None
        assert progress.current_step is None
    
    def test_complete_step_failure(self) -> None:
        """Test completing a step with failure."""
        step = ProgressStep("test", "Test Step")
        progress = MultiStepProgress("Test", [step])
        
        progress.start_step("test")
        progress.complete_step("test", success=False, error_message="Test error")
        
        updated_step = progress.get_step("test")
        assert updated_step.status == StepStatus.FAILED
        assert updated_step.end_time is not None
        assert updated_step.error_message == "Test error"
    
    def test_skip_step(self) -> None:
        """Test skipping a step."""
        step = ProgressStep("test", "Test Step")
        progress = MultiStepProgress("Test", [step])
        
        progress.skip_step("test", reason="Not needed")
        
        updated_step = progress.get_step("test")
        assert updated_step.status == StepStatus.SKIPPED
        assert updated_step.end_time is not None
        assert updated_step.metadata["skip_reason"] == "Not needed"
    
    def test_update_step_progress(self) -> None:
        """Test updating step progress."""
        step = ProgressStep("test", "Test Step")
        progress = MultiStepProgress("Test", [step])
        
        progress.start_step("test")
        progress.update_step_progress("test", 50.0, description="Half way")
        
        updated_step = progress.get_step("test")
        assert updated_step.progress == 50.0
        assert updated_step.description == "Half way"
    
    def test_update_step_progress_bounds(self) -> None:
        """Test progress bounds are enforced."""
        step = ProgressStep("test", "Test Step")
        progress = MultiStepProgress("Test", [step])
        
        progress.update_step_progress("test", 150.0)
        assert progress.get_step("test").progress == 100.0
        
        progress.update_step_progress("test", -50.0)
        assert progress.get_step("test").progress == 0.0
    
    def test_cancel(self) -> None:
        """Test cancelling operation."""
        progress = MultiStepProgress("Test", [])
        
        assert not progress.is_cancelled()
        progress.cancel()
        assert progress.is_cancelled()
    
    def test_get_overall_progress(self) -> None:
        """Test calculating overall progress."""
        steps = [
            ProgressStep("step1", "Step 1"),
            ProgressStep("step2", "Step 2"),
            ProgressStep("step3", "Step 3"),
        ]
        
        progress = MultiStepProgress("Test", steps)
        
        # Initially all pending
        assert progress.get_overall_progress() == 0.0
        
        # Complete first step
        progress.complete_step("step1", success=True)
        assert progress.get_overall_progress() == pytest.approx(33.33, rel=0.1)
        
        # Skip second step
        progress.skip_step("step2")
        # Now only 2 active steps, 1 complete
        assert progress.get_overall_progress() == 50.0
        
        # Complete third step
        progress.complete_step("step3", success=True)
        assert progress.get_overall_progress() == 100.0
    
    def test_create_status_table(self) -> None:
        """Test creating status table."""
        steps = [
            ProgressStep("step1", "Step 1", description="First step"),
            ProgressStep("step2", "Step 2"),
        ]
        
        progress = MultiStepProgress("Test Operation", steps)
        progress.start_step("step1")
        progress.update_step_progress("step1", 50.0)
        
        table = progress.create_status_table()
        assert isinstance(table, Table)
        assert table.title == "Test Operation"
    
    def test_create_installation_report(self) -> None:
        """Test creating installation report."""
        steps = [
            ProgressStep("step1", "Install A"),
            ProgressStep("step2", "Install B"),
            ProgressStep("step3", "Install C"),
        ]
        
        progress = MultiStepProgress("Installing Components", steps)
        
        # Simulate installation
        progress.complete_step("step1", success=True)
        progress.complete_step("step2", success=False, error_message="Network error")
        progress.skip_step("step3", reason="Dependency missing")
        
        panel = progress.create_installation_report("components")
        assert isinstance(panel, Panel)
        assert panel.title == "Installation Summary"
        # Failed items should make border red
        assert panel.border_style == "red"
    
    def test_format_duration(self) -> None:
        """Test duration formatting."""
        progress = MultiStepProgress("Test", [])
        
        assert progress._format_duration(30.5) == "30.5s"
        assert progress._format_duration(90.0) == "1.5m"
        assert progress._format_duration(3900.0) == "1.1h"


class TestCancellableProgress:
    """Test CancellableProgress class."""
    
    def test_cancellable_progress_creation(self) -> None:
        """Test creating cancellable progress."""
        progress = CancellableProgress(
            title="Test Operation",
            cancel_key="x",
        )
        
        assert progress.title == "Test Operation"
        assert progress.cancel_key == "x"
        assert not progress.is_cancelled()
    
    @patch('claude_code_setup.ui.progress.threading.Thread')
    def test_track_context_manager(self, mock_thread_class) -> None:
        """Test track context manager."""
        mock_thread = MagicMock()
        mock_thread_class.return_value = mock_thread
        
        progress = CancellableProgress("Test")
        
        with progress.track("Processing", total=100) as tracker:
            assert hasattr(tracker, 'update')
            assert hasattr(tracker, 'complete')
        
        # Thread should be started
        mock_thread.start.assert_called_once()
    
    def test_cancellable_tracker_update(self) -> None:
        """Test cancellable tracker update."""
        from claude_code_setup.ui.progress import CancellableTracker
        
        mock_progress = MagicMock()
        cancel_event = threading.Event()
        
        tracker = CancellableTracker(mock_progress, 1, cancel_event)
        
        # Normal update
        tracker.update(advance=10, description="Processing")
        mock_progress.update.assert_called_once_with(1, advance=10, description="Processing")
        
        # Update when cancelled
        cancel_event.set()
        with pytest.raises(KeyboardInterrupt, match="Operation cancelled by user"):
            tracker.update(advance=5)
    
    def test_cancellable_tracker_complete(self) -> None:
        """Test cancellable tracker complete."""
        from claude_code_setup.ui.progress import CancellableTracker
        
        mock_progress = MagicMock()
        mock_progress.tasks = {1: MagicMock(total=100)}
        cancel_event = threading.Event()
        
        tracker = CancellableTracker(mock_progress, 1, cancel_event)
        
        tracker.complete("Done!")
        # The complete method makes two calls - one for description, one for completed
        calls = mock_progress.update.call_args_list
        assert len(calls) == 2
        assert calls[0] == ((1,), {'description': 'Done!'})
        assert calls[1] == ((1,), {'completed': 100})


class TestAdvancedProgress:
    """Test AdvancedProgress class."""
    
    def test_advanced_progress_creation(self) -> None:
        """Test creating advanced progress."""
        progress = AdvancedProgress(
            show_spinner=True,
            show_bar=True,
            show_percentage=True,
            show_time=True,
            show_speed=False,
        )
        
        assert progress.console is not None
        assert hasattr(progress, 'progress')
        assert progress.tasks == {}
    
    @patch('claude_code_setup.ui.progress.Progress')
    def test_track_context_manager(self, mock_progress_class) -> None:
        """Test track context manager."""
        mock_progress = MagicMock()
        mock_progress.__enter__.return_value = mock_progress
        mock_progress.__exit__.return_value = None
        mock_progress.add_task.return_value = 1
        mock_progress_class.return_value = mock_progress
        
        advanced = AdvancedProgress()
        
        with advanced.track("Processing", total=100) as tracker:
            assert hasattr(tracker, 'update')
            assert hasattr(tracker, 'set_total')
            assert hasattr(tracker, 'complete')
        
        mock_progress.add_task.assert_called_once_with("Processing", total=100)
    
    def test_simple_tracker_update(self) -> None:
        """Test simple tracker update."""
        from claude_code_setup.ui.progress import SimpleTracker
        
        mock_progress = MagicMock()
        tracker = SimpleTracker(mock_progress, 1)
        
        tracker.update(10, "Processing files")
        mock_progress.update.assert_called_once_with(1, advance=10, description="Processing files")
        
        tracker.set_total(200)
        mock_progress.update.assert_called_with(1, total=200)
        
        mock_progress.tasks = {1: MagicMock(total=200)}
        tracker.complete("All done!")
        # Check that description was set and then completed was set to 200
        calls = mock_progress.update.call_args_list
        assert calls[-2] == ((1,), {'description': 'All done!'})
        assert calls[-1] == ((1,), {'completed': 200})