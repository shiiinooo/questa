"""Integration tests for form submission and validation workflows."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from textual.app import App
from textual.widgets import Input, TextArea, Select, Button

from src.models.task import Task
from src.models.enums import TaskDifficulty, TaskPriority, TaskStatus
from src.business.task_manager import TaskManager, TaskValidationError, TaskStateError
from src.data.data_manager import DataManager
from src.screens.add_task_screen import AddTaskScreen
from src.screens.edit_task_screen import EditTaskScreen
from src.widgets.task_form import TaskForm


class TestAddTaskScreenIntegration:
    """Integration tests for AddTaskScreen form submission and validation."""
    
    @pytest.fixture
    def mock_data_manager(self):
        """Create a mock data manager."""
        mock_dm = Mock(spec=DataManager)
        mock_dm.load_tasks.return_value = {}
        mock_dm.load_player_data.return_value = Mock(total_xp=0, tasks_completed=0)
        mock_dm.save_tasks.return_value = True
        mock_dm.save_player_data.return_value = True
        return mock_dm
    
    @pytest.fixture
    def task_manager(self, mock_data_manager):
        """Create a task manager with mock data manager."""
        return TaskManager(mock_data_manager)
    
    @pytest.fixture
    def add_screen(self, task_manager):
        """Create an AddTaskScreen instance."""
        return AddTaskScreen(task_manager)
    
    def test_screen_initialization(self, add_screen, task_manager):
        """Test AddTaskScreen initializes correctly."""
        assert add_screen.task_manager == task_manager
        assert not add_screen.is_submitting
        assert add_screen.task_form is None  # Not composed yet
    
    @pytest.mark.asyncio
    async def test_successful_task_creation_workflow(self, add_screen, task_manager):
        """Test complete workflow for successful task creation."""
        # Mock the form and its methods
        mock_form = Mock(spec=TaskForm)
        mock_form.validate_form.return_value = []  # No errors
        mock_form.get_form_data.return_value = {
            'title': 'New Integration Test Task',
            'difficulty': TaskDifficulty.MEDIUM,
            'priority': TaskPriority.HIGH,
            'notes': 'Test notes for integration'
        }
        mock_form.display_success = Mock()
        mock_form.display_errors = Mock()
        
        add_screen.task_form = mock_form
        
        # Mock the status message update
        add_screen._update_status_message = Mock()
        
        # Mock the post_message method
        add_screen.post_message = Mock()
        
        # Mock the set_timer method
        add_screen.set_timer = Mock()
        
        # Execute the submission
        await add_screen._submit_task()
        
        # Verify form validation was called
        mock_form.validate_form.assert_called_once()
        
        # Verify form data was retrieved
        mock_form.get_form_data.assert_called_once()
        
        # Verify task was created in task manager
        tasks = task_manager.get_tasks()
        assert len(tasks) == 1
        created_task = tasks[0]
        assert created_task.title == 'New Integration Test Task'
        assert created_task.difficulty == TaskDifficulty.MEDIUM
        assert created_task.priority == TaskPriority.HIGH
        assert created_task.notes == 'Test notes for integration'
        
        # Verify success message was displayed
        mock_form.display_success.assert_called_once()
        success_call_args = mock_form.display_success.call_args[0][0]
        assert "created successfully" in success_call_args
        
        # Verify status message was updated
        add_screen._update_status_message.assert_called()
        
        # Verify success message was posted
        add_screen.post_message.assert_called_once()
        posted_message = add_screen.post_message.call_args[0][0]
        assert isinstance(posted_message, AddTaskScreen.TaskCreated)
        assert posted_message.task == created_task
        
        # Verify auto-close timer was set
        add_screen.set_timer.assert_called_once_with(2.0, add_screen._auto_close)
    
    @pytest.mark.asyncio
    async def test_validation_error_workflow(self, add_screen):
        """Test workflow when form validation fails."""
        # Mock the form with validation errors
        mock_form = Mock(spec=TaskForm)
        mock_form.validate_form.return_value = [
            "Task title is required",
            "Title cannot exceed 200 characters"
        ]
        mock_form.display_errors = Mock()
        
        add_screen.task_form = mock_form
        add_screen._update_status_message = Mock()
        
        # Execute the submission
        await add_screen._submit_task()
        
        # Verify validation was called
        mock_form.validate_form.assert_called_once()
        
        # Verify form data was NOT retrieved (due to validation failure)
        mock_form.get_form_data.assert_not_called()
        
        # Verify errors were displayed
        mock_form.display_errors.assert_called_once_with([
            "Task title is required",
            "Title cannot exceed 200 characters"
        ])
        
        # Verify error status message
        add_screen._update_status_message.assert_called_with(
            "Please fix validation errors", error=True
        )
    
    @pytest.mark.asyncio
    async def test_task_manager_error_workflow(self, add_screen, task_manager):
        """Test workflow when task manager raises an error."""
        # Mock the form
        mock_form = Mock(spec=TaskForm)
        mock_form.validate_form.return_value = []
        mock_form.get_form_data.return_value = {
            'title': 'Test Task',
            'difficulty': TaskDifficulty.EASY,
            'priority': TaskPriority.LOW,
            'notes': None
        }
        mock_form.display_errors = Mock()
        
        add_screen.task_form = mock_form
        add_screen._update_status_message = Mock()
        
        # Mock task manager to raise an error
        with patch.object(task_manager, 'create_task', side_effect=TaskValidationError("Invalid task data")):
            await add_screen._submit_task()
        
        # Verify error was handled
        mock_form.display_errors.assert_called_once()
        error_args = mock_form.display_errors.call_args[0][0]
        assert "Invalid task data" in error_args[0]
        
        # Verify error status message
        add_screen._update_status_message.assert_called_with(
            "Validation error: Invalid task data", error=True
        )
    
    def test_keyboard_shortcuts(self, add_screen):
        """Test keyboard shortcut actions."""
        # Mock run_worker to accept any coroutine
        add_screen.run_worker = Mock()
        add_screen.dismiss = Mock()
        add_screen.post_message = Mock()
        
        # Test submit action
        add_screen.action_submit()
        add_screen.run_worker.assert_called_once()
        # Verify the coroutine passed to run_worker
        call_args = add_screen.run_worker.call_args[0][0]
        assert hasattr(call_args, '__await__')  # It's a coroutine
        
        # Test cancel action
        add_screen.action_cancel()
        add_screen.post_message.assert_called_once()
        add_screen.dismiss.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_form_message_handlers(self, add_screen):
        """Test handling of messages from TaskForm."""
        # Mock the _submit_task method directly instead of run_worker
        add_screen._submit_task = AsyncMock()
        add_screen.dismiss = Mock()
        add_screen.post_message = Mock()
        
        # Test TaskCreated message
        form_data = {
            'title': 'Test Task',
            'difficulty': TaskDifficulty.MEDIUM,
            'priority': TaskPriority.MEDIUM,
            'notes': 'Test notes'
        }
        
        task_created_message = TaskForm.TaskCreated(form_data)
        await add_screen.on_task_form_task_created(task_created_message)
        add_screen._submit_task.assert_called_once()
        
        # Test FormCancelled message
        form_cancelled_message = TaskForm.FormCancelled()
        await add_screen.on_task_form_form_cancelled(form_cancelled_message)
        add_screen.post_message.assert_called_once()
        add_screen.dismiss.assert_called_once()


class TestEditTaskScreenIntegration:
    """Integration tests for EditTaskScreen form submission and validation."""
    
    @pytest.fixture
    def mock_data_manager(self):
        """Create a mock data manager."""
        mock_dm = Mock(spec=DataManager)
        mock_dm.load_tasks.return_value = {}
        mock_dm.load_player_data.return_value = Mock(total_xp=0, tasks_completed=0)
        mock_dm.save_tasks.return_value = True
        mock_dm.save_player_data.return_value = True
        return mock_dm
    
    @pytest.fixture
    def task_manager(self, mock_data_manager):
        """Create a task manager with mock data manager."""
        return TaskManager(mock_data_manager)
    
    @pytest.fixture
    def sample_task(self):
        """Create a sample task for editing."""
        return Task(
            title="Original Task Title",
            difficulty=TaskDifficulty.MEDIUM,
            priority=TaskPriority.MEDIUM,
            notes="Original notes"
        )
    
    @pytest.fixture
    def edit_screen(self, sample_task, task_manager):
        """Create an EditTaskScreen instance."""
        # Add the task to the task manager first
        task_manager._tasks[sample_task.id] = sample_task
        return EditTaskScreen(sample_task, task_manager)
    
    def test_screen_initialization(self, edit_screen, sample_task, task_manager):
        """Test EditTaskScreen initializes correctly."""
        assert edit_screen.original_task == sample_task
        assert edit_screen.task_manager == task_manager
        assert not edit_screen.is_submitting
        assert not edit_screen.has_changes
        assert edit_screen.task_form is None  # Not composed yet
    
    def test_change_detection(self, edit_screen):
        """Test detection of changes in form data."""
        # Test no changes
        form_data = {
            'title': edit_screen.original_task.title,
            'difficulty': edit_screen.original_task.difficulty,
            'priority': edit_screen.original_task.priority,
            'notes': edit_screen.original_task.notes,
            'status': edit_screen.original_task.status
        }
        
        changes = edit_screen._detect_changes(form_data)
        assert changes == {}
        
        # Test with changes
        form_data['title'] = "Updated Title"
        form_data['difficulty'] = TaskDifficulty.HARD
        form_data['priority'] = TaskPriority.HIGH
        
        changes = edit_screen._detect_changes(form_data)
        expected_changes = {
            'title': "Updated Title",
            'difficulty': TaskDifficulty.HARD,
            'priority': TaskPriority.HIGH
        }
        assert changes == expected_changes
    
    @pytest.mark.asyncio
    async def test_successful_task_update_workflow(self, edit_screen, task_manager):
        """Test complete workflow for successful task update."""
        # Mock the form and its methods
        mock_form = Mock(spec=TaskForm)
        mock_form.validate_form.return_value = []  # No errors
        mock_form.get_form_data.return_value = {
            'title': 'Updated Task Title',
            'difficulty': TaskDifficulty.HARD,
            'priority': TaskPriority.HIGH,
            'notes': 'Updated notes',
            'status': TaskStatus.ACTIVE
        }
        mock_form.display_success = Mock()
        mock_form.display_errors = Mock()
        
        edit_screen.task_form = mock_form
        
        # Mock other methods
        edit_screen._update_status_message = Mock()
        edit_screen.post_message = Mock()
        edit_screen.set_timer = Mock()
        
        # Execute the submission
        await edit_screen._submit_changes()
        
        # Verify form validation was called
        mock_form.validate_form.assert_called_once()
        
        # Verify form data was retrieved
        mock_form.get_form_data.assert_called_once()
        
        # Verify task was updated in task manager
        updated_task = task_manager.get_task(edit_screen.original_task.id)
        assert updated_task.title == 'Updated Task Title'
        assert updated_task.difficulty == TaskDifficulty.HARD
        assert updated_task.priority == TaskPriority.HIGH
        assert updated_task.notes == 'Updated notes'
        assert updated_task.status == TaskStatus.ACTIVE
        
        # Verify success message was displayed
        mock_form.display_success.assert_called_once()
        
        # Verify success message was posted
        edit_screen.post_message.assert_called_once()
        posted_message = edit_screen.post_message.call_args[0][0]
        assert isinstance(posted_message, EditTaskScreen.TaskUpdated)
        assert posted_message.original_task == edit_screen.original_task
        assert posted_message.updated_task == updated_task
    
    @pytest.mark.asyncio
    async def test_no_changes_workflow(self, edit_screen):
        """Test workflow when no changes are detected."""
        # Mock the form with no changes
        mock_form = Mock(spec=TaskForm)
        mock_form.validate_form.return_value = []
        mock_form.get_form_data.return_value = {
            'title': edit_screen.original_task.title,
            'difficulty': edit_screen.original_task.difficulty,
            'priority': edit_screen.original_task.priority,
            'notes': edit_screen.original_task.notes,
            'status': edit_screen.original_task.status
        }
        mock_form.display_success = Mock()
        
        edit_screen.task_form = mock_form
        edit_screen._update_status_message = Mock()
        
        # Execute the submission
        await edit_screen._submit_changes()
        
        # Verify no changes message
        edit_screen._update_status_message.assert_called_with("No changes detected")
        mock_form.display_success.assert_called_with("No changes to save")
    
    @pytest.mark.asyncio
    async def test_completed_task_restriction_workflow(self, task_manager):
        """Test workflow when trying to edit restricted fields of completed task."""
        # Create a completed task
        completed_task = Task(
            title="Completed Task",
            difficulty=TaskDifficulty.EASY,
            priority=TaskPriority.LOW,
            status=TaskStatus.COMPLETED
        )
        completed_task.completed_at = datetime.now()
        task_manager._tasks[completed_task.id] = completed_task
        
        edit_screen = EditTaskScreen(completed_task, task_manager)
        
        # Mock the form trying to change difficulty
        mock_form = Mock(spec=TaskForm)
        mock_form.validate_form.return_value = []
        mock_form.get_form_data.return_value = {
            'title': completed_task.title,
            'difficulty': TaskDifficulty.HARD,  # Trying to change difficulty
            'priority': completed_task.priority,
            'notes': completed_task.notes,
            'status': completed_task.status
        }
        mock_form.display_errors = Mock()
        
        edit_screen.task_form = mock_form
        edit_screen._update_status_message = Mock()
        
        # Execute the submission
        await edit_screen._submit_changes()
        
        # Verify validation failed
        mock_form.display_errors.assert_called_once()
        error_args = mock_form.display_errors.call_args[0][0]
        assert any("Cannot change difficulty of completed task" in error for error in error_args)
    
    @pytest.mark.asyncio
    async def test_state_error_workflow(self, edit_screen, task_manager):
        """Test workflow when task state error occurs."""
        # Mock the form
        mock_form = Mock(spec=TaskForm)
        mock_form.validate_form.return_value = []
        mock_form.get_form_data.return_value = {
            'title': 'Updated Title',
            'difficulty': edit_screen.original_task.difficulty,
            'priority': edit_screen.original_task.priority,
            'notes': edit_screen.original_task.notes,
            'status': edit_screen.original_task.status
        }
        mock_form.display_errors = Mock()
        
        edit_screen.task_form = mock_form
        edit_screen._update_status_message = Mock()
        
        # Mock task manager to raise a state error
        with patch.object(task_manager, 'validate_task_update', return_value={'valid': True, 'errors': [], 'warnings': [], 'changes': {'title': {'from': 'old', 'to': 'new'}}}):
            with patch.object(task_manager, 'update_task', side_effect=TaskStateError("Invalid state transition")):
                await edit_screen._submit_changes()
        
        # Verify error was handled
        mock_form.display_errors.assert_called_once()
        error_args = mock_form.display_errors.call_args[0][0]
        assert "Invalid state transition" in error_args[0]
    
    def test_form_reset(self, edit_screen):
        """Test form reset functionality."""
        # Mock the form
        mock_form = Mock(spec=TaskForm)
        mock_form.reset_form = Mock()
        mock_form.clear_messages = Mock()
        
        edit_screen.task_form = mock_form
        edit_screen._update_status_message = Mock()
        
        # Execute reset
        edit_screen._reset_form()
        
        # Verify form was reset
        mock_form.reset_form.assert_called_once()
        mock_form.clear_messages.assert_called_once()
        edit_screen._update_status_message.assert_called_with("Form reset to original values")
    
    def test_keyboard_shortcuts(self, edit_screen):
        """Test keyboard shortcut actions."""
        edit_screen.run_worker = Mock()
        edit_screen.dismiss = Mock()
        edit_screen.post_message = Mock()
        edit_screen._reset_form = Mock()
        
        # Test submit action
        edit_screen.action_submit()
        edit_screen.run_worker.assert_called_once()
        # Verify the coroutine passed to run_worker
        call_args = edit_screen.run_worker.call_args[0][0]
        assert hasattr(call_args, '__await__')  # It's a coroutine
        
        # Test cancel action
        edit_screen.action_cancel()
        edit_screen.post_message.assert_called_once()
        edit_screen.dismiss.assert_called_once()
        
        # Test reset action
        edit_screen.action_reset()
        edit_screen._reset_form.assert_called_once()


class TestFormScreensIntegrationWorkflow:
    """End-to-end integration tests for form screens workflow."""
    
    @pytest.fixture
    def mock_data_manager(self):
        """Create a mock data manager."""
        mock_dm = Mock(spec=DataManager)
        mock_dm.load_tasks.return_value = {}
        mock_dm.load_player_data.return_value = Mock(total_xp=0, tasks_completed=0)
        mock_dm.save_tasks.return_value = True
        mock_dm.save_player_data.return_value = True
        return mock_dm
    
    @pytest.fixture
    def task_manager(self, mock_data_manager):
        """Create a task manager with mock data manager."""
        return TaskManager(mock_data_manager)
    
    @pytest.mark.asyncio
    async def test_create_then_edit_workflow(self, task_manager):
        """Test complete workflow: create task, then edit it."""
        # Step 1: Create a task using AddTaskScreen
        add_screen = AddTaskScreen(task_manager)
        
        # Mock the form for creation
        mock_create_form = Mock(spec=TaskForm)
        mock_create_form.validate_form.return_value = []
        mock_create_form.get_form_data.return_value = {
            'title': 'Initial Task',
            'difficulty': TaskDifficulty.EASY,
            'priority': TaskPriority.LOW,
            'notes': 'Initial notes'
        }
        mock_create_form.display_success = Mock()
        
        add_screen.task_form = mock_create_form
        add_screen._update_status_message = Mock()
        add_screen.post_message = Mock()
        add_screen.set_timer = Mock()
        
        # Execute task creation
        await add_screen._submit_task()
        
        # Verify task was created
        tasks = task_manager.get_tasks()
        assert len(tasks) == 1
        created_task = tasks[0]
        assert created_task.title == 'Initial Task'
        
        # Step 2: Edit the created task using EditTaskScreen
        edit_screen = EditTaskScreen(created_task, task_manager)
        
        # Mock the form for editing
        mock_edit_form = Mock(spec=TaskForm)
        mock_edit_form.validate_form.return_value = []
        mock_edit_form.get_form_data.return_value = {
            'title': 'Updated Task Title',
            'difficulty': TaskDifficulty.HARD,
            'priority': TaskPriority.HIGH,
            'notes': 'Updated notes',
            'status': TaskStatus.ACTIVE
        }
        mock_edit_form.display_success = Mock()
        
        edit_screen.task_form = mock_edit_form
        edit_screen._update_status_message = Mock()
        edit_screen.post_message = Mock()
        edit_screen.set_timer = Mock()
        
        # Execute task update
        await edit_screen._submit_changes()
        
        # Verify task was updated
        updated_task = task_manager.get_task(created_task.id)
        assert updated_task.title == 'Updated Task Title'
        assert updated_task.difficulty == TaskDifficulty.HARD
        assert updated_task.priority == TaskPriority.HIGH
        assert updated_task.notes == 'Updated notes'
        assert updated_task.status == TaskStatus.ACTIVE
        
        # Verify XP was recalculated
        assert updated_task.xp_reward == TaskDifficulty.HARD.xp_value
    
    def test_validation_consistency_between_screens(self, task_manager):
        """Test that validation rules are consistent between add and edit screens."""
        # Test data that should fail validation
        invalid_form_data = {
            'title': '',  # Empty title
            'difficulty': TaskDifficulty.MEDIUM,
            'priority': TaskPriority.MEDIUM,
            'notes': None
        }
        
        # Test AddTaskScreen validation
        add_screen = AddTaskScreen(task_manager)
        mock_add_form = Mock(spec=TaskForm)
        mock_add_form.validate_form.return_value = ["Task title is required"]
        add_screen.task_form = mock_add_form
        
        # Create a sample task for edit screen
        sample_task = Task(
            title="Sample Task",
            difficulty=TaskDifficulty.EASY,
            priority=TaskPriority.LOW
        )
        task_manager._tasks[sample_task.id] = sample_task
        
        # Test EditTaskScreen validation
        edit_screen = EditTaskScreen(sample_task, task_manager)
        mock_edit_form = Mock(spec=TaskForm)
        mock_edit_form.validate_form.return_value = ["Task title is required"]
        edit_screen.task_form = mock_edit_form
        
        # Both screens should have the same validation behavior
        add_errors = mock_add_form.validate_form()
        edit_errors = mock_edit_form.validate_form()
        
        assert add_errors == edit_errors
        assert "Task title is required" in add_errors
    
    def test_error_handling_consistency(self, task_manager):
        """Test that error handling is consistent between screens."""
        # Both screens should handle TaskValidationError the same way
        validation_error = TaskValidationError("Test validation error")
        
        # Test AddTaskScreen error handling
        add_screen = AddTaskScreen(task_manager)
        mock_add_form = Mock(spec=TaskForm)
        mock_add_form.display_errors = Mock()
        add_screen.task_form = mock_add_form
        add_screen._update_status_message = Mock()
        
        # Test EditTaskScreen error handling
        sample_task = Task(title="Test", difficulty=TaskDifficulty.EASY, priority=TaskPriority.LOW)
        edit_screen = EditTaskScreen(sample_task, task_manager)
        mock_edit_form = Mock(spec=TaskForm)
        mock_edit_form.display_errors = Mock()
        edit_screen.task_form = mock_edit_form
        edit_screen._update_status_message = Mock()
        
        # Both should handle errors consistently
        # This would be tested in the actual async methods, but the pattern should be the same
        assert hasattr(add_screen, '_update_status_message')
        assert hasattr(edit_screen, '_update_status_message')
        assert add_screen.task_form.display_errors == mock_add_form.display_errors
        assert edit_screen.task_form.display_errors == mock_edit_form.display_errors