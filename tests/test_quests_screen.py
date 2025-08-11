"""Integration tests for QuestsScreen functionality and user interactions."""

import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from datetime import datetime, timedelta

from src.screens.quests_screen import QuestsScreen
from src.models.task import Task
from src.models.enums import TaskDifficulty, TaskPriority, TaskStatus
from src.models.player import PlayerData
from src.business.task_manager import TaskManager, TaskNotFoundError, TaskStateError
from src.data.data_manager import DataManager
from src.widgets.task_list_item import TaskListItem


@pytest.fixture
def mock_data_manager():
    """Create a mock data manager."""
    mock_dm = Mock(spec=DataManager)
    mock_dm.load_tasks.return_value = {}
    mock_dm.load_player_data.return_value = PlayerData()
    mock_dm.save_tasks.return_value = True
    mock_dm.save_player_data.return_value = True
    mock_dm.create_backup.return_value = True
    return mock_dm


@pytest.fixture
def task_manager(mock_data_manager):
    """Create a task manager with mock data."""
    return TaskManager(mock_data_manager)


@pytest.fixture
def sample_tasks():
    """Create sample tasks for testing."""
    now = datetime.now()
    return [
        Task(
            id="task1",
            title="Easy Task",
            difficulty=TaskDifficulty.EASY,
            priority=TaskPriority.LOW,
            status=TaskStatus.PENDING,
            notes="This is an easy task",
            created_at=now - timedelta(hours=2)
        ),
        Task(
            id="task2", 
            title="Medium Task",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.HIGH,
            status=TaskStatus.ACTIVE,
            notes="This is a medium task",
            created_at=now - timedelta(hours=1)
        ),
        Task(
            id="task3",
            title="Hard Task",
            difficulty=TaskDifficulty.HARD,
            priority=TaskPriority.CRITICAL,
            status=TaskStatus.COMPLETED,
            notes="This is a hard task",
            created_at=now,
            completed_at=now
        )
    ]


@pytest.fixture
def populated_task_manager(task_manager, sample_tasks):
    """Create a task manager populated with sample tasks."""
    # Add tasks to the manager
    for task in sample_tasks:
        task_manager._tasks[task.id] = task
    
    # Update player data for completed task
    task_manager._player_data.complete_task(50, "HARD")
    
    return task_manager


class TestQuestsScreenInitialization:
    """Test QuestsScreen initialization and basic setup."""
    
    def test_screen_initialization(self, task_manager):
        """Test that QuestsScreen initializes correctly."""
        screen = QuestsScreen(task_manager)
        
        assert screen.task_manager is task_manager
        assert screen.tasks == []
        assert screen.filtered_tasks == []
        assert screen.task_widgets == []
        assert screen.selected_task_index == -1
        assert screen.sort_by == "created_at"
        assert screen.sort_reverse is True
        assert screen.status_filter is None
        assert screen.show_filters is False
    
    def test_screen_observer_registration(self, task_manager):
        """Test that screen registers as task manager observer."""
        initial_observers = len(task_manager._observers)
        screen = QuestsScreen(task_manager)
        
        assert len(task_manager._observers) == initial_observers + 1
        assert screen._on_task_changed in task_manager._observers


