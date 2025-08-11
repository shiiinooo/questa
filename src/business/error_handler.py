"""Comprehensive error handling system with user-friendly messages and recovery mechanisms."""

import logging
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum
from datetime import datetime

from ..models.enums import TaskStatus, TaskDifficulty, TaskPriority
from .task_validator import TaskValidationError


# Configure logging
logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for user feedback."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors for better handling."""
    VALIDATION = "validation"
    PERSISTENCE = "persistence"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    USER_INPUT = "user_input"


class UserFriendlyError:
    """Container for user-friendly error information."""
    
    def __init__(
        self,
        title: str,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        technical_details: Optional[str] = None,
        suggested_actions: Optional[List[str]] = None,
        recoverable: bool = True,
        recovery_actions: Optional[List[Callable]] = None
    ):
        """Initialize user-friendly error.
        
        Args:
            title: Short error title for display
            message: User-friendly error message
            severity: Error severity level
            category: Error category
            technical_details: Technical error details for logging
            suggested_actions: List of suggested user actions
            recoverable: Whether error is recoverable
            recovery_actions: List of recovery action functions
        """
        self.title = title
        self.message = message
        self.severity = severity
        self.category = category
        self.technical_details = technical_details
        self.suggested_actions = suggested_actions or []
        self.recoverable = recoverable
        self.recovery_actions = recovery_actions or []
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            'title': self.title,
            'message': self.message,
            'severity': self.severity.value,
            'category': self.category.value,
            'technical_details': self.technical_details,
            'suggested_actions': self.suggested_actions,
            'recoverable': self.recoverable,
            'timestamp': self.timestamp.isoformat()
        }


