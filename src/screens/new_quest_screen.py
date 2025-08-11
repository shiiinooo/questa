"""NewQuestScreen - Terminal-style screen for creating new quests/tasks."""

from typing import Optional, List
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import (
    Button, Label, Input, Select, TextArea, Static
)
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive

from ..models.task import Task
from ..models.enums import TaskStatus, TaskDifficulty, TaskPriority
from ..data.data_manager import DataManager
from ..widgets.feedback_system import FeedbackSystem
from ..widgets.terminal_header import TerminalHeaderSimple
from ..widgets.terminal_footer import TerminalFooterWithHelp
from ..widgets.terminal_panel import TerminalPanel
from ..widgets.priority_indicator import XPCalculatorWidget
from ..terminal_utils import get_terminal_formatter, format_xp_display


class NewQuestScreen(Screen):
    """Terminal-style screen for creating new quests with comprehensive form fields."""

    BINDINGS = [
        Binding("ctrl+s", "save_quest", "Save Quest", show=True),
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("tab", "next_field", "Next Field", show=True),
        Binding("shift+tab", "previous_field", "Previous Field", show=True),
        Binding("f1", "show_help", "Help", show=True),
    ]

    # Form fields - reactive for real-time updates
    title = reactive("")
    description = reactive("")
    difficulty = reactive(TaskDifficulty.MEDIUM)
    priority = reactive(TaskPriority.MEDIUM)
    category = reactive("")
    files_paths = reactive("")
    tags = reactive("")
    estimated_time = reactive("")
    acceptance_criteria = reactive("")
    notes = reactive("")

    def __init__(self, data_manager: DataManager, **kwargs):
        """Initialize the new quest screen."""
        super().__init__(**kwargs)
        self.data_manager = data_manager
        self.feedback_system = FeedbackSystem()
        self.formatter = get_terminal_formatter()
        self.form_valid = False
        self.calculated_xp = 0

    def compose(self) -> ComposeResult:
        """Compose the new quest screen layout."""
        # Terminal header
        yield TerminalHeaderSimple(
            screen_name="New Quest",
            user_name="Player"  # TODO: Get from player data
        )
        
        # Main content area
        with Container(classes="terminal-content"):
            # Main form panel
            with TerminalPanel(
                title="Create New Quest",
                scrollable=True,
                focusable=True
            ) as form_panel:
                with Container(id="form-container"):
                    # Quest title section
                    yield Label("Quest Title *", classes="form-label terminal-highlight")
                    yield Input(
                        placeholder="Enter quest title (e.g., 'Implement user authentication')...",
                        id="title-input",
                        classes="terminal-input"
                    )
                    yield Static("", id="title-validation", classes="form-validation-message")
                    
                    # Difficulty and Priority row
                    with Horizontal(classes="form-row"):
                        with Vertical(classes="form-field"):
                            yield Label("Difficulty *", classes="form-label terminal-highlight")
                            yield Select(
                                options=[
                                    (TaskDifficulty.EASY, f"Easy ({TaskDifficulty.EASY.xp_value} XP)"),
                                    (TaskDifficulty.MEDIUM, f"Medium ({TaskDifficulty.MEDIUM.xp_value} XP)"),
                                    (TaskDifficulty.HARD, f"Hard ({TaskDifficulty.HARD.xp_value} XP)")
                                ],
                                value=TaskDifficulty.MEDIUM,
                                id="difficulty-select",
                                classes="terminal-select"
                            )
                        
                        with Vertical(classes="form-field"):
                            yield Label("Priority *", classes="form-label terminal-highlight")
                            yield Select(
                                options=[
                                    (TaskPriority.LOW, "● Low (0.8x multiplier)"),
                                    (TaskPriority.MEDIUM, "◆ Medium (1.0x multiplier)"),
                                    (TaskPriority.HIGH, "▲ High (1.3x multiplier)"),
                                    (TaskPriority.CRITICAL, "★ Critical (1.6x multiplier)")
                                ],
                                value=TaskPriority.MEDIUM,
                                id="priority-select",
                                classes="terminal-select"
                            )
                    
                    # Category and Estimated Time row
                    with Horizontal(classes="form-row"):
                        with Vertical(classes="form-field"):
                            yield Label("Category", classes="form-label terminal-highlight")
                            yield Select(
                                options=[
                                    ("", "Select category..."),
                                    ("development", "Development"),
                                    ("bug-fix", "Bug Fix"),
                                    ("feature", "Feature"),
                                    ("refactor", "Refactoring"),
                                    ("testing", "Testing"),
                                    ("documentation", "Documentation"),
                                    ("research", "Research"),
                                    ("deployment", "Deployment"),
                                    ("maintenance", "Maintenance")
                                ],
                                value="",
                                id="category-select",
                                classes="terminal-select"
                            )
                        
                        with Vertical(classes="form-field"):
                            yield Label("Estimated Time", classes="form-label terminal-highlight")
                            yield Input(
                                placeholder="e.g., '2 hours', '1 day', '30 minutes'",
                                id="time-input",
                                classes="terminal-input"
                            )
                    
                    # Files/Paths section
                    yield Label("Related Files/Paths", classes="form-label terminal-highlight")
                    yield Input(
                        placeholder="Enter file paths separated by commas (e.g., 'src/auth.py, tests/test_auth.py')",
                        id="files-input",
                        classes="terminal-input"
                    )
                    
                    # Tags section
                    yield Label("Tags", classes="form-label terminal-highlight")
                    yield Input(
                        placeholder="Enter tags separated by commas (e.g., 'backend, authentication, security')",
                        id="tags-input",
                        classes="terminal-input"
                    )
                    
                    # Description section
                    yield Label("Quest Description", classes="form-label terminal-highlight")
                    yield TextArea(
                        placeholder="Describe the quest objectives, requirements, and any important details...",
                        id="description-input",
                        classes="terminal-textarea"
                    )
                    yield Static("", id="description-validation", classes="form-validation-message")
                    
                    # Acceptance Criteria section
                    yield Label("Acceptance Criteria", classes="form-label terminal-highlight")
                    yield TextArea(
                        placeholder="List the specific criteria that must be met to complete this quest:\n• Criterion 1\n• Criterion 2\n• Criterion 3",
                        id="acceptance-input",
                        classes="terminal-textarea"
                    )
                    yield Static("", id="acceptance-validation", classes="form-validation-message")
                    
                    # Additional Notes section
                    yield Label("Additional Notes", classes="form-label terminal-highlight")
                    yield TextArea(
                        placeholder="Any additional notes, dependencies, or considerations...",
                        id="notes-input",
                        classes="terminal-textarea"
                    )
                    
                    # XP Reward Preview Section
                    yield Label("XP Reward Preview", classes="form-label terminal-highlight")
                    yield XPCalculatorWidget(
                        difficulty=self.difficulty,
                        priority=self.priority,
                        id="xp-calculator"
                    )
                    
                    # Action buttons
                    with Horizontal(classes="form-actions"):
                        yield Button(
                            "Save Quest (Ctrl+S)", 
                            action="save_quest", 
                            classes="primary-button",
                            id="save-button"
                        )
                        yield Button(
                            "Cancel (Esc)", 
                            action="cancel", 
                            classes="secondary-button"
                        )
        
        # Terminal footer with contextual help
        yield TerminalFooterWithHelp(
            commands=[
                ("save", "Save Quest"),
                ("cancel", "Cancel"),
                ("back", "Back"),
                ("help", "Help")
            ],
            help_text="Use Tab to navigate between fields, Enter to submit"
        )
        
        # Feedback system
        yield self.feedback_system

    def on_mount(self) -> None:
        """Handle screen mount event."""
        # Set focus to title input
        title_input = self.query_one("#title-input", Input)
        if title_input:
            title_input.focus()
        
        # Update XP preview
        self._update_xp_preview()
        
        # Set contextual help
        footer = self.query_one(TerminalFooterWithHelp)
        footer.set_contextual_help("form")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input field changes."""
        input_id = event.input.id
        
        if input_id == "title-input":
            self.title = event.value
        elif input_id == "files-input":
            self.files_paths = event.value
        elif input_id == "tags-input":
            self.tags = event.value
        elif input_id == "time-input":
            self.estimated_time = event.value
        
        # Update XP preview when relevant fields change
        if input_id in ["title-input", "difficulty-select", "priority-select"]:
            self._update_xp_preview()
        
        # Validate form
        self._validate_form()

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Handle text area changes."""
        textarea_id = event.text_area.id
        
        if textarea_id == "description-input":
            self.description = event.text_area.text
        elif textarea_id == "acceptance-input":
            self.acceptance_criteria = event.text_area.text
        elif textarea_id == "notes-input":
            self.notes = event.text_area.text
        
        # Validate form
        self._validate_form()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select field changes."""
        select_id = event.select.id
        
        if select_id == "difficulty-select":
            self.difficulty = event.value
        elif select_id == "priority-select":
            self.priority = event.value
        elif select_id == "category-select":
            self.category = event.value
        
        # Update XP preview
        self._update_xp_preview()
        
        # Validate form
        self._validate_form()

    def _validate_form(self) -> None:
        """Validate the form and update validation state."""
        validation_errors = []
        
        # Required field validation
        if not self.title.strip():
            validation_errors.append("Title is required")
        elif len(self.title.strip()) > 200:
            validation_errors.append("Title cannot exceed 200 characters")
        
        if not self.difficulty:
            validation_errors.append("Difficulty is required")
        
        if not self.priority:
            validation_errors.append("Priority is required")
        
        # Optional field validation
        if self.estimated_time.strip():
            # Basic validation for estimated time format
            time_str = self.estimated_time.strip().lower()
            valid_time_units = ['minute', 'hour', 'day', 'week', 'min', 'hr', 'h', 'm', 'd', 'w']
            has_valid_unit = any(unit in time_str for unit in valid_time_units)
            has_number = any(char.isdigit() for char in time_str)
            
            if not (has_valid_unit and has_number):
                validation_errors.append("Estimated time should include a number and time unit (e.g., '2 hours', '30 minutes')")
        
        # Tags validation
        if self.tags.strip():
            tag_list = [tag.strip() for tag in self.tags.split(",") if tag.strip()]
            if len(tag_list) > 10:
                validation_errors.append("Maximum 10 tags allowed")
            
            for tag in tag_list:
                if len(tag) > 50:
                    validation_errors.append(f"Tag '{tag}' is too long (max 50 characters)")
        
        # Description validation
        if self.description.strip() and len(self.description.strip()) > 2000:
            validation_errors.append("Description cannot exceed 2000 characters")
        
        # Acceptance criteria validation
        if self.acceptance_criteria.strip() and len(self.acceptance_criteria.strip()) > 1000:
            validation_errors.append("Acceptance criteria cannot exceed 1000 characters")
        
        # Notes validation
        if self.notes.strip() and len(self.notes.strip()) > 1000:
            validation_errors.append("Notes cannot exceed 1000 characters")
        
        # Update form validity
        self.form_valid = len(validation_errors) == 0
        
        # Update save button state
        try:
            save_button = self.query_one("#save-button", Button)
            save_button.disabled = not self.form_valid
        except:
            pass
        
        # Update field-specific validation messages
        self._update_validation_messages(validation_errors)

    def _update_validation_messages(self, validation_errors: list) -> None:
        """Update validation messages for form fields."""
        try:
            # Title validation
            title_validation = self.query_one("#title-validation", Static)
            if not self.title.strip():
                title_validation.update("Required field")
                title_validation.add_class("error")
            elif len(self.title.strip()) > 200:
                title_validation.update(f"Too long ({len(self.title)} / 200 characters)")
                title_validation.add_class("error")
            elif self.title.strip():
                title_validation.update(f"{len(self.title)} / 200 characters")
                title_validation.remove_class("error")
                title_validation.add_class("success")
            else:
                title_validation.update("")
                title_validation.remove_class("error")
                title_validation.remove_class("success")
            
            # Description validation
            description_validation = self.query_one("#description-validation", Static)
            if self.description.strip():
                char_count = len(self.description.strip())
                if char_count > 2000:
                    description_validation.update(f"Too long ({char_count} / 2000 characters)")
                    description_validation.add_class("error")
                else:
                    description_validation.update(f"{char_count} / 2000 characters")
                    description_validation.remove_class("error")
                    description_validation.add_class("success")
            else:
                description_validation.update("Optional - describe quest objectives and requirements")
                description_validation.remove_class("error")
                description_validation.remove_class("success")
            
            # Acceptance criteria validation
            acceptance_validation = self.query_one("#acceptance-validation", Static)
            if self.acceptance_criteria.strip():
                char_count = len(self.acceptance_criteria.strip())
                if char_count > 1000:
                    acceptance_validation.update(f"Too long ({char_count} / 1000 characters)")
                    acceptance_validation.add_class("error")
                else:
                    acceptance_validation.update(f"{char_count} / 1000 characters")
                    acceptance_validation.remove_class("error")
                    acceptance_validation.add_class("success")
            else:
                acceptance_validation.update("Optional - list specific completion criteria")
                acceptance_validation.remove_class("error")
                acceptance_validation.remove_class("success")
                
        except Exception as e:
            # Silently handle validation message update errors
            pass

    def _update_xp_preview(self) -> None:
        """Update the XP reward preview based on current form values."""
        try:
            # Update the XP calculator widget
            xp_calculator = self.query_one("#xp-calculator", XPCalculatorWidget)
            if xp_calculator:
                xp_calculator.update_values(
                    difficulty=self.difficulty,
                    priority=self.priority
                )
                # Store the calculated XP for later use
                self.calculated_xp = xp_calculator.get_calculated_xp()
            else:
                # Fallback calculation if widget not found
                base_xp = self.difficulty.xp_value if self.difficulty else TaskDifficulty.MEDIUM.xp_value
                priority_multipliers = {
                    TaskPriority.LOW: 0.8,
                    TaskPriority.MEDIUM: 1.0,
                    TaskPriority.HIGH: 1.3,
                    TaskPriority.CRITICAL: 1.6
                }
                multiplier = priority_multipliers.get(self.priority, 1.0)
                self.calculated_xp = int(base_xp * multiplier)
                
        except Exception as e:
            # Fallback calculation on error
            try:
                base_xp = self.difficulty.xp_value if self.difficulty else TaskDifficulty.MEDIUM.xp_value
                priority_multipliers = {
                    TaskPriority.LOW: 0.8,
                    TaskPriority.MEDIUM: 1.0,
                    TaskPriority.HIGH: 1.3,
                    TaskPriority.CRITICAL: 1.6
                }
                multiplier = priority_multipliers.get(self.priority, 1.0)
                self.calculated_xp = int(base_xp * multiplier)
            except:
                self.calculated_xp = 30  # Default medium difficulty XP

    def action_save_quest(self) -> None:
        """Save the new quest."""
        if not self.form_valid:
            self.feedback_system.show_warning(
                "Please fill in all required fields (Title, Difficulty, Priority)",
                title="Missing Required Fields"
            )
            return
        
        try:
            # Parse tags
            tag_list = [tag.strip() for tag in self.tags.split(",") if tag.strip()]
            
            # Parse files/paths
            files_list = [path.strip() for path in self.files_paths.split(",") if path.strip()]
            
            # Combine description and acceptance criteria
            full_description = self.description.strip()
            if self.acceptance_criteria.strip():
                if full_description:
                    full_description += "\n\nAcceptance Criteria:\n" + self.acceptance_criteria.strip()
                else:
                    full_description = "Acceptance Criteria:\n" + self.acceptance_criteria.strip()
            
            # Create new task
            new_task = Task(
                title=self.title.strip(),
                description=full_description,
                difficulty=self.difficulty,
                priority=self.priority,
                notes=self.notes.strip() if self.notes.strip() else None,
                tags=tag_list,
                status=TaskStatus.PENDING
            )
            
            # Add custom attributes for quest-specific data
            if hasattr(new_task, '__dict__'):
                new_task.__dict__.update({
                    'category': self.category,
                    'estimated_time': self.estimated_time.strip() if self.estimated_time.strip() else None,
                    'files_paths': files_list,
                    'acceptance_criteria': self.acceptance_criteria.strip() if self.acceptance_criteria.strip() else None
                })
            
            # Add task to data manager
            self.data_manager.add_task(new_task)
            
            # Save data
            self.data_manager.save_data()
            
            # Show success feedback
            self.feedback_system.show_success(
                f"Quest '{new_task.title}' created successfully! You'll earn {format_xp_display(self.calculated_xp)} when completed.",
                title="Quest Created"
            )
            
            # Post message for parent screens
            self.post_message(self.QuestCreated(new_task))
            
            # Return to previous screen
            self.app.pop_screen()
            
        except Exception as e:
            # Handle specific error types
            error_message = str(e)
            
            if "validation error" in error_message.lower() or "invalid" in error_message.lower():
                self.feedback_system.show_error(
                    f"Validation error: {error_message}",
                    title="Invalid Quest Data"
                )
            elif "duplicate" in error_message.lower():
                self.feedback_system.show_error(
                    f"Quest with this title already exists: {error_message}",
                    title="Duplicate Quest"
                )
            else:
                self.feedback_system.show_error(
                    f"Error creating quest: {error_message}",
                    title="Creation Failed"
                )

    def action_cancel(self) -> None:
        """Cancel quest creation and return to previous screen."""
        # Post message for parent screens
        self.post_message(self.FormCancelled())
        
        # Return to previous screen
        self.app.pop_screen()

    def action_show_help(self) -> None:
        """Show help information for the quest creation form."""
        help_text = """