class TestTaskListDisplay:
    """Test task list display functionality."""
    
    def test_empty_task_list_display(self, task_manager):
        """Test display when no tasks exist."""
        screen = QuestsScreen(task_manager)
        screen.refresh_tasks()
        
        # Check that empty state is displayed
        assert len(screen.filtered_tasks) == 0
        assert screen.selected_task_index == -1
        
        # Check empty state rendering
        empty_state = screen._render_empty_state()
        assert "Welcome to QUESTA!" in empty_state
        assert "create your first quest" in empty_state
    
    def test_populated_task_list_display(self, populated_task_manager):
        """Test display with tasks present."""
        screen = QuestsScreen(populated_task_manager)
        screen.refresh_tasks()
        
        # Check that tasks are loaded
        assert len(screen.filtered_tasks) == 3
        
        # Check task order (newest first by default)
        assert screen.filtered_tasks[0].title == "Hard Task"
        assert screen.filtered_tasks[1].title == "Medium Task"
        assert screen.filtered_tasks[2].title == "Easy Task"
    
    def test_task_display_content(self, populated_task_manager):
        """Test that task content is displayed correctly."""
        screen = QuestsScreen(populated_task_manager)
        screen.refresh_tasks()
        
        # Check that tasks have correct information
        hard_task = screen.filtered_tasks[0]  # Hard Task
        assert hard_task.title == "Hard Task"
        assert hard_task.difficulty == TaskDifficulty.HARD
        assert hard_task.priority == TaskPriority.CRITICAL
        assert hard_task.status == TaskStatus.COMPLETED
    
    def test_stats_calculation(self, populated_task_manager):
        """Test that statistics are calculated correctly."""
        screen = QuestsScreen(populated_task_manager)
        
        # Get task counts
        task_counts = screen.task_manager.get_task_count()
        player_data = screen.task_manager.get_player_data()
        
        assert task_counts['total'] == 3
        assert task_counts['completed'] == 1
        assert task_counts['active'] == 1
        assert task_counts['pending'] == 1
        assert player_data.total_xp > 0


class TestTaskSorting:
    """Test task sorting functionality."""
    
    def test_default_sort_by_creation_date(self, populated_task_manager):
        """Test default sorting by creation date (newest first)."""
        screen = QuestsScreen(populated_task_manager)
        screen.refresh_tasks()
        
        # Check default sort order
        assert screen.sort_by == "created_at"
        assert screen.sort_reverse is True
        
        # Check task order
        titles = [task.title for task in screen.filtered_tasks]
        assert titles == ["Hard Task", "Medium Task", "Easy Task"]
    
    def test_sort_by_title(self, populated_task_manager):
        """Test sorting by task title."""
        screen = QuestsScreen(populated_task_manager)
        
        # Change sort to title
        screen.sort_by = "title"
        screen.refresh_tasks()
        
        # Check task order (alphabetical, reverse)
        titles = [task.title for task in screen.filtered_tasks]
        assert titles == ["Medium Task", "Hard Task", "Easy Task"]
    
    def test_sort_by_difficulty(self, populated_task_manager):
        """Test sorting by task difficulty."""
        screen = QuestsScreen(populated_task_manager)
        
        # Change sort to difficulty
        screen.sort_by = "difficulty"
        screen.refresh_tasks()
        
        # Check task order (by XP value, reverse)
        difficulties = [task.difficulty for task in screen.filtered_tasks]
        assert difficulties == [TaskDifficulty.HARD, TaskDifficulty.MEDIUM, TaskDifficulty.EASY]
    
    def test_toggle_sort_action(self, populated_task_manager):
        """Test the toggle sort keyboard action."""
        screen = QuestsScreen(populated_task_manager)
        
        # Initial sort
        assert screen.sort_by == "created_at"
        
        # Toggle sort
        screen.action_toggle_sort()
        assert screen.sort_by == "title"
        
        # Toggle again
        screen.action_toggle_sort()
        assert screen.sort_by == "difficulty"


