"""Unit tests for TaskValidator with comprehensive validation scenarios."""

import pytest
from datetime import datetime

from src.business.task_validator import TaskValidator, TaskValidationError
from src.models.enums import TaskDifficulty, TaskPriority, TaskStatus


class TestTaskValidator:
    """Test TaskValidator validation methods."""
    
    def test_validate_title_success(self):
        """Test successful title validation."""
        valid_titles = [
            "Valid task title",
            "Task with numbers 123",
            "A" * 200,  # Max length
            "Task-with-dashes",
            "Task_with_underscores"
        ]
        
        for title in valid_titles:
            assert TaskValidator.validate_title(title) is True
    
    def test_validate_title_empty(self):
        """Test title validation with empty strings."""
        invalid_titles = ["", "   ", "\t\n"]
        
        for title in invalid_titles:
            with pytest.raises(TaskValidationError, match="Title cannot be empty"):
                TaskValidator.validate_title(title)
    
    def test_validate_title_too_long(self):
        """Test title validation with excessive length."""
        long_title = "A" * 201
        
        with pytest.raises(TaskValidationError, match="cannot exceed 200 characters"):
            TaskValidator.validate_title(long_title)
    
    def test_validate_title_invalid_type(self):
        """Test title validation with non-string types."""
        invalid_types = [123, None, [], {}]
        
        for invalid_title in invalid_types:
            with pytest.raises(TaskValidationError, match="Title must be a string"):
                TaskValidator.validate_title(invalid_title)
    
    def test_validate_title_special_characters_start(self):
        """Test title validation with special characters at start."""
        invalid_titles = ["@invalid", "#invalid", "!invalid"]
        
        for title in invalid_titles:
            with pytest.raises(TaskValidationError, match="cannot start with special characters"):
                TaskValidator.validate_title(title)
    
    def test_validate_difficulty_success(self):
        """Test successful difficulty validation."""
        for difficulty in TaskDifficulty:
            assert TaskValidator.validate_difficulty(difficulty) is True
    
    def test_validate_difficulty_invalid_type(self):
        """Test difficulty validation with invalid types."""
        invalid_difficulties = ["Easy", 1, None, []]
        
        for difficulty in invalid_difficulties:
            with pytest.raises(TaskValidationError, match="must be a TaskDifficulty enum"):
                TaskValidator.validate_difficulty(difficulty)
    
    def test_validate_priority_success(self):
        """Test successful priority validation."""
        for priority in TaskPriority:
            assert TaskValidator.validate_priority(priority) is True
    
    def test_validate_priority_invalid_type(self):
        """Test priority validation with invalid types."""
        invalid_priorities = ["High", 1, None, []]
        
        for priority in invalid_priorities:
            with pytest.raises(TaskValidationError, match="must be a TaskPriority enum"):
                TaskValidator.validate_priority(priority)
    
    def test_validate_status_success(self):
        """Test successful status validation."""
        for status in TaskStatus:
            assert TaskValidator.validate_status(status) is True
    
    def test_validate_status_invalid_type(self):
        """Test status validation with invalid types."""
        invalid_statuses = ["Pending", 1, None, []]
        
        for status in invalid_statuses:
            with pytest.raises(TaskValidationError, match="must be a TaskStatus enum"):
                TaskValidator.validate_status(status)
    
    def test_validate_notes_success(self):
        """Test successful notes validation."""
        valid_notes = [
            None,
            "",
            "Valid notes",
            "A" * 1000,  # Max length
            "Notes with\nnewlines"
        ]
        
        for notes in valid_notes:
            assert TaskValidator.validate_notes(notes) is True
    
    def test_validate_notes_too_long(self):
        """Test notes validation with excessive length."""
        long_notes = "A" * 1001
        
        with pytest.raises(TaskValidationError, match="cannot exceed 1000 characters"):
            TaskValidator.validate_notes(long_notes)
    
    def test_validate_notes_invalid_type(self):
        """Test notes validation with invalid types."""
        invalid_notes = [123, [], {}]
        
        for notes in invalid_notes:
            with pytest.raises(TaskValidationError, match="Notes must be a string or None"):
                TaskValidator.validate_notes(notes)
    
    def test_validate_status_transition_success(self):
        """Test successful status transitions."""
        valid_transitions = [
            (TaskStatus.PENDING, TaskStatus.ACTIVE),
            (TaskStatus.PENDING, TaskStatus.BLOCKED),
            (TaskStatus.PENDING, TaskStatus.COMPLETED),
            (TaskStatus.ACTIVE, TaskStatus.PENDING),
            (TaskStatus.ACTIVE, TaskStatus.BLOCKED),
            (TaskStatus.ACTIVE, TaskStatus.COMPLETED),
            (TaskStatus.BLOCKED, TaskStatus.PENDING),
            (TaskStatus.BLOCKED, TaskStatus.ACTIVE),
            (TaskStatus.BLOCKED, TaskStatus.COMPLETED)
        ]
        
        for current, new in valid_transitions:
            assert TaskValidator.validate_status_transition(current, new) is True
    
    def test_validate_status_transition_invalid(self):
        """Test invalid status transitions."""
        # Completed tasks cannot transition to other states
        invalid_transitions = [
            (TaskStatus.COMPLETED, TaskStatus.PENDING),
            (TaskStatus.COMPLETED, TaskStatus.ACTIVE),
            (TaskStatus.COMPLETED, TaskStatus.BLOCKED)
        ]
        
        for current, new in invalid_transitions:
            with pytest.raises(TaskValidationError, match="Cannot transition from"):
                TaskValidator.validate_status_transition(current, new)
    
    def test_validate_status_transition_invalid_types(self):
        """Test status transition validation with invalid types."""
        with pytest.raises(TaskValidationError, match="must be TaskStatus enum values"):
            TaskValidator.validate_status_transition("PENDING", TaskStatus.ACTIVE)
    
    def test_validate_task_data_success(self):
        """Test successful task data validation."""
        valid_data = {
            'title': 'Valid task',
            'difficulty': TaskDifficulty.MEDIUM,
            'priority': TaskPriority.HIGH,
            'notes': 'Optional notes'
        }
        
        errors = TaskValidator.validate_task_data(valid_data)
        assert errors == []
    
    def test_validate_task_data_missing_required(self):
        """Test task data validation with missing required fields."""
        incomplete_data = {
            'title': 'Valid task'
            # Missing difficulty and priority
        }
        
        errors = TaskValidator.validate_task_data(incomplete_data)
        assert len(errors) == 2
        assert any("Missing required field: difficulty" in error for error in errors)
        assert any("Missing required field: priority" in error for error in errors)
    
    def test_validate_task_data_string_enums(self):
        """Test task data validation with string enum values."""
        data_with_strings = {
            'title': 'Valid task',
            'difficulty': 'MEDIUM',
            'priority': 'HIGH',
            'status': 'PENDING'
        }
        
        errors = TaskValidator.validate_task_data(data_with_strings)
        assert errors == []
        
        # Check that strings were converted to enums
        assert data_with_strings['difficulty'] == TaskDifficulty.MEDIUM
        assert data_with_strings['priority'] == TaskPriority.HIGH
        assert data_with_strings['status'] == TaskStatus.PENDING
    
    def test_validate_task_data_invalid_string_enums(self):
        """Test task data validation with invalid string enum values."""
        data_with_invalid_strings = {
            'title': 'Valid task',
            'difficulty': 'INVALID',
            'priority': 'WRONG',
            'status': 'BADSTATUS'
        }
        
        errors = TaskValidator.validate_task_data(data_with_invalid_strings)
        assert len(errors) == 3
        assert any("Invalid difficulty: INVALID" in error for error in errors)
        assert any("Invalid priority: WRONG" in error for error in errors)
        assert any("Invalid status: BADSTATUS" in error for error in errors)
    
    def test_validate_task_data_invalid_timestamps(self):
        """Test task data validation with invalid timestamps."""
        data_with_bad_timestamps = {
            'title': 'Valid task',
            'difficulty': TaskDifficulty.EASY,
            'priority': TaskPriority.LOW,
            'created_at': 'invalid-timestamp',
            'completed_at': 'also-invalid'
        }
        
        errors = TaskValidator.validate_task_data(data_with_bad_timestamps)
        assert len(errors) == 2
        assert any("Invalid created_at timestamp format" in error for error in errors)
        assert any("Invalid completed_at timestamp format" in error for error in errors)
    
    def test_validate_task_update_success(self):
        """Test successful task update validation."""
        current_data = {
            'id': 'task-1',
            'title': 'Current task',
            'difficulty': TaskDifficulty.EASY,
            'priority': TaskPriority.LOW,
            'status': TaskStatus.PENDING,
            'created_at': datetime.now()
        }
        
        update_data = {
            'title': 'Updated task',
            'priority': TaskPriority.HIGH
        }
        
        errors = TaskValidator.validate_task_update(current_data, update_data)
        assert errors == []
    
    def test_validate_task_update_immutable_fields(self):
        """Test task update validation with immutable fields."""
        current_data = {
            'id': 'task-1',
            'status': TaskStatus.PENDING
        }
        
        update_data = {
            'id': 'new-id',
            'created_at': datetime.now()
        }
        
        errors = TaskValidator.validate_task_update(current_data, update_data)
        assert len(errors) == 2
        assert any("Cannot update immutable field: id" in error for error in errors)
        assert any("Cannot update immutable field: created_at" in error for error in errors)
    
    def test_validate_task_update_completed_task_restrictions(self):
        """Test task update validation for completed tasks."""
        current_data = {
            'status': TaskStatus.COMPLETED,
            'difficulty': TaskDifficulty.EASY
        }
        
        update_data = {
            'difficulty': TaskDifficulty.HARD,
            'xp_reward': 50
        }
        
        errors = TaskValidator.validate_task_update(current_data, update_data)
        assert len(errors) == 2
        assert any("Cannot update difficulty for completed task" in error for error in errors)
        assert any("Cannot update xp_reward for completed task" in error for error in errors)
    
    def test_validate_task_update_invalid_status_transition(self):
        """Test task update validation with invalid status transition."""
        current_data = {
            'status': TaskStatus.COMPLETED
        }
        
        update_data = {
            'status': TaskStatus.PENDING
        }
        
        errors = TaskValidator.validate_task_update(current_data, update_data)
        assert len(errors) == 1
        assert "Cannot transition from" in errors[0]
    
    def test_sanitize_task_data_success(self):
        """Test task data sanitization."""
        dirty_data = {
            'title': '  Messy Title  ',
            'notes': '  Some notes  ',
            'difficulty': 'MEDIUM',
            'priority': 'high',
            'status': 'pending'
        }
        
        sanitized = TaskValidator.sanitize_task_data(dirty_data)
        
        assert sanitized['title'] == 'Messy Title'
        assert sanitized['notes'] == 'Some notes'
        assert sanitized['difficulty'] == TaskDifficulty.MEDIUM
        assert sanitized['priority'] == TaskPriority.HIGH
        assert sanitized['status'] == TaskStatus.PENDING
    
    def test_sanitize_task_data_empty_notes(self):
        """Test task data sanitization with empty notes."""
        data = {
            'title': 'Valid title',
            'notes': '   '  # Only whitespace
        }
        
        sanitized = TaskValidator.sanitize_task_data(data)
        assert sanitized['notes'] is None
    
    def test_sanitize_task_data_invalid_enum_strings(self):
        """Test task data sanitization with invalid enum strings."""
        data = {
            'title': 'Valid title',
            'difficulty': 'INVALID',
            'priority': 'WRONG'
        }
        
        sanitized = TaskValidator.sanitize_task_data(data)
        
        # Invalid enum strings should remain as strings for validation to catch
        assert sanitized['difficulty'] == 'INVALID'
        assert sanitized['priority'] == 'WRONG'