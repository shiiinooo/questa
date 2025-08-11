"""TaskForm widget for task creation and editing with validation."""

from typing import Optional, List, Dict, Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Input, TextArea, Select, Button, Label, Static
from textual.validation import ValidationResult, Validator
from textual.message import Message

from ..models.task import Task
from ..models.enums import TaskDifficulty, TaskPriority, TaskStatus


class TaskTitleValidator(Validator):
    """Validator for task titles."""
    
    def validate(self, value: str) -> ValidationResult:
        """Validate task title."""
        if not value or not value.strip():
            return self.failure("Task title cannot be empty")
        
        if len(value.strip()) > 200:
            return self.failure("Task title cannot exceed 200 characters")
        
        return self.success()


class TaskForm(Widget):
    """Widget for task creation and editing with validation."""
    
    DEFAULT_CSS = """
    TaskForm {
        height: auto;
        padding: 1;
        border: solid $primary;
        background: $surface;
    }
    
    TaskForm .form-field {
        margin: 1 0;
    }
    
    TaskForm .form-label {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }
    
    TaskForm .form-input {
        width: 100%;
    }
    
    TaskForm .form-buttons {
        margin-top: 2;
        align: center middle;
    }
    
    TaskForm .error-message {
        color: $error;
        text-style: italic;
        margin-top: 1;
    }
    
    TaskForm .success-message {
        color: $success;
        text-style: bold;
        margin-top: 1;
    }
    """
    
    def __init__(self, task: Optional[Task] = None, **kwargs):
        """Initialize TaskForm for creating or editing a task."""
        super().__init__(**kwargs)
        self._task = task
        self.is_editing = task is not None
        self._validation_errors: List[str] = []
    
    @property
    def task(self) -> Optional[Task]:
        """Get the current task being edited."""
        return self._task
    
    def compose(self) -> ComposeResult:
        """Compose the task form layout."""
        with Vertical():
            # Form title
            form_title = "Edit Task" if self.is_editing else "Create New Task"
            yield Label(form_title, classes="form-title")
            
            # Task title field
            with Vertical(classes="form-field"):
                yield Label("Title *", classes="form-label")
                title_value = self._task.title if self.is_editing else ""
                yield Input(
                    value=title_value,
                    placeholder="Enter task title...",
                    validators=[TaskTitleValidator()],
                    id="title_input",
                    classes="form-input"
                )
            
            # Difficulty selection
            with Vertical(classes="form-field"):
                yield Label("Difficulty", classes="form-label")
                difficulty_options = [(diff.display_name, diff) for diff in TaskDifficulty]
                default_difficulty = self._task.difficulty if self.is_editing else TaskDifficulty.MEDIUM
                yield Select(
                    options=difficulty_options,
                    value=default_difficulty,
                    id="difficulty_select",
                    classes="form-input"
                )
            
            # Priority selection
            with Vertical(classes="form-field"):
                yield Label("Priority", classes="form-label")
                priority_options = [(prio.value, prio) for prio in TaskPriority]
                default_priority = self._task.priority if self.is_editing else TaskPriority.MEDIUM
                yield Select(
                    options=priority_options,
                    value=default_priority,
                    id="priority_select",
                    classes="form-input"
                )
            
            # Status selection (only for editing)
            if self.is_editing:
                with Vertical(classes="form-field"):
                    yield Label("Status", classes="form-label")
                    status_options = [(status.value, status) for status in TaskStatus]
                    yield Select(
                        options=status_options,
                        value=self._task.status,
                        id="status_select",
                        classes="form-input"
                    )
            
            # Notes field
            with Vertical(classes="form-field"):
                yield Label("Notes (Optional)", classes="form-label")
                notes_value = self._task.notes if self.is_editing and self._task.notes else ""
                yield TextArea(
                    text=notes_value,
                    id="notes_input",
                    classes="form-input"
                )
            
            # Validation errors display
            yield Static("", id="error_display", classes="error-message")
            
            # Form buttons
            with Horizontal(classes="form-buttons"):
                submit_text = "Update Task" if self.is_editing else "Create Task"
                yield Button(submit_text, variant="primary", id="submit_button")
                yield Button("Cancel", variant="default", id="cancel_button")
    
    def validate_form(self) -> List[str]:
        """Validate all form fields and return list of errors."""
        errors = []
        
        # Get form values
        title_input = self.query_one("#title_input", Input)
        
        # Validate title
        if not title_input.value or not title_input.value.strip():
            errors.append("Task title is required")
        elif len(title_input.value.strip()) > 200:
            errors.append("Task title cannot exceed 200 characters")
        
        # Additional validation for editing
        if self.is_editing:
            status_select = self.query_one("#status_select", Select)
            if status_select.value and self._task:
                if not self._task.can_transition_to(status_select.value):
                    errors.append(f"Cannot transition from {self._task.status} to {status_select.value}")
        
        self._validation_errors = errors
        return errors
    
    def get_form_data(self) -> Dict[str, Any]:
        """Extract form data as dictionary."""
        title_input = self.query_one("#title_input", Input)
        difficulty_select = self.query_one("#difficulty_select", Select)
        priority_select = self.query_one("#priority_select", Select)
        notes_input = self.query_one("#notes_input", TextArea)
        
        data = {
            'title': title_input.value.strip(),
            'difficulty': difficulty_select.value,
            'priority': priority_select.value,
            'notes': notes_input.text.strip() if notes_input.text.strip() else None
        }
        
        # Add status for editing
        if self.is_editing:
            status_select = self.query_one("#status_select", Select)
            data['status'] = status_select.value
        
        return data
    
    def display_errors(self, errors: List[str]) -> None:
        """Display validation errors in the form."""
        error_display = self.query_one("#error_display", Static)
        if errors:
            error_text = "Errors:\n" + "\n".join(f"• {error}" for error in errors)
            error_display.update(error_text)
        else:
            error_display.update("")
    
    def display_success(self, message: str) -> None:
        """Display success message in the form."""
        error_display = self.query_one("#error_display", Static)
        error_display.remove_class("error-message")
        error_display.add_class("success-message")
        error_display.update(message)
    
    def clear_messages(self) -> None:
        """Clear all error and success messages."""
        error_display = self.query_one("#error_display", Static)
        error_display.remove_class("success-message")
        error_display.add_class("error-message")
        error_display.update("")
    
    def reset_form(self) -> None:
        """Reset form to initial state."""
        title_input = self.query_one("#title_input", Input)
        difficulty_select = self.query_one("#difficulty_select", Select)
        priority_select = self.query_one("#priority_select", Select)
        notes_input = self.query_one("#notes_input", TextArea)
        
        if not self.is_editing:
            title_input.value = ""
            difficulty_select.value = TaskDifficulty.MEDIUM
            priority_select.value = TaskPriority.MEDIUM
            notes_input.text = ""
        else:
            # Reset to original task values
            title_input.value = self._task.title
            difficulty_select.value = self._task.difficulty
            priority_select.value = self._task.priority
            notes_input.text = self._task.notes or ""
            
            if self.is_editing:
                status_select = self.query_one("#status_select", Select)
                status_select.value = self._task.status
        
        self.clear_messages()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "submit_button":
            await self._handle_submit()
        elif event.button.id == "cancel_button":
            await self._handle_cancel()
    
    async def _handle_submit(self) -> None:
        """Handle form submission."""
        errors = self.validate_form()
        
        if errors:
            self.display_errors(errors)
            return
        
        form_data = self.get_form_data()
        
        if self.is_editing:
            self.post_message(self.TaskUpdated(self._task, form_data))
        else:
            self.post_message(self.TaskCreated(form_data))
    
    async def _handle_cancel(self) -> None:
        """Handle form cancellation."""
        self.post_message(self.FormCancelled())
    
    class TaskCreated(Message):
        """Message sent when a new task is created."""
        
        def __init__(self, form_data: Dict[str, Any]):
            super().__init__()
            self.form_data = form_data
    
    class TaskUpdated(Message):
        """Message sent when a task is updated."""
        
        def __init__(self, original_task: Task, form_data: Dict[str, Any]):
            super().__init__()
            self.original_task = original_task
            self.form_data = form_data
    
    class FormCancelled(Message):
        """Message sent when form is cancelled."""
        pass