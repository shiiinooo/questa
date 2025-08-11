"""Comprehensive tests for task completion and XP award system workflow."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import tempfile
import shutil
from pathlib import Path

from src.business.task_manager import TaskManager, TaskStateError, TaskNotFoundError
from src.business.xp_calculator import XPCalculator
from src.data.data_manager import DataManager
from src.models.enums import TaskDifficulty, TaskPriority, TaskStatus
from src.models.task import Task
from src.models.player import PlayerData


class TestTaskCompletionWorkflow:
    """Test comprehensive task completion and XP award system workflow."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary directory for test data."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def task_manager(self, temp_data_dir):
        """Create TaskManager with real DataManager for integration testing."""
        data_manager = DataManager(temp_data_dir)
        return TaskManager(data_manager)
    
    def test_basic_task_completion_workflow(self, task_manager):
        """Test basic task completion workflow with XP award.
        
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
        """
        # Create a task
        task = task_manager.create_task(
            title="Implement user authentication",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.HIGH,
            notes="JWT tokens and bcrypt hashing"
        )
        
        # Verify initial state
        assert not task.is_completed
        assert task.completed_at is None
        assert task.status == TaskStatus.PENDING
        
        # Get initial player data
        initial_player_data = task_manager.get_player_data()
        initial_xp = initial_player_data.total_xp
        initial_tasks_completed = initial_player_data.tasks_completed
        initial_level = initial_player_data.level
        
        # Complete the task
        completed_task, xp_earned = task_manager.complete_task(task.id)
        
        # Verify task completion (Requirement 3.1)
        assert completed_task.is_completed
        assert completed_task.status == TaskStatus.COMPLETED
        assert completed_task.completed_at is not None
        assert isinstance(completed_task.completed_at, datetime)
        
        # Verify XP award (Requirement 3.2)
        assert xp_earned > 0
        assert xp_earned >= TaskDifficulty.MEDIUM.xp_value  # At least base XP
        
        # Verify player data updates (Requirement 3.4)
        updated_player_data = task_manager.get_player_data()
        assert updated_player_data.total_xp == initial_xp + xp_earned
        assert updated_player_data.tasks_completed == initial_tasks_completed + 1
        assert updated_player_data.medium_tasks_completed == 1
        assert updated_player_data.current_streak == 1
        assert updated_player_data.last_activity is not None
        
        # Verify statistics tracking (Requirement 3.6)
        stats = updated_player_data.get_statistics()
        assert stats['tasks_completed'] == 1
        assert stats['total_xp'] == xp_earned
        assert stats['medium_tasks_completed'] == 1
        assert stats['current_streak'] == 1
        
        # Verify level progression if applicable
        if updated_player_data.level > initial_level:
            assert updated_player_data.level == initial_level + 1
    
    def test_duplicate_completion_prevention(self, task_manager):
        """Test duplicate completion prevention and validation.
        
        Requirements: 3.7
        """
        # Create and complete a task
        task = task_manager.create_task(
            title="Test task",
            difficulty=TaskDifficulty.EASY,
            priority=TaskPriority.LOW
        )
        
        # Complete the task first time
        completed_task, xp_earned = task_manager.complete_task(task.id)
        assert completed_task.is_completed
        
        # Get player data after first completion
        player_data_after_first = task_manager.get_player_data()
        first_completion_xp = player_data_after_first.total_xp
        first_completion_count = player_data_after_first.tasks_completed
        
        # Attempt to complete the same task again (should fail)
        with pytest.raises(TaskStateError, match="already completed"):
            task_manager.complete_task(task.id)
        
        # Verify player data unchanged after failed duplicate completion
        player_data_after_duplicate = task_manager.get_player_data()
        assert player_data_after_duplicate.total_xp == first_completion_xp
        assert player_data_after_duplicate.tasks_completed == first_completion_count
    
    def test_completion_timestamp_recording(self, task_manager):
        """Test completion timestamp recording accuracy.
        
        Requirements: 3.3
        """
        # Create a task
        task = task_manager.create_task(
            title="Timestamp test task",
            difficulty=TaskDifficulty.HARD,
            priority=TaskPriority.CRITICAL
        )
        
        # Record time before completion
        before_completion = datetime.now()
        
        # Complete the task
        completed_task, _ = task_manager.complete_task(task.id)
        
        # Record time after completion
        after_completion = datetime.now()
        
        # Verify completion timestamp is within expected range
        assert completed_task.completed_at is not None
        assert before_completion <= completed_task.completed_at <= after_completion
        
        # Verify timestamp persists after reload
        reloaded_task = task_manager.get_task(task.id)
        assert reloaded_task.completed_at == completed_task.completed_at
    
    def test_xp_calculation_with_bonuses(self, task_manager):
        """Test XP calculation with various bonuses.
        
        Requirements: 3.2
        """
        # First, complete 3 tasks to build up a streak
        for i in range(3):
            task = task_manager.create_task(
                title=f"Streak builder {i+1}",
                difficulty=TaskDifficulty.EASY,
                priority=TaskPriority.LOW
            )
            task_manager.complete_task(task.id)
        
        # Verify we have a streak of 3
        player_data = task_manager.get_player_data()
        assert player_data.current_streak == 3
        
        # Now create a task to test the streak bonus
        bonus_task = task_manager.create_task(
            title="Streak bonus test task",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.HIGH
        )
        
        # Preview XP - should have streak bonus
        xp_preview = task_manager.preview_task_xp(bonus_task.id)
        
        # Verify base XP is correct
        assert xp_preview['base_xp'] == TaskDifficulty.MEDIUM.xp_value
        
        # Verify priority bonus for HIGH priority
        assert xp_preview['priority_multiplier'] == 1.1
        
        # Verify streak bonus is applied (streak of 3 should give 1.1x multiplier)
        assert xp_preview['streak_multiplier'] == 1.1
        
        # Complete the task and verify XP earned matches preview
        completed_task, xp_earned = task_manager.complete_task(bonus_task.id)
        assert xp_earned == xp_preview['total_xp']
        
        # Verify the XP includes bonuses (should be more than base XP)
        base_xp = TaskDifficulty.MEDIUM.xp_value
        assert xp_earned > base_xp
        
        # Test that streak continues to build
        final_player_data = task_manager.get_player_data()
        assert final_player_data.current_streak == 4
    
    def test_level_progression_tracking(self, task_manager):
        """Test player level calculation and progression tracking.
        
        Requirements: 3.4, 3.6
        """
        # Create enough tasks to trigger level up
        tasks = []
        for i in range(5):
            task = task_manager.create_task(
                title=f"Level up task {i+1}",
                difficulty=TaskDifficulty.HARD,  # 50 XP each
                priority=TaskPriority.CRITICAL
            )
            tasks.append(task)
        
        initial_player_data = task_manager.get_player_data()
        initial_level = initial_player_data.level
        
        # Complete tasks and track level progression
        for i, task in enumerate(tasks):
            completed_task, xp_earned = task_manager.complete_task(task.id)
            
            player_data = task_manager.get_player_data()
            
            # Verify XP accumulation
            expected_min_xp = (i + 1) * TaskDifficulty.HARD.xp_value
            assert player_data.total_xp >= expected_min_xp
            
            # Verify level calculation consistency
            calculated_level = XPCalculator.calculate_level(player_data.total_xp)
            assert player_data.level == calculated_level
            
            # Verify level progression properties
            assert player_data.xp_for_current_level <= player_data.total_xp
            assert player_data.xp_for_next_level > player_data.total_xp
            assert player_data.xp_to_next_level >= 0
            assert 0.0 <= player_data.level_progress <= 1.0
        
        # Verify final level is higher than initial (should level up with 250+ XP)
        final_player_data = task_manager.get_player_data()
        assert final_player_data.level >= initial_level
        if final_player_data.total_xp >= 100:  # Level 2 threshold
            assert final_player_data.level > initial_level
    
    def test_statistics_tracking_comprehensive(self, task_manager):
        """Test comprehensive statistics tracking during completion.
        
        Requirements: 3.6
        """
        # Create tasks of different difficulties
        easy_task = task_manager.create_task(
            "Easy task", TaskDifficulty.EASY, TaskPriority.LOW
        )
        medium_task = task_manager.create_task(
            "Medium task", TaskDifficulty.MEDIUM, TaskPriority.MEDIUM
        )
        hard_task = task_manager.create_task(
            "Hard task", TaskDifficulty.HARD, TaskPriority.HIGH
        )
        
        # Complete tasks in sequence
        task_manager.complete_task(easy_task.id)
        task_manager.complete_task(medium_task.id)
        task_manager.complete_task(hard_task.id)
        
        # Verify comprehensive statistics
        player_data = task_manager.get_player_data()
        stats = player_data.get_statistics()
        
        # Verify task completion counts
        assert stats['tasks_completed'] == 3
        assert stats['easy_tasks_completed'] == 1
        assert stats['medium_tasks_completed'] == 1
        assert stats['hard_tasks_completed'] == 1
        
        # Verify XP tracking
        expected_min_xp = 15 + 30 + 50  # Base XP for each difficulty
        assert stats['total_xp'] >= expected_min_xp
        
        # Verify streak tracking
        assert stats['current_streak'] == 3
        
        # Verify level progression
        assert stats['level'] >= 1
        assert stats['xp_to_next_level'] >= 0
        assert 0.0 <= stats['level_progress'] <= 1.0
        
        # Verify last activity timestamp
        assert stats['last_activity'] is not None
    
    def test_completion_with_different_task_states(self, task_manager):
        """Test task completion from different initial states.
        
        Requirements: 3.1
        """
        # Test completion from PENDING state
        pending_task = task_manager.create_task(
            "Pending task", TaskDifficulty.EASY, TaskPriority.LOW
        )
        assert pending_task.status == TaskStatus.PENDING
        
        completed_pending, _ = task_manager.complete_task(pending_task.id)
        assert completed_pending.status == TaskStatus.COMPLETED
        
        # Test completion from ACTIVE state
        active_task = task_manager.create_task(
            "Active task", TaskDifficulty.MEDIUM, TaskPriority.MEDIUM
        )
        task_manager.update_task(active_task.id, status=TaskStatus.ACTIVE)
        assert task_manager.get_task(active_task.id).status == TaskStatus.ACTIVE
        
        completed_active, _ = task_manager.complete_task(active_task.id)
        assert completed_active.status == TaskStatus.COMPLETED
        
        # Test completion from BLOCKED state
        blocked_task = task_manager.create_task(
            "Blocked task", TaskDifficulty.HARD, TaskPriority.HIGH
        )
        task_manager.update_task(blocked_task.id, status=TaskStatus.BLOCKED)
        assert task_manager.get_task(blocked_task.id).status == TaskStatus.BLOCKED
        
        completed_blocked, _ = task_manager.complete_task(blocked_task.id)
        assert completed_blocked.status == TaskStatus.COMPLETED
    
    def test_completion_error_handling(self, task_manager):
        """Test error handling in completion workflow.
        
        Requirements: 3.7
        """
        # Test completing non-existent task
        with pytest.raises(TaskNotFoundError):
            task_manager.complete_task("non-existent-task-id")
        
        # Test completing already completed task
        task = task_manager.create_task(
            "Test task", TaskDifficulty.EASY, TaskPriority.LOW
        )
        task_manager.complete_task(task.id)
        
        with pytest.raises(TaskStateError, match="already completed"):
            task_manager.complete_task(task.id)
    
    def test_completion_data_persistence(self, task_manager, temp_data_dir):
        """Test that completion data persists across sessions.
        
        Requirements: 3.3, 3.4
        """
        # Create and complete a task
        task = task_manager.create_task(
            "Persistent task", TaskDifficulty.MEDIUM, TaskPriority.HIGH
        )
        completed_task, xp_earned = task_manager.complete_task(task.id)
        
        # Get completion data
        completion_time = completed_task.completed_at
        player_xp = task_manager.get_player_data().total_xp
        
        # Create new TaskManager instance (simulate app restart)
        new_data_manager = DataManager(temp_data_dir)
        new_task_manager = TaskManager(new_data_manager)
        
        # Verify task completion persisted
        loaded_task = new_task_manager.get_task(task.id)
        assert loaded_task.is_completed
        assert loaded_task.completed_at == completion_time
        
        # Verify player data persisted
        loaded_player_data = new_task_manager.get_player_data()
        assert loaded_player_data.total_xp == player_xp
        assert loaded_player_data.tasks_completed == 1
    
    def test_visual_feedback_confirmation(self, task_manager):
        """Test visual feedback confirmation through observer pattern.
        
        Requirements: 3.5
        """
        observer_calls = []
        
        def completion_observer(action, task):
            observer_calls.append((action, task.id, task.status))
        
        task_manager.add_observer(completion_observer)
        
        # Create and complete a task
        task = task_manager.create_task(
            "Observer test task", TaskDifficulty.EASY, TaskPriority.LOW
        )
        task_manager.complete_task(task.id)
        
        # Verify observer was called for creation and completion
        assert len(observer_calls) >= 2
        
        # Find completion notification
        completion_calls = [call for call in observer_calls if call[0] == 'completed']
        assert len(completion_calls) == 1
        
        action, task_id, status = completion_calls[0]
        assert action == 'completed'
        assert task_id == task.id
        assert status == TaskStatus.COMPLETED
    
    def test_xp_award_edge_cases(self, task_manager):
        """Test XP award system edge cases.
        
        Requirements: 3.2
        """
        # Test minimum XP award (Easy task, no bonuses)
        easy_task = task_manager.create_task(
            "Minimum XP task", TaskDifficulty.EASY, TaskPriority.LOW
        )
        
        # Complete on different day to avoid daily bonus
        with patch('src.models.task.datetime') as mock_datetime:
            yesterday = datetime.now() - timedelta(days=1)
            mock_datetime.now.return_value = yesterday
            easy_task.created_at = yesterday
        
        completed_easy, xp_earned = task_manager.complete_task(easy_task.id)
        assert xp_earned >= TaskDifficulty.EASY.xp_value  # At least base XP
        
        # Test maximum XP award (Hard task, high priority, with streak)
        # First build up streak
        for i in range(3):
            streak_task = task_manager.create_task(
                f"Streak builder {i}", TaskDifficulty.EASY, TaskPriority.LOW
            )
            task_manager.complete_task(streak_task.id)
        
        # Now complete high-value task
        hard_task = task_manager.create_task(
            "Maximum XP task", TaskDifficulty.HARD, TaskPriority.CRITICAL
        )
        completed_hard, max_xp_earned = task_manager.complete_task(hard_task.id)
        
        # Should earn significantly more than base XP due to bonuses
        assert max_xp_earned > TaskDifficulty.HARD.xp_value
        
        # Verify XP preview matches actual award
        # Create another similar task to test preview
        preview_task = task_manager.create_task(
            "Preview test task", TaskDifficulty.HARD, TaskPriority.CRITICAL
        )
        preview = task_manager.preview_task_xp(preview_task.id)
        completed_preview, preview_xp_earned = task_manager.complete_task(preview_task.id)
        
        # XP should match preview (allowing for small differences due to timing)
        assert abs(preview_xp_earned - preview['total_xp']) <= 1