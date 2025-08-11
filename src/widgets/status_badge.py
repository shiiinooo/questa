"""StatusBadge widget with color-coded status indicators."""

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label

from ..models.enums import TaskStatus


class StatusBadge(Widget):
    """Widget for displaying task status with color-coded indicators."""
    
    DEFAULT_CSS = """
    StatusBadge {
        width: auto;
        height: 1;
        margin: 0 1;
    }
    
    StatusBadge .status-label {
        text-align: center;
        text-style: bold;
        padding: 0 1;
        border-radius: 1;
    }
    
    StatusBadge .status-pending {
        background: $warning;
        color: $warning-darken-3;
    }
    
    StatusBadge .status-active {
        background: $primary;
        color: $primary-darken-3;
    }
    
    StatusBadge .status-blocked {
        background: $error;
        color: $error-darken-3;
    }
    
    StatusBadge .status-completed {
        background: $success;
        color: $success-darken-3;
    }
    """
    
    def __init__(self, status: TaskStatus, **kwargs):
        """Initialize StatusBadge with a task status."""
        super().__init__(**kwargs)
        self.status = status
    
    def compose(self) -> ComposeResult:
        """Compose the status badge layout."""
        status_class = f"status-{self.status.value.lower()}"
        yield Label(
            self.status.value.upper(),
            classes=f"status-label {status_class}"
        )
    
    def update_status(self, status: TaskStatus) -> None:
        """Update the displayed status and refresh the widget."""
        self.status = status
        self.refresh()
    
    @property
    def status_color(self) -> str:
        """Get the color associated with the current status."""
        color_map = {
            TaskStatus.PENDING: "warning",
            TaskStatus.ACTIVE: "primary", 
            TaskStatus.BLOCKED: "error",
            TaskStatus.COMPLETED: "success"
        }
        return color_map.get(self.status, "surface")
    
    @property
    def status_symbol(self) -> str:
        """Get a symbol representation of the status."""
        symbol_map = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.ACTIVE: "🔄",
            TaskStatus.BLOCKED: "🚫", 
            TaskStatus.COMPLETED: "✅"
        }
        return symbol_map.get(self.status, "❓")