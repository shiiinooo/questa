"""Task management with CRUD operations and business logic."""

from typing import Dict, List, Optional, Tuple, Callable, Any
from datetime import datetime
import uuid
import logging

from ..models.task import Task
from ..models.player import PlayerData
from ..models.enums import TaskDifficulty, TaskPriority, TaskStatus
from ..data.data_manager import DataManager, DataPersistenceError
from .task_validator import TaskValidator, TaskValidationError
from .xp_calculator import XPCalculator


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskManagerError(Exception):
    """Base exception for task manager operations."""
    pass


class TaskNotFoundError(TaskManagerError):
    """Raised when requested task doesn't exist."""
    pass


class TaskStateError(TaskManagerError):
    """Raised when invalid state transitions are attempted."""
    pass


class TaskManager:
    """Task management with CRUD operations and business logic."""
    
    def __init__(self, data_manager: DataManager):
        """Initialize TaskManager with data persistence.
        
        Args:
            data_manager: DataManager instance for persistence
        """
        self._data_manager = data_manager
        self._tasks: Dict[str, Task] = {}
        self._player_data: PlayerData = PlayerData()
        self._observers: List[Callable[[str, Task], None]] = []
        
        # Load existing data
        self._load_data()
        
        logger.info(f"TaskManager initialized with {len(self._tasks)} tasks")
    
    def _load_data(self) -> None:
        """Load tasks and player data from storage."""
        try:
            self._tasks = self._data_manager.load_tasks()
            self._player_data = self._data_manager.load_player_data()
            logger.info("Successfully loaded data from storage")
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            # Continue with empty data rather than failing
            self._tasks = {}
            self._player_data = PlayerData()
    
    def _save_data(self) -> None:
        """Save tasks and player data to storage."""
        try:
            self._data_manager.save_tasks(self._tasks)
            self._data_manager.save_player_data(self._player_data)
            logger.debug("Successfully saved data to storage")
        except DataPersistenceError as e:
            logger.error(f"Failed to save data: {e}")
            raise TaskManagerError(f"Failed to save data: {e}") from e
    
    def add_observer(self, observer: Callable[[str, Task], None]) -> None:
        """Add observer for task changes.
        
        Args:
            observer: Callback function (action, task)
        """
        self._observers.append(observer)
    
    def remove_observer(self, observer: Callable[[str, Task], None]) -> None:
        """Remove observer for task changes.
        
        Args:
            observer: Callback function to remove
        """
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_observers(self, action: str, task: Task) -> None:
        """Notify observers of task changes.
        
        Args:
            action: Action performed (created, updated, completed, deleted)
            task: Task that was changed
        """
        for observer in self._observers:
            try:
                observer(action, task)
            except Exception as e:
                logger.warning(f"Observer notification failed: {e}")
    
    def create_task(self, title: str, difficulty: TaskDifficulty, 
                   priority: TaskPriority, notes: Optional[str] = None,
                   task_id: Optional[str] = None) -> Task:
        """Create and validate new task.
        
        Args:
            title: Task title
            difficulty: Task difficulty level
            priority: Task priority level
            notes: Optional task notes
            task_id: Optional custom task ID (generates UUID if None)
            
        Returns:
            Task: Created task
            
        Raises:
            TaskValidationError: If task data is invalid
            TaskManagerError: If task creation fails
        """
        try:
            # Validate input data
            task_data = {
                'title': title,
                'difficulty': difficulty,
                'priority': priority,
                'notes': notes
            }
            
            # Sanitize data
            task_data = TaskValidator.sanitize_task_data(task_data)
            
            # Validate data
            errors = TaskValidator.validate_task_data(task_data)
            if errors:
                raise TaskValidationError(f"Task validation failed: {'; '.join(errors)}")
            
            # Generate ID if not provided
            if task_id is None:
                task_id = str(uuid.uuid4())
            elif task_id in self._tasks:
                raise TaskManagerError(f"Task with ID {task_id} already exists")
            
            # Create task
            task = Task(
                id=task_id,
                title=task_data['title'],
                difficulty=task_data['difficulty'],
                priority=task_data['priority'],
                notes=task_data['notes']
            )
            
            # Store task
            self._tasks[task.id] = task
            
            # Save data
            self._save_data()
            
            # Notify observers
            self._notify_observers('created', task)
            
            logger.info(f"Created task: {task.title} ({task.id})")
            return task
            
        except TaskValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise TaskManagerError(f"Failed to create task: {e}") from e
    
    def get_task(self, task_id: str) -> Task:
        """Get task by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task: Task object
            
        Raises:
            TaskNotFoundError: If task doesn't exist
        """
        if task_id not in self._tasks:
            raise TaskNotFoundError(f"Task with ID {task_id} not found")
        
        return self._tasks[task_id]
    
    def get_tasks(self, status_filter: Optional[TaskStatus] = None,
                  difficulty_filter: Optional[TaskDifficulty] = None,
                  priority_filter: Optional[TaskPriority] = None,
                  sort_by: str = 'created_at',
                  reverse: bool = True) -> List[Task]:
        """Retrieve tasks with optional filtering and sorting.
        
        Args:
            status_filter: Filter by task status
            difficulty_filter: Filter by task difficulty
            priority_filter: Filter by task priority
            sort_by: Field to sort by (created_at, title, difficulty, priority, status)
            reverse: Sort in reverse order
            
        Returns:
            List[Task]: Filtered and sorted tasks
        """
        tasks = list(self._tasks.values())
        
        # Apply filters
        if status_filter is not None:
            tasks = [task for task in tasks if task.status == status_filter]
        
        if difficulty_filter is not None:
            tasks = [task for task in tasks if task.difficulty == difficulty_filter]
        
        if priority_filter is not None:
            tasks = [task for task in tasks if task.priority == priority_filter]
        
        # Sort tasks
        sort_key_map = {
            'created_at': lambda t: t.created_at,
            'title': lambda t: t.title.lower(),
            'difficulty': lambda t: t.difficulty.xp_value,
            'priority': lambda t: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].index(t.priority.name),
            'status': lambda t: ['PENDING', 'ACTIVE', 'BLOCKED', 'COMPLETED'].index(t.status.name)
        }
        
        if sort_by in sort_key_map:
            tasks.sort(key=sort_key_map[sort_by], reverse=reverse)
        
        return tasks
    
    def update_task(self, task_id: str, **updates) -> Task:
        """Update task with validation and XP recalculation.
        
        Args:
            task_id: Task identifier
            **updates: Fields to update
            
        Returns:
            Task: Updated task
            
        Raises:
            TaskNotFoundError: If task doesn't exist
            TaskValidationError: If update data is invalid
            TaskStateError: If trying to update completed task inappropriately
            TaskManagerError: If update fails
        """
        try:
            # Get existing task
            task = self.get_task(task_id)
            original_difficulty = task.difficulty
            original_xp = task.xp_reward
            
            # Create current data dict with proper enum values
            current_data = {
                'id': task.id,
                'title': task.title,
                'difficulty': task.difficulty,
                'priority': task.priority,
                'status': task.status,
                'notes': task.notes,
                'created_at': task.created_at,
                'completed_at': task.completed_at
            }
            
            # Sanitize update data
            updates = TaskValidator.sanitize_task_data(updates)
            
            # Validate update
            errors = TaskValidator.validate_task_update(current_data, updates)
            if errors:
                # Check if errors are related to completed task restrictions
                for error in errors:
                    if "Cannot update difficulty for completed task" in error:
                        raise TaskStateError(
                            f"Cannot change difficulty of completed task {task_id}. "
                            "This would affect XP history and player progression."
                        )
                    elif "Cannot transition from Completed" in error:
                        raise TaskStateError(
                            f"Cannot change status of completed task {task_id} away from completed. "
                            "This would affect XP history and player progression."
                        )
                    elif "Title validation error" in error:
                        raise TaskValidationError(f"Title validation failed: {error.split(': ', 1)[1]}")
                
                # For other validation errors, raise as TaskValidationError
                raise TaskValidationError(f"Task update validation failed: {'; '.join(errors)}")
            
            # Special handling for completed tasks (additional check)
            if task.is_completed:
                restricted_fields = ['difficulty', 'status']
                for field in restricted_fields:
                    if field in updates:
                        if field == 'difficulty':
                            raise TaskStateError(
                                f"Cannot change difficulty of completed task {task_id}. "
                                "This would affect XP history and player progression."
                            )
                        elif field == 'status' and updates[field] != TaskStatus.COMPLETED:
                            raise TaskStateError(
                                f"Cannot change status of completed task {task_id} away from completed. "
                                "This would affect XP history and player progression."
                            )
            
            # Apply updates with proper validation
            for field, value in updates.items():
                if field == 'title':
                    old_title = task.title
                    task.title = value
                    try:
                        task._validate_title()  # Re-validate title
                    except ValueError as e:
                        task.title = old_title  # Restore original
                        raise TaskValidationError(f"Title validation failed: {e}")
                        
                elif field == 'difficulty':
                    try:
                        task.update_difficulty(value)
                        logger.info(f"Task {task_id} difficulty changed from {original_difficulty} to {value}, XP updated from {original_xp} to {task.xp_reward}")
                    except ValueError as e:
                        raise TaskStateError(f"Cannot update difficulty: {e}")
                        
                elif field == 'priority':
                    task.priority = value
                    
                elif field == 'notes':
                    task.notes = value
                    
                elif field == 'status':
                    try:
                        task.update_status(value)
                        logger.info(f"Task {task_id} status changed to {value}")
                    except ValueError as e:
                        raise TaskStateError(f"Invalid status transition: {e}")
            
            # Save data
            self._save_data()
            
            # Notify observers
            self._notify_observers('updated', task)
            
            logger.info(f"Updated task: {task.title} ({task.id})")
            return task
            
        except (TaskNotFoundError, TaskValidationError, TaskStateError):
            raise
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            raise TaskManagerError(f"Failed to update task: {e}") from e
    
    def complete_task(self, task_id: str) -> Tuple[Task, int]:
        """Complete task and return task + XP earned.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Tuple[Task, int]: (completed task, XP earned)
            
        Raises:
            TaskNotFoundError: If task doesn't exist
            TaskStateError: If task is already completed
            TaskManagerError: If completion fails
        """
        try:
            # Get task
            task = self.get_task(task_id)
            
            # Check if already completed
            if task.is_completed:
                raise TaskStateError(f"Task {task_id} is already completed")
            
            # Calculate XP reward
            xp_earned = XPCalculator.calculate_total_xp(task, self._player_data)
            
            # Complete task
            task.complete()
            
            # Update player data
            new_level, level_up = self._player_data.complete_task(xp_earned, task.difficulty.name)
            
            # Save data
            self._save_data()
            
            # Notify observers
            self._notify_observers('completed', task)
            
            logger.info(f"Completed task: {task.title} ({task.id}) - Earned {xp_earned} XP")
            
            if level_up:
                logger.info(f"Player leveled up to level {new_level}!")
            
            return task, xp_earned
            
        except (TaskNotFoundError, TaskStateError):
            raise
        except Exception as e:
            logger.error(f"Failed to complete task {task_id}: {e}")
            raise TaskManagerError(f"Failed to complete task: {e}") from e
    
    def delete_task(self, task_id: str, force: bool = False) -> dict:
        """Delete task with comprehensive safety checks and warnings.
        
        Args:
            task_id: Task identifier
            force: Force deletion even for completed tasks
            
        Returns:
            dict: Deletion result with warnings and task info
            
        Raises:
            TaskNotFoundError: If task doesn't exist
            TaskStateError: If trying to delete completed task without force
            TaskManagerError: If deletion fails
        """
        try:
            # Get task
            task = self.get_task(task_id)
            
            # Prepare result with task information
            result = {
                'success': False,
                'task_info': {
                    'id': task.id,
                    'title': task.title,
                    'status': task.status.name,
                    'difficulty': task.difficulty.name,
                    'xp_reward': task.xp_reward,
                    'is_completed': task.is_completed,
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None
                },
                'warnings': [],
                'requires_confirmation': False
            }
            
            # Safety checks and warnings
            if task.is_completed:
                if not force:
                    result['requires_confirmation'] = True
                    result['warnings'].append(
                        f"Task '{task.title}' is completed and has awarded {task.xp_reward} XP. "
                        "Deleting it will not affect your earned XP, but the task history will be lost permanently."
                    )
                    raise TaskStateError(
                        f"Cannot delete completed task '{task.title}' ({task_id}) without confirmation. "
                        "Use force=True to confirm deletion of completed tasks."
                    )
                else:
                    result['warnings'].append(
                        f"Deleting completed task '{task.title}' - XP history will be preserved but task record will be lost."
                    )
            
            # Additional warnings for active tasks
            if task.status == TaskStatus.ACTIVE:
                result['warnings'].append(
                    f"Deleting active task '{task.title}' - consider marking as blocked or pending instead."
                )
            
            # High priority task warning
            if task.priority in [TaskPriority.HIGH, TaskPriority.CRITICAL]:
                result['warnings'].append(
                    f"Deleting {task.priority.name.lower()} priority task '{task.title}' - ensure this is intentional."
                )
            
            # Create backup before deletion
            try:
                self._data_manager.create_backup()
                logger.debug("Created backup before task deletion")
            except Exception as e:
                logger.warning(f"Failed to create backup before deletion: {e}")
                result['warnings'].append("Could not create backup before deletion")
            
            # Remove task
            del self._tasks[task_id]
            
            # Save data
            self._save_data()
            
            # Notify observers
            self._notify_observers('deleted', task)
            
            result['success'] = True
            logger.info(f"Deleted task: {task.title} ({task.id}) - Warnings: {len(result['warnings'])}")
            
            return result
            
        except (TaskNotFoundError, TaskStateError):
            raise
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            raise TaskManagerError(f"Failed to delete task: {e}") from e
    
    def get_task_count(self) -> Dict[str, int]:
        """Get task count statistics.
        
        Returns:
            Dict[str, int]: Task counts by status
        """
        counts = {status.name.lower(): 0 for status in TaskStatus}
        
        for task in self._tasks.values():
            counts[task.status.name.lower()] += 1
        
        counts['total'] = len(self._tasks)
        return counts
    
    def get_player_data(self) -> PlayerData:
        """Get current player data.
        
        Returns:
            PlayerData: Current player data
        """
        return self._player_data
    
    def preview_task_xp(self, task_id: str) -> dict:
        """Preview XP reward for completing a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            dict: XP reward breakdown
            
        Raises:
            TaskNotFoundError: If task doesn't exist
        """
        task = self.get_task(task_id)
        return XPCalculator.preview_xp_reward(task, self._player_data)
    
    def bulk_update_status(self, task_ids: List[str], new_status: TaskStatus) -> List[Task]:
        """Update status for multiple tasks.
        
        Args:
            task_ids: List of task identifiers
            new_status: New status to apply
            
        Returns:
            List[Task]: Successfully updated tasks
            
        Raises:
            TaskManagerError: If bulk update fails
        """
        updated_tasks = []
        errors = []
        
        for task_id in task_ids:
            try:
                task = self.update_task(task_id, status=new_status)
                updated_tasks.append(task)
            except Exception as e:
                errors.append(f"Task {task_id}: {str(e)}")
        
        if errors:
            logger.warning(f"Bulk update had errors: {'; '.join(errors)}")
        
        logger.info(f"Bulk updated {len(updated_tasks)} tasks to {new_status}")
        return updated_tasks
    
    def search_tasks(self, query: str, fields: Optional[List[str]] = None) -> List[Task]:
        """Search tasks by text query.
        
        Args:
            query: Search query
            fields: Fields to search in (default: title, notes)
            
        Returns:
            List[Task]: Matching tasks
        """
        if not query.strip():
            return []
        
        if fields is None:
            fields = ['title', 'notes']
        
        query_lower = query.lower()
        matching_tasks = []
        
        for task in self._tasks.values():
            for field in fields:
                field_value = getattr(task, field, None)
                if field_value and query_lower in str(field_value).lower():
                    matching_tasks.append(task)
                    break
        
        return matching_tasks
    
    def check_deletion_safety(self, task_id: str) -> dict:
        """Check if task deletion requires confirmation and generate warnings.
        
        Args:
            task_id: Task identifier
            
        Returns:
            dict: Safety check results with warnings and confirmation requirements
            
        Raises:
            TaskNotFoundError: If task doesn't exist
        """
        try:
            task = self.get_task(task_id)
            
            result = {
                'requires_confirmation': False,
                'warnings': [],
                'safety_level': 'safe',  # safe, caution, danger
                'task_info': {
                    'title': task.title,
                    'status': task.status.name,
                    'difficulty': task.difficulty.name,
                    'priority': task.priority.name,
                    'is_completed': task.is_completed,
                    'xp_reward': task.xp_reward
                }
            }
            
            # Check for completed task
            if task.is_completed:
                result['requires_confirmation'] = True
                result['safety_level'] = 'danger'
                result['warnings'].append(
                    f"This completed task has awarded {task.xp_reward} XP. "
                    "Deletion will not affect your earned XP but will remove the task from history."
                )
            
            # Check for active task
            elif task.status == TaskStatus.ACTIVE:
                result['requires_confirmation'] = True
                result['safety_level'] = 'caution'
                result['warnings'].append(
                    "This task is currently active. Consider marking it as blocked or pending instead."
                )
            
            # Check for high priority
            if task.priority in [TaskPriority.HIGH, TaskPriority.CRITICAL]:
                result['requires_confirmation'] = True
                if result['safety_level'] == 'safe':
                    result['safety_level'] = 'caution'
                result['warnings'].append(
                    f"This is a {task.priority.name.lower()} priority task. Ensure deletion is intentional."
                )
            
            # Check for high XP value
            if task.xp_reward >= 50:  # Hard tasks
                if result['safety_level'] == 'safe':
                    result['safety_level'] = 'caution'
                result['warnings'].append(
                    f"This task has a high XP value ({task.xp_reward} XP). Consider completing it instead."
                )
            
            return result
            
        except TaskNotFoundError:
            raise
    
    def validate_task_update(self, task_id: str, **updates) -> dict:
        """Validate task update without applying changes.
        
        Args:
            task_id: Task identifier
            **updates: Fields to update
            
        Returns:
            dict: Validation results with errors and warnings
            
        Raises:
            TaskNotFoundError: If task doesn't exist
        """
        try:
            task = self.get_task(task_id)
            
            result = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'changes': {}
            }
            
            # Create current data dict
            current_data = {
                'id': task.id,
                'title': task.title,
                'difficulty': task.difficulty,
                'priority': task.priority,
                'status': task.status,
                'notes': task.notes,
                'created_at': task.created_at,
                'completed_at': task.completed_at
            }
            
            # Sanitize update data
            sanitized_updates = TaskValidator.sanitize_task_data(updates)
            
            # Validate update
            validation_errors = TaskValidator.validate_task_update(current_data, sanitized_updates)
            if validation_errors:
                result['valid'] = False
                result['errors'].extend(validation_errors)
            
            # Check for changes and generate warnings
            for field, new_value in sanitized_updates.items():
                current_value = getattr(task, field)
                
                if current_value != new_value:
                    result['changes'][field] = {
                        'from': current_value.name if hasattr(current_value, 'name') else current_value,
                        'to': new_value.name if hasattr(new_value, 'name') else new_value
                    }
                    
                    # Generate specific warnings
                    if field == 'difficulty' and task.is_completed:
                        result['errors'].append("Cannot change difficulty of completed task")
                        result['valid'] = False
                    elif field == 'difficulty':
                        old_xp = current_value.xp_value
                        new_xp = new_value.xp_value
                        if old_xp != new_xp:
                            result['warnings'].append(
                                f"Difficulty change will update XP reward from {old_xp} to {new_xp}"
                            )
                    elif field == 'status':
                        if current_value == TaskStatus.COMPLETED and new_value != TaskStatus.COMPLETED:
                            result['errors'].append("Cannot change status away from completed")
                            result['valid'] = False
                        elif new_value == TaskStatus.COMPLETED:
                            result['warnings'].append(
                                f"Completing task will award {task.xp_reward} XP"
                            )
                    elif field == 'priority':
                        if new_value in [TaskPriority.HIGH, TaskPriority.CRITICAL]:
                            result['warnings'].append(
                                f"Setting task to {new_value.name.lower()} priority"
                            )
            
            return result
            
        except TaskNotFoundError:
            raise
    
    def load_data(self) -> None:
        """Public method to reload data from storage."""
        self._load_data()
    
    def save_data(self) -> None:
        """Public method to save data to storage."""
        self._save_data()