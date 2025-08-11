"""Unit tests for TaskManager with comprehensive CRUD and business logic scenarios."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import uuid

from src.business.task_manager import (
    TaskManager, TaskManagerError, TaskNotFoundError, TaskStateError
)
from src.business.task_validator import TaskValidationError
from src.data.data_manager import DataManager, DataPersistenceError
from src.models.enums import TaskDifficulty, TaskPriority, TaskStatus
from src.models.task import Task
from src.models.player import PlayerData


class TestTaskManager:
    """Test TaskManager CRUD operations and business logic."""
    
    @pytest.fixture
    def mock_data_manager(self):
        """Create mock DataManager for testing."""
        mock_dm = Mock(spec=DataManager)
        mock_dm.load_tasks.return_value = {}
        mock_dm.load_player_data.return_value = PlayerData()
        mock_dm.save_tasks.return_value = True
        mock_dm.save_player_data.return_value = True
        return mock_dm
    
    @pytest.fixture
    def task_manager(self, mock_data_manager):
        """Create TaskManager instance for testing."""
        return TaskManager(mock_data_manager)
    
    @pytest.fixture
    def sample_task(self):
        """Create sample task for testing."""
        return Task(
            title="Test task",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.HIGH,
            notes="Test notes"
        )
    
    def test_init_loads_data(self, mock_data_manager):
        """Test TaskManager initialization loads data."""
        mock_tasks = {"task1": Mock()}
        mock_player = PlayerData(total_xp=100)
        
        mock_data_manager.load_tasks.return_value = mock_tasks
        mock_data_manager.load_player_data.return_value = mock_player
        
        tm = TaskManager(mock_data_manager)
        
        assert tm._tasks == mock_tasks
        assert tm._player_data.total_xp == 100
        mock_data_manager.load_tasks.assert_called_once()
        mock_data_manager.load_player_data.assert_called_once()
    
    def test_init_handles_load_failure(self, mock_data_manager):
        """Test TaskManager initialization handles data load failures gracefully."""
        mock_data_manager.load_tasks.side_effect = Exception("Load failed")
        
        tm = TaskManager(mock_data_manager)
        
        # Should continue with empty data
        assert tm._tasks == {}
        assert isinstance(tm._player_data, PlayerData)
    
    def test_create_task_success(self, task_manager, mock_data_manager):
        """Test successful task creation."""
        task = task_manager.create_task(
            title="New task",
            difficulty=TaskDifficulty.EASY,
            priority=TaskPriority.LOW,
            notes="Task notes"
        )
        
        assert task.title == "New task"
        assert task.difficulty == TaskDifficulty.EASY
        assert task.priority == TaskPriority.LOW
        assert task.notes == "Task notes"
        assert task.status == TaskStatus.PENDING
        assert task.id in task_manager._tasks
        
        mock_data_manager.save_tasks.assert_called_once()
        mock_data_manager.save_player_data.assert_called_once()
    
    def test_create_task_with_custom_id(self, task_manager):
        """Test task creation with custom ID."""
        custom_id = "custom-task-id"
        
        task = task_manager.create_task(
            title="Custom ID task",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.MEDIUM,
            task_id=custom_id
        )
        
        assert task.id == custom_id
        assert custom_id in task_manager._tasks
    
    def test_create_task_duplicate_id(self, task_manager):
        """Test task creation with duplicate ID fails."""
        task_id = "duplicate-id"
        
        # Create first task
        task_manager.create_task(
            title="First task",
            difficulty=TaskDifficulty.EASY,
            priority=TaskPriority.LOW,
            task_id=task_id
        )
        
        # Try to create second task with same ID
        with pytest.raises(TaskManagerError, match="already exists"):
            task_manager.create_task(
                title="Second task",
                difficulty=TaskDifficulty.MEDIUM,
                priority=TaskPriority.HIGH,
                task_id=task_id
            )
    
    def test_create_task_validation_error(self, task_manager):
        """Test task creation with validation errors."""
        with pytest.raises(TaskValidationError):
            task_manager.create_task(
                title="",  # Empty title should fail validation
                difficulty=TaskDifficulty.EASY,
                priority=TaskPriority.LOW
            )
    
    def test_create_task_save_failure(self, task_manager, mock_data_manager):
        """Test task creation handles save failures."""
        mock_data_manager.save_tasks.side_effect = DataPersistenceError("Save failed")
        
        with pytest.raises(TaskManagerError, match="Failed to save data"):
            task_manager.create_task(
                title="Test task",
                difficulty=TaskDifficulty.EASY,
                priority=TaskPriority.LOW
            )
    
    def test_get_task_success(self, task_manager, sample_task):
        """Test successful task retrieval."""
        task_manager._tasks[sample_task.id] = sample_task
        
        retrieved_task = task_manager.get_task(sample_task.id)
        assert retrieved_task == sample_task
    
    def test_get_task_not_found(self, task_manager):
        """Test task retrieval with non-existent ID."""
        with pytest.raises(TaskNotFoundError, match="not found"):
            task_manager.get_task("non-existent-id")
    
    def test_get_tasks_no_filter(self, task_manager):
        """Test getting all tasks without filters."""
        task1 = Task("Task 1", TaskDifficulty.EASY, TaskPriority.LOW)
        task2 = Task("Task 2", TaskDifficulty.HARD, TaskPriority.HIGH)
        
        task_manager._tasks[task1.id] = task1
        task_manager._tasks[task2.id] = task2
        
        tasks = task_manager.get_tasks()
        assert len(tasks) == 2
        assert task1 in tasks
        assert task2 in tasks
    
    def test_get_tasks_status_filter(self, task_manager):
        """Test getting tasks with status filter."""
        task1 = Task("Task 1", TaskDifficulty.EASY, TaskPriority.LOW)
        task2 = Task("Task 2", TaskDifficulty.HARD, TaskPriority.HIGH)
        task2.status = TaskStatus.COMPLETED
        
        task_manager._tasks[task1.id] = task1
        task_manager._tasks[task2.id] = task2
        
        pending_tasks = task_manager.get_tasks(status_filter=TaskStatus.PENDING)
        assert len(pending_tasks) == 1
        assert task1 in pending_tasks
        
        completed_tasks = task_manager.get_tasks(status_filter=TaskStatus.COMPLETED)
        assert len(completed_tasks) == 1
        assert task2 in completed_tasks
    
    def test_get_tasks_multiple_filters(self, task_manager):
        """Test getting tasks with multiple filters."""
        task1 = Task("Task 1", TaskDifficulty.EASY, TaskPriority.LOW)
        task2 = Task("Task 2", TaskDifficulty.EASY, TaskPriority.HIGH)
        task3 = Task("Task 3", TaskDifficulty.HARD, TaskPriority.LOW)
        
        task_manager._tasks[task1.id] = task1
        task_manager._tasks[task2.id] = task2
        task_manager._tasks[task3.id] = task3
        
        filtered_tasks = task_manager.get_tasks(
            difficulty_filter=TaskDifficulty.EASY,
            priority_filter=TaskPriority.LOW
        )
        
        assert len(filtered_tasks) == 1
        assert task1 in filtered_tasks
    
    def test_get_tasks_sorting(self, task_manager):
        """Test task sorting functionality."""
        # Create tasks with different creation times
        task1 = Task("A Task", TaskDifficulty.EASY, TaskPriority.LOW)
        task2 = Task("B Task", TaskDifficulty.MEDIUM, TaskPriority.HIGH)
        task3 = Task("C Task", TaskDifficulty.HARD, TaskPriority.CRITICAL)
        
        task_manager._tasks[task1.id] = task1
        task_manager._tasks[task2.id] = task2
        task_manager._tasks[task3.id] = task3
        
        # Test title sorting
        tasks_by_title = task_manager.get_tasks(sort_by='title', reverse=False)
        assert tasks_by_title[0].title == "A Task"
        assert tasks_by_title[1].title == "B Task"
        assert tasks_by_title[2].title == "C Task"
        
        # Test difficulty sorting
        tasks_by_difficulty = task_manager.get_tasks(sort_by='difficulty', reverse=False)
        assert tasks_by_difficulty[0].difficulty == TaskDifficulty.EASY
        assert tasks_by_difficulty[1].difficulty == TaskDifficulty.MEDIUM
        assert tasks_by_difficulty[2].difficulty == TaskDifficulty.HARD
    
    def test_update_task_success(self, task_manager, sample_task):
        """Test successful task update."""
        task_manager._tasks[sample_task.id] = sample_task
        
        updated_task = task_manager.update_task(
            sample_task.id,
            title="Updated title",
            priority=TaskPriority.CRITICAL
        )
        
        assert updated_task.title == "Updated title"
        assert updated_task.priority == TaskPriority.CRITICAL
        assert updated_task.difficulty == sample_task.difficulty  # Unchanged
    
    def test_update_task_not_found(self, task_manager):
        """Test task update with non-existent ID."""
        with pytest.raises(TaskNotFoundError):
            task_manager.update_task("non-existent", title="New title")
    
    def test_update_task_validation_error(self, task_manager, sample_task):
        """Test task update with validation errors."""
        task_manager._tasks[sample_task.id] = sample_task
        
        with pytest.raises(TaskValidationError):
            task_manager.update_task(sample_task.id, title="")  # Empty title
    
    def test_complete_task_success(self, task_manager, sample_task):
        """Test successful task completion."""
        task_manager._tasks[sample_task.id] = sample_task
        
        completed_task, xp_earned = task_manager.complete_task(sample_task.id)
        
        assert completed_task.is_completed
        assert completed_task.completed_at is not None
        assert xp_earned > 0
        assert task_manager._player_data.tasks_completed == 1
        assert task_manager._player_data.total_xp == xp_earned
    
    def test_complete_task_already_completed(self, task_manager, sample_task):
        """Test completing already completed task."""
        sample_task.status = TaskStatus.COMPLETED
        task_manager._tasks[sample_task.id] = sample_task
        
        with pytest.raises(TaskStateError, match="already completed"):
            task_manager.complete_task(sample_task.id)
    
    def test_complete_task_not_found(self, task_manager):
        """Test completing non-existent task."""
        with pytest.raises(TaskNotFoundError):
            task_manager.complete_task("non-existent")
    
    def test_delete_task_success(self, task_manager, sample_task):
        """Test successful task deletion."""
        task_manager._tasks[sample_task.id] = sample_task
        
        result = task_manager.delete_task(sample_task.id)
        
        assert result['success'] is True
        assert sample_task.id not in task_manager._tasks
    
    def test_delete_completed_task_without_force(self, task_manager, sample_task):
        """Test deleting completed task without force flag."""
        sample_task.status = TaskStatus.COMPLETED
        task_manager._tasks[sample_task.id] = sample_task
        
        with pytest.raises(TaskStateError, match="without confirmation"):
            task_manager.delete_task(sample_task.id)
    
    def test_delete_completed_task_with_force(self, task_manager, sample_task):
        """Test deleting completed task with force flag."""
        sample_task.status = TaskStatus.COMPLETED
        task_manager._tasks[sample_task.id] = sample_task
        
        result = task_manager.delete_task(sample_task.id, force=True)
        
        assert result['success'] is True
        assert sample_task.id not in task_manager._tasks
    
    def test_delete_task_not_found(self, task_manager):
        """Test deleting non-existent task."""
        with pytest.raises(TaskNotFoundError):
            task_manager.delete_task("non-existent")
    
    def test_get_task_count(self, task_manager):
        """Test task count statistics."""
        task1 = Task("Task 1", TaskDifficulty.EASY, TaskPriority.LOW)
        task2 = Task("Task 2", TaskDifficulty.MEDIUM, TaskPriority.HIGH)
        task2.status = TaskStatus.COMPLETED
        task3 = Task("Task 3", TaskDifficulty.HARD, TaskPriority.CRITICAL)
        task3.status = TaskStatus.ACTIVE
        
        task_manager._tasks[task1.id] = task1
        task_manager._tasks[task2.id] = task2
        task_manager._tasks[task3.id] = task3
        
        counts = task_manager.get_task_count()
        
        assert counts['total'] == 3
        assert counts['pending'] == 1
        assert counts['completed'] == 1
        assert counts['active'] == 1
        assert counts['blocked'] == 0
    
    def test_get_player_data(self, task_manager):
        """Test getting player data."""
        task_manager._player_data.total_xp = 150
        task_manager._player_data.tasks_completed = 5
        
        player_data = task_manager.get_player_data()
        
        assert player_data.total_xp == 150
        assert player_data.tasks_completed == 5
    
    def test_preview_task_xp(self, task_manager, sample_task):
        """Test XP preview for task completion."""
        task_manager._tasks[sample_task.id] = sample_task
        
        preview = task_manager.preview_task_xp(sample_task.id)
        
        assert 'base_xp' in preview
        assert 'total_xp' in preview
        assert 'breakdown' in preview
        assert preview['base_xp'] == sample_task.difficulty.xp_value
    
    def test_bulk_update_status(self, task_manager):
        """Test bulk status update."""
        task1 = Task("Task 1", TaskDifficulty.EASY, TaskPriority.LOW)
        task2 = Task("Task 2", TaskDifficulty.MEDIUM, TaskPriority.HIGH)
        task3 = Task("Task 3", TaskDifficulty.HARD, TaskPriority.CRITICAL)
        
        task_manager._tasks[task1.id] = task1
        task_manager._tasks[task2.id] = task2
        task_manager._tasks[task3.id] = task3
        
        task_ids = [task1.id, task2.id, task3.id]
        updated_tasks = task_manager.bulk_update_status(task_ids, TaskStatus.ACTIVE)
        
        assert len(updated_tasks) == 3
        for task in updated_tasks:
            assert task.status == TaskStatus.ACTIVE
    
    def test_bulk_update_status_partial_failure(self, task_manager):
        """Test bulk status update with some failures."""
        task1 = Task("Task 1", TaskDifficulty.EASY, TaskPriority.LOW)
        task2 = Task("Task 2", TaskDifficulty.MEDIUM, TaskPriority.HIGH)
        task2.status = TaskStatus.COMPLETED  # Cannot transition from completed
        
        task_manager._tasks[task1.id] = task1
        task_manager._tasks[task2.id] = task2
        
        task_ids = [task1.id, task2.id, "non-existent"]
        updated_tasks = task_manager.bulk_update_status(task_ids, TaskStatus.ACTIVE)
        
        # Only task1 should be updated successfully
        assert len(updated_tasks) == 1
        assert updated_tasks[0].id == task1.id
        assert updated_tasks[0].status == TaskStatus.ACTIVE
    
    def test_search_tasks(self, task_manager):
        """Test task search functionality."""
        task1 = Task("Implement authentication", TaskDifficulty.EASY, TaskPriority.LOW)
        task1.notes = "JWT tokens"
        task2 = Task("Fix bug in login", TaskDifficulty.MEDIUM, TaskPriority.HIGH)
        task2.notes = "Password validation"
        task3 = Task("Add user dashboard", TaskDifficulty.HARD, TaskPriority.CRITICAL)
        
        task_manager._tasks[task1.id] = task1
        task_manager._tasks[task2.id] = task2
        task_manager._tasks[task3.id] = task3
        
        # Search by title
        results = task_manager.search_tasks("authentication")
        assert len(results) == 1
        assert task1 in results
        
        # Search by notes
        results = task_manager.search_tasks("password")
        assert len(results) == 1
        assert task2 in results
        
        # Search with no matches
        results = task_manager.search_tasks("nonexistent")
        assert len(results) == 0
        
        # Empty search
        results = task_manager.search_tasks("")
        assert len(results) == 0
    
    def test_observer_pattern(self, task_manager):
        """Test observer pattern for task changes."""
        observer_calls = []
        
        def test_observer(action, task):
            observer_calls.append((action, task.id))
        
        task_manager.add_observer(test_observer)
        
        # Create task
        task = task_manager.create_task(
            "Test task", TaskDifficulty.EASY, TaskPriority.LOW
        )
        
        # Update task
        task_manager.update_task(task.id, title="Updated task")
        
        # Complete task
        task_manager.complete_task(task.id)
        
        # Delete task
        task_manager.delete_task(task.id, force=True)
        
        # Check observer was called for all actions
        assert len(observer_calls) == 4
        assert observer_calls[0] == ('created', task.id)
        assert observer_calls[1] == ('updated', task.id)
        assert observer_calls[2] == ('completed', task.id)
        assert observer_calls[3] == ('deleted', task.id)
        
        # Remove observer
        task_manager.remove_observer(test_observer)
        
        # Create another task - observer should not be called
        task2 = task_manager.create_task(
            "Another task", TaskDifficulty.MEDIUM, TaskPriority.HIGH
        )
        
        # Observer calls should remain the same
        assert len(observer_calls) == 4
    
    def test_observer_exception_handling(self, task_manager):
        """Test that observer exceptions don't break task operations."""
        def failing_observer(action, task):
            raise Exception("Observer failed")
        
        task_manager.add_observer(failing_observer)
        
        # Task creation should still succeed despite observer failure
        task = task_manager.create_task(
            "Test task", TaskDifficulty.EASY, TaskPriority.LOW
        )
        
        assert task.id in task_manager._tasks