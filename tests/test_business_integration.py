"""Integration tests for business logic layer components working together."""

import pytest
from unittest.mock import Mock
from pathlib import Path
import tempfile
import shutil

from src.business.task_manager import TaskManager
from src.business.task_validator import TaskValidator
from src.business.xp_calculator import XPCalculator
from src.data.data_manager import DataManager
from src.models.enums import TaskDifficulty, TaskPriority, TaskStatus
from src.models.task import Task
from src.models.player import PlayerData


class TestBusinessLogicIntegration:
    """Test integration between TaskManager, TaskValidator, and XPCalculator."""
    
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
    
    def test_complete_task_workflow(self, task_manager):
        """Test complete workflow: create -> update -> complete -> delete task."""
        # Create task
        task = task_manager.create_task(
            title="Implement authentication system",
            difficulty=TaskDifficulty.HARD,
            priority=TaskPriority.CRITICAL,
            notes="Use JWT tokens and bcrypt for password hashing"
        )
        
        assert task.title == "Implement authentication system"
        assert task.difficulty == TaskDifficulty.HARD
        assert task.priority == TaskPriority.CRITICAL
        assert task.status == TaskStatus.PENDING
        assert task.xp_reward == 50  # Hard difficulty XP
        
        # Update task
        updated_task = task_manager.update_task(
            task.id,
            title="Implement secure authentication system",
            priority=TaskPriority.HIGH,
            notes="Use JWT tokens, bcrypt, and add 2FA support"
        )
        
        assert updated_task.title == "Implement secure authentication system"
        assert updated_task.priority == TaskPriority.HIGH
        assert updated_task.difficulty == TaskDifficulty.HARD  # Unchanged
        assert updated_task.xp_reward == 50  # Still hard difficulty
        
        # Preview XP before completion
        xp_preview = task_manager.preview_task_xp(task.id)
        assert xp_preview['base_xp'] == 50
        assert xp_preview['priority_multiplier'] == 1.1  # High priority bonus
        
        # Complete task
        completed_task, xp_earned = task_manager.complete_task(task.id)
        
        assert completed_task.is_completed
        assert completed_task.completed_at is not None
        assert xp_earned >= 50  # At least base XP, possibly more with bonuses
        
        # Check player data was updated
        player_data = task_manager.get_player_data()
        assert player_data.total_xp == xp_earned
        assert player_data.tasks_completed == 1
        assert player_data.hard_tasks_completed == 1
        
        # Try to update completed task (should have restrictions)
        with pytest.raises(Exception):  # Should fail due to validation
            task_manager.update_task(task.id, difficulty=TaskDifficulty.EASY)
        
        # Delete completed task (requires force)
        with pytest.raises(Exception):  # Should fail without force
            task_manager.delete_task(task.id)
        
        # Delete with force should succeed
        result = task_manager.delete_task(task.id, force=True)
        assert result['success'] is True
        
        # Task should be gone
        with pytest.raises(Exception):
            task_manager.get_task(task.id)
    
    def test_xp_calculation_integration(self, task_manager):
        """Test XP calculation integration with task completion."""
        # Create multiple tasks to build up streak
        tasks = []
        for i in range(3):
            task = task_manager.create_task(
                title=f"Task {i+1}",
                difficulty=TaskDifficulty.MEDIUM,
                priority=TaskPriority.HIGH
            )
            tasks.append(task)
        
        total_xp_earned = 0
        
        # Complete tasks one by one to build streak
        for i, task in enumerate(tasks):
            completed_task, xp_earned = task_manager.complete_task(task.id)
            total_xp_earned += xp_earned
            
            player_data = task_manager.get_player_data()
            assert player_data.tasks_completed == i + 1
            assert player_data.current_streak == i + 1
            assert player_data.total_xp == total_xp_earned
            
            # Later tasks should earn more XP due to streak bonus
            if i > 0:
                # Should have streak bonus after first task
                assert xp_earned > 30  # Base XP for medium difficulty
    
    def test_validation_integration(self, task_manager):
        """Test validation integration across all operations."""
        # Test creation validation
        with pytest.raises(Exception):
            task_manager.create_task(
                title="",  # Empty title should fail
                difficulty=TaskDifficulty.EASY,
                priority=TaskPriority.LOW
            )
        
        # Create valid task
        task = task_manager.create_task(
            title="Valid task",
            difficulty=TaskDifficulty.EASY,
            priority=TaskPriority.LOW
        )
        
        # Test update validation
        with pytest.raises(Exception):
            task_manager.update_task(
                task.id,
                title="A" * 201  # Too long title should fail
            )
        
        # Test status transition validation
        task_manager.update_task(task.id, status=TaskStatus.ACTIVE)
        task_manager.update_task(task.id, status=TaskStatus.COMPLETED)
        
        # Cannot transition from completed
        with pytest.raises(Exception):
            task_manager.update_task(task.id, status=TaskStatus.PENDING)
    
    def test_data_persistence_integration(self, task_manager, temp_data_dir):
        """Test data persistence across TaskManager sessions."""
        # Create and complete a task
        task = task_manager.create_task(
            title="Persistent task",
            difficulty=TaskDifficulty.HARD,
            priority=TaskPriority.CRITICAL
        )
        
        completed_task, xp_earned = task_manager.complete_task(task.id)
        
        # Create new TaskManager instance (simulating app restart)
        data_manager = DataManager(temp_data_dir)
        new_task_manager = TaskManager(data_manager)
        
        # Data should be loaded from storage
        loaded_task = new_task_manager.get_task(task.id)
        assert loaded_task.title == "Persistent task"
        assert loaded_task.is_completed
        assert loaded_task.completed_at is not None
        
        loaded_player_data = new_task_manager.get_player_data()
        assert loaded_player_data.total_xp == xp_earned
        assert loaded_player_data.tasks_completed == 1
    
    def test_bulk_operations_integration(self, task_manager):
        """Test bulk operations with validation and XP calculation."""
        # Create multiple tasks
        tasks = []
        for i in range(5):
            task = task_manager.create_task(
                title=f"Bulk task {i+1}",
                difficulty=TaskDifficulty.EASY,
                priority=TaskPriority.LOW
            )
            tasks.append(task)
        
        # Bulk update status
        task_ids = [task.id for task in tasks[:3]]
        updated_tasks = task_manager.bulk_update_status(task_ids, TaskStatus.ACTIVE)
        
        assert len(updated_tasks) == 3
        for task in updated_tasks:
            assert task.status == TaskStatus.ACTIVE
        
        # Complete all active tasks
        for task in updated_tasks:
            task_manager.complete_task(task.id)
        
        # Check final state
        player_data = task_manager.get_player_data()
        assert player_data.tasks_completed == 3
        assert player_data.total_xp > 0
        
        # Get task counts
        counts = task_manager.get_task_count()
        assert counts['completed'] == 3
        assert counts['pending'] == 2
        assert counts['total'] == 5
    
    def test_search_and_filter_integration(self, task_manager):
        """Test search and filtering with various task states."""
        # Create diverse tasks
        auth_task = task_manager.create_task(
            title="Implement authentication",
            difficulty=TaskDifficulty.HARD,
            priority=TaskPriority.CRITICAL,
            notes="JWT and OAuth integration"
        )
        
        ui_task = task_manager.create_task(
            title="Design user interface",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.HIGH,
            notes="React components and styling"
        )
        
        db_task = task_manager.create_task(
            title="Database optimization",
            difficulty=TaskDifficulty.EASY,
            priority=TaskPriority.LOW,
            notes="Index creation and query optimization"
        )
        
        # Update statuses
        task_manager.update_task(auth_task.id, status=TaskStatus.ACTIVE)
        task_manager.complete_task(ui_task.id)
        
        # Test filtering
        active_tasks = task_manager.get_tasks(status_filter=TaskStatus.ACTIVE)
        assert len(active_tasks) == 1
        assert active_tasks[0].id == auth_task.id
        
        completed_tasks = task_manager.get_tasks(status_filter=TaskStatus.COMPLETED)
        assert len(completed_tasks) == 1
        assert completed_tasks[0].id == ui_task.id
        
        hard_tasks = task_manager.get_tasks(difficulty_filter=TaskDifficulty.HARD)
        assert len(hard_tasks) == 1
        assert hard_tasks[0].id == auth_task.id
        
        # Test search
        auth_results = task_manager.search_tasks("authentication")
        assert len(auth_results) == 1
        assert auth_results[0].id == auth_task.id
        
        react_results = task_manager.search_tasks("React")
        assert len(react_results) == 1
        assert react_results[0].id == ui_task.id
        
        # Test sorting
        tasks_by_difficulty = task_manager.get_tasks(sort_by='difficulty', reverse=True)
        assert tasks_by_difficulty[0].difficulty == TaskDifficulty.HARD
        assert tasks_by_difficulty[-1].difficulty == TaskDifficulty.EASY
    
    def test_error_handling_integration(self, task_manager):
        """Test error handling across business logic components."""
        # Create a task
        task = task_manager.create_task(
            title="Test task",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.HIGH
        )
        
        # Complete it
        task_manager.complete_task(task.id)
        
        # Try various invalid operations
        with pytest.raises(Exception):
            task_manager.complete_task(task.id)  # Already completed
        
        with pytest.raises(Exception):
            task_manager.complete_task("non-existent")  # Doesn't exist
        
        with pytest.raises(Exception):
            task_manager.update_task(task.id, difficulty=TaskDifficulty.EASY)  # Can't change completed task difficulty
        
        with pytest.raises(Exception):
            task_manager.delete_task(task.id)  # Can't delete completed without force
        
        with pytest.raises(Exception):
            task_manager.get_task("non-existent")  # Doesn't exist
        
        with pytest.raises(Exception):
            task_manager.update_task("non-existent", title="New title")  # Doesn't exist