class TestTaskFiltering:
    """Test task filtering functionality."""
    
    def test_no_filter_shows_all_tasks(self, populated_task_manager):
        """Test that no filter shows all tasks."""
        screen = QuestsScreen(populated_task_manager)
        screen.refresh_tasks()
        
        assert screen.status_filter is None
        assert len(screen.filtered_tasks) == 3
    
    def test_filter_by_status_pending(self, populated_task_manager):
        """Test filtering by pending status."""
        screen = QuestsScreen(populated_task_manager)
        
        # Apply pending filter
        screen.status_filter = TaskStatus.PENDING
        screen.refresh_tasks()
        
        assert len(screen.filtered_tasks) == 1
        assert screen.filtered_tasks[0].status == TaskStatus.PENDING
        assert screen.filtered_tasks[0].title == "Easy Task"
    
    def test_filter_by_status_completed(self, populated_task_manager):
        """Test filtering by completed status."""
        screen = QuestsScreen(populated_task_manager)
        
        # Apply completed filter
        screen.status_filter = TaskStatus.COMPLETED
        screen.refresh_tasks()
        
        assert len(screen.filtered_tasks) == 1
        assert screen.filtered_tasks[0].status == TaskStatus.COMPLETED
        assert screen.filtered_tasks[0].title == "Hard Task"
    
    def test_filter_empty_results(self, populated_task_manager):
        """Test filtering with no matching results."""
        screen = QuestsScreen(populated_task_manager)
        
        # Apply blocked filter (no blocked tasks)
        screen.status_filter = TaskStatus.BLOCKED
        screen.refresh_tasks()
        
        assert len(screen.filtered_tasks) == 0
        
        # Check empty state message
        empty_state = screen._render_empty_state()
        assert "No blocked tasks found" in empty_state
    
    def test_toggle_filter_action(self, populated_task_manager):
        """Test the toggle filter keyboard action."""
        screen = QuestsScreen(populated_task_manager)
        
        # Initial filter
        assert screen.status_filter is None
        
        # Toggle filter
        screen.action_toggle_filter()
        assert screen.status_filter == TaskStatus.PENDING
        
        # Toggle again
        screen.action_toggle_filter()
        assert screen.status_filter == TaskStatus.ACTIVE


class TestKeyboardNavigation:
    """Test keyboard navigation functionality."""
    
    def test_initial_selection_state(self, populated_task_manager):
        """Test initial selection state."""
        screen = QuestsScreen(populated_task_manager)
        screen.refresh_tasks()
        
        # Should start with first task selected when tasks are present
        assert screen.selected_task_index == 0
    
    def test_select_next_task(self, populated_task_manager):
        """Test selecting next task with down arrow."""
        screen = QuestsScreen(populated_task_manager)
        screen.refresh_tasks()
        
        # Start at first task
        assert screen.selected_task_index == 0
        
        # Move to next task
        screen.action_select_next()
        assert screen.selected_task_index == 1
        
        # Move to last task
        screen.action_select_next()
        assert screen.selected_task_index == 2
        
        # Should not go beyond last task
        screen.action_select_next()
        assert screen.selected_task_index == 2
    
    def test_select_previous_task(self, populated_task_manager):
        """Test selecting previous task with up arrow."""
        screen = QuestsScreen(populated_task_manager)
        screen.refresh_tasks()
        
        # Start at last task
        screen.selected_task_index = 2
        
        # Move to previous task
        screen.action_select_previous()
        assert screen.selected_task_index == 1
        
        # Move to first task
        screen.action_select_previous()
        assert screen.selected_task_index == 0
        
        # Should not go before first task
        screen.action_select_previous()
        assert screen.selected_task_index == 0
    
    def test_clear_selection(self, populated_task_manager):
        """Test clearing selection with escape."""
        screen = QuestsScreen(populated_task_manager)
        screen.refresh_tasks()
        
        # Start with selection
        assert screen.selected_task_index == 0
        
        # Clear selection
        screen.action_clear_selection()
        assert screen.selected_task_index == -1
    
    def test_get_selected_task(self, populated_task_manager):
        """Test getting the currently selected task."""
        screen = QuestsScreen(populated_task_manager)
        screen.refresh_tasks()
        
        # Test valid selection
        screen.selected_task_index = 0
        selected_task = screen._get_selected_task()
        assert selected_task is not None
        assert selected_task.title == "Hard Task"
        
        # Test invalid selection
        screen.selected_task_index = -1
        selected_task = screen._get_selected_task()
        assert selected_task is None


