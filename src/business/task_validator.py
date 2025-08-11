"""Task validation logic with comprehensive validation rules."""

from typing import List, Optional, Dict, Any
import re
from datetime import datetime

from ..models.enums import TaskDifficulty, TaskPriority, TaskStatus


class TaskValidationError(Exception):
    """Raised when task data validation fails."""
    pass


class TaskValidator:
    """Comprehensive task validation with business rules."""
    
    # Validation constants
    MIN_TITLE_LENGTH = 1
    MAX_TITLE_LENGTH = 200
    MAX_NOTES_LENGTH = 1000
    
    # Title validation patterns
    INVALID_TITLE_PATTERNS = [
        r'^\s*$',  # Only whitespace
        r'^[^a-zA-Z0-9]',  # Starts with special character
    ]
    
    @classmethod
    def validate_title(cls, title: str) -> bool:
        """Validate task title requirements.
        
        Args:
            title: Task title to validate
            
        Returns:
            bool: True if title is valid
            
        Raises:
            TaskValidationError: If title validation fails
        """
        if not isinstance(title, str):
            raise TaskValidationError("Title must be a string")
        
        # Check for empty or whitespace-only strings first
        if not title or not title.strip():
            raise TaskValidationError("Title cannot be empty")
        
        # Check length
        if len(title) > cls.MAX_TITLE_LENGTH:
            raise TaskValidationError(f"Title cannot exceed {cls.MAX_TITLE_LENGTH} characters")
        
        # Check for invalid patterns (excluding whitespace check since we handled it above)
        invalid_patterns = [r'^[^a-zA-Z0-9]']  # Starts with special character
        for pattern in invalid_patterns:
            if re.match(pattern, title.strip()):
                raise TaskValidationError("Title cannot start with special characters")
        
        return True
    
    @classmethod
    def validate_difficulty(cls, difficulty: Any) -> bool:
        """Validate task difficulty.
        
        Args:
            difficulty: Task difficulty to validate
            
        Returns:
            bool: True if difficulty is valid
            
        Raises:
            TaskValidationError: If difficulty validation fails
        """
        if not isinstance(difficulty, TaskDifficulty):
            raise TaskValidationError("Difficulty must be a TaskDifficulty enum value")
        
        return True
    
    @classmethod
    def validate_priority(cls, priority: Any) -> bool:
        """Validate task priority.
        
        Args:
            priority: Task priority to validate
            
        Returns:
            bool: True if priority is valid
            
        Raises:
            TaskValidationError: If priority validation fails
        """
        if not isinstance(priority, TaskPriority):
            raise TaskValidationError("Priority must be a TaskPriority enum value")
        
        return True
    
    @classmethod
    def validate_status(cls, status: Any) -> bool:
        """Validate task status.
        
        Args:
            status: Task status to validate
            
        Returns:
            bool: True if status is valid
            
        Raises:
            TaskValidationError: If status validation fails
        """
        if not isinstance(status, TaskStatus):
            raise TaskValidationError("Status must be a TaskStatus enum value")
        
        return True
    
    @classmethod
    def validate_notes(cls, notes: Optional[str]) -> bool:
        """Validate task notes.
        
        Args:
            notes: Task notes to validate
            
        Returns:
            bool: True if notes are valid
            
        Raises:
            TaskValidationError: If notes validation fails
        """
        if notes is None:
            return True
        
        if not isinstance(notes, str):
            raise TaskValidationError("Notes must be a string or None")
        
        if len(notes) > cls.MAX_NOTES_LENGTH:
            raise TaskValidationError(f"Notes cannot exceed {cls.MAX_NOTES_LENGTH} characters")
        
        return True
    
    @classmethod
    def validate_status_transition(cls, current: TaskStatus, new: TaskStatus) -> bool:
        """Validate allowed status transitions.
        
        Args:
            current: Current task status
            new: New task status
            
        Returns:
            bool: True if transition is valid
            
        Raises:
            TaskValidationError: If transition validation fails
        """
        if not isinstance(current, TaskStatus) or not isinstance(new, TaskStatus):
            raise TaskValidationError("Both current and new status must be TaskStatus enum values")
        
        if not current.can_transition_to(new):
            raise TaskValidationError(f"Cannot transition from {current} to {new}")
        
        return True
    
    @classmethod
    def validate_task_data(cls, task_data: Dict[str, Any]) -> List[str]:
        """Comprehensive task data validation.
        
        Args:
            task_data: Dictionary containing task data
            
        Returns:
            List[str]: List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate required fields
        required_fields = ['title', 'difficulty', 'priority']
        for field in required_fields:
            if field not in task_data:
                errors.append(f"Missing required field: {field}")
                continue
        
        # Validate title
        if 'title' in task_data:
            try:
                cls.validate_title(task_data['title'])
            except TaskValidationError as e:
                errors.append(f"Title validation error: {str(e)}")
        
        # Validate difficulty
        if 'difficulty' in task_data:
            try:
                if isinstance(task_data['difficulty'], str):
                    # Try to convert string to enum
                    try:
                        difficulty = TaskDifficulty[task_data['difficulty'].upper()]
                        task_data['difficulty'] = difficulty
                    except KeyError:
                        errors.append(f"Invalid difficulty: {task_data['difficulty']}")
                else:
                    cls.validate_difficulty(task_data['difficulty'])
            except TaskValidationError as e:
                errors.append(f"Difficulty validation error: {str(e)}")
        
        # Validate priority
        if 'priority' in task_data:
            try:
                if isinstance(task_data['priority'], str):
                    # Try to convert string to enum
                    try:
                        priority = TaskPriority[task_data['priority'].upper()]
                        task_data['priority'] = priority
                    except KeyError:
                        errors.append(f"Invalid priority: {task_data['priority']}")
                else:
                    cls.validate_priority(task_data['priority'])
            except TaskValidationError as e:
                errors.append(f"Priority validation error: {str(e)}")
        
        # Validate status if provided
        if 'status' in task_data:
            try:
                if isinstance(task_data['status'], str):
                    # Try to convert string to enum
                    try:
                        status = TaskStatus[task_data['status'].upper()]
                        task_data['status'] = status
                    except KeyError:
                        errors.append(f"Invalid status: {task_data['status']}")
                else:
                    cls.validate_status(task_data['status'])
            except TaskValidationError as e:
                errors.append(f"Status validation error: {str(e)}")
        
        # Validate notes if provided
        if 'notes' in task_data:
            try:
                cls.validate_notes(task_data['notes'])
            except TaskValidationError as e:
                errors.append(f"Notes validation error: {str(e)}")
        
        # Validate timestamps if provided
        if 'created_at' in task_data:
            try:
                if isinstance(task_data['created_at'], str):
                    datetime.fromisoformat(task_data['created_at'])
                elif not isinstance(task_data['created_at'], datetime):
                    errors.append("created_at must be a datetime or ISO format string")
            except ValueError:
                errors.append("Invalid created_at timestamp format")
        
        if 'completed_at' in task_data and task_data['completed_at'] is not None:
            try:
                if isinstance(task_data['completed_at'], str):
                    datetime.fromisoformat(task_data['completed_at'])
                elif not isinstance(task_data['completed_at'], datetime):
                    errors.append("completed_at must be a datetime, ISO format string, or None")
            except ValueError:
                errors.append("Invalid completed_at timestamp format")
        
        return errors
    
    @classmethod
    def validate_task_update(cls, current_task_data: Dict[str, Any], 
                           update_data: Dict[str, Any]) -> List[str]:
        """Validate task update operations.
        
        Args:
            current_task_data: Current task data
            update_data: Data to update
            
        Returns:
            List[str]: List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check if trying to update immutable fields
        immutable_fields = ['id', 'created_at']
        for field in immutable_fields:
            if field in update_data:
                errors.append(f"Cannot update immutable field: {field}")
        
        # If task is completed, restrict certain updates
        current_status = current_task_data.get('status')
        if current_status == TaskStatus.COMPLETED:
            restricted_fields = ['difficulty', 'xp_reward']
            for field in restricted_fields:
                if field in update_data:
                    errors.append(f"Cannot update {field} for completed task")
        
        # Validate status transitions
        if 'status' in update_data:
            try:
                cls.validate_status_transition(current_status, update_data['status'])
            except TaskValidationError as e:
                errors.append(str(e))
        
        # Validate individual fields in update data (but don't require all fields for updates)
        update_copy = update_data.copy()
        field_errors = cls._validate_partial_task_data(update_copy)
        errors.extend(field_errors)
        
        return errors
    
    @classmethod
    def _validate_partial_task_data(cls, task_data: Dict[str, Any]) -> List[str]:
        """Validate partial task data (for updates, not requiring all fields).
        
        Args:
            task_data: Dictionary containing partial task data
            
        Returns:
            List[str]: List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate title if provided
        if 'title' in task_data:
            try:
                cls.validate_title(task_data['title'])
            except TaskValidationError as e:
                errors.append(f"Title validation error: {str(e)}")
        
        # Validate difficulty if provided
        if 'difficulty' in task_data:
            try:
                if isinstance(task_data['difficulty'], str):
                    # Try to convert string to enum
                    try:
                        difficulty = TaskDifficulty[task_data['difficulty'].upper()]
                        task_data['difficulty'] = difficulty
                    except KeyError:
                        errors.append(f"Invalid difficulty: {task_data['difficulty']}")
                else:
                    cls.validate_difficulty(task_data['difficulty'])
            except TaskValidationError as e:
                errors.append(f"Difficulty validation error: {str(e)}")
        
        # Validate priority if provided
        if 'priority' in task_data:
            try:
                if isinstance(task_data['priority'], str):
                    # Try to convert string to enum
                    try:
                        priority = TaskPriority[task_data['priority'].upper()]
                        task_data['priority'] = priority
                    except KeyError:
                        errors.append(f"Invalid priority: {task_data['priority']}")
                else:
                    cls.validate_priority(task_data['priority'])
            except TaskValidationError as e:
                errors.append(f"Priority validation error: {str(e)}")
        
        # Validate status if provided
        if 'status' in task_data:
            try:
                if isinstance(task_data['status'], str):
                    # Try to convert string to enum
                    try:
                        status = TaskStatus[task_data['status'].upper()]
                        task_data['status'] = status
                    except KeyError:
                        errors.append(f"Invalid status: {task_data['status']}")
                else:
                    cls.validate_status(task_data['status'])
            except TaskValidationError as e:
                errors.append(f"Status validation error: {str(e)}")
        
        # Validate notes if provided
        if 'notes' in task_data:
            try:
                cls.validate_notes(task_data['notes'])
            except TaskValidationError as e:
                errors.append(f"Notes validation error: {str(e)}")
        
        # Validate timestamps if provided
        if 'created_at' in task_data:
            try:
                if isinstance(task_data['created_at'], str):
                    datetime.fromisoformat(task_data['created_at'])
                elif not isinstance(task_data['created_at'], datetime):
                    errors.append("created_at must be a datetime or ISO format string")
            except ValueError:
                errors.append("Invalid created_at timestamp format")
        
        if 'completed_at' in task_data and task_data['completed_at'] is not None:
            try:
                if isinstance(task_data['completed_at'], str):
                    datetime.fromisoformat(task_data['completed_at'])
                elif not isinstance(task_data['completed_at'], datetime):
                    errors.append("completed_at must be a datetime, ISO format string, or None")
            except ValueError:
                errors.append("Invalid completed_at timestamp format")
        
        return errors
    
    @classmethod
    def sanitize_task_data(cls, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize and clean task data.
        
        Args:
            task_data: Raw task data
            
        Returns:
            Dict[str, Any]: Sanitized task data
        """
        sanitized = task_data.copy()
        
        # Clean title
        if 'title' in sanitized and isinstance(sanitized['title'], str):
            sanitized['title'] = sanitized['title'].strip()
        
        # Clean notes
        if 'notes' in sanitized and isinstance(sanitized['notes'], str):
            sanitized['notes'] = sanitized['notes'].strip() or None
        
        # Convert string enums to enum objects
        if 'difficulty' in sanitized and isinstance(sanitized['difficulty'], str):
            try:
                sanitized['difficulty'] = TaskDifficulty[sanitized['difficulty'].upper()]
            except KeyError:
                pass  # Let validation catch this
        
        if 'priority' in sanitized and isinstance(sanitized['priority'], str):
            try:
                sanitized['priority'] = TaskPriority[sanitized['priority'].upper()]
            except KeyError:
                pass  # Let validation catch this
        
        if 'status' in sanitized and isinstance(sanitized['status'], str):
            try:
                sanitized['status'] = TaskStatus[sanitized['status'].upper()]
            except KeyError:
                pass  # Let validation catch this
        
        return sanitized