class ErrorHandler:
    """Comprehensive error handler with user-friendly messages and recovery."""
    
    # Error message templates
    ERROR_TEMPLATES = {
        # Validation errors
        'empty_title': {
            'title': 'Invalid Task Title',
            'message': 'Task title cannot be empty. Please enter a descriptive title for your task.',
            'severity': ErrorSeverity.WARNING,
            'category': ErrorCategory.VALIDATION,
            'suggested_actions': ['Enter a clear, descriptive title', 'Use 3-50 characters for best results']
        },
        'title_too_long': {
            'title': 'Title Too Long',
            'message': 'Task title is too long (maximum 200 characters). Please shorten your title.',
            'severity': ErrorSeverity.WARNING,
            'category': ErrorCategory.VALIDATION,
            'suggested_actions': ['Shorten the title to under 200 characters', 'Use notes field for additional details']
        },
        'invalid_difficulty': {
            'title': 'Invalid Difficulty',
            'message': 'Please select a valid difficulty level (Easy, Medium, or Hard).',
            'severity': ErrorSeverity.WARNING,
            'category': ErrorCategory.VALIDATION,
            'suggested_actions': ['Choose Easy (15 XP), Medium (30 XP), or Hard (50 XP)']
        },
        'invalid_priority': {
            'title': 'Invalid Priority',
            'message': 'Please select a valid priority level (Low, Medium, High, or Critical).',
            'severity': ErrorSeverity.WARNING,
            'category': ErrorCategory.VALIDATION,
            'suggested_actions': ['Choose Low, Medium, High, or Critical priority']
        },
        'invalid_status_transition': {
            'title': 'Invalid Status Change',
            'message': 'Cannot change task status from {current} to {new}. This transition is not allowed.',
            'severity': ErrorSeverity.ERROR,
            'category': ErrorCategory.BUSINESS_LOGIC,
            'suggested_actions': ['Check allowed status transitions', 'Use a valid intermediate status']
        },
        
        # Task state errors
        'task_already_completed': {
            'title': 'Task Already Completed',
            'message': 'This task is already completed and cannot be completed again.',
            'severity': ErrorSeverity.WARNING,
            'category': ErrorCategory.BUSINESS_LOGIC,
            'suggested_actions': ['Create a new task if more work is needed', 'Check task status before completing']
        },
        'completed_task_restriction': {
            'title': 'Cannot Modify Completed Task',
            'message': 'Cannot change {field} for completed tasks. This preserves XP history and progression.',
            'severity': ErrorSeverity.ERROR,
            'category': ErrorCategory.BUSINESS_LOGIC,
            'suggested_actions': ['Create a new task with the desired settings', 'Only title and notes can be updated']
        },
        'task_not_found': {
            'title': 'Task Not Found',
            'message': 'The requested task could not be found. It may have been deleted or moved.',
            'severity': ErrorSeverity.ERROR,
            'category': ErrorCategory.BUSINESS_LOGIC,
            'suggested_actions': ['Refresh the task list', 'Check if task was deleted', 'Return to main screen']
        },
        
        # Data persistence errors
        'save_failed': {
            'title': 'Save Failed',
            'message': 'Could not save your changes. Your data may not be preserved.',
            'severity': ErrorSeverity.CRITICAL,
            'category': ErrorCategory.PERSISTENCE,
            'suggested_actions': ['Try saving again', 'Check disk space', 'Restart the application'],
            'recoverable': True
        },
        'load_failed': {
            'title': 'Load Failed',
            'message': 'Could not load task data. Starting with empty task list.',
            'severity': ErrorSeverity.ERROR,
            'category': ErrorCategory.PERSISTENCE,
            'suggested_actions': ['Check if data files exist', 'Restore from backup if available', 'Contact support if data is critical']
        },
        'backup_failed': {
            'title': 'Backup Failed',
            'message': 'Could not create backup before operation. Proceeding without backup.',
            'severity': ErrorSeverity.WARNING,
            'category': ErrorCategory.PERSISTENCE,
            'suggested_actions': ['Check disk space', 'Ensure write permissions', 'Manual backup recommended']
        },
        'data_corruption': {
            'title': 'Data Corruption Detected',
            'message': 'Task data appears to be corrupted. Attempting recovery from backup.',
            'severity': ErrorSeverity.CRITICAL,
            'category': ErrorCategory.PERSISTENCE,
            'suggested_actions': ['Allow automatic recovery', 'Check backup files', 'Contact support if recovery fails']
        },
        
        # System errors
        'unexpected_error': {
            'title': 'Unexpected Error',
            'message': 'An unexpected error occurred. The operation could not be completed.',
            'severity': ErrorSeverity.ERROR,
            'category': ErrorCategory.SYSTEM,
            'suggested_actions': ['Try the operation again', 'Restart the application', 'Check system resources']
        },
        'permission_denied': {
            'title': 'Permission Denied',
            'message': 'Cannot access or modify files. Check file permissions.',
            'severity': ErrorSeverity.ERROR,
            'category': ErrorCategory.SYSTEM,
            'suggested_actions': ['Check file permissions', 'Run with appropriate privileges', 'Contact system administrator']
        },
        'disk_space_low': {
            'title': 'Low Disk Space',
            'message': 'Available disk space is low. Save operations may fail.',
            'severity': ErrorSeverity.WARNING,
            'category': ErrorCategory.SYSTEM,
            'suggested_actions': ['Free up disk space', 'Move files to another location', 'Clean temporary files']
        }
    }
    
    @classmethod
    def handle_validation_error(cls, error: Exception, context: Optional[Dict[str, Any]] = None) -> UserFriendlyError:
        """Handle validation errors with user-friendly messages.
        
        Args:
            error: The validation error
            context: Additional context for error handling
            
        Returns:
            UserFriendlyError: User-friendly error information
        """
        error_msg = str(error).lower()
        context = context or {}
        
        # Map specific validation errors to templates
        if 'title cannot be empty' in error_msg or 'title is required' in error_msg:
            template = cls.ERROR_TEMPLATES['empty_title']
        elif 'title cannot exceed' in error_msg or 'title too long' in error_msg:
            template = cls.ERROR_TEMPLATES['title_too_long']
        elif 'difficulty' in error_msg and ('invalid' in error_msg or 'validation error' in error_msg):
            template = cls.ERROR_TEMPLATES['invalid_difficulty']
        elif 'priority' in error_msg and 'invalid' in error_msg:
            template = cls.ERROR_TEMPLATES['invalid_priority']
        elif 'cannot transition' in error_msg:
            template = cls.ERROR_TEMPLATES['invalid_status_transition'].copy()
            # Extract current and new status from context if available
            if 'current_status' in context and 'new_status' in context:
                template['message'] = template['message'].format(
                    current=context['current_status'],
                    new=context['new_status']
                )
        else:
            # Generic validation error
            template = {
                'title': 'Validation Error',
                'message': f'Input validation failed: {str(error)}',
                'severity': ErrorSeverity.WARNING,
                'category': ErrorCategory.VALIDATION,
                'suggested_actions': ['Check your input and try again', 'Ensure all required fields are filled']
            }
        
        return UserFriendlyError(
            title=template['title'],
            message=template['message'],
            severity=template['severity'],
            category=template['category'],
            technical_details=str(error),
            suggested_actions=template['suggested_actions']
        )
    
    @classmethod
    def handle_business_logic_error(cls, error: Exception, context: Optional[Dict[str, Any]] = None) -> UserFriendlyError:
        """Handle business logic errors with user-friendly messages.
        
        Args:
            error: The business logic error
            context: Additional context for error handling
            
        Returns:
            UserFriendlyError: User-friendly error information
        """
        error_msg = str(error).lower()
        context = context or {}
        
        # Map specific business logic errors to templates
        if 'already completed' in error_msg:
            template = cls.ERROR_TEMPLATES['task_already_completed']
        elif 'cannot change' in error_msg and 'completed task' in error_msg:
            template = cls.ERROR_TEMPLATES['completed_task_restriction'].copy()
            # Extract field name from context
            if 'field' in context:
                template['message'] = template['message'].format(field=context['field'])
        elif 'not found' in error_msg:
            template = cls.ERROR_TEMPLATES['task_not_found']
        elif 'cannot transition' in error_msg:
            template = cls.ERROR_TEMPLATES['invalid_status_transition'].copy()
            if 'current_status' in context and 'new_status' in context:
                template['message'] = template['message'].format(
                    current=context['current_status'],
                    new=context['new_status']
                )
        else:
            # Generic business logic error
            template = {
                'title': 'Operation Failed',
                'message': f'The operation could not be completed: {str(error)}',
                'severity': ErrorSeverity.ERROR,
                'category': ErrorCategory.BUSINESS_LOGIC,
                'suggested_actions': ['Check task status and try again', 'Refresh the task list']
            }
        
        return UserFriendlyError(
            title=template['title'],
            message=template['message'],
            severity=template['severity'],
            category=template['category'],
            technical_details=str(error),
            suggested_actions=template['suggested_actions']
        )
    
    @classmethod
    def handle_persistence_error(cls, error: Exception, context: Optional[Dict[str, Any]] = None) -> UserFriendlyError:
        """Handle data persistence errors with user-friendly messages.
        
        Args:
            error: The persistence error
            context: Additional context for error handling
            
        Returns:
            UserFriendlyError: User-friendly error information
        """
        error_msg = str(error).lower()
        context = context or {}
        
        # Map specific persistence errors to templates
        if 'save' in error_msg and 'failed' in error_msg:
            template = cls.ERROR_TEMPLATES['save_failed']
        elif 'load' in error_msg and 'failed' in error_msg:
            template = cls.ERROR_TEMPLATES['load_failed']
        elif 'backup' in error_msg and 'failed' in error_msg:
            template = cls.ERROR_TEMPLATES['backup_failed']
        elif 'corrupt' in error_msg or 'invalid json' in error_msg:
            template = cls.ERROR_TEMPLATES['data_corruption']
        elif 'permission denied' in error_msg or 'access denied' in error_msg:
            template = cls.ERROR_TEMPLATES['permission_denied']
        elif 'no space' in error_msg or 'disk full' in error_msg:
            template = cls.ERROR_TEMPLATES['disk_space_low']
        else:
            # Generic persistence error
            template = {
                'title': 'Data Error',
                'message': f'A data operation failed: {str(error)}',
                'severity': ErrorSeverity.ERROR,
                'category': ErrorCategory.PERSISTENCE,
                'suggested_actions': ['Try the operation again', 'Check file permissions', 'Ensure adequate disk space']
            }
        
        return UserFriendlyError(
            title=template['title'],
            message=template['message'],
            severity=template['severity'],
            category=template['category'],
            technical_details=str(error),
            suggested_actions=template['suggested_actions'],
            recoverable=template.get('recoverable', True)
        )
    
    @classmethod
    def handle_system_error(cls, error: Exception, context: Optional[Dict[str, Any]] = None) -> UserFriendlyError:
        """Handle system errors with user-friendly messages.
        
        Args:
            error: The system error
            context: Additional context for error handling
            
        Returns:
            UserFriendlyError: User-friendly error information
        """
        error_msg = str(error).lower()
        
        # Map specific system errors to templates
        if 'permission denied' in error_msg:
            template = cls.ERROR_TEMPLATES['permission_denied']
        elif 'no space' in error_msg or 'disk full' in error_msg:
            template = cls.ERROR_TEMPLATES['disk_space_low']
        else:
            template = cls.ERROR_TEMPLATES['unexpected_error']
        
        return UserFriendlyError(
            title=template['title'],
            message=template['message'],
            severity=template['severity'],
            category=template['category'],
            technical_details=str(error),
            suggested_actions=template['suggested_actions']
        )
    
    @classmethod
    def handle_generic_error(cls, error: Exception, context: Optional[Dict[str, Any]] = None) -> UserFriendlyError:
        """Handle generic errors with fallback user-friendly messages.
        
        Args:
            error: The generic error
            context: Additional context for error handling
            
        Returns:
            UserFriendlyError: User-friendly error information
        """
        # Log the error for debugging
        logger.error(f"Unhandled error: {error}", exc_info=True)
        
        return UserFriendlyError(
            title="Unexpected Error",
            message="An unexpected error occurred. Please try again or contact support if the problem persists.",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SYSTEM,
            technical_details=str(error),
            suggested_actions=[
                "Try the operation again",
                "Restart the application",
                "Contact support if the problem persists"
            ]
        )
    
    @classmethod
    def create_confirmation_requirement(
        cls,
        title: str,
        message: str,
        warning_level: str = "caution",
        consequences: Optional[List[str]] = None,
        alternatives: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a confirmation requirement for destructive actions.
        
        Args:
            title: Confirmation dialog title
            message: Main confirmation message
            warning_level: Level of warning (safe, caution, danger)
            consequences: List of consequences of the action
            alternatives: List of alternative actions
            
        Returns:
            Dict containing confirmation requirement details
        """
        return {
            'title': title,
            'message': message,
            'warning_level': warning_level,
            'consequences': consequences or [],
            'alternatives': alternatives or [],
            'timestamp': datetime.now().isoformat()
        }
    
    @classmethod
    def create_success_feedback(
        cls,
        title: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        next_actions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create success feedback for completed operations.
        
        Args:
            title: Success message title
            message: Main success message
            details: Additional details about the operation
            next_actions: Suggested next actions
            
        Returns:
            Dict containing success feedback details
        """
        return {
            'title': title,
            'message': message,
            'details': details or {},
            'next_actions': next_actions or [],
            'timestamp': datetime.now().isoformat()
        }
    
    @classmethod
    def get_error_recovery_suggestions(cls, error_category: ErrorCategory) -> List[str]:
        """Get recovery suggestions based on error category.
        
        Args:
            error_category: Category of the error
            
        Returns:
            List of recovery suggestions
        """
        recovery_suggestions = {
            ErrorCategory.VALIDATION: [
                "Check your input and correct any errors",
                "Ensure all required fields are filled",
                "Verify data formats and constraints"
            ],
            ErrorCategory.PERSISTENCE: [
                "Try the operation again",
                "Check file permissions and disk space",
                "Restart the application if problems persist",
                "Restore from backup if available"
            ],
            ErrorCategory.BUSINESS_LOGIC: [
                "Check task status and constraints",
                "Refresh the task list",
                "Try a different approach or sequence"
            ],
            ErrorCategory.SYSTEM: [
                "Restart the application",
                "Check system resources",
                "Contact system administrator if needed"
            ],
            ErrorCategory.USER_INPUT: [
                "Review your input and try again",
                "Check for typos or formatting issues",
                "Use the help system for guidance"
            ]
        }
        
        return recovery_suggestions.get(error_category, [
            "Try the operation again",
            "Restart the application",
            "Contact support if the problem persists"
        ])