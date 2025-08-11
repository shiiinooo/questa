"""Comprehensive tests for error handling and user feedback systems."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.business.error_handler import (
    ErrorHandler, UserFriendlyError, ErrorSeverity, ErrorCategory
)
from src.business.error_recovery import ErrorRecoveryManager, RecoveryResult
from src.business.task_manager import (
    TaskManager, TaskManagerError, TaskValidationError, TaskStateError, TaskNotFoundError
)
from src.business.task_validator import TaskValidationError as ValidatorError
from src.data.data_manager import DataManager, DataPersistenceError
from src.models.task import Task
from src.models.player import PlayerData
from src.models.enums import TaskDifficulty, TaskPriority, TaskStatus


class TestErrorHandler:
    """Test the ErrorHandler class."""
    
    def test_handle_validation_error_empty_title(self):
        """Test handling of empty title validation error."""
        error = ValidatorError("Title cannot be empty")
        
        user_error = ErrorHandler.handle_validation_error(error)
        
        assert user_error.title == "Invalid Task Title"
        assert "cannot be empty" in user_error.message
        assert user_error.severity == ErrorSeverity.WARNING
        assert user_error.category == ErrorCategory.VALIDATION
        assert "Enter a clear, descriptive title" in user_error.suggested_actions
    
    def test_handle_validation_error_title_too_long(self):
        """Test handling of title too long validation error."""
        error = ValidatorError("Title cannot exceed 200 characters")
        
        user_error = ErrorHandler.handle_validation_error(error)
        
        assert user_error.title == "Title Too Long"
        assert "too long" in user_error.message
        assert user_error.severity == ErrorSeverity.WARNING
        assert any("Shorten the title" in action for action in user_error.suggested_actions)
    
    def test_handle_validation_error_invalid_difficulty(self):
        """Test handling of invalid difficulty validation error."""
        error = ValidatorError("Difficulty validation error: must be a TaskDifficulty enum")
        
        user_error = ErrorHandler.handle_validation_error(error)
        
        assert user_error.title == "Invalid Difficulty"
        assert "valid difficulty level" in user_error.message
        assert any("Easy (15 XP), Medium (30 XP), or Hard (50 XP)" in action for action in user_error.suggested_actions)
    
    def test_handle_validation_error_status_transition(self):
        """Test handling of invalid status transition error."""
        error = ValidatorError("Cannot transition from COMPLETED to PENDING")
        context = {
            'current_status': 'COMPLETED',
            'new_status': 'PENDING'
        }
        
        user_error = ErrorHandler.handle_validation_error(error, context)
        
        assert user_error.title == "Invalid Status Change"
        assert "COMPLETED to PENDING" in user_error.message
        assert user_error.severity == ErrorSeverity.ERROR
    
    def test_handle_business_logic_error_already_completed(self):
        """Test handling of already completed error."""
        error = TaskStateError("Task is already completed")
        
        user_error = ErrorHandler.handle_business_logic_error(error)
        
        assert user_error.title == "Task Already Completed"
        assert "already completed" in user_error.message
        assert user_error.severity == ErrorSeverity.WARNING
        assert any("Create a new task" in action for action in user_error.suggested_actions)
    
    def test_handle_business_logic_error_completed_task_restriction(self):
        """Test handling of completed task restriction error."""
        error = TaskStateError("Cannot change difficulty for completed task")
        context = {'field': 'difficulty'}
        
        user_error = ErrorHandler.handle_business_logic_error(error, context)
        
        assert user_error.title == "Cannot Modify Completed Task"
        assert "difficulty" in user_error.message
        assert "preserves XP history" in user_error.message
        assert user_error.severity == ErrorSeverity.ERROR
    
    def test_handle_business_logic_error_task_not_found(self):
        """Test handling of task not found error."""
        error = TaskNotFoundError("Task with ID abc123 not found")
        
        user_error = ErrorHandler.handle_business_logic_error(error)
        
        assert user_error.title == "Task Not Found"
        assert "could not be found" in user_error.message
        assert "Refresh the task list" in user_error.suggested_actions
    
    def test_handle_persistence_error_save_failed(self):
        """Test handling of save failure error."""
        error = DataPersistenceError("Failed to save tasks: Permission denied")
        
        user_error = ErrorHandler.handle_persistence_error(error)
        
        assert user_error.title == "Save Failed"
        assert "Could not save" in user_error.message
        assert user_error.severity == ErrorSeverity.CRITICAL
        assert "Try saving again" in user_error.suggested_actions
    
    def test_handle_persistence_error_load_failed(self):
        """Test handling of load failure error."""
        error = DataPersistenceError("Failed to load tasks: File not found")
        
        user_error = ErrorHandler.handle_persistence_error(error)
        
        assert user_error.title == "Load Failed"
        assert "Could not load" in user_error.message
        assert "empty task list" in user_error.message
        assert any("Restore from backup" in action for action in user_error.suggested_actions)
    
    def test_handle_persistence_error_data_corruption(self):
        """Test handling of data corruption error."""
        error = DataPersistenceError("Invalid JSON in tasks file")
        
        user_error = ErrorHandler.handle_persistence_error(error)
        
        assert user_error.title == "Data Corruption Detected"
        assert "corrupted" in user_error.message
        assert "recovery from backup" in user_error.message
        assert user_error.severity == ErrorSeverity.CRITICAL
    
    def test_handle_system_error_permission_denied(self):
        """Test handling of permission denied error."""
        error = PermissionError("Permission denied")
        
        user_error = ErrorHandler.handle_system_error(error)
        
        assert user_error.title == "Permission Denied"
        assert "file permissions" in user_error.message
        assert "Check file permissions" in user_error.suggested_actions
    
    def test_handle_generic_error(self):
        """Test handling of generic unknown error."""
        error = RuntimeError("Something went wrong")
        
        user_error = ErrorHandler.handle_generic_error(error)
        
        assert user_error.title == "Unexpected Error"
        assert "unexpected error occurred" in user_error.message
        assert user_error.severity == ErrorSeverity.ERROR
        assert user_error.category == ErrorCategory.SYSTEM
        assert "Try the operation again" in user_error.suggested_actions
    
    def test_create_confirmation_requirement(self):
        """Test creating confirmation requirements."""
        confirmation = ErrorHandler.create_confirmation_requirement(
            title="Delete Task",
            message="Are you sure?",
            warning_level="danger",
            consequences=["Task will be deleted permanently"],
            alternatives=["Mark as blocked instead"]
        )
        
        assert confirmation['title'] == "Delete Task"
        assert confirmation['message'] == "Are you sure?"
        assert confirmation['warning_level'] == "danger"
        assert "Task will be deleted permanently" in confirmation['consequences']
        assert "Mark as blocked instead" in confirmation['alternatives']
        assert 'timestamp' in confirmation
    
    def test_create_success_feedback(self):
        """Test creating success feedback."""
        success = ErrorHandler.create_success_feedback(
            title="Task Created",
            message="Task created successfully",
            details={'xp_reward': 30},
            next_actions=["Complete the task to earn XP"]
        )
        
        assert success['title'] == "Task Created"
        assert success['message'] == "Task created successfully"
        assert success['details']['xp_reward'] == 30
        assert any("Complete the task" in action for action in success['next_actions'])
        assert 'timestamp' in success
    
    def test_get_error_recovery_suggestions(self):
        """Test getting error recovery suggestions by category."""
        validation_suggestions = ErrorHandler.get_error_recovery_suggestions(ErrorCategory.VALIDATION)
        assert "Check your input" in validation_suggestions[0]
        
        persistence_suggestions = ErrorHandler.get_error_recovery_suggestions(ErrorCategory.PERSISTENCE)
        assert "Try the operation again" in persistence_suggestions[0]
        
        business_suggestions = ErrorHandler.get_error_recovery_suggestions(ErrorCategory.BUSINESS_LOGIC)
        assert "Check task status" in business_suggestions[0]
        
        system_suggestions = ErrorHandler.get_error_recovery_suggestions(ErrorCategory.SYSTEM)
        assert "Restart the application" in system_suggestions[0]


class TestErrorRecoveryManager:
    """Test the ErrorRecoveryManager class."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary data directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def data_manager(self, temp_data_dir):
        """Create a DataManager with temporary directory."""
        return DataManager(temp_data_dir)
    
    @pytest.fixture
    def recovery_manager(self, data_manager):
        """Create an ErrorRecoveryManager."""
        return ErrorRecoveryManager(data_manager)
    
    def test_attempt_recovery_unknown_error_type(self, recovery_manager):
        """Test recovery attempt for unknown error type."""
        error = RuntimeError("Unknown error")
        
        result = recovery_manager.attempt_recovery("unknown_type", error)
        
        assert isinstance(result, RecoveryResult)
        assert not result.success
        assert "Generic recovery" in result.message
        assert len(recovery_manager.recovery_log) == 1
    
    def test_recover_from_corruption_with_backup(self, recovery_manager, temp_data_dir):
        """Test recovery from data corruption with available backup."""
        # Create corrupted main file
        tasks_file = recovery_manager.data_manager.tasks_file
        tasks_file.write_text("corrupted json {")
        
        # Create valid backup file
        backup_file = tasks_file.with_suffix('.json.backup')
        valid_data = {
            "tasks": {
                "task1": {
                    "id": "task1",
                    "title": "Test Task",
                    "difficulty": "MEDIUM",
                    "priority": "MEDIUM",
                    "status": "PENDING",
                    "notes": None,
                    "xp_reward": 30,
                    "created_at": datetime.now().isoformat(),
                    "completed_at": None
                }
            },
            "version": "1.0",
            "last_modified": datetime.now().isoformat()
        }
        backup_file.write_text(json.dumps(valid_data, indent=2))
        
        error = DataPersistenceError("Invalid JSON in tasks file")
        context = {'corrupted_files': [str(tasks_file)]}
        
        result = recovery_manager.attempt_recovery("data_corruption", error, context)
        
        assert result.success
        assert "recovery completed" in result.message
        assert "Restored tasks from backup" in result.actions_taken
        assert result.recovered_data['tasks'] == 1
    
    def test_recover_from_corruption_without_backup(self, recovery_manager, temp_data_dir):
        """Test recovery from data corruption without backup."""
        # Create corrupted main file
        tasks_file = recovery_manager.data_manager.tasks_file
        tasks_file.write_text("corrupted json {")
        
        error = DataPersistenceError("Invalid JSON in tasks file")
        context = {'corrupted_files': [str(tasks_file)]}
        
        result = recovery_manager.attempt_recovery("data_corruption", error, context)
        
        assert not result.success
        assert "starting with empty data" in result.message
        assert "Created new empty data files" in result.actions_taken
        assert any("All data was lost" in warning for warning in result.warnings)
    
    def test_recover_from_save_failure_disk_space(self, recovery_manager):
        """Test recovery from save failure due to disk space."""
        error = DataPersistenceError("No space left on device")
        
        with patch('shutil.disk_usage') as mock_disk_usage:
            mock_disk_usage.return_value = Mock(free=500)  # Very low space
            
            result = recovery_manager.attempt_recovery("save_failure", error)
            
            assert not result.success
            assert "Low disk space detected" in result.warnings
    
    def test_recover_from_save_failure_permissions(self, recovery_manager, temp_data_dir):
        """Test recovery from save failure due to permissions."""
        error = DataPersistenceError("Permission denied")
        
        # Mock permission test to fail
        with patch.object(Path, 'write_text', side_effect=PermissionError("Permission denied")):
            result = recovery_manager.attempt_recovery("save_failure", error)
            
            assert not result.success
            assert "permission issues" in result.message
    
    def test_recover_from_load_failure_with_backup(self, recovery_manager, temp_data_dir):
        """Test recovery from load failure with backup available."""
        # Create backup files
        tasks_backup = recovery_manager.data_manager.tasks_file.with_suffix('.json.backup')
        tasks_data = {"tasks": {"task1": {"id": "task1", "title": "Test"}}}
        tasks_backup.write_text(json.dumps(tasks_data))
        
        player_backup = recovery_manager.data_manager.player_file.with_suffix('.json.backup')
        player_data = {"player": {"total_xp": 100}}
        player_backup.write_text(json.dumps(player_data))
        
        error = DataPersistenceError("Failed to load tasks")
        
        result = recovery_manager.attempt_recovery("load_failure", error)
        
        assert result.success
        assert "Load failure recovered" in result.message
        assert "Loaded tasks from backup" in result.actions_taken
        assert "Loaded player data from backup" in result.actions_taken
    
    def test_recover_from_load_failure_without_backup(self, recovery_manager):
        """Test recovery from load failure without backup."""
        error = DataPersistenceError("Failed to load tasks")
        
        result = recovery_manager.attempt_recovery("load_failure", error)
        
        assert result.success
        assert "Load failure recovered" in result.message
        assert "Created default empty data files" in result.actions_taken
        assert any("starting with empty data" in warning for warning in result.warnings)
    
    def test_recover_from_backup_failure(self, recovery_manager, temp_data_dir):
        """Test recovery from backup failure."""
        # Create existing data files
        recovery_manager.data_manager.tasks_file.write_text('{"tasks": {}}')
        recovery_manager.data_manager.player_file.write_text('{"player": {}}')
        
        error = Exception("Backup failed")
        
        result = recovery_manager.attempt_recovery("backup_failure", error)
        
        assert result.success
        assert "emergency backup" in result.message
        assert any("emergency" in action for action in result.actions_taken)
    
    def test_recover_from_permission_error(self, recovery_manager):
        """Test recovery from permission error."""
        error = PermissionError("Permission denied")
        
        with patch('pathlib.Path.mkdir'), \
             patch('pathlib.Path.write_text'), \
             patch('pathlib.Path.unlink'):
            
            result = recovery_manager.attempt_recovery("permission_error", error)
            
            assert result.success
            assert "alternative directory" in result.message
    
    def test_recover_from_disk_space_error(self, recovery_manager, temp_data_dir):
        """Test recovery from disk space error."""
        # Create some temporary files to clean up
        temp_file1 = temp_data_dir / "temp1.tmp"
        temp_file1.write_text("temp data")
        temp_file2 = temp_data_dir / "backup1.backup"
        temp_file2.write_text("backup data")
        
        error = OSError("No space left on device")
        
        result = recovery_manager.attempt_recovery("disk_space_error", error)
        
        # Should clean up temp files
        assert not temp_file1.exists()
        assert "Cleaned up" in " ".join(result.actions_taken)
    
    def test_recover_from_validation_error(self, recovery_manager):
        """Test recovery from validation error."""
        error = ValidatorError("Title cannot be empty")
        invalid_data = {"title": "", "difficulty": "MEDIUM"}
        context = {"invalid_data": invalid_data}
        
        result = recovery_manager.attempt_recovery("validation_error", error, context)
        
        assert result.success
        assert "data sanitization" in result.message
        assert result.recovered_data['fixed_data']['title'] == "Untitled Task"
    
    def test_recover_from_state_error_already_completed(self, recovery_manager):
        """Test recovery from state error - already completed."""
        error = TaskStateError("Task is already completed")
        
        result = recovery_manager.attempt_recovery("state_error", error)
        
        assert result.success
        assert "already in desired state" in result.message
        assert any("already completed" in warning for warning in result.warnings)
    
    def test_recover_from_state_error_invalid_transition(self, recovery_manager):
        """Test recovery from state error - invalid transition."""
        error = TaskStateError("Cannot transition from COMPLETED to PENDING")
        context = {"current_status": TaskStatus.COMPLETED}
        
        result = recovery_manager.attempt_recovery("state_error", error, context)
        
        assert not result.success
        assert "invalid transition" in result.message
        assert "Valid transitions" in " ".join(result.warnings)
    
    def test_recovery_log(self, recovery_manager):
        """Test recovery logging functionality."""
        error = RuntimeError("Test error")
        
        # Perform recovery
        recovery_manager.attempt_recovery("test_type", error)
        
        # Check log
        log = recovery_manager.get_recovery_log()
        assert len(log) == 1
        assert log[0]['error_type'] == "test_type"
        assert log[0]['error_message'] == "Test error"
        assert 'timestamp' in log[0]
        assert 'result' in log[0]
        
        # Clear log
        recovery_manager.clear_recovery_log()
        assert len(recovery_manager.get_recovery_log()) == 0
    
    def test_sanitize_invalid_data(self, recovery_manager):
        """Test data sanitization functionality."""
        invalid_data = {
            "title": "  ",  # Empty after strip
            "difficulty": "medium",  # Wrong case
            "priority": "invalid",  # Invalid value
            "status": "ACTIVE",  # String instead of enum
            "notes": 123  # Wrong type
        }
        
        sanitized = recovery_manager._sanitize_invalid_data(invalid_data)
        
        assert sanitized['title'] == "Untitled Task"
        assert sanitized['difficulty'] == TaskDifficulty.MEDIUM
        assert sanitized['priority'] == TaskPriority.MEDIUM
        assert sanitized['status'] == TaskStatus.ACTIVE
        assert sanitized['notes'] == "123"
    
    def test_create_empty_data_files(self, recovery_manager):
        """Test creation of empty data files."""
        recovery_manager._create_empty_data_files()
        
        # Check tasks file
        assert recovery_manager.data_manager.tasks_file.exists()
        with open(recovery_manager.data_manager.tasks_file) as f:
            tasks_data = json.load(f)
        assert tasks_data['tasks'] == {}
        assert tasks_data['version'] == "1.0"
        
        # Check player file
        assert recovery_manager.data_manager.player_file.exists()
        with open(recovery_manager.data_manager.player_file) as f:
            player_data = json.load(f)
        assert player_data['player']['total_xp'] == 0
        assert player_data['player']['tasks_completed'] == 0


