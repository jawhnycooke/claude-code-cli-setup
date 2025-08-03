"""Tests for enhanced UI components."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from rich.console import Console
from io import StringIO

from claude_code_setup.ui.prompts import (
    SelectOption,
    MultiSelectPrompt,
    ConfirmationDialog,
    ValidatedPrompt,
    create_choice_table,
    show_selection_summary,
)
from claude_code_setup.ui.progress import (
    ProgressStep,
    StepStatus,
    AdvancedProgress,
    MultiStepProgress,
)
from claude_code_setup.ui.validation import (
    ValidationLevel,
    ValidationMessage,
    ValidationFeedback,
    RealTimeValidator,
    ErrorDisplay,
    create_required_validator,
    create_regex_validator,
    create_choice_validator,
    create_length_validator,
)


class TestSelectOption:
    """Test SelectOption dataclass."""
    
    def test_select_option_creation(self):
        """Test creating SelectOption instances."""
        option = SelectOption("value1", "Label 1")
        assert option.value == "value1"
        assert option.label == "Label 1"
        assert option.description is None
        assert option.selected is False
        assert option.enabled is True
    
    def test_select_option_with_all_fields(self):
        """Test SelectOption with all fields."""
        option = SelectOption(
            value="test",
            label="Test Option",
            description="A test option",
            selected=True,
            enabled=False
        )
        assert option.value == "test"
        assert option.label == "Test Option"
        assert option.description == "A test option"
        assert option.selected is True
        assert option.enabled is False


class TestMultiSelectPrompt:
    """Test MultiSelectPrompt class."""
    
    def test_initialization(self):
        """Test MultiSelectPrompt initialization."""
        options = [
            SelectOption("opt1", "Option 1"),
            SelectOption("opt2", "Option 2"),
        ]
        prompt = MultiSelectPrompt("Choose options", options)
        
        assert prompt.title == "Choose options"
        assert len(prompt.options) == 2
        assert prompt.min_selections == 0
        assert prompt.max_selections is None
        assert prompt.show_help is True
    
    def test_parse_selection_numbers(self):
        """Test parsing number selections."""
        options = [
            SelectOption("opt1", "Option 1"),
            SelectOption("opt2", "Option 2"),
            SelectOption("opt3", "Option 3"),
        ]
        prompt = MultiSelectPrompt("Test", options)
        
        # Test single selection
        result = prompt._parse_selection("1")
        assert result == ["opt1"]
        
        # Test multiple selections
        result = prompt._parse_selection("1,3")
        assert result == ["opt1", "opt3"]
        
        # Test space separated
        result = prompt._parse_selection("1 2")
        assert result == ["opt1", "opt2"]
    
    def test_parse_selection_special(self):
        """Test parsing special selections."""
        options = [
            SelectOption("opt1", "Option 1"),
            SelectOption("opt2", "Option 2"),
        ]
        prompt = MultiSelectPrompt("Test", options)
        
        # Test 'all'
        result = prompt._parse_selection("all")
        assert result == ["opt1", "opt2"]
        
        # Test 'none'
        result = prompt._parse_selection("none")
        assert result == []
    
    def test_parse_selection_invalid(self):
        """Test parsing invalid selections."""
        options = [SelectOption("opt1", "Option 1")]
        prompt = MultiSelectPrompt("Test", options)
        
        # Test invalid number
        with pytest.raises(ValueError, match="not a valid option number"):
            prompt._parse_selection("5")
        
        # Test non-number
        with pytest.raises(ValueError, match="not a valid option number"):
            prompt._parse_selection("abc")
    
    @patch('claude_code_setup.ui.prompts.Prompt.ask')
    @patch('claude_code_setup.ui.prompts.console')
    def test_ask_with_selections(self, mock_console, mock_prompt):
        """Test ask method with user selections."""
        options = [
            SelectOption("opt1", "Option 1"),
            SelectOption("opt2", "Option 2"),
        ]
        prompt = MultiSelectPrompt("Test", options, min_selections=1)
        
        # Mock user input
        mock_prompt.return_value = "1,2"
        
        result = prompt.ask()
        assert result == ["opt1", "opt2"]
        
        # Verify console interactions
        assert mock_console.print.called
        assert mock_prompt.called
    
    @patch('claude_code_setup.ui.prompts.Prompt.ask')
    @patch('claude_code_setup.ui.prompts.console')
    def test_ask_validation_errors(self, mock_console, mock_prompt):
        """Test ask method with validation errors."""
        options = [SelectOption("opt1", "Option 1")]
        prompt = MultiSelectPrompt("Test", options, min_selections=2)
        
        # Mock user input - first invalid, then exit
        mock_prompt.side_effect = ["1", KeyboardInterrupt()]
        
        with pytest.raises(SystemExit):
            prompt.ask()
        
        # Should show error message about minimum selections
        error_calls = [call for call in mock_console.print.call_args_list 
                      if "at least 2" in str(call)]
        assert len(error_calls) > 0


class TestConfirmationDialog:
    """Test ConfirmationDialog class."""
    
    def test_initialization(self):
        """Test ConfirmationDialog initialization."""
        dialog = ConfirmationDialog("Test", "Are you sure?")
        
        assert dialog.title == "Test"
        assert dialog.message == "Are you sure?"
        assert dialog.details == {}
        assert dialog.default is True
        assert dialog.danger is False
    
    @patch('claude_code_setup.ui.prompts.Confirm.ask')
    @patch('claude_code_setup.ui.prompts.console')
    def test_ask_normal(self, mock_console, mock_confirm):
        """Test normal confirmation dialog."""
        dialog = ConfirmationDialog("Confirm", "Proceed?")
        mock_confirm.return_value = True
        
        result = dialog.ask()
        assert result is True
        
        # Verify panel was printed
        assert mock_console.print.called
        # Just verify that print was called with a Panel object
        panel_arg = mock_console.print.call_args_list[0][0][0]
        assert hasattr(panel_arg, 'title')  # Rich Panel has title attribute
    
    @patch('claude_code_setup.ui.prompts.Confirm.ask')
    @patch('claude_code_setup.ui.prompts.console')
    def test_ask_danger(self, mock_console, mock_confirm):
        """Test danger confirmation dialog."""
        dialog = ConfirmationDialog("Warning", "Delete everything?", danger=True)
        mock_confirm.return_value = False
        
        result = dialog.ask()
        assert result is False
        
        # Verify panel was printed
        assert mock_console.print.called
        panel_arg = mock_console.print.call_args_list[0][0][0]
        assert hasattr(panel_arg, 'title')  # Rich Panel has title attribute


class TestValidatedPrompt:
    """Test ValidatedPrompt class."""
    
    def test_initialization(self):
        """Test ValidatedPrompt initialization."""
        def validator(value):
            return True, None
        
        prompt = ValidatedPrompt("Enter value", validator)
        assert prompt.message == "Enter value"
        assert prompt.validator == validator
        assert prompt.default is None
        assert prompt.password is False
    
    @patch('claude_code_setup.ui.prompts.Prompt.ask')
    def test_ask_valid_input(self, mock_prompt):
        """Test ask with valid input."""
        def validator(value):
            return True, None
        
        prompt = ValidatedPrompt("Test", validator)
        mock_prompt.return_value = "valid"
        
        result = prompt.ask()
        assert result == "valid"
    
    @patch('claude_code_setup.ui.prompts.Prompt.ask')
    @patch('claude_code_setup.ui.prompts.console')
    def test_ask_invalid_then_valid(self, mock_console, mock_prompt):
        """Test ask with invalid input followed by valid."""
        def validator(value):
            if value == "invalid":
                return False, "Value is invalid"
            return True, None
        
        prompt = ValidatedPrompt("Test", validator)
        mock_prompt.side_effect = ["invalid", "valid"]
        
        result = prompt.ask()
        assert result == "valid"
        
        # Check error message was shown
        error_calls = [call for call in mock_console.print.call_args_list 
                      if "Value is invalid" in str(call)]
        assert len(error_calls) > 0


class TestValidationMessage:
    """Test ValidationMessage dataclass."""
    
    def test_validation_message_creation(self):
        """Test creating ValidationMessage instances."""
        msg = ValidationMessage(ValidationLevel.ERROR, "Test error")
        assert msg.level == ValidationLevel.ERROR
        assert msg.message == "Test error"
        assert msg.field is None
        assert msg.code is None
    
    def test_validation_message_with_all_fields(self):
        """Test ValidationMessage with all fields."""
        msg = ValidationMessage(
            ValidationLevel.WARNING,
            "Test warning",
            field="test_field",
            code="TEST_CODE"
        )
        assert msg.level == ValidationLevel.WARNING
        assert msg.message == "Test warning"
        assert msg.field == "test_field"
        assert msg.code == "TEST_CODE"


class TestValidationFeedback:
    """Test ValidationFeedback class."""
    
    def test_initialization(self):
        """Test ValidationFeedback initialization."""
        feedback = ValidationFeedback()
        assert feedback.title == "Validation Results"
        assert feedback.show_success is True
        assert len(feedback.messages) == 0
    
    def test_add_message(self):
        """Test adding validation messages."""
        feedback = ValidationFeedback()
        feedback.add_message(ValidationLevel.ERROR, "Test error")
        
        assert len(feedback.messages) == 1
        assert feedback.messages[0].level == ValidationLevel.ERROR
        assert feedback.messages[0].message == "Test error"
    
    def test_has_errors(self):
        """Test error detection."""
        feedback = ValidationFeedback()
        assert not feedback.has_errors()
        
        feedback.add_message(ValidationLevel.WARNING, "Warning")
        assert not feedback.has_errors()
        
        feedback.add_message(ValidationLevel.ERROR, "Error")
        assert feedback.has_errors()
    
    def test_has_warnings(self):
        """Test warning detection."""
        feedback = ValidationFeedback()
        assert not feedback.has_warnings()
        
        feedback.add_message(ValidationLevel.ERROR, "Error")
        assert not feedback.has_warnings()
        
        feedback.add_message(ValidationLevel.WARNING, "Warning")
        assert feedback.has_warnings()
    
    def test_clear_messages(self):
        """Test clearing messages."""
        feedback = ValidationFeedback()
        feedback.add_message(ValidationLevel.ERROR, "Error")
        feedback.add_message(ValidationLevel.WARNING, "Warning")
        
        # Clear specific level
        feedback.clear_messages(ValidationLevel.ERROR)
        assert len(feedback.messages) == 1
        assert feedback.messages[0].level == ValidationLevel.WARNING
        
        # Clear all
        feedback.clear_messages()
        assert len(feedback.messages) == 0
    
    @patch('claude_code_setup.ui.validation.console')
    def test_display_no_messages(self, mock_console):
        """Test display with no messages."""
        feedback = ValidationFeedback()
        feedback.display()
        
        # Should show success panel
        assert mock_console.print.called
        panel_arg = mock_console.print.call_args_list[0][0][0]
        assert hasattr(panel_arg, 'renderable')  # Rich Panel has renderable attribute
    
    @patch('claude_code_setup.ui.validation.console')
    def test_display_with_errors(self, mock_console):
        """Test display with error messages."""
        feedback = ValidationFeedback()
        feedback.add_message(ValidationLevel.ERROR, "Test error")
        feedback.display()
        
        # Should show error panel
        assert mock_console.print.called
        panel_arg = mock_console.print.call_args_list[0][0][0]
        assert hasattr(panel_arg, 'renderable')  # Rich Panel has renderable attribute


class TestProgressStep:
    """Test ProgressStep dataclass."""
    
    def test_progress_step_creation(self):
        """Test creating ProgressStep instances."""
        step = ProgressStep("step1", "Step 1")
        assert step.id == "step1"
        assert step.title == "Step 1"
        assert step.description is None
        assert step.status == StepStatus.PENDING
        assert step.progress == 0.0
        assert step.error_message is None
        assert step.start_time is None
        assert step.end_time is None
        assert isinstance(step.metadata, dict)


class TestMultiStepProgress:
    """Test MultiStepProgress class."""
    
    def test_initialization(self):
        """Test MultiStepProgress initialization."""
        steps = [
            ProgressStep("step1", "Step 1"),
            ProgressStep("step2", "Step 2"),
        ]
        progress = MultiStepProgress("Test Operation", steps)
        
        assert progress.title == "Test Operation"
        assert len(progress.steps) == 2
        assert "step1" in progress.steps
        assert "step2" in progress.steps
        assert progress.step_order == ["step1", "step2"]
    
    def test_get_step(self):
        """Test getting steps by ID."""
        steps = [ProgressStep("step1", "Step 1")]
        progress = MultiStepProgress("Test", steps)
        
        step = progress.get_step("step1")
        assert step.id == "step1"
        
        with pytest.raises(ValueError, match="Step 'invalid' not found"):
            progress.get_step("invalid")
    
    def test_start_step(self):
        """Test starting a step."""
        steps = [ProgressStep("step1", "Step 1")]
        progress = MultiStepProgress("Test", steps)
        
        progress.start_step("step1")
        
        step = progress.get_step("step1")
        assert step.status == StepStatus.IN_PROGRESS
        assert step.start_time is not None
        assert progress.current_step == "step1"
    
    def test_complete_step(self):
        """Test completing a step."""
        steps = [ProgressStep("step1", "Step 1")]
        progress = MultiStepProgress("Test", steps)
        
        progress.start_step("step1")
        progress.complete_step("step1")
        
        step = progress.get_step("step1")
        assert step.status == StepStatus.COMPLETED
        assert step.end_time is not None
        assert step.progress == 100.0
        assert progress.current_step is None
    
    def test_complete_step_with_error(self):
        """Test completing a step with error."""
        steps = [ProgressStep("step1", "Step 1")]
        progress = MultiStepProgress("Test", steps)
        
        progress.start_step("step1")
        progress.complete_step("step1", success=False, error_message="Test error")
        
        step = progress.get_step("step1")
        assert step.status == StepStatus.FAILED
        assert step.error_message == "Test error"
    
    def test_skip_step(self):
        """Test skipping a step."""
        steps = [ProgressStep("step1", "Step 1")]
        progress = MultiStepProgress("Test", steps)
        
        progress.skip_step("step1", "Not needed")
        
        step = progress.get_step("step1")
        assert step.status == StepStatus.SKIPPED
        assert step.metadata["skip_reason"] == "Not needed"
    
    def test_get_overall_progress(self):
        """Test calculating overall progress."""
        steps = [
            ProgressStep("step1", "Step 1"),
            ProgressStep("step2", "Step 2"),
        ]
        progress = MultiStepProgress("Test", steps)
        
        # Initially 0%
        assert progress.get_overall_progress() == 0.0
        
        # One step at 50%
        progress.update_step_progress("step1", 50.0)
        assert progress.get_overall_progress() == 25.0
        
        # Both steps at 100%
        progress.update_step_progress("step1", 100.0)
        progress.update_step_progress("step2", 100.0)
        assert progress.get_overall_progress() == 100.0
    
    def test_cancellation(self):
        """Test cancellation functionality."""
        steps = [ProgressStep("step1", "Step 1")]
        progress = MultiStepProgress("Test", steps)
        
        assert not progress.is_cancelled()
        
        progress.cancel()
        assert progress.is_cancelled()


class TestCommonValidators:
    """Test common validator functions."""
    
    def test_required_validator(self):
        """Test required field validator."""
        validator = create_required_validator("test_field")
        
        # Valid input
        result = validator("some value")
        assert len(result) == 0
        
        # Invalid input
        result = validator("")
        assert len(result) == 1
        assert result[0].level == ValidationLevel.ERROR
        assert "required" in result[0].message
        
        # Whitespace only
        result = validator("   ")
        assert len(result) == 1
    
    def test_regex_validator(self):
        """Test regex pattern validator."""
        # Email pattern
        validator = create_regex_validator(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "email"
        )
        
        # Valid email
        result = validator("test@example.com")
        assert len(result) == 0
        
        # Invalid email
        result = validator("invalid-email")
        assert len(result) == 1
        assert result[0].level == ValidationLevel.ERROR
    
    def test_choice_validator(self):
        """Test choice validator."""
        validator = create_choice_validator(["option1", "option2"], "choice")
        
        # Valid choice
        result = validator("option1")
        assert len(result) == 0
        
        # Invalid choice
        result = validator("option3")
        assert len(result) == 1
        assert result[0].level == ValidationLevel.ERROR
        assert "must be one of" in result[0].message
    
    def test_choice_validator_case_insensitive(self):
        """Test case insensitive choice validator."""
        validator = create_choice_validator(
            ["Option1", "Option2"], 
            "choice", 
            case_sensitive=False
        )
        
        # Valid choice (different case)
        result = validator("option1")
        assert len(result) == 0
        
        # Still invalid
        result = validator("option3")
        assert len(result) == 1
    
    def test_length_validator(self):
        """Test length validator."""
        validator = create_length_validator(min_length=3, max_length=10, field_name="test")
        
        # Valid length
        result = validator("valid")
        assert len(result) == 0
        
        # Too short
        result = validator("ab")
        assert len(result) == 1
        assert result[0].level == ValidationLevel.ERROR
        assert "at least 3" in result[0].message
        
        # Too long
        result = validator("this is too long")
        assert len(result) == 1
        assert "at most 10" in result[0].message