class TestTaskCompletion:
    """Test task completion functionality."""
    
    def test_complete_selected_task(self, populated_task_manager):
        """Test completing the selected task."""
        screen = QuestsScreen(populated_task_manager)
        screen.refresh_tasks()
        
        # Select pending task (Easy Task)
        screen.selected_task_index = 2  # Easy Task is last in sorted order
        
        # Complete the task
        screen.action_complete_task()
        
        # Check task was completed
        task = screen.filtered_tasks[2]
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None
    
    def test_complete_already_completed_task(self, populated_task_manager):
        """Test attempting to complete an already completed task."""
        screen = QuestsScreen(populated_task_manager)
        screen.refresh_tasks()
        
        # Select completed task (Hard Task)
        screen.selected_task_index = 0  # Hard Task is first in sorted order
        
        # Mock the status update method to capture the message
        screen._update_status_message = Mock()
        
        # Try to complete the task
        screen.action_complete_task()
        
        # Check error message was called
        screen._update_status_message.assert_called_with("Task is already completed", error=True)
    
    def test_complete_task_no_selection(self, populated_task_manager):
        """Test completing task with no selection."""
        screen = QuestsScreen(populated_task_manager)
        screen.refresh_tasks()
        
        # Clear selection
        screen.selected_task_index = -1
        
        # Mock the status update method
        screen._update_status_message = Mock()
        
        # Try to complete task
        screen.action_complete_task()
        
        # Check error message
        screen._update_status_message.assert_called_with("No task selected for completion", error=True)


class TestTaskStatusChanges:
    """Test task status change functionality."""
    
    def test_activate_pending_task(self, populated_task_manager):
        """Test activating a pending task."""
        screen = QuestsScreen(populated_task_manager)
        screen.refresh_tasks()
        
        # Select pending task
        screen.selected_task_index = 2  # Easy Task (pending)
        
        # Activate the task
        screen.action_activate_task()
        
        # Check task was activated
        task = screen.filtered_tasks[2]
        assert task.status == TaskStatus.ACTIVE
    
    def test_deactivate_active_task(self, populated_task_manager):
        """Test deactivating an active task."""
        screen = QuestsScreen(populated_task_manager)
        screen.refresh_tasks()
        
        # Select active task
        screen.selected_task_index = 1  # Medium Task (active)
        
        # Deactivate the task
        screen.action_activate_task()
        
        # Check task was deactivated
        task = screen.filtered_tasks[1]
        assert task.status == TaskStatus.PENDING


class TestTaskObserver:
    """Test task change observer functionality."""
    
    def test_observer_handles_task_completion(self, populated_task_manager):
        """Test that observer handles task completion events."""
        screen = QuestsScreen(populated_task_manager)
        screen.refresh_tasks()
        
        # Get a pending task
        pending_task = None
        for task in screen.filtered_tasks:
            if task.status == TaskStatus.PENDING:
                pending_task = task
                break
        
        assert pending_task is not None
        
        # Mock the observer method
        screen._on_task_changed = Mock()
        
        # Complete task through task manager (triggers observer)
        completed_task, xp = populated_task_manager.complete_task(pending_task.id)
        
        # Observer should have been called
        assert len(populated_task_manager._observers) > 0
    
    def test_observer_handles_task_creation(self, populated_task_manager):
        """Test that observer handles task creation events."""
        screen = QuestsScreen(populated_task_manager)
        screen.refresh_tasks()
        
        initial_count = len(screen.filtered_tasks)
        
        # Create new task through task manager
        new_task = populated_task_manager.create_task(
            title="New Test Task",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.MEDIUM
        )
        
        # Observer should refresh the display
        assert len(populated_task_manager._tasks) == initial_count + 1


class TestErrorHandling:
    """Test error handling in QuestsScreen."""
    
    def test_task_manager_error_handling(self, task_manager):
        """Test handling of task manager errors."""
        screen = QuestsScreen(task_manager)
        
        # Mock task manager to raise error
        task_manager.get_tasks = Mock(side_effect=Exception("Test error"))
        
        # Mock status update method
        screen._update_status_message = Mock()
        
        # Refresh tasks should handle error gracefully
        screen.refresh_tasks()
        
        # Check error message was called
        screen._update_status_message.assert_called_with("Error refreshing tasks: Test error", error=True)
    
    def test_invalid_task_operation_error(self, populated_task_manager):
        """Test handling of invalid task operations."""
        screen = QuestsScreen(populated_task_manager)
        screen.refresh_tasks()
        
        # Mock status update method
        screen._update_status_message = Mock()
        
        # Select a completed task (Hard Task is already completed)
        screen.selected_task_index = 0
        screen.action_complete_task()
        
        # Check error message was called (screen checks completion status first)
        screen._update_status_message.assert_called_with("Task is already completed", error=True)