class TestIntegratedErrorHandling:
    """Test integrated error handling across the system."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary data directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def task_manager(self, temp_data_dir):
        """Create a TaskManager with temporary directory."""
        data_manager = DataManager(temp_data_dir)
        return TaskManager(data_manager)
    
    def test_task_creation_error_handling(self, task_manager):
        """Test error handling in task creation workflow."""
        # Test validation error
        with pytest.raises(TaskValidationError) as exc_info:
            task_manager.create_task(
                title="",  # Empty title
                difficulty=TaskDifficulty.MEDIUM,
                priority=TaskPriority.MEDIUM
            )
        
        # Convert to user-friendly error
        user_error = ErrorHandler.handle_validation_error(exc_info.value)
        assert user_error.title == "Invalid Task Title"
        assert user_error.severity == ErrorSeverity.WARNING
    
    def test_task_completion_error_handling(self, task_manager):
        """Test error handling in task completion workflow."""
        # Create and complete a task
        task = task_manager.create_task(
            title="Test Task",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.MEDIUM
        )
        task_manager.complete_task(task.id)
        
        # Try to complete again
        with pytest.raises(TaskStateError) as exc_info:
            task_manager.complete_task(task.id)
        
        # Convert to user-friendly error
        user_error = ErrorHandler.handle_business_logic_error(exc_info.value)
        assert user_error.title == "Task Already Completed"
        assert user_error.severity == ErrorSeverity.WARNING
    
    def test_task_update_error_handling(self, task_manager):
        """Test error handling in task update workflow."""
        # Create and complete a task
        task = task_manager.create_task(
            title="Test Task",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.MEDIUM
        )
        task_manager.complete_task(task.id)
        
        # Try to change difficulty of completed task
        with pytest.raises(TaskStateError) as exc_info:
            task_manager.update_task(task.id, difficulty=TaskDifficulty.HARD)
        
        # Convert to user-friendly error
        context = {'field': 'difficulty'}
        user_error = ErrorHandler.handle_business_logic_error(exc_info.value, context)
        assert user_error.title == "Cannot Modify Completed Task"
        assert "difficulty" in user_error.message
    
    def test_task_deletion_error_handling(self, task_manager):
        """Test error handling in task deletion workflow."""
        # Create and complete a task
        task = task_manager.create_task(
            title="Test Task",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.MEDIUM
        )
        task_manager.complete_task(task.id)
        
        # Try to delete without force
        with pytest.raises(TaskStateError) as exc_info:
            task_manager.delete_task(task.id)
        
        # Convert to user-friendly error
        user_error = ErrorHandler.handle_business_logic_error(exc_info.value)
        assert "confirmation" in user_error.message.lower()
    
    def test_data_persistence_error_handling(self, task_manager):
        """Test error handling for data persistence errors."""
        # Mock a save failure
        with patch.object(task_manager._data_manager, 'save_tasks', 
                         side_effect=DataPersistenceError("Disk full")):
            
            with pytest.raises(TaskManagerError) as exc_info:
                task_manager.create_task(
                    title="Test Task",
                    difficulty=TaskDifficulty.MEDIUM,
                    priority=TaskPriority.MEDIUM
                )
            
            # Convert to user-friendly error
            user_error = ErrorHandler.handle_persistence_error(exc_info.value)
            assert user_error.category == ErrorCategory.PERSISTENCE
    
    def test_error_recovery_integration(self, temp_data_dir):
        """Test integration of error recovery with task manager."""
        data_manager = DataManager(temp_data_dir)
        recovery_manager = ErrorRecoveryManager(data_manager)
        
        # Create corrupted data file
        data_manager.tasks_file.write_text("corrupted json {")
        
        # Attempt recovery
        error = DataPersistenceError("Invalid JSON")
        result = recovery_manager.attempt_recovery("data_corruption", error)
        
        # Should create empty files as fallback
        assert result.success or "empty data" in result.message
        assert data_manager.tasks_file.exists()
    
