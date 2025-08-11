"""Visual feedback system for successful operations and state changes."""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widget import Widget
from textual.widgets import Label, Static, ProgressBar
from textual.reactive import reactive
from textual.timer import Timer
from textual.message import Message

from ..business.error_handler import ErrorSeverity


class FeedbackType:
    """Types of feedback messages."""
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    PROGRESS = "progress"


class FeedbackMessage:
    """Container for feedback message information."""
    
    def __init__(
        self,
        message: str,
        feedback_type: str = FeedbackType.INFO,
        title: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        duration: float = 3.0,
        dismissible: bool = True,
        actions: Optional[List[Dict[str, Any]]] = None
    ):
        """Initialize feedback message.
        
        Args:
            message: Main feedback message
            feedback_type: Type of feedback (success, info, warning, error, progress)
            title: Optional title for the message
            details: Additional details about the operation
            duration: How long to show the message (0 for permanent)
            dismissible: Whether user can dismiss the message
            actions: Optional action buttons
        """
        self.message = message
        self.feedback_type = feedback_type
        self.title = title
        self.details = details or {}
        self.duration = duration
        self.dismissible = dismissible
        self.actions = actions or []
        self.timestamp = datetime.now()
        self.id = f"feedback_{self.timestamp.timestamp()}"


class FeedbackWidget(Widget):
    """Widget for displaying individual feedback messages."""
    
    DEFAULT_CSS = """
    FeedbackWidget {
        height: auto;
        margin: 1 0;
        padding: 1;
        border: solid transparent;
        background: $surface;
    }
    
    FeedbackWidget.success {
        background: $success;
        color: $success-lighten-3;
        border: solid $success-darken-1;
    }
    
    FeedbackWidget.info {
        background: $primary;
        color: $primary-lighten-3;
        border: solid $primary-darken-1;
    }
    
    FeedbackWidget.warning {
        background: $warning;
        color: $warning-lighten-3;
        border: solid $warning-darken-1;
    }
    
    FeedbackWidget.error {
        background: $error;
        color: $error-lighten-3;
        border: solid $error-darken-1;
    }
    
    FeedbackWidget.progress {
        background: $accent;
        color: $accent-lighten-3;
        border: solid $accent-darken-1;
    }
    
    FeedbackWidget .feedback-header {
        text-style: bold;
        margin-bottom: 1;
    }
    
    FeedbackWidget .feedback-message {
        margin-bottom: 1;
    }
    
    FeedbackWidget .feedback-details {
        color: rgba(255, 255, 255, 0.8);
        text-style: italic;
        margin-bottom: 1;
    }
    
    FeedbackWidget .feedback-timestamp {
        color: rgba(255, 255, 255, 0.6);
        text-style: italic;
        text-align: right;
    }
    
    FeedbackWidget .feedback-actions {
        margin-top: 1;
    }
    
    FeedbackWidget .dismiss-button {
        text-align: right;
        color: rgba(255, 255, 255, 0.8);
        text-style: bold;
    }
    """
    
    def __init__(self, feedback_message: FeedbackMessage, **kwargs):
        """Initialize feedback widget.
        
        Args:
            feedback_message: The feedback message to display
        """
        super().__init__(**kwargs)
        self.feedback_message = feedback_message
        self.add_class(feedback_message.feedback_type)
        
        # Set up auto-dismiss timer if duration > 0 and we're in an app context
        if feedback_message.duration > 0:
            try:
                self.set_timer(feedback_message.duration, self._auto_dismiss)
            except RuntimeError:
                # Not in an event loop context (e.g., during testing)
                pass
    
    def compose(self) -> ComposeResult:
        """Compose the feedback widget layout."""
        with Vertical():
            # Header with icon and title
            icon_map = {
                FeedbackType.SUCCESS: "✅",
                FeedbackType.INFO: "ℹ️",
                FeedbackType.WARNING: "⚠️",
                FeedbackType.ERROR: "❌",
                FeedbackType.PROGRESS: "⏳"
            }
            
            icon = icon_map.get(self.feedback_message.feedback_type, "ℹ️")
            
            if self.feedback_message.title:
                header_text = f"{icon} {self.feedback_message.title}"
            else:
                header_text = icon
            
            yield Label(header_text, classes="feedback-header")
            
            # Main message
            yield Label(self.feedback_message.message, classes="feedback-message")
            
            # Details if available
            if self.feedback_message.details:
                details_text = self._format_details(self.feedback_message.details)
                if details_text:
                    yield Label(details_text, classes="feedback-details")
            
            # Progress bar for progress messages
            if self.feedback_message.feedback_type == FeedbackType.PROGRESS:
                progress = self.feedback_message.details.get('progress', 0)
                yield ProgressBar(total=100, progress=progress, id="progress_bar")
            
            # Action buttons if available
            if self.feedback_message.actions:
                with Horizontal(classes="feedback-actions"):
                    for action in self.feedback_message.actions:
                        yield Label(f"[{action.get('key', '?')}] {action.get('label', 'Action')}")
            
            # Timestamp and dismiss option
            with Horizontal():
                timestamp_text = self.feedback_message.timestamp.strftime("%H:%M:%S")
                yield Label(timestamp_text, classes="feedback-timestamp")
                
                if self.feedback_message.dismissible:
                    yield Label("[ESC] Dismiss", classes="dismiss-button")
    
    def _format_details(self, details: Dict[str, Any]) -> str:
        """Format details dictionary into readable text.
        
        Args:
            details: Details dictionary
            
        Returns:
            Formatted details string
        """
        formatted_parts = []
        
        # Handle common detail types
        if 'xp_earned' in details:
            formatted_parts.append(f"XP Earned: {details['xp_earned']}")
        
        if 'level_up' in details and details['level_up']:
            formatted_parts.append(f"Level Up! New Level: {details.get('new_level', '?')}")
        
        if 'tasks_affected' in details:
            formatted_parts.append(f"Tasks Affected: {details['tasks_affected']}")
        
        if 'changes' in details:
            changes = details['changes']
            if isinstance(changes, dict):
                change_parts = []
                for field, change_info in changes.items():
                    if isinstance(change_info, dict) and 'from' in change_info and 'to' in change_info:
                        change_parts.append(f"{field}: {change_info['from']} → {change_info['to']}")
                    else:
                        change_parts.append(f"{field}: {change_info}")
                if change_parts:
                    formatted_parts.append(f"Changes: {', '.join(change_parts)}")
        
        if 'duration' in details:
            formatted_parts.append(f"Duration: {details['duration']}")
        
        if 'file_path' in details:
            formatted_parts.append(f"File: {details['file_path']}")
        
        # Handle generic key-value pairs
        for key, value in details.items():
            if key not in ['xp_earned', 'level_up', 'new_level', 'tasks_affected', 'changes', 'duration', 'file_path', 'progress']:
                if isinstance(value, (str, int, float, bool)):
                    formatted_parts.append(f"{key.replace('_', ' ').title()}: {value}")
        
        return " | ".join(formatted_parts)
    
    def _auto_dismiss(self) -> None:
        """Auto-dismiss the feedback message."""
        self.post_message(self.DismissRequested(self.feedback_message.id))
    
    def update_progress(self, progress: int) -> None:
        """Update progress bar for progress messages.
        
        Args:
            progress: Progress percentage (0-100)
        """
        if self.feedback_message.feedback_type == FeedbackType.PROGRESS:
            try:
                progress_bar = self.query_one("#progress_bar", ProgressBar)
                progress_bar.progress = progress
                self.feedback_message.details['progress'] = progress
            except:
                pass  # Progress bar not found
    
    class DismissRequested(Message):
        """Message sent when feedback should be dismissed."""
        
        def __init__(self, feedback_id: str):
            super().__init__()
            self.feedback_id = feedback_id