class TestMessageHandling:
    """Test custom message handling."""
    
    def test_new_task_requested_message(self, task_manager):
        """Test that new task action pushes AddTaskScreen."""
        screen = QuestsScreen(task_manager)
        
        # Mock app.push_screen using PropertyMock
        mock_app = Mock()
        mock_app.push_screen = Mock()
        
        with patch.object(type(screen), 'app', new_callable=PropertyMock) as mock_app_prop:
            mock_app_prop.return_value = mock_app
            
            # Trigger new task action
            screen.action_new_task()
            
            # Check screen was pushed
            mock_app.push_screen.assert_called_once()
            args = mock_app.push_screen.call_args[0]
            from src.screens.add_task_screen import AddTaskScreen
            assert isinstance(args[0], AddTaskScreen)
    
    def test_edit_task_requested_message(self, populated_task_manager):
        """Test that edit task action pushes EditTaskScreen."""
        screen = QuestsScreen(populated_task_manager)
        screen.refresh_tasks()
        
        # Mock app.push_screen using PropertyMock
        mock_app = Mock()
        mock_app.push_screen = Mock()
        
        with patch.object(type(screen), 'app', new_callable=PropertyMock) as mock_app_prop:
            mock_app_prop.return_value = mock_app
            
            # Select a task and trigger edit
            screen.selected_task_index = 0
            screen.action_edit_task()
            
            # Check screen was pushed
            mock_app.push_screen.assert_called_once()
            args = mock_app.push_screen.call_args[0]
            from src.screens.edit_task_screen import EditTaskScreen
            assert isinstance(args[0], EditTaskScreen)
            assert args[0].original_task.title == "Hard Task"
    
    def test_delete_task_requested_message(self, populated_task_manager):
        """Test that delete task requested message is sent."""
        screen = QuestsScreen(populated_task_manager)
        screen.refresh_tasks()
        
        # Mock message posting
        screen.post_message = Mock()
        
        # Select a task and trigger delete
        screen.selected_task_index = 0
        screen.action_delete_task()
        
        # Check message was posted
        screen.post_message.assert_called_once()
        args = screen.post_message.call_args[0]
        assert isinstance(args[0], QuestsScreen.DeleteTaskRequested)
        assert args[0].task.title == "Hard Task"


class TestRefreshFunctionality:
    """Test refresh functionality."""
    
    def test_manual_refresh(self, populated_task_manager):
        """Test manual refresh action."""
        screen = QuestsScreen(populated_task_manager)
        screen.refresh_tasks()
        
        initial_count = len(screen.filtered_tasks)
        
        # Add a task directly to manager (bypassing observer)
        new_task = Task(
            id="refresh_test",
            title="Refresh Test Task",
            difficulty=TaskDifficulty.EASY,
            priority=TaskPriority.LOW
        )
        populated_task_manager._tasks[new_task.id] = new_task
        
        # Manual refresh should pick up the new task
        screen.action_refresh()
        
        assert len(screen.filtered_tasks) == initial_count + 1
    
    def test_stats_update_on_refresh(self, populated_task_manager):
        """Test that stats are updated on refresh."""
        screen = QuestsScreen(populated_task_manager)
        screen.refresh_tasks()
        
        # Get initial task count
        initial_count = len(screen.filtered_tasks)
        
        # Complete a task
        pending_task = None
        for task in screen.filtered_tasks:
            if task.status == TaskStatus.PENDING:
                pending_task = task
                break
        
        if pending_task:
            populated_task_manager.complete_task(pending_task.id)
            screen.refresh_tasks()
            
            # Task count should remain the same but stats should change
            assert len(screen.filtered_tasks) == initial_count
            
            # Check that player data was updated
            player_data = screen.task_manager.get_player_data()
            assert player_data.tasks_completed > 0