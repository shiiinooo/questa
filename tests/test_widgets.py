"""Unit tests for Textual UI widgets."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from textual.app import App
from textual.widgets import Input, TextArea, Select, Button

from src.models.task import Task
from src.models.enums import TaskDifficulty, TaskPriority, TaskStatus
from src.widgets.task_list_item import TaskListItem
from src.widgets.status_badge import StatusBadge
from src.widgets.priority_indicator import PriorityIndicator
from src.widgets.task_form import TaskForm, TaskTitleValidator


class TestTaskListItem:
    """Test cases for TaskListItem widget."""
    
    def test_init_with_task(self):
        """Test TaskListItem initialization with a task."""
        task = Task(
            title="Test Task",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.HIGH,
            notes="Test notes"
        )
        
        item = TaskListItem(task)
        
        assert item.task == task
        assert not item.selected
    
    def test_init_with_completed_task(self):
        """Test TaskListItem initialization with completed task."""
        task = Task(
            title="Completed Task",
            difficulty=TaskDifficulty.EASY,
            priority=TaskPriority.LOW,
            status=TaskStatus.COMPLETED
        )
        task.completed_at = datetime.now()
        
        item = TaskListItem(task)
        
        assert item.task == task
        assert "completed" in item.classes
    
    def test_update_task(self):
        """Test updating the displayed task."""
        original_task = Task(
            title="Original Task",
            difficulty=TaskDifficulty.EASY,
            priority=TaskPriority.LOW
        )
        
        updated_task = Task(
            title="Updated Task",
            difficulty=TaskDifficulty.HARD,
            priority=TaskPriority.CRITICAL
        )
        
        item = TaskListItem(original_task)
        item.update_task(updated_task)
        
        assert item.task == updated_task
    
    def test_set_selected(self):
        """Test setting selection state."""
        task = Task(
            title="Test Task",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.MEDIUM
        )
        
        item = TaskListItem(task)
        
        # Test selecting
        item.set_selected(True)
        assert item.selected
        assert "selected" in item.classes
        
        # Test deselecting
        item.set_selected(False)
        assert not item.selected
        assert "selected" not in item.classes
    
    def test_task_selected_message(self):
        """Test TaskSelected message creation."""
        task = Task(
            title="Test Task",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.MEDIUM
        )
        
        message = TaskListItem.TaskSelected(task)
        assert message.task == task


class TestStatusBadge:
    """Test cases for StatusBadge widget."""
    
    def test_init_with_status(self):
        """Test StatusBadge initialization with different statuses."""
        for status in TaskStatus:
            badge = StatusBadge(status)
            assert badge.status == status
    
    def test_update_status(self):
        """Test updating the displayed status."""
        badge = StatusBadge(TaskStatus.PENDING)
        
        badge.update_status(TaskStatus.COMPLETED)
        assert badge.status == TaskStatus.COMPLETED
    
    def test_status_color_property(self):
        """Test status color mapping."""
        test_cases = [
            (TaskStatus.PENDING, "warning"),
            (TaskStatus.ACTIVE, "primary"),
            (TaskStatus.BLOCKED, "error"),
            (TaskStatus.COMPLETED, "success")
        ]
        
        for status, expected_color in test_cases:
            badge = StatusBadge(status)
            assert badge.status_color == expected_color
    
    def test_status_symbol_property(self):
        """Test status symbol mapping."""
        test_cases = [
            (TaskStatus.PENDING, "⏳"),
            (TaskStatus.ACTIVE, "🔄"),
            (TaskStatus.BLOCKED, "🚫"),
            (TaskStatus.COMPLETED, "✅")
        ]
        
        for status, expected_symbol in test_cases:
            badge = StatusBadge(status)
            assert badge.status_symbol == expected_symbol


class TestPriorityIndicator:
    """Test cases for PriorityIndicator widget."""
    
    def test_init_with_priority(self):
        """Test PriorityIndicator initialization with different priorities."""
        for priority in TaskPriority:
            indicator = PriorityIndicator(priority)
            assert indicator.priority == priority
    
    def test_update_priority(self):
        """Test updating the displayed priority."""
        indicator = PriorityIndicator(TaskPriority.LOW)
        
        indicator.update_priority(TaskPriority.CRITICAL)
        assert indicator.priority == TaskPriority.CRITICAL
    
    def test_priority_color_property(self):
        """Test priority color mapping."""
        test_cases = [
            (TaskPriority.LOW, "surface-lighten-1"),
            (TaskPriority.MEDIUM, "warning"),
            (TaskPriority.HIGH, "error-lighten-2"),
            (TaskPriority.CRITICAL, "error")
        ]
        
        for priority, expected_color in test_cases:
            indicator = PriorityIndicator(priority)
            assert indicator.priority_color == expected_color
    
    def test_priority_symbol_property(self):
        """Test priority symbol mapping."""
        test_cases = [
            (TaskPriority.LOW, "⬇️"),
            (TaskPriority.MEDIUM, "➡️"),
            (TaskPriority.HIGH, "⬆️"),
            (TaskPriority.CRITICAL, "🔥")
        ]
        
        for priority, expected_symbol in test_cases:
            indicator = PriorityIndicator(priority)
            assert indicator.priority_symbol == expected_symbol
    
    def test_priority_level_property(self):
        """Test priority level mapping for sorting."""
        test_cases = [
            (TaskPriority.LOW, 1),
            (TaskPriority.MEDIUM, 2),
            (TaskPriority.HIGH, 3),
            (TaskPriority.CRITICAL, 4)
        ]
        
        for priority, expected_level in test_cases:
            indicator = PriorityIndicator(priority)
            assert indicator.priority_level == expected_level


class TestTaskTitleValidator:
    """Test cases for TaskTitleValidator."""
    
    def test_valid_title(self):
        """Test validation of valid titles."""
        validator = TaskTitleValidator()
        
        valid_titles = [
            "Valid Task Title",
            "A" * 200,  # Maximum length
            "Task with numbers 123",
            "Task with special chars !@#$%"
        ]
        
        for title in valid_titles:
            result = validator.validate(title)
            assert result.is_valid
    
    def test_empty_title(self):
        """Test validation of empty titles."""
        validator = TaskTitleValidator()
        
        invalid_titles = ["", "   ", "\t\n"]
        
        for title in invalid_titles:
            result = validator.validate(title)
            assert not result.is_valid
            assert "cannot be empty" in str(result.failure_descriptions)
    
    def test_title_too_long(self):
        """Test validation of titles that are too long."""
        validator = TaskTitleValidator()
        
        long_title = "A" * 201  # Over maximum length
        result = validator.validate(long_title)
        
        assert not result.is_valid
        assert "cannot exceed 200 characters" in str(result.failure_descriptions)


class TestTaskForm:
    """Test cases for TaskForm widget."""
    
    def test_init_for_new_task(self):
        """Test TaskForm initialization for creating new task."""
        form = TaskForm()
        
        assert form.task is None
        assert not form.is_editing
        assert form._validation_errors == []
    
    def test_init_for_editing_task(self):
        """Test TaskForm initialization for editing existing task."""
        task = Task(
            title="Existing Task",
            difficulty=TaskDifficulty.HARD,
            priority=TaskPriority.HIGH,
            notes="Existing notes"
        )
        
        form = TaskForm(task)
        
        assert form.task == task
        assert form.is_editing
        assert form._validation_errors == []
    
    def test_validate_form_valid_data(self):
        """Test form validation with valid data."""
        form = TaskForm()
        
        # Mock form inputs
        with patch.object(form, 'query_one') as mock_query:
            mock_input = Mock()
            mock_input.value = "Valid Task Title"
            mock_query.return_value = mock_input
            
            errors = form.validate_form()
            assert errors == []
    
    def test_validate_form_empty_title(self):
        """Test form validation with empty title."""
        form = TaskForm()
        
        # Mock form inputs
        with patch.object(form, 'query_one') as mock_query:
            mock_input = Mock()
            mock_input.value = ""
            mock_query.return_value = mock_input
            
            errors = form.validate_form()
            assert len(errors) == 1
            assert "Task title is required" in errors[0]
    
    def test_validate_form_title_too_long(self):
        """Test form validation with title too long."""
        form = TaskForm()
        
        # Mock form inputs
        with patch.object(form, 'query_one') as mock_query:
            mock_input = Mock()
            mock_input.value = "A" * 201  # Too long
            mock_query.return_value = mock_input
            
            errors = form.validate_form()
            assert len(errors) == 1
            assert "cannot exceed 200 characters" in errors[0]
    
    def test_validate_form_invalid_status_transition(self):
        """Test form validation with invalid status transition."""
        completed_task = Task(
            title="Completed Task",
            difficulty=TaskDifficulty.EASY,
            priority=TaskPriority.LOW,
            status=TaskStatus.COMPLETED
        )
        
        form = TaskForm(completed_task)
        
        # Mock form inputs
        with patch.object(form, 'query_one') as mock_query:
            def mock_query_side_effect(selector, widget_type=None):
                if selector == "#title_input":
                    mock_input = Mock()
                    mock_input.value = "Valid Title"
                    return mock_input
                elif selector == "#status_select":
                    mock_select = Mock()
                    mock_select.value = TaskStatus.PENDING  # Invalid transition
                    return mock_select
                return Mock()
            
            mock_query.side_effect = mock_query_side_effect
            
            errors = form.validate_form()
            assert len(errors) == 1
            assert "Cannot transition" in errors[0]
    
    def test_get_form_data_new_task(self):
        """Test extracting form data for new task."""
        form = TaskForm()
        
        # Mock form inputs
        with patch.object(form, 'query_one') as mock_query:
            def mock_query_side_effect(selector, widget_type=None):
                if selector == "#title_input":
                    mock_input = Mock()
                    mock_input.value = "New Task Title"
                    return mock_input
                elif selector == "#difficulty_select":
                    mock_select = Mock()
                    mock_select.value = TaskDifficulty.HARD
                    return mock_select
                elif selector == "#priority_select":
                    mock_select = Mock()
                    mock_select.value = TaskPriority.HIGH
                    return mock_select
                elif selector == "#notes_input":
                    mock_textarea = Mock()
                    mock_textarea.text = "Task notes"
                    return mock_textarea
                return Mock()
            
            mock_query.side_effect = mock_query_side_effect
            
            data = form.get_form_data()
            
            expected_data = {
                'title': 'New Task Title',
                'difficulty': TaskDifficulty.HARD,
                'priority': TaskPriority.HIGH,
                'notes': 'Task notes'
            }
            
            assert data == expected_data
    
    def test_get_form_data_editing_task(self):
        """Test extracting form data for editing task."""
        task = Task(
            title="Existing Task",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.MEDIUM
        )
        
        form = TaskForm(task)
        
        # Mock form inputs
        with patch.object(form, 'query_one') as mock_query:
            def mock_query_side_effect(selector, widget_type=None):
                if selector == "#title_input":
                    mock_input = Mock()
                    mock_input.value = "Updated Task Title"
                    return mock_input
                elif selector == "#difficulty_select":
                    mock_select = Mock()
                    mock_select.value = TaskDifficulty.HARD
                    return mock_select
                elif selector == "#priority_select":
                    mock_select = Mock()
                    mock_select.value = TaskPriority.HIGH
                    return mock_select
                elif selector == "#status_select":
                    mock_select = Mock()
                    mock_select.value = TaskStatus.ACTIVE
                    return mock_select
                elif selector == "#notes_input":
                    mock_textarea = Mock()
                    mock_textarea.text = "Updated notes"
                    return mock_textarea
                return Mock()
            
            mock_query.side_effect = mock_query_side_effect
            
            data = form.get_form_data()
            
            expected_data = {
                'title': 'Updated Task Title',
                'difficulty': TaskDifficulty.HARD,
                'priority': TaskPriority.HIGH,
                'status': TaskStatus.ACTIVE,
                'notes': 'Updated notes'
            }
            
            assert data == expected_data
    
    def test_task_created_message(self):
        """Test TaskCreated message creation."""
        form_data = {
            'title': 'New Task',
            'difficulty': TaskDifficulty.MEDIUM,
            'priority': TaskPriority.MEDIUM,
            'notes': 'Task notes'
        }
        
        message = TaskForm.TaskCreated(form_data)
        assert message.form_data == form_data
    
    def test_task_updated_message(self):
        """Test TaskUpdated message creation."""
        task = Task(
            title="Original Task",
            difficulty=TaskDifficulty.EASY,
            priority=TaskPriority.LOW
        )
        
        form_data = {
            'title': 'Updated Task',
            'difficulty': TaskDifficulty.HARD,
            'priority': TaskPriority.HIGH,
            'notes': 'Updated notes'
        }
        
        message = TaskForm.TaskUpdated(task, form_data)
        assert message.original_task == task
        assert message.form_data == form_data
    
    def test_form_cancelled_message(self):
        """Test FormCancelled message creation."""
        message = TaskForm.FormCancelled()
        assert isinstance(message, TaskForm.FormCancelled)