class FeedbackSystem(Widget):
    """System for managing and displaying feedback messages."""
    
    DEFAULT_CSS = """
    FeedbackSystem {
        height: auto;
        max-height: 50%;
        overflow-y: auto;
        background: transparent;
        padding: 1;
    }
    
    FeedbackSystem .feedback-container {
        height: auto;
    }
    
    FeedbackSystem .no-messages {
        text-align: center;
        color: $text-muted;
        text-style: italic;
        padding: 2;
    }
    """
    
    # Reactive properties
    message_count = reactive(0)
    
    def __init__(self, max_messages: int = 10, **kwargs):
        """Initialize feedback system.
        
        Args:
            max_messages: Maximum number of messages to keep
        """
        super().__init__(**kwargs)
        self.max_messages = max_messages
        self.messages: List[FeedbackMessage] = []
        self.message_widgets: Dict[str, FeedbackWidget] = {}
    
    def compose(self) -> ComposeResult:
        """Compose the feedback system layout."""
        with Vertical(classes="feedback-container", id="feedback_container"):
            yield Label("No messages", classes="no-messages", id="no_messages")
    
    def add_message(self, feedback_message: FeedbackMessage) -> None:
        """Add a new feedback message.
        
        Args:
            feedback_message: The feedback message to add
        """
        # Add to messages list
        self.messages.append(feedback_message)
        
        # Limit number of messages
        if len(self.messages) > self.max_messages:
            oldest_message = self.messages.pop(0)
            self._remove_message_widget(oldest_message.id)
        
        # Create and mount widget
        message_widget = FeedbackWidget(feedback_message)
        self.message_widgets[feedback_message.id] = message_widget
        
        try:
            container = self.query_one("#feedback_container")
            container.mount(message_widget)
            
            # Hide "no messages" label
            no_messages_label = self.query_one("#no_messages")
            no_messages_label.display = False
            
        except:
            pass  # Container not ready yet
        
        self.message_count = len(self.messages)
    
    def remove_message(self, message_id: str) -> None:
        """Remove a feedback message by ID.
        
        Args:
            message_id: ID of the message to remove
        """
        # Remove from messages list
        self.messages = [msg for msg in self.messages if msg.id != message_id]
        
        # Remove widget
        self._remove_message_widget(message_id)
        
        # Show "no messages" label if no messages left
        if not self.messages:
            try:
                no_messages_label = self.query_one("#no_messages")
                no_messages_label.display = True
            except:
                pass
        
        self.message_count = len(self.messages)
    
    def _remove_message_widget(self, message_id: str) -> None:
        """Remove a message widget.
        
        Args:
            message_id: ID of the message widget to remove
        """
        if message_id in self.message_widgets:
            widget = self.message_widgets[message_id]
            try:
                widget.remove()
            except:
                pass  # Widget already removed
            del self.message_widgets[message_id]
    
    def clear_messages(self) -> None:
        """Clear all feedback messages."""
        for message_id in list(self.message_widgets.keys()):
            self._remove_message_widget(message_id)
        
        self.messages.clear()
        self.message_widgets.clear()
        
        try:
            no_messages_label = self.query_one("#no_messages")
            no_messages_label.display = True
        except:
            pass
        
        self.message_count = 0
    
    def update_progress_message(self, message_id: str, progress: int, message: Optional[str] = None) -> None:
        """Update a progress message.
        
        Args:
            message_id: ID of the progress message
            progress: New progress value (0-100)
            message: Optional new message text
        """
        # Find the message in our list and update it
        for msg in self.messages:
            if msg.id == message_id:
                msg.details['progress'] = progress
                if message:
                    msg.message = message
                break
        
        # Update the widget if it exists
        if message_id in self.message_widgets:
            widget = self.message_widgets[message_id]
            widget.update_progress(progress)
            
            if message:
                # Update the widget's message label
                try:
                    message_label = widget.query_one(".feedback-message", Label)
                    message_label.update(message)
                except:
                    pass
    
    def get_message_count_by_type(self, feedback_type: str) -> int:
        """Get count of messages by type.
        
        Args:
            feedback_type: Type of feedback to count
            
        Returns:
            Number of messages of the specified type
        """
        return sum(1 for msg in self.messages if msg.feedback_type == feedback_type)
    
    def has_errors(self) -> bool:
        """Check if there are any error messages.
        
        Returns:
            True if there are error messages
        """
        return self.get_message_count_by_type(FeedbackType.ERROR) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warning messages.
        
        Returns:
            True if there are warning messages
        """
        return self.get_message_count_by_type(FeedbackType.WARNING) > 0
    
    def on_feedback_widget_dismiss_requested(self, message: FeedbackWidget.DismissRequested) -> None:
        """Handle feedback widget dismiss requests."""
        self.remove_message(message.feedback_id)
    
    # Convenience methods for common feedback types
    def show_success(
        self,
        message: str,
        title: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        duration: float = 3.0
    ) -> str:
        """Show a success message.
        
        Args:
            message: Success message
            title: Optional title
            details: Optional details
            duration: Display duration
            
        Returns:
            Message ID
        """
        feedback_msg = FeedbackMessage(
            message=message,
            feedback_type=FeedbackType.SUCCESS,
            title=title,
            details=details,
            duration=duration
        )
        self.add_message(feedback_msg)
        return feedback_msg.id
    
    def show_info(
        self,
        message: str,
        title: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        duration: float = 3.0
    ) -> str:
        """Show an info message.
        
        Args:
            message: Info message
            title: Optional title
            details: Optional details
            duration: Display duration
            
        Returns:
            Message ID
        """
        feedback_msg = FeedbackMessage(
            message=message,
            feedback_type=FeedbackType.INFO,
            title=title,
            details=details,
            duration=duration
        )
        self.add_message(feedback_msg)
        return feedback_msg.id
    
    def show_warning(
        self,
        message: str,
        title: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        duration: float = 5.0
    ) -> str:
        """Show a warning message.
        
        Args:
            message: Warning message
            title: Optional title
            details: Optional details
            duration: Display duration
            
        Returns:
            Message ID
        """
        feedback_msg = FeedbackMessage(
            message=message,
            feedback_type=FeedbackType.WARNING,
            title=title,
            details=details,
            duration=duration
        )
        self.add_message(feedback_msg)
        return feedback_msg.id
    
    def show_error(
        self,
        message: str,
        title: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        duration: float = 0  # Errors don't auto-dismiss
    ) -> str:
        """Show an error message.
        
        Args:
            message: Error message
            title: Optional title
            details: Optional details
            duration: Display duration (0 = permanent)
            
        Returns:
            Message ID
        """
        feedback_msg = FeedbackMessage(
            message=message,
            feedback_type=FeedbackType.ERROR,
            title=title,
            details=details,
            duration=duration
        )
        self.add_message(feedback_msg)
        return feedback_msg.id
    
    def show_progress(
        self,
        message: str,
        progress: int = 0,
        title: Optional[str] = None,
        duration: float = 0  # Progress messages don't auto-dismiss
    ) -> str:
        """Show a progress message.
        
        Args:
            message: Progress message
            progress: Initial progress (0-100)
            title: Optional title
            duration: Display duration (0 = permanent)
            
        Returns:
            Message ID
        """
        feedback_msg = FeedbackMessage(
            message=message,
            feedback_type=FeedbackType.PROGRESS,
            title=title,
            details={'progress': progress},
            duration=duration
        )
        self.add_message(feedback_msg)
        return feedback_msg.id