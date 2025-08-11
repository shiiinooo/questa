"""Tests for Task model."""

import pytest
from datetime import datetime
from src.models.task import Task
from src.models.enums import TaskDifficulty, TaskPriority, TaskStatus


class TestTask:
    """Test Task model."""
    
    def test_task_creation_with_required_fields(self):
        """Test creating a task with required fields."""
        task = Task(
            title="Test Task",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.HIGH
        )
        
        assert task.title == "Test Task"
        assert task.difficulty == TaskDifficulty.MEDIUM
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING
        assert task.notes is None
        assert task.xp_reward == 30  # Medium difficulty XP
        assert isinstance(task.id, str)
        assert len(task.id) > 0
        assert isinstance(task.created_at, datetime)
        assert task.completed_at is None
    
    def test_task_creation_with_all_fields(self):
        """Test creating a task with all fields."""
        created_at = datetime.now()
        task = Task(
            title="Complete Task",
            difficulty=TaskDifficulty.HARD,
            priority=TaskPriority.CRITICAL,
            status=TaskStatus.ACTIVE,
            notes="Important task notes",
            id="custom-id",
            created_at=created_at
        )
        
        assert task.title == "Complete Task"
        assert task.difficulty == TaskDifficulty.HARD
        assert task.priority == TaskPriority.CRITICAL
        assert task.status == TaskStatus.ACTIVE
        assert task.notes == "Important task notes"
        assert task.id == "custom-id"
        assert task.created_at == created_at
        assert task.xp_reward == 50  # Hard difficulty XP
    
    def test_task_title_validation(self):
        """Test task title validation."""
        # Empty title should raise error
        with pytest.raises(ValueError, match="Task title cannot be empty"):
            Task(title="", difficulty=TaskDifficulty.EASY, priority=TaskPriority.LOW)
        
        # Whitespace-only title should raise error
        with pytest.raises(ValueError, match="Task title cannot be empty"):
            Task(title="   ", difficulty=TaskDifficulty.EASY, priority=TaskPriority.LOW)
        
        # Title too long should raise error
        long_title = "x" * 201
        with pytest.raises(ValueError, match="Task title cannot exceed 200 characters"):
            Task(title=long_title, difficulty=TaskDifficulty.EASY, priority=TaskPriority.LOW)
        
        # Title with whitespace should be trimmed
        task = Task(title="  Test Task  ", difficulty=TaskDifficulty.EASY, priority=TaskPriority.LOW)
        assert task.title == "Test Task"
    
    def test_xp_reward_calculation(self):
        """Test XP reward calculation based on difficulty."""
        easy_task = Task("Easy", TaskDifficulty.EASY, TaskPriority.LOW)
        assert easy_task.xp_reward == 15
        
        medium_task = Task("Medium", TaskDifficulty.MEDIUM, TaskPriority.LOW)
        assert medium_task.xp_reward == 30
        
        hard_task = Task("Hard", TaskDifficulty.HARD, TaskPriority.LOW)
        assert hard_task.xp_reward == 50
    
    def test_task_properties(self):
        """Test task status properties."""
        task = Task("Test", TaskDifficulty.EASY, TaskPriority.LOW)
        
        # Initially pending
        assert not task.is_completed
        assert not task.is_active
        assert not task.is_blocked
        
        # Set to active
        task.status = TaskStatus.ACTIVE
        assert not task.is_completed
        assert task.is_active
        assert not task.is_blocked
        
        # Set to blocked
        task.status = TaskStatus.BLOCKED
        assert not task.is_completed
        assert not task.is_active
        assert task.is_blocked
        
        # Set to completed
        task.status = TaskStatus.COMPLETED
        assert task.is_completed
        assert not task.is_active
        assert not task.is_blocked
    
    def test_task_completion(self):
        """Test task completion logic."""
        task = Task("Test", TaskDifficulty.MEDIUM, TaskPriority.LOW)
        
        # Complete the task
        xp_earned = task.complete()
        
        assert task.is_completed
        assert task.status == TaskStatus.COMPLETED
        assert isinstance(task.completed_at, datetime)
        assert xp_earned == 30  # Medium difficulty XP
        
        # Trying to complete again should raise error
        with pytest.raises(ValueError, match="Task is already completed"):
            task.complete()
    
    def test_status_transition_validation(self):
        """Test status transition validation."""
        task = Task("Test", TaskDifficulty.EASY, TaskPriority.LOW)
        
        # Valid transitions from PENDING
        assert task.can_transition_to(TaskStatus.ACTIVE)
        assert task.can_transition_to(TaskStatus.BLOCKED)
        assert task.can_transition_to(TaskStatus.COMPLETED)
        
        # Update to ACTIVE
        task.update_status(TaskStatus.ACTIVE)
        assert task.status == TaskStatus.ACTIVE
        
        # Valid transitions from ACTIVE
        assert task.can_transition_to(TaskStatus.PENDING)
        assert task.can_transition_to(TaskStatus.BLOCKED)
        assert task.can_transition_to(TaskStatus.COMPLETED)
        
        # Complete the task
        task.update_status(TaskStatus.COMPLETED)
        assert task.status == TaskStatus.COMPLETED
        assert isinstance(task.completed_at, datetime)
        
        # No transitions allowed from COMPLETED
        assert not task.can_transition_to(TaskStatus.PENDING)
        assert not task.can_transition_to(TaskStatus.ACTIVE)
        assert not task.can_transition_to(TaskStatus.BLOCKED)
        
        # Trying invalid transition should raise error
        with pytest.raises(ValueError, match="Cannot transition from"):
            task.update_status(TaskStatus.PENDING)
    
    def test_difficulty_update(self):
        """Test updating task difficulty."""
        task = Task("Test", TaskDifficulty.EASY, TaskPriority.LOW)
        assert task.xp_reward == 15
        
        # Update difficulty
        task.update_difficulty(TaskDifficulty.HARD)
        assert task.difficulty == TaskDifficulty.HARD
        assert task.xp_reward == 50
        
        # Complete the task
        task.complete()
        
        # Cannot update difficulty of completed task
        with pytest.raises(ValueError, match="Cannot change difficulty of completed task"):
            task.update_difficulty(TaskDifficulty.MEDIUM)
    
    def test_task_serialization(self):
        """Test task to_dict and from_dict methods."""
        original_task = Task(
            title="Serialization Test",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.HIGH,
            status=TaskStatus.ACTIVE,
            notes="Test notes",
            id="test-id"
        )
        
        # Convert to dict
        task_dict = original_task.to_dict()
        
        expected_keys = {'id', 'title', 'difficulty', 'priority', 'status', 
                        'notes', 'xp_reward', 'created_at', 'completed_at'}
        assert set(task_dict.keys()) == expected_keys
        
        assert task_dict['id'] == "test-id"
        assert task_dict['title'] == "Serialization Test"
        assert task_dict['difficulty'] == "MEDIUM"
        assert task_dict['priority'] == "HIGH"
        assert task_dict['status'] == "ACTIVE"
        assert task_dict['notes'] == "Test notes"
        assert task_dict['xp_reward'] == 30
        assert task_dict['completed_at'] is None
        
        # Convert back from dict
        restored_task = Task.from_dict(task_dict)
        
        assert restored_task.id == original_task.id
        assert restored_task.title == original_task.title
        assert restored_task.difficulty == original_task.difficulty
        assert restored_task.priority == original_task.priority
        assert restored_task.status == original_task.status
        assert restored_task.notes == original_task.notes
        assert restored_task.xp_reward == original_task.xp_reward
        assert restored_task.created_at == original_task.created_at
        assert restored_task.completed_at == original_task.completed_at
    
    def test_completed_task_serialization(self):
        """Test serialization of completed task."""
        task = Task("Test", TaskDifficulty.EASY, TaskPriority.LOW)
        task.complete()
        
        task_dict = task.to_dict()
        assert task_dict['status'] == "COMPLETED"
        assert task_dict['completed_at'] is not None
        
        restored_task = Task.from_dict(task_dict)
        assert restored_task.is_completed
        assert restored_task.completed_at is not None
        assert restored_task.completed_at == task.completed_at