Quest Creation Help:

Required Fields:
• Title: A clear, descriptive name for your quest
• Difficulty: Determines base XP reward (Easy: 15, Medium: 30, Hard: 50)
• Priority: Affects XP multiplier (Low: 0.8x, Medium: 1.0x, High: 1.3x, Critical: 1.6x)

Optional Fields:
• Category: Helps organize your quests
• Estimated Time: Your time estimate for completion
• Files/Paths: Related code files or directories
• Tags: Keywords for filtering and organization
• Description: Detailed quest objectives and requirements
• Acceptance Criteria: Specific conditions that must be met
• Notes: Additional information or dependencies

Navigation:
• Tab/Shift+Tab: Move between fields
• Ctrl+S: Save quest
• Esc: Cancel and return
• F1: Show this help
"""
        
        self.feedback_system.show_info(help_text, title="Quest Creation Help")

    def action_next_field(self) -> None:
        """Move focus to the next form field."""
        current_focus = self.focused
        if current_focus:
            # Define the field order
            field_order = [
                "#title-input",
                "#difficulty-select",
                "#priority-select",
                "#category-select",
                "#time-input",
                "#files-input",
                "#tags-input",
                "#description-input",
                "#acceptance-input",
                "#notes-input",
                "#save-button"
            ]
            
            try:
                current_index = field_order.index(current_focus.id)
                next_index = (current_index + 1) % len(field_order)
                next_widget = self.query_one(field_order[next_index])
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
            # Define the field order
            field_order = [
                "#title-input",
                "#difficulty-select",
                "#priority-select",
                "#category-select",
                "#time-input",
                "#files-input",
                "#tags-input",
                "#description-input",
                "#acceptance-input",
                "#notes-input",
                "#save-button"
            ]
            
            try:
                current_index = field_order.index(current_focus.id)
                prev_index = (current_index - 1) % len(field_order)
                prev_widget = self.query_one(field_order[prev_index])
                if prev_widget:
                    prev_widget.focus()
            except (ValueError, AttributeError):
                # Fallback to first field
                first_widget = self.query_one("#title-input", Input)
                if first_widget:
                    first_widget.focus()

    # Custom messages for parent screen communication
    class QuestCreated(Message):
        """Message sent when a quest is successfully created."""
        
        def __init__(self, task: Task):
            super().__init__()
            self.task = task

    class FormCancelled(Message):
        """Message sent when the form is cancelled."""
        pass