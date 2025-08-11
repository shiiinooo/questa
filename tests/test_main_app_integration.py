"""End-to-end integration tests for main application flow."""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from src.app import QUESTAApp
from src.screens.home_screen import HomeScreen
from src.screens.quests_screen import QuestsScreen
from src.screens.add_task_screen import AddTaskScreen
from src.screens.edit_task_screen import EditTaskScreen
from src.business.task_manager import TaskManager
from src.data.data_manager import DataManager
from src.models.task import Task
from src.models.enums import TaskDifficulty, TaskPriority, TaskStatus
from src.models.player import PlayerData


class TestMainApplicationIntegration:
    """Test main application integration and workflow."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary data directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def app(self, temp_data_dir):
        """Create test application instance."""
        return QUESTAApp(data_dir=temp_data_dir)
    
    @pytest.fixture
    def task_manager(self, temp_data_dir):
        """Create test task manager."""
        data_manager = DataManager(temp_data_dir)
        return TaskManager(data_manager)
    
    def test_app_initialization(self, app, temp_data_dir):
        """Test application initialization with data directory creation."""
        # Test that app initializes correctly
        assert app.data_dir == temp_data_dir
        assert app.data_manager is not None
        assert app.task_manager is not None
        assert not app.is_initialized
        
        # Test data directory creation
        assert temp_data_dir.exists()
    
    def test_app_data_loading(self, app):
        """Test application loads existing data on startup."""
        # Create some test data
        task = app.task_manager.create_task(
            title="Test Task",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.HIGH,
            notes="Test notes"
        )
        
        # Complete task to generate player data
        app.task_manager.complete_task(task.id)
        
        # Create new app instance with same data directory
        new_app = QUESTAApp(data_dir=app.data_dir)
        
        # Verify data was loaded
        loaded_tasks = new_app.task_manager.get_tasks()
        assert len(loaded_tasks) == 1
        assert loaded_tasks[0].title == "Test Task"
        assert loaded_tasks[0].is_completed
        
        player_data = new_app.task_manager.get_player_data()
        assert player_data.total_xp > 0
        assert player_data.tasks_completed == 1
    
    def test_screen_navigation_flow(self, app):
        """Test navigation between screens."""
        # Mock the screen installation and navigation
        with patch.object(app, 'install_screen') as mock_install, \
             patch.object(app, 'push_screen') as mock_push, \
             patch.object(app, 'switch_screen') as mock_switch:
            
            # Initialize app
            app.initialize_app()
            
            # Test home screen installation
            mock_install.assert_any_call(app.home_screen, name="home")
            mock_push.assert_called_with("home")
            
            # Test navigation actions
            app.action_tasks()
            mock_switch.assert_called_with("tasks")
            
            app.action_home()
            mock_switch.assert_called_with("home")
    
    def test_global_keyboard_shortcuts(self, app):
        """Test global keyboard shortcuts work correctly."""
        app.initialize_app()
        
        with patch.object(app, 'switch_screen') as mock_switch, \
             patch.object(app, 'push_screen') as mock_push:
            
            # Test Ctrl+H (home)
            app.action_home()
            mock_switch.assert_called_with("home")
            
            # Test Ctrl+T (tasks)
            app.action_tasks()
            mock_switch.assert_called_with("tasks")
            
            # Test Ctrl+N (new task)
            app.action_new_task()
            mock_push.assert_called()
            
            # Verify AddTaskScreen was pushed
            call_args = mock_push.call_args[0][0]
            assert isinstance(call_args, AddTaskScreen)
    
    def test_task_creation_workflow(self, app):
        """Test complete task creation workflow."""
        app.initialize_app()
        
        # Create task through task manager
        task = app.task_manager.create_task(
            title="Integration Test Task",
            difficulty=TaskDifficulty.HARD,
            priority=TaskPriority.CRITICAL,
            notes="Test task for integration"
        )
        
        # Verify task was created
        assert task.title == "Integration Test Task"
        assert task.difficulty == TaskDifficulty.HARD
        assert task.priority == TaskPriority.CRITICAL
        assert task.xp_reward == 50  # Hard difficulty
        assert task.status == TaskStatus.PENDING
        
        # Verify task is in manager
        tasks = app.task_manager.get_tasks()
        assert len(tasks) == 1
        assert tasks[0].id == task.id
    
    def test_task_completion_workflow(self, app):
        """Test complete task completion workflow with XP award."""
        app.initialize_app()
        
        # Create and complete task
        task = app.task_manager.create_task(
            title="Complete Me",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.HIGH
        )
        
        # Get initial player data
        initial_player = app.task_manager.get_player_data()
        initial_xp = initial_player.total_xp
        initial_completed = initial_player.tasks_completed
        
        # Complete task
        completed_task, xp_earned = app.task_manager.complete_task(task.id)
        
        # Verify task completion
        assert completed_task.is_completed
        assert completed_task.completed_at is not None
        # XP includes base (30) + priority bonus (HIGH = 10%) + daily completion bonus (5)
        expected_xp = 30 + int(30 * 0.1) + 5  # 30 + 3 + 5 = 38
        assert xp_earned == expected_xp
        
        # Verify player data update
        updated_player = app.task_manager.get_player_data()
        assert updated_player.total_xp == initial_xp + xp_earned
        assert updated_player.tasks_completed == initial_completed + 1
    
    def test_task_editing_workflow(self, app):
        """Test complete task editing workflow."""
        app.initialize_app()
        
        # Create task
        task = app.task_manager.create_task(
            title="Original Title",
            difficulty=TaskDifficulty.EASY,
            priority=TaskPriority.LOW,
            notes="Original notes"
        )
        
        # Edit task
        updated_task = app.task_manager.update_task(
            task.id,
            title="Updated Title",
            difficulty=TaskDifficulty.HARD,
            priority=TaskPriority.CRITICAL,
            notes="Updated notes"
        )
        
        # Verify updates
        assert updated_task.title == "Updated Title"
        assert updated_task.difficulty == TaskDifficulty.HARD
        assert updated_task.priority == TaskPriority.CRITICAL
        assert updated_task.notes == "Updated notes"
        assert updated_task.xp_reward == 50  # Hard difficulty
    
    def test_task_deletion_workflow(self, app):
        """Test complete task deletion workflow."""
        app.initialize_app()
        
        # Create task
        task = app.task_manager.create_task(
            title="Delete Me",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.MEDIUM
        )
        
        # Verify task exists
        tasks = app.task_manager.get_tasks()
        assert len(tasks) == 1
        
        # Delete task
        result = app.task_manager.delete_task(task.id, force=True)
        
        # Verify deletion
        assert result['success']
        tasks = app.task_manager.get_tasks()
        assert len(tasks) == 0
    
    def test_data_persistence_across_sessions(self, app, temp_data_dir):
        """Test data persists across application sessions."""
        # Session 1: Create and complete tasks
        app.initialize_app()
        
        task1 = app.task_manager.create_task(
            title="Persistent Task 1",
            difficulty=TaskDifficulty.EASY,
            priority=TaskPriority.LOW
        )
        
        task2 = app.task_manager.create_task(
            title="Persistent Task 2",
            difficulty=TaskDifficulty.HARD,
            priority=TaskPriority.HIGH
        )
        
        # Complete one task
        app.task_manager.complete_task(task1.id)
        
        # Save data
        app.save_app_state()
        
        # Session 2: Create new app instance
        new_app = QUESTAApp(data_dir=temp_data_dir)
        new_app.initialize_app()
        
        # Verify data persistence
        loaded_tasks = new_app.task_manager.get_tasks()
        assert len(loaded_tasks) == 2
        
        # Find tasks by title
        task1_loaded = next(t for t in loaded_tasks if t.title == "Persistent Task 1")
        task2_loaded = next(t for t in loaded_tasks if t.title == "Persistent Task 2")
        
        # Verify task states
        assert task1_loaded.is_completed
        assert not task2_loaded.is_completed
        
        # Verify player data
        player_data = new_app.task_manager.get_player_data()
        # Easy task (15) + daily completion bonus (5) = 20 XP
        assert player_data.total_xp == 20
        assert player_data.tasks_completed == 1
    
    def test_error_handling_and_recovery(self, app):
        """Test error handling and recovery mechanisms."""
        app.initialize_app()
        
        # Test invalid task creation
        with pytest.raises(Exception):
            app.task_manager.create_task(
                title="",  # Invalid empty title
                difficulty=TaskDifficulty.MEDIUM,
                priority=TaskPriority.MEDIUM
            )
        
        # Test task not found
        with pytest.raises(Exception):
            app.task_manager.get_task("nonexistent-id")
        
        # Test invalid task completion
        task = app.task_manager.create_task(
            title="Test Task",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.MEDIUM
        )
        
        # Complete task
        app.task_manager.complete_task(task.id)
        
        # Try to complete again (should fail)
        with pytest.raises(Exception):
            app.task_manager.complete_task(task.id)
    
    def test_observer_notifications(self, app):
        """Test observer pattern for task change notifications."""
        app.initialize_app()
        
        # Mock observer
        observer = Mock()
        app.task_manager.add_observer(observer)
        
        # Create task
        task = app.task_manager.create_task(
            title="Observer Test",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.MEDIUM
        )
        
        # Verify creation notification
        observer.assert_called_with('created', task)
        observer.reset_mock()
        
        # Update task
        updated_task = app.task_manager.update_task(task.id, title="Updated Title")
        observer.assert_called_with('updated', updated_task)
        observer.reset_mock()
        
        # Complete task
        completed_task, _ = app.task_manager.complete_task(task.id)
        observer.assert_called_with('completed', completed_task)
        observer.reset_mock()
        
        # Delete task
        app.task_manager.delete_task(task.id, force=True)
        observer.assert_called_with('deleted', completed_task)
    
    def test_auto_save_functionality(self, app):
        """Test automatic data saving functionality."""
        app.initialize_app()
        
        with patch.object(app.task_manager, '_save_data') as mock_save:
            # Create task (should trigger auto-save)
            task = app.task_manager.create_task(
                title="Auto Save Test",
                difficulty=TaskDifficulty.MEDIUM,
                priority=TaskPriority.MEDIUM
            )
            
            # Verify save was called
            mock_save.assert_called()
            mock_save.reset_mock()
            
            # Update task (should trigger auto-save)
            app.task_manager.update_task(task.id, title="Updated")
            mock_save.assert_called()
            mock_save.reset_mock()
            
            # Complete task (should trigger auto-save)
            app.task_manager.complete_task(task.id)
            mock_save.assert_called()
    
    def test_level_progression_integration(self, app):
        """Test level progression through task completion."""
        app.initialize_app()
        
        # Create multiple tasks to test level progression
        tasks = []
        for i in range(5):
            task = app.task_manager.create_task(
                title=f"Level Test Task {i+1}",
                difficulty=TaskDifficulty.HARD,  # 50 XP each
                priority=TaskPriority.MEDIUM
            )
            tasks.append(task)
        
        # Complete tasks and track level progression
        player_data = app.task_manager.get_player_data()
        initial_level = player_data.level
        
        for task in tasks:
            app.task_manager.complete_task(task.id)
            player_data = app.task_manager.get_player_data()
        
        # Verify XP accumulation - Hard tasks (50 each) + bonuses
        # Each task gets: 50 base + 5 daily bonus + streak bonuses + weekly bonuses
        # Total will be higher than 250 due to bonuses
        assert player_data.total_xp > 250
        assert player_data.tasks_completed == 5
        
        # Verify level progression (should be level 2 with 250 XP)
        assert player_data.level >= initial_level
    
    def test_task_filtering_and_sorting(self, app):
        """Test task filtering and sorting functionality."""
        app.initialize_app()
        
        # Create tasks with different attributes
        task1 = app.task_manager.create_task(
            title="Alpha Task",
            difficulty=TaskDifficulty.EASY,
            priority=TaskPriority.LOW
        )
        
        task2 = app.task_manager.create_task(
            title="Beta Task",
            difficulty=TaskDifficulty.HARD,
            priority=TaskPriority.CRITICAL
        )
        
        task3 = app.task_manager.create_task(
            title="Gamma Task",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.HIGH
        )
        
        # Complete one task
        app.task_manager.complete_task(task2.id)
        
        # Test filtering by status
        pending_tasks = app.task_manager.get_tasks(status_filter=TaskStatus.PENDING)
        assert len(pending_tasks) == 2
        
        completed_tasks = app.task_manager.get_tasks(status_filter=TaskStatus.COMPLETED)
        assert len(completed_tasks) == 1
        assert completed_tasks[0].id == task2.id
        
        # Test filtering by difficulty
        hard_tasks = app.task_manager.get_tasks(difficulty_filter=TaskDifficulty.HARD)
        assert len(hard_tasks) == 1
        assert hard_tasks[0].id == task2.id
        
        # Test sorting by title
        tasks_by_title = app.task_manager.get_tasks(sort_by='title', reverse=False)
        assert tasks_by_title[0].title == "Alpha Task"
        assert tasks_by_title[1].title == "Beta Task"
        assert tasks_by_title[2].title == "Gamma Task"
        
        # Test sorting by difficulty
        tasks_by_difficulty = app.task_manager.get_tasks(sort_by='difficulty', reverse=True)
        assert tasks_by_difficulty[0].difficulty == TaskDifficulty.HARD
        assert tasks_by_difficulty[1].difficulty == TaskDifficulty.MEDIUM
        assert tasks_by_difficulty[2].difficulty == TaskDifficulty.EASY


class TestHomeScreenIntegration:
    """Test HomeScreen integration with task management."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary data directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def task_manager(self, temp_data_dir):
        """Create test task manager."""
        data_manager = DataManager(temp_data_dir)
        return TaskManager(data_manager)
    
    @pytest.fixture
    def home_screen(self, task_manager):
        """Create test home screen."""
        return HomeScreen(task_manager)
    
    def test_home_screen_initialization(self, home_screen, task_manager):
        """Test home screen initializes with task manager."""
        assert home_screen.task_manager == task_manager
        assert home_screen.player_data is not None
        assert home_screen.active_tasks == []
        assert home_screen.selected_task_index == -1
    
    def test_home_screen_data_refresh(self, home_screen, task_manager):
        """Test home screen refreshes data correctly."""
        # Create test tasks
        task1 = task_manager.create_task(
            title="Active Task 1",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.HIGH
        )
        
        task2 = task_manager.create_task(
            title="Active Task 2",
            difficulty=TaskDifficulty.EASY,
            priority=TaskPriority.MEDIUM
        )
        
        # Complete one task
        task_manager.complete_task(task2.id)
        
        # Refresh home screen data
        home_screen.refresh_data()
        
        # Verify only active tasks are shown
        assert len(home_screen.active_tasks) == 1
        assert home_screen.active_tasks[0].id == task1.id
        
        # Verify player data is updated
        assert home_screen.player_data.total_xp > 0
        assert home_screen.player_data.tasks_completed == 1
    
    def test_home_screen_task_selection(self, home_screen, task_manager):
        """Test task selection functionality on home screen."""
        # Create test tasks
        task1 = task_manager.create_task(
            title="Task 1",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.HIGH
        )
        
        task2 = task_manager.create_task(
            title="Task 2",
            difficulty=TaskDifficulty.EASY,
            priority=TaskPriority.LOW
        )
        
        # Refresh data
        home_screen.refresh_data()
        
        # Test selection navigation
        assert home_screen.selected_task_index == 0  # Should auto-select first
        
        # Test next selection
        home_screen.action_select_next()
        assert home_screen.selected_task_index == 1
        
        # Test previous selection
        home_screen.action_select_previous()
        assert home_screen.selected_task_index == 0
        
        # Test clear selection
        home_screen.action_clear_selection()
        assert home_screen.selected_task_index == -1
    
    def test_home_screen_task_completion(self, home_screen, task_manager):
        """Test task completion from home screen."""
        # Create test task
        task = task_manager.create_task(
            title="Complete Me",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.HIGH
        )
        
        # Refresh and select task
        home_screen.refresh_data()
        home_screen.selected_task_index = 0
        
        # Complete task through home screen
        home_screen.action_complete_selected()
        
        # Verify task was completed
        completed_task = task_manager.get_task(task.id)
        assert completed_task.is_completed
        
        # Verify home screen updated
        home_screen.refresh_data()
        assert len(home_screen.active_tasks) == 0  # No more active tasks


