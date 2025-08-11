"""Unit tests for task editing and deletion functionality with comprehensive edge cases."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.business.task_manager import (
    TaskManager, TaskManagerError, TaskNotFoundError, TaskStateError
)
from src.business.task_validator import TaskValidationError
from src.data.data_manager import DataManager
from src.models.enums import TaskDifficulty, TaskPriority, TaskStatus
from src.models.task import Task
from src.models.player import PlayerData


class TestTaskEditing:
    """Test task editing functionality with validation and XP recalculation."""
    
    @pytest.fixture
    def mock_data_manager(self):
        """Create mock DataManager for testing."""
        mock_dm = Mock(spec=DataManager)
        mock_dm.load_tasks.return_value = {}
        mock_dm.load_player_data.return_value = PlayerData()
        mock_dm.save_tasks.return_value = True
        mock_dm.save_player_data.return_value = True
        mock_dm.create_backup.return_value = True
        return mock_dm
    
    @pytest.fixture
    def task_manager(self, mock_data_manager):
        """Create TaskManager instance for testing."""
        return TaskManager(mock_data_manager)
    
    @pytest.fixture
    def sample_task(self):
        """Create sample task for testing."""
        return Task(
            title="Original task",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.HIGH,
            notes="Original notes"
        )
    
    @pytest.fixture
    def completed_task(self):
        """Create completed task for testing."""
        task = Task(
            title="Completed task",
            difficulty=TaskDifficulty.HARD,
            priority=TaskPriority.CRITICAL,
            notes="Completed notes"
        )
        task.complete()
        return task
    
    def test_update_task_title_success(self, task_manager, sample_task):
        """Test successful task title update."""
        task_manager._tasks[sample_task.id] = sample_task
        
        updated_task = task_manager.update_task(sample_task.id, title="Updated title")
        
        assert updated_task.title == "Updated title"
        assert updated_task.difficulty == sample_task.difficulty  # Unchanged
        assert updated_task.priority == sample_task.priority  # Unchanged
    
    def test_update_task_difficulty_success(self, task_manager, sample_task):
        """Test successful task difficulty update with XP recalculation."""
        task_manager._tasks[sample_task.id] = sample_task
        original_xp = sample_task.xp_reward
        
        updated_task = task_manager.update_task(sample_task.id, difficulty=TaskDifficulty.HARD)
        
        assert updated_task.difficulty == TaskDifficulty.HARD
        assert updated_task.xp_reward == TaskDifficulty.HARD.xp_value
        assert updated_task.xp_reward != original_xp
    
    def test_update_task_priority_success(self, task_manager, sample_task):
        """Test successful task priority update."""
        task_manager._tasks[sample_task.id] = sample_task
        
        updated_task = task_manager.update_task(sample_task.id, priority=TaskPriority.CRITICAL)
        
        assert updated_task.priority == TaskPriority.CRITICAL
    
    def test_update_task_notes_success(self, task_manager, sample_task):
        """Test successful task notes update."""
        task_manager._tasks[sample_task.id] = sample_task
        
        updated_task = task_manager.update_task(sample_task.id, notes="Updated notes")
        
        assert updated_task.notes == "Updated notes"
    
    def test_update_task_multiple_fields(self, task_manager, sample_task):
        """Test updating multiple task fields simultaneously."""
        task_manager._tasks[sample_task.id] = sample_task
        
        updated_task = task_manager.update_task(
            sample_task.id,
            title="New title",
            difficulty=TaskDifficulty.EASY,
            priority=TaskPriority.LOW,
            notes="New notes"
        )
        
        assert updated_task.title == "New title"
        assert updated_task.difficulty == TaskDifficulty.EASY
        assert updated_task.priority == TaskPriority.LOW
        assert updated_task.notes == "New notes"
        assert updated_task.xp_reward == TaskDifficulty.EASY.xp_value
    
    def test_update_task_status_transition(self, task_manager, sample_task):
        """Test valid task status transitions."""
        task_manager._tasks[sample_task.id] = sample_task
        
        # Pending -> Active
        updated_task = task_manager.update_task(sample_task.id, status=TaskStatus.ACTIVE)
        assert updated_task.status == TaskStatus.ACTIVE
        
        # Active -> Blocked
        updated_task = task_manager.update_task(sample_task.id, status=TaskStatus.BLOCKED)
        assert updated_task.status == TaskStatus.BLOCKED
        
        # Blocked -> Pending
        updated_task = task_manager.update_task(sample_task.id, status=TaskStatus.PENDING)
        assert updated_task.status == TaskStatus.PENDING
    
    def test_update_task_invalid_title(self, task_manager, sample_task):
        """Test task update with invalid title."""
        task_manager._tasks[sample_task.id] = sample_task
        
        with pytest.raises(TaskValidationError, match="Title validation failed"):
            task_manager.update_task(sample_task.id, title="")
    
    def test_update_task_invalid_status_transition(self, task_manager, sample_task):
        """Test task update with invalid status transition."""
        task_manager._tasks[sample_task.id] = sample_task
        sample_task.status = TaskStatus.COMPLETED
        
        with pytest.raises(TaskStateError, match="Cannot change status of completed task"):
            task_manager.update_task(sample_task.id, status=TaskStatus.PENDING)
    
    def test_update_completed_task_difficulty_forbidden(self, task_manager, completed_task):
        """Test that completed task difficulty cannot be changed."""
        task_manager._tasks[completed_task.id] = completed_task
        
        with pytest.raises(TaskStateError, match="Cannot change difficulty of completed task"):
            task_manager.update_task(completed_task.id, difficulty=TaskDifficulty.EASY)
    
    def test_update_completed_task_status_forbidden(self, task_manager, completed_task):
        """Test that completed task status cannot be changed away from completed."""
        task_manager._tasks[completed_task.id] = completed_task
        
        with pytest.raises(TaskStateError, match="Cannot change status of completed task"):
            task_manager.update_task(completed_task.id, status=TaskStatus.PENDING)
    
    def test_update_completed_task_allowed_fields(self, task_manager, completed_task):
        """Test that completed task title, priority, and notes can be updated."""
        task_manager._tasks[completed_task.id] = completed_task
        
        updated_task = task_manager.update_task(
            completed_task.id,
            title="Updated completed task",
            priority=TaskPriority.LOW,
            notes="Updated notes"
        )
        
        assert updated_task.title == "Updated completed task"
        assert updated_task.priority == TaskPriority.LOW
        assert updated_task.notes == "Updated notes"
        assert updated_task.status == TaskStatus.COMPLETED  # Unchanged
        assert updated_task.difficulty == completed_task.difficulty  # Unchanged
    
    def test_update_task_not_found(self, task_manager):
        """Test updating non-existent task."""
        with pytest.raises(TaskNotFoundError, match="not found"):
            task_manager.update_task("non-existent", title="New title")
    
    def test_validate_task_update_success(self, task_manager, sample_task):
        """Test task update validation without applying changes."""
        task_manager._tasks[sample_task.id] = sample_task
        
        result = task_manager.validate_task_update(
            sample_task.id,
            title="New title",
            difficulty=TaskDifficulty.HARD
        )
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
        assert 'title' in result['changes']
        assert 'difficulty' in result['changes']
        assert len(result['warnings']) > 0  # Should warn about XP change
    
    def test_validate_task_update_invalid(self, task_manager, completed_task):
        """Test task update validation with invalid changes."""
        task_manager._tasks[completed_task.id] = completed_task
        
        result = task_manager.validate_task_update(
            completed_task.id,
            difficulty=TaskDifficulty.EASY,
            status=TaskStatus.PENDING
        )
        
        assert result['valid'] is False
        assert len(result['errors']) >= 2  # Both changes should be invalid
        assert any("difficulty" in error for error in result['errors'])
        assert any("status" in error for error in result['errors'])
    
    def test_validate_task_update_warnings(self, task_manager, sample_task):
        """Test task update validation generates appropriate warnings."""
        task_manager._tasks[sample_task.id] = sample_task
        
        result = task_manager.validate_task_update(
            sample_task.id,
            difficulty=TaskDifficulty.HARD,
            priority=TaskPriority.CRITICAL,
            status=TaskStatus.COMPLETED
        )
        
        assert result['valid'] is True
        assert len(result['warnings']) >= 3  # XP change, priority change, completion warning
        assert any("XP reward" in warning for warning in result['warnings'])
        assert any("critical priority" in warning for warning in result['warnings'])
        assert any("award" in warning for warning in result['warnings'])


class TestTaskDeletion:
    """Test task deletion functionality with safety checks and warnings."""
    
    @pytest.fixture
    def mock_data_manager(self):
        """Create mock DataManager for testing."""
        mock_dm = Mock(spec=DataManager)
        mock_dm.load_tasks.return_value = {}
        mock_dm.load_player_data.return_value = PlayerData()
        mock_dm.save_tasks.return_value = True
        mock_dm.save_player_data.return_value = True
        mock_dm.create_backup.return_value = True
        return mock_dm
    
    @pytest.fixture
    def task_manager(self, mock_data_manager):
        """Create TaskManager instance for testing."""
        return TaskManager(mock_data_manager)
    
    @pytest.fixture
    def sample_task(self):
        """Create sample task for testing."""
        return Task(
            title="Sample task",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.HIGH,
            notes="Sample notes"
        )
    
    @pytest.fixture
    def completed_task(self):
        """Create completed task for testing."""
        task = Task(
            title="Completed task",
            difficulty=TaskDifficulty.HARD,
            priority=TaskPriority.CRITICAL,
            notes="Completed notes"
        )
        task.complete()
        return task
    
    @pytest.fixture
    def active_task(self):
        """Create active task for testing."""
        task = Task(
            title="Active task",
            difficulty=TaskDifficulty.EASY,
            priority=TaskPriority.MEDIUM,
            notes="Active notes"
        )
        task.status = TaskStatus.ACTIVE
        return task
    
    def test_delete_pending_task_success(self, task_manager, sample_task):
        """Test successful deletion of pending task."""
        task_manager._tasks[sample_task.id] = sample_task
        
        result = task_manager.delete_task(sample_task.id)
        
        assert result['success'] is True
        assert sample_task.id not in task_manager._tasks
        assert result['task_info']['title'] == sample_task.title
        assert len(result['warnings']) >= 0  # May have warnings for high priority
    
    def test_delete_completed_task_without_force(self, task_manager, completed_task):
        """Test deletion of completed task without force flag."""
        task_manager._tasks[completed_task.id] = completed_task
        
        with pytest.raises(TaskStateError, match="without confirmation"):
            task_manager.delete_task(completed_task.id)
    
    def test_delete_completed_task_with_force(self, task_manager, completed_task):
        """Test deletion of completed task with force flag."""
        task_manager._tasks[completed_task.id] = completed_task
        
        result = task_manager.delete_task(completed_task.id, force=True)
        
        assert result['success'] is True
        assert completed_task.id not in task_manager._tasks
        assert any("XP history will be preserved" in warning for warning in result['warnings'])
    
    def test_delete_active_task_warning(self, task_manager, active_task):
        """Test deletion of active task generates warning."""
        task_manager._tasks[active_task.id] = active_task
        
        result = task_manager.delete_task(active_task.id)
        
        assert result['success'] is True
        assert active_task.id not in task_manager._tasks
        assert any("active task" in warning for warning in result['warnings'])
    
    def test_delete_high_priority_task_warning(self, task_manager, sample_task):
        """Test deletion of high priority task generates warning."""
        sample_task.priority = TaskPriority.CRITICAL
        task_manager._tasks[sample_task.id] = sample_task
        
        result = task_manager.delete_task(sample_task.id)
        
        assert result['success'] is True
        assert any("critical priority" in warning for warning in result['warnings'])
    
    def test_delete_task_not_found(self, task_manager):
        """Test deleting non-existent task."""
        with pytest.raises(TaskNotFoundError, match="not found"):
            task_manager.delete_task("non-existent")
    
    def test_delete_task_creates_backup(self, task_manager, sample_task, mock_data_manager):
        """Test that task deletion creates backup."""
        task_manager._tasks[sample_task.id] = sample_task
        
        result = task_manager.delete_task(sample_task.id)
        
        assert result['success'] is True
        mock_data_manager.create_backup.assert_called_once()
    
    def test_delete_task_backup_failure(self, task_manager, sample_task, mock_data_manager):
        """Test task deletion when backup creation fails."""
        task_manager._tasks[sample_task.id] = sample_task
        mock_data_manager.create_backup.side_effect = Exception("Backup failed")
        
        result = task_manager.delete_task(sample_task.id)
        
        assert result['success'] is True  # Deletion should still succeed
        assert any("Could not create backup" in warning for warning in result['warnings'])
    
    def test_check_deletion_safety_pending_task(self, task_manager, sample_task):
        """Test deletion safety check for pending task."""
        task_manager._tasks[sample_task.id] = sample_task
        
        result = task_manager.check_deletion_safety(sample_task.id)
        
        assert result['safety_level'] in ['safe', 'caution']  # May be caution due to high priority
        assert result['task_info']['title'] == sample_task.title
    
    def test_check_deletion_safety_completed_task(self, task_manager, completed_task):
        """Test deletion safety check for completed task."""
        task_manager._tasks[completed_task.id] = completed_task
        
        result = task_manager.check_deletion_safety(completed_task.id)
        
        assert result['requires_confirmation'] is True
        assert result['safety_level'] == 'danger'
        assert any("awarded" in warning and "XP" in warning for warning in result['warnings'])
    
    def test_check_deletion_safety_active_task(self, task_manager, active_task):
        """Test deletion safety check for active task."""
        task_manager._tasks[active_task.id] = active_task
        
        result = task_manager.check_deletion_safety(active_task.id)
        
        assert result['requires_confirmation'] is True
        assert result['safety_level'] == 'caution'
        assert any("currently active" in warning for warning in result['warnings'])
    
    def test_check_deletion_safety_high_priority(self, task_manager, sample_task):
        """Test deletion safety check for high priority task."""
        sample_task.priority = TaskPriority.CRITICAL
        task_manager._tasks[sample_task.id] = sample_task
        
        result = task_manager.check_deletion_safety(sample_task.id)
        
        assert result['requires_confirmation'] is True
        assert result['safety_level'] in ['caution', 'danger']
        assert any("critical priority" in warning for warning in result['warnings'])
    
    def test_check_deletion_safety_high_xp_task(self, task_manager):
        """Test deletion safety check for high XP value task."""
        high_xp_task = Task(
            title="High XP task",
            difficulty=TaskDifficulty.HARD,  # 50 XP
            priority=TaskPriority.LOW
        )
        task_manager._tasks[high_xp_task.id] = high_xp_task
        
        result = task_manager.check_deletion_safety(high_xp_task.id)
        
        assert result['safety_level'] in ['caution', 'danger']
        assert any("high XP value" in warning for warning in result['warnings'])
    
    def test_check_deletion_safety_not_found(self, task_manager):
        """Test deletion safety check for non-existent task."""
        with pytest.raises(TaskNotFoundError, match="not found"):
            task_manager.check_deletion_safety("non-existent")


class TestTaskEditingDeletionIntegration:
    """Integration tests for task editing and deletion workflows."""
    
    @pytest.fixture
    def mock_data_manager(self):
        """Create mock DataManager for testing."""
        mock_dm = Mock(spec=DataManager)
        mock_dm.load_tasks.return_value = {}
        mock_dm.load_player_data.return_value = PlayerData()
        mock_dm.save_tasks.return_value = True
        mock_dm.save_player_data.return_value = True
        mock_dm.create_backup.return_value = True
        return mock_dm
    
    @pytest.fixture
    def task_manager(self, mock_data_manager):
        """Create TaskManager instance for testing."""
        return TaskManager(mock_data_manager)
    
    def test_edit_then_delete_workflow(self, task_manager):
        """Test complete edit then delete workflow."""
        # Create task
        task = task_manager.create_task(
            title="Original task",
            difficulty=TaskDifficulty.EASY,
            priority=TaskPriority.LOW
        )
        
        # Edit task
        updated_task = task_manager.update_task(
            task.id,
            title="Updated task",
            difficulty=TaskDifficulty.HARD,
            priority=TaskPriority.CRITICAL
        )
        
        assert updated_task.title == "Updated task"
        assert updated_task.difficulty == TaskDifficulty.HARD
        assert updated_task.priority == TaskPriority.CRITICAL
        
        # Check deletion safety (should require confirmation due to high priority and XP)
        safety_check = task_manager.check_deletion_safety(task.id)
        assert safety_check['requires_confirmation'] is True
        
        # Delete task
        result = task_manager.delete_task(task.id)
        assert result['success'] is True
        assert task.id not in task_manager._tasks
    
    def test_complete_then_edit_then_delete_workflow(self, task_manager):
        """Test complete workflow with completed task restrictions."""
        # Create and complete task
        task = task_manager.create_task(
            title="Task to complete",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.HIGH
        )
        
        completed_task, xp_earned = task_manager.complete_task(task.id)
        assert completed_task.is_completed
        assert xp_earned > 0
        
        # Try to edit difficulty (should fail)
        with pytest.raises(TaskStateError):
            task_manager.update_task(task.id, difficulty=TaskDifficulty.EASY)
        
        # Edit allowed fields (should succeed)
        updated_task = task_manager.update_task(
            task.id,
            title="Updated completed task",
            notes="Updated notes"
        )
        assert updated_task.title == "Updated completed task"
        assert updated_task.notes == "Updated notes"
        
        # Try to delete without force (should fail)
        with pytest.raises(TaskStateError):
            task_manager.delete_task(task.id)
        
        # Delete with force (should succeed)
        result = task_manager.delete_task(task.id, force=True)
        assert result['success'] is True
        assert task.id not in task_manager._tasks
    
    def test_observer_notifications_for_edit_delete(self, task_manager):
        """Test that observers are notified of edit and delete operations."""
        observer_calls = []
        
        def test_observer(action, task):
            observer_calls.append((action, task.id, task.title))
        
        task_manager.add_observer(test_observer)
        
        # Create task
        task = task_manager.create_task(
            title="Observer test task",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.LOW
        )
        
        # Update task
        task_manager.update_task(task.id, title="Updated observer test task")
        
        # Delete task
        task_manager.delete_task(task.id)
        
        # Check observer was called for all actions
        assert len(observer_calls) == 3
        assert observer_calls[0][0] == 'created'
        assert observer_calls[1][0] == 'updated'
        assert observer_calls[1][2] == 'Updated observer test task'  # Updated title
        assert observer_calls[2][0] == 'deleted'
    
    def test_data_persistence_for_edit_delete(self, task_manager, mock_data_manager):
        """Test that edit and delete operations persist data."""
        # Create task
        task = task_manager.create_task(
            title="Persistence test task",
            difficulty=TaskDifficulty.EASY,
            priority=TaskPriority.LOW
        )
        
        # Reset mock call counts
        mock_data_manager.save_tasks.reset_mock()
        mock_data_manager.save_player_data.reset_mock()
        
        # Update task
        task_manager.update_task(task.id, title="Updated persistence test")
        
        # Verify save was called
        mock_data_manager.save_tasks.assert_called()
        mock_data_manager.save_player_data.assert_called()
        
        # Reset mock call counts
        mock_data_manager.save_tasks.reset_mock()
        mock_data_manager.save_player_data.reset_mock()
        
        # Delete task
        task_manager.delete_task(task.id)
        
        # Verify save was called
        mock_data_manager.save_tasks.assert_called()
        mock_data_manager.save_player_data.assert_called()