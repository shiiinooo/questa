"""AddTaskScreen - Screen for creating new tasks."""

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


class AddTaskScreen(Screen):
    """Screen for adding new tasks to the system."""

    BINDINGS = [
        Binding("ctrl+s", "save_task", "Save Task", show=True),
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

    def __init__(self, data_manager: DataManager, **kwargs):
        """Initialize the add task screen."""
        super().__init__(**kwargs)
        self.data_manager = data_manager
        self.feedback_system = FeedbackSystem()
        self.form_valid = False

    def compose(self) -> ComposeResult:
        """Compose the add task screen layout."""
        yield Header(show_clock=True)
        
        with Container(classes="tui-content"):
            # Main form area
            with Container(classes="form-container"):
                yield Label("Create New Task", classes="form-title")
                
                # Task title
                yield Label("Title *", classes="form-label")
                yield Input(
                    placeholder="Enter task title...",
                    id="title-input",
                    classes="form-input"
                )
                
                # Task description
                yield Label("Description", classes="form-label")
                yield TextArea(
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
                            value=TaskDifficulty.MEDIUM,
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
                            value=TaskPriority.MEDIUM,
                            id="priority-select",
                            classes="form-select"
                        )
                
                # Notes
                yield Label("Notes", classes="form-label")
                yield TextArea(
                    placeholder="Additional notes...",
                    id="notes-input",
                    classes="form-textarea"
                )
                
                # Tags
                yield Label("Tags", classes="form-label")
                yield Input(
                    placeholder="Enter tags separated by commas...",
                    id="tags-input",
                    classes="form-input"
                )
                
                # XP preview
                yield Label("XP Reward Preview", classes="form-label")
                yield Static("", id="xp-preview", classes="xp-preview")
                
                # Action buttons
                with Horizontal(classes="form-actions"):
                    yield Button("Save Task (Ctrl+S)", action="save_task", classes="primary-button")
                    yield Button("Cancel (Esc)", action="cancel", classes="secondary-button")
        
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
        if input_id in ["title-input", "difficulty-select", "priority-select"]:
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
        
        # Update XP preview
        self._update_xp_preview()
        
        # Validate form
        self._validate_form()

    def _validate_form(self) -> None:
        """Validate the form and update validation state."""
        self.form_valid = bool(self.title.strip())
        
        # Update button states
        save_button = self.query_one("Button[action='save_task']", Button)
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

    def action_save_task(self) -> None:
        """Save the new task."""
        if not self.form_valid:
            self.feedback_system.show_warning("Please fill in all required fields")
            return
        
        try:
            # Parse tags
            tag_list = [tag.strip() for tag in self.tags.split(",") if tag.strip()]
            
            # Create new task
            new_task = Task(
                title=self.title.strip(),
                description=self.description.strip(),
                difficulty=self.difficulty,
                priority=self.priority,
                notes=self.notes.strip(),
                tags=tag_list,
                status=TaskStatus.PENDING
            )
            
            # Add task to data manager
            self.data_manager.add_task(new_task)
            
            # Save data
            self.data_manager.save_data()
            
            # Show success feedback
            self.feedback_system.show_success(
                f"Task '{new_task.title}' created successfully!",
                title="Task Created"
            )
            
            # Post message for parent screens
            self.post_message(self.TaskCreated(new_task))
            
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
            elif "duplicate" in error_message.lower():
                self.feedback_system.show_error(
                    f"Task with this title already exists: {error_message}",
                    title="Duplicate Task"
                )
            else:
                self.feedback_system.show_error(
                    f"Error creating task: {error_message}",
                    title="Creation Failed"
                )

    def action_cancel(self) -> None:
        """Cancel task creation and return to previous screen."""
        # Post message for parent screens
        self.post_message(self.FormCancelled())
        
        # Return to previous screen
        self.app.pop_screen()

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
    class TaskCreated(Message):
        """Message sent when a task is successfully created."""
        
        def __init__(self, task: Task):
            super().__init__()
            self.task = task

    class FormCancelled(Message):
        """Message sent when the form is cancelled."""
        pass