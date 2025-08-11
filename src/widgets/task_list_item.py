"""TaskListItem - Widget for displaying individual tasks in lists."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Label, Button
from textual.message import Message
from textual.binding import Binding

from ..models.task import Task
from ..models.enums import TaskStatus, TaskPriority
from .status_badge import StatusBadge
from .priority_indicator import PriorityIndicator


class TaskListItem(Widget):
    """A widget representing a single task in a list."""

    BINDINGS = [
        Binding("enter", "select", "Select Task", show=True),
        Binding("space", "select", "Select Task", show=True),
        Binding("e", "edit", "Edit Task", show=True),
        Binding("d", "delete", "Delete Task", show=True),
        Binding("c", "complete", "Complete Task", show=True),
    ]

    def __init__(self, task: Task, **kwargs):
        """Initialize the task list item.
        
        Args:
            task: The task to display
        """
        super().__init__(**kwargs)
        # Store underlying task to avoid clashing with any inherited attributes
        self._task = task
        # Public selection state expected by tests
        self.selected = False
        # Initialize classes to reflect current task state
        try:
            self._update_classes()
        except Exception:
            # Safe-guard for early init before DOM exists
            pass

    @property
    def task(self) -> Task:
        """Expose the underlying task as a read-only property for tests/UI."""
        return self._task

    def compose(self) -> ComposeResult:
        """Compose the task list item layout."""
        # Guard against incorrect objects being passed (e.g., asyncio.Task)
        if not isinstance(self._task, Task):
            with Horizontal():
                with Vertical(classes="task-content"):
                    yield Label("Invalid task", classes="task-title")
            return

        with Horizontal():
            # Status and priority indicators
            with Vertical(classes="indicators"):
                yield StatusBadge(self._task.status)
                yield PriorityIndicator(self._task.priority)
            
            # Task details
            with Vertical(classes="task-content"):
                yield Label(self._task.title, classes="task-title")
                if getattr(self._task, "description", None):
                    yield Label(self._task.description, classes="task-description")
                yield Label(f"XP: {self._task.xp_reward}", classes="task-xp")
                
                # Tags if present
                if getattr(self._task, "tags", None):
                    yield Label(f"Tags: {', '.join(self._task.tags)}", classes="task-tags")
                
                # Notes if present
                if self._task.notes:
                    yield Label(f"Notes: {self._task.notes}", classes="task-notes")

    def update_task(self, task: Task) -> None:
        """Update the displayed task and refresh the widget."""
        if isinstance(task, Task):
            self._task = task
        self._update_classes()
        self.refresh()

    def set_selected(self, selected: bool) -> None:
        """Set the selection state of this item."""
        self.selected = selected
        self._update_classes()

    def _update_classes(self) -> None:
        """Update CSS classes based on current state."""
        if self.selected:
            self.add_class("selected")
        else:
            self.remove_class("selected")
        
        # Add status-based classes
        self.remove_class("pending", "active", "completed", "blocked")
        self.add_class(self._task.status.value.lower())
        
        # Add priority-based classes
        self.remove_class("low", "medium", "high", "critical")
        self.add_class(self._task.priority.value.lower())

    def action_select(self) -> None:
        """Handle task selection."""
        self.post_message(self.TaskSelected(self._task))

    def action_edit(self) -> None:
        """Handle edit action."""
        self.post_message(self.TaskEditRequested(self._task))

    def action_delete(self) -> None:
        """Handle delete action."""
        self.post_message(self.TaskDeleteRequested(self._task))

    def action_complete(self) -> None:
        """Handle complete action."""
        self.post_message(self.TaskCompleteRequested(self._task))

    # Custom messages for parent communication
    class TaskSelected(Message):
        """Message sent when a task is selected."""
        
        def __init__(self, task: Task):
            super().__init__()
            self.task = task

    class TaskEditRequested(Message):
        """Message sent when task editing is requested."""
        
        def __init__(self, task: Task):
            super().__init__()
            self.task = task

    class TaskDeleteRequested(Message):
        """Message sent when task deletion is requested."""
        
        def __init__(self, task: Task):
            super().__init__()
            self.task = task

    class TaskCompleteRequested(Message):
        """Message sent when task completion is requested."""
        
        def __init__(self, task: Task):
            super().__init__()
            self.task = task