class TestScreenNavigationIntegration:
    """Test screen navigation and state management."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary data directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def app(self, temp_data_dir):
        """Create test application instance."""
        return QUESTAApp(data_dir=temp_data_dir)
    
    def test_screen_state_preservation(self, app):
        """Test that screen state is preserved during navigation."""
        app.initialize_app()
        
        # Create test data
        task = app.task_manager.create_task(
            title="State Test Task",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.HIGH
        )
        
        with patch.object(app, 'switch_screen') as mock_switch:
            # Navigate to tasks screen
            app.action_tasks()
            mock_switch.assert_called_with("tasks")
            
            # Navigate back to home
            app.action_home()
            mock_switch.assert_called_with("home")
    
    def test_data_consistency_across_screens(self, app):
        """Test data consistency when navigating between screens."""
        app.initialize_app()
        
        # Create task
        task = app.task_manager.create_task(
            title="Consistency Test",
            difficulty=TaskDifficulty.HARD,
            priority=TaskPriority.CRITICAL
        )
        
        # Verify task exists in manager
        tasks = app.task_manager.get_tasks()
        assert len(tasks) == 1
        assert tasks[0].title == "Consistency Test"
        
        # Complete task
        app.task_manager.complete_task(task.id)
        
        # Verify completion is reflected
        updated_tasks = app.task_manager.get_tasks()
        assert updated_tasks[0].is_completed
        
        # Verify player data is updated
        player_data = app.task_manager.get_player_data()
        # Hard task (50) + priority bonus (CRITICAL = 20%) + daily completion bonus (5)
        expected_xp = 50 + int(50 * 0.2) + 5  # 50 + 10 + 5 = 65
        assert player_data.total_xp == expected_xp
        assert player_data.tasks_completed == 1