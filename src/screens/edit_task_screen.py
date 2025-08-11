"""EditTaskScreen - Screen for editing existing tasks."""

from typing import Optional
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import (
    Button, Header, Footer, Label, Input, Select, 
    TextArea, Checkbox, Static
)
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive

from ..models.task import Task
from ..models.enums import TaskStatus, TaskDifficulty, TaskPriority
from ..data.data_manager import DataManager
from ..widgets.feedback_system import FeedbackSystem


class EditTaskScreen(Screen):
    """Screen for editing existing tasks."""

    BINDINGS = [
        Binding("ctrl+s", "save_changes", "Save Changes", show=True),
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("tab", "next_field", "Next Field", show=True),
        Binding("shift+tab", "previous_field", "Previous Field", show=True),
    ]

    # Form fields
    title = reactive("")
    description = reactive("")
    difficulty = reactive(TaskDifficulty.MEDIUM)
    priority = reactive(TaskPriority.MEDIUM)
    notes = reactive("")
    tags = reactive("")
    status = reactive(TaskStatus.PENDING)

    def __init__(self, data_manager: DataManager, task: Task, **kwargs):
        """Initialize the edit task screen."""
        super().__init__(**kwargs)
        self.data_manager = data_manager
        self.original_task = task
        self.feedback_system = FeedbackSystem()
        self.form_valid = False
        
        # Initialize form fields with current task values
        self.title = task.title
        self.description = task.description or ""
        self.difficulty = task.difficulty
        self.priority = task.priority
        self.notes = task.notes or ""
        self.tags = ", ".join(task.tags) if task.tags else ""
        self.status = task.status

    def compose(self) -> ComposeResult:
        """Compose the edit task screen layout."""
        yield Header(show_clock=True)
        
        with Container(classes="tui-content"):
            # Main form area
            with Container(classes="form-container"):
                yield Label("Edit Task", classes="form-title")
                
                # Task title
                yield Label("Title *", classes="form-label")
                yield Input(
                    value=self.title,
                    placeholder="Enter task title...",
                    id="title-input",
                    classes="form-input"
                )
                
                # Task description
                yield Label("Description", classes="form-label")
                yield TextArea(
                    value=self.description,
                    placeholder="Enter task description...",
                    id="description-input",
                    classes="form-textarea"
                )
                
                # Difficulty and priority row
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-field"):
                        yield Label("Difficulty *", classes="form-label")
                        yield Select(
                            options=[
                                (TaskDifficulty.EASY, "Easy"),
                                (TaskDifficulty.MEDIUM, "Medium"),
                                (TaskDifficulty.HARD, "Hard")
                            ],
                            value=self.difficulty,
                            id="difficulty-select",
                            classes="form-select"
                        )
                    
                    with Vertical(classes="form-field"):
                        yield Label("Priority *", classes="form-label")
                        yield Select(
                            options=[
                                (TaskPriority.LOW, "Low"),
                                (TaskPriority.MEDIUM, "Medium"),
                                (TaskPriority.HIGH, "High"),
                                (TaskPriority.CRITICAL, "Critical")
                            ],
                            value=self.priority,
                            id="priority-select",
                            classes="form-select"
                        )
                
                # Status
                yield Label("Status", classes="form-label")
                yield Select(
                    options=[
                        (TaskStatus.PENDING, "Pending"),
                        (TaskStatus.ACTIVE, "Active"),
                        (TaskStatus.COMPLETED, "Completed"),
                        (TaskStatus.BLOCKED, "Blocked")
                    ],
                    value=self.status,
                    id="status-select",
                    classes="form-select"
                )
                
                # Notes
                yield Label("Notes", classes="form-label")
                yield TextArea(
                    value=self.notes,
                    placeholder="Additional notes...",
                    id="notes-input",
                    classes="form-textarea"
                )
                
                # Tags
                yield Label("Tags", classes="form-label")
                yield Input(
                    value=self.tags,
                    placeholder="Enter tags separated by commas...",
                    id="tags-input",
                    classes="form-input"
                )
                
                # XP preview
                yield Label("XP Reward Preview", classes="form-label")
                yield Static("", id="xp-preview", classes="xp-preview")
                
                # Action buttons
                with Horizontal(classes="form-actions"):
                    yield Button("Save Changes (Ctrl+S)", action="save_changes", classes="primary-button")
                    yield Button("Cancel (Esc)", action="cancel", classes="secondary-button")
                    yield Button("Delete Task", action="delete_task", classes="danger-button")
        
        yield Footer()
        yield self.feedback_system

    def on_mount(self) -> None:
        """Handle screen mount event."""
        # Set focus to title input
        title_input = self.query_one("#title-input", Input)
        if title_input:
            title_input.focus()
        
        # Update XP preview
        self._update_xp_preview()
        
        # Validate form
        self._validate_form()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input field changes."""
        input_id = event.input.id
        
        if input_id == "title-input":
            self.title = event.value
        elif input_id == "description-input":
            self.description = event.value
        elif input_id == "notes-input":
            self.notes = event.value
        elif input_id == "tags-input":
            self.tags = event.value
        
        # Update XP preview when relevant fields change
        if input_id in ["title-input", "difficulty-input", "priority-input"]:
            self._update_xp_preview()
        
        # Validate form
        self._validate_form()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select field changes."""
        select_id = event.select.id
        
        if select_id == "difficulty-select":
            self.difficulty = event.value
        elif select_id == "priority-select":
            self.priority = event.value
        elif select_id == "status-select":
            self.status = event.value
        
        # Update XP preview
        self._update_xp_preview()
        
        # Validate form
        self._validate_form()

    def _validate_form(self) -> None:
        """Validate the form and update validation state."""
        self.form_valid = bool(self.title.strip())
        
        # Update button states
        save_button = self.query_one("Button[action='save_changes']", Button)
        if save_button:
            save_button.disabled = not self.form_valid

    def _update_xp_preview(self) -> None:
        """Update the XP reward preview."""
        try:
            # Calculate XP based on difficulty and priority
            base_xp = {
                TaskDifficulty.EASY: 10,
                TaskDifficulty.MEDIUM: 25,
                TaskDifficulty.HARD: 50
            }.get(self.difficulty, 25)
            
            priority_multiplier = {
                TaskPriority.LOW: 0.8,
                TaskPriority.MEDIUM: 1.0,
                TaskPriority.HIGH: 1.3,
                TaskPriority.CRITICAL: 1.6
            }.get(self.priority, 1.0)
            
            xp_reward = int(base_xp * priority_multiplier)
            
            # Update preview
            xp_preview = self.query_one("#xp-preview", Static)
            if xp_preview:
                xp_preview.update(f"Estimated XP: {xp_reward}")
                
        except Exception as e:
            # Update preview with error
            xp_preview = self.query_one("#xp-preview", Static)
            if xp_preview:
                xp_preview.update("Error calculating XP")

    def action_save_changes(self) -> None:
        """Save the task changes."""
        if not self.form_valid:
            self.feedback_system.show_warning("Please fill in all required fields")
            return
        
        try:
            # Parse tags
            tag_list = [tag.strip() for tag in self.tags.split(",") if tag.strip()]
            
            # Update task attributes
            self.original_task.title = self.title.strip()
            self.original_task.description = self.description.strip()
            self.original_task.difficulty = self.difficulty
            self.original_task.priority = self.priority
            self.original_task.notes = self.notes.strip()
            self.original_task.tags = tag_list
            self.original_task.status = self.status
            
            # Update XP reward based on new difficulty/priority
            base_xp = {
                TaskDifficulty.EASY: 10,
                TaskDifficulty.MEDIUM: 25,
                TaskDifficulty.HARD: 50
            }.get(self.difficulty, 25)
            
            priority_multiplier = {
                TaskPriority.LOW: 0.8,
                TaskPriority.MEDIUM: 1.0,
                TaskPriority.HIGH: 1.3,
                TaskPriority.CRITICAL: 1.6
            }.get(self.priority, 1.0)
            
            self.original_task.xp_reward = int(base_xp * priority_multiplier)
            
            # Save data
            self.data_manager.save_data()
            
            # Show success feedback
            self.feedback_system.show_success(
                f"Task '{self.original_task.title}' updated successfully!",
                title="Task Updated"
            )
            
            # Post message for parent screens
            self.post_message(self.TaskUpdated(self.original_task))
            
            # Return to previous screen
            self.app.pop_screen()
            
        except Exception as e:
            # Handle specific error types
            error_message = str(e)
            
            if "validation error" in error_message.lower() or "invalid" in error_message.lower():
                self.feedback_system.show_error(
                    f"Validation error: {error_message}",
                    title="Invalid Task Data"
                )
            elif "not found" in error_message.lower():
                self.feedback_system.show_error(
                    f"Task not found: {error_message}",
                    title="Task Not Found"
                )
            else:
                self.feedback_system.show_error(
                    f"Error updating task: {error_message}",
                    title="Update Failed"
                )

    def action_cancel(self) -> None:
        """Cancel editing and return to previous screen."""
        # Post message for parent screens
        self.post_message(self.FormCancelled())
        
        # Return to previous screen
        self.app.pop_screen()

    def action_delete_task(self) -> None:
        """Delete the current task."""
        try:
            # Remove task from data manager
            self.data_manager.remove_task(self.original_task.id)
            
            # Save data
            self.data_manager.save_data()
            
            # Show success feedback
            self.feedback_system.show_success(
                f"Task '{self.original_task.title}' deleted successfully!",
                title="Task Deleted"
            )
            
            # Post message for parent screens
            self.post_message(self.TaskDeleted(self.original_task))
            
            # Return to previous screen
            self.app.pop_screen()
            
        except Exception as e:
            self.feedback_system.show_error(
                f"Error deleting task: {e}",
                title="Deletion Failed"
            )

    def action_next_field(self) -> None:
        """Move focus to the next form field."""
        current_focus = self.focused
        if current_focus:
            # Find next focusable widget
            focusable_widgets = [
                "#title-input",
                "#description-input", 
                "#difficulty-select",
                "#priority-select",
                "#status-select",
                "#notes-input",
                "#tags-input"
            ]
            
            try:
                current_index = focusable_widgets.index(current_focus.id)
                next_index = (current_index + 1) % len(focusable_widgets)
                next_widget = self.query_one(focusable_widgets[next_index])
                if next_widget:
                    next_widget.focus()
            except (ValueError, AttributeError):
                # Fallback to first field
                first_widget = self.query_one("#title-input", Input)
                if first_widget:
                    first_widget.focus()

    def action_previous_field(self) -> None:
        """Move focus to the previous form field."""
        current_focus = self.focused
        if current_focus:
            # Find previous focusable widget
            focusable_widgets = [
                "#title-input",
                "#description-input", 
                "#difficulty-select",
                "#priority-select",
                "#status-select",
                "#notes-input",
                "#tags-input"
            ]
            
            try:
                current_index = focusable_widgets.index(current_focus.id)
                prev_index = (current_index - 1) % len(focusable_widgets)
                prev_widget = self.query_one(focusable_widgets[prev_index])
                if prev_widget:
                    prev_widget.focus()
            except (ValueError, AttributeError):
                # Fallback to first field
                first_widget = self.query_one("#title-input", Input)
                if first_widget:
                    first_widget.focus()

    # Custom messages for parent screen communication
    class TaskUpdated(Message):
        """Message sent when a task is successfully updated."""
        
        def __init__(self, updated_task: Task):
            super().__init__()
            self.updated_task = updated_task

    class TaskDeleted(Message):
        """Message sent when a task is successfully deleted."""
        
        def __init__(self, deleted_task: Task):
            super().__init__()
            self.deleted_task = deleted_task

    class FormCancelled(Message):
        """Message sent when the form is cancelled."""
        pass