"""Confirmation dialog widgets for destructive actions with comprehensive warnings."""

from typing import List, Optional, Callable, Dict, Any
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Center
from textual.screen import ModalScreen
from textual.widgets import Label, Button, Static
from textual.message import Message
from textual.binding import Binding

from ..models.task import Task


class ConfirmationDialog(ModalScreen):
    """Modal confirmation dialog for destructive actions."""
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "confirm", "Confirm"),
        Binding("y", "confirm", "Yes"),
        Binding("n", "cancel", "No"),
    ]
    
    DEFAULT_CSS = """
    ConfirmationDialog {
        align: center middle;
    }
    
    ConfirmationDialog > Vertical {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 2;
    }
    
    ConfirmationDialog .dialog-title {
        text-align: center;
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }
    
    ConfirmationDialog .dialog-message {
        text-align: center;
        color: $text;
        margin-bottom: 2;
    }
    
    ConfirmationDialog .warning-safe {
        background: $success;
        color: $success-lighten-3;
        padding: 1;
        margin: 1 0;
        border: solid $success-darken-1;
    }
    
    ConfirmationDialog .warning-caution {
        background: $warning;
        color: $warning-lighten-3;
        padding: 1;
        margin: 1 0;
        border: solid $warning-darken-1;
    }
    
    ConfirmationDialog .warning-danger {
        background: $error;
        color: $error-lighten-3;
        padding: 1;
        margin: 1 0;
        border: solid $error-darken-1;
    }
    
    ConfirmationDialog .consequences-list {
        margin: 1 0;
        padding: 1;
        background: $surface-lighten-1;
        border: solid $surface-lighten-2;
    }
    
    ConfirmationDialog .consequences-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }
    
    ConfirmationDialog .consequence-item {
        color: $text-muted;
        margin-left: 2;
    }
    
    ConfirmationDialog .alternatives-list {
        margin: 1 0;
        padding: 1;
        background: $accent-lighten-3;
        border: solid $accent;
    }
    
    ConfirmationDialog .alternatives-title {
        text-style: bold;
        color: $accent-darken-2;
        margin-bottom: 1;
    }
    
    ConfirmationDialog .alternative-item {
        color: $accent-darken-1;
        margin-left: 2;
    }
    
    ConfirmationDialog .button-container {
        margin-top: 2;
        align: center middle;
    }
    
    ConfirmationDialog .confirm-button {
        margin: 0 1;
    }
    
    ConfirmationDialog .cancel-button {
        margin: 0 1;
    }
    """
    
    def __init__(
        self,
        title: str,
        message: str,
        warning_level: str = "caution",
        consequences: Optional[List[str]] = None,
        alternatives: Optional[List[str]] = None,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        **kwargs
    ):
        """Initialize confirmation dialog.
        
        Args:
            title: Dialog title
            message: Main confirmation message
            warning_level: Warning level (safe, caution, danger)
            consequences: List of consequences
            alternatives: List of alternative actions
            confirm_text: Text for confirm button
            cancel_text: Text for cancel button
        """
        super().__init__(**kwargs)
        self.dialog_title = title
        self.dialog_message = message
        self.warning_level = warning_level
        self.consequences = consequences or []
        self.alternatives = alternatives or []
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text
    
    def compose(self) -> ComposeResult:
        """Compose the confirmation dialog layout."""
        with Vertical():
            # Dialog title
            yield Label(self.dialog_title, classes="dialog-title")
            
            # Main message
            yield Label(self.dialog_message, classes="dialog-message")
            
            # Warning indicator based on level
            warning_class = f"warning-{self.warning_level}"
            warning_icons = {
                "safe": "✅",
                "caution": "⚠️",
                "danger": "🚨"
            }
            warning_messages = {
                "safe": "This action is safe and can be undone.",
                "caution": "This action requires confirmation.",
                "danger": "This action is permanent and cannot be undone!"
            }
            
            icon = warning_icons.get(self.warning_level, "⚠️")
            warning_msg = warning_messages.get(self.warning_level, "Please confirm this action.")
            
            with Static(classes=warning_class):
                yield Label(f"{icon} {warning_msg}")
            
            # Consequences section
            if self.consequences:
                with Vertical(classes="consequences-list"):
                    yield Label("⚡ Consequences:", classes="consequences-title")
                    for consequence in self.consequences:
                        yield Label(f"• {consequence}", classes="consequence-item")
            
            # Alternatives section
            if self.alternatives:
                with Vertical(classes="alternatives-list"):
                    yield Label("💡 Alternatives:", classes="alternatives-title")
                    for alternative in self.alternatives:
                        yield Label(f"• {alternative}", classes="alternative-item")
            
            # Buttons
            with Horizontal(classes="button-container"):
                if self.warning_level == "danger":
                    yield Button(self.confirm_text, variant="error", id="confirm_button", classes="confirm-button")
                elif self.warning_level == "caution":
                    yield Button(self.confirm_text, variant="warning", id="confirm_button", classes="confirm-button")
                else:
                    yield Button(self.confirm_text, variant="primary", id="confirm_button", classes="confirm-button")
                
                yield Button(self.cancel_text, variant="default", id="cancel_button", classes="cancel-button")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "confirm_button":
            self.dismiss(True)
        elif event.button.id == "cancel_button":
            self.dismiss(False)
    
    def action_confirm(self) -> None:
        """Confirm action via keyboard."""
        self.dismiss(True)
    
    def action_cancel(self) -> None:
        """Cancel action via keyboard."""
        self.dismiss(False)


class TaskDeletionDialog(ConfirmationDialog):
    """Specialized confirmation dialog for task deletion."""
    
    def __init__(self, task: Task, safety_info: Dict[str, Any], **kwargs):
        """Initialize task deletion dialog.
        
        Args:
            task: Task to be deleted
            safety_info: Safety information from task manager
        """
        # Determine warning level and messages based on safety info
        warning_level = safety_info.get('safety_level', 'caution')
        
        title = f"Delete Task: {task.title}"
        
        if task.is_completed:
            message = f"Are you sure you want to delete the completed task '{task.title}'?"
        elif task.status.name == "ACTIVE":
            message = f"Are you sure you want to delete the active task '{task.title}'?"
        else:
            message = f"Are you sure you want to delete the task '{task.title}'?"
        
        # Build consequences list
        consequences = []
        if task.is_completed:
            consequences.append(f"Task history will be permanently lost")
            consequences.append(f"Earned XP ({task.xp_reward}) will remain in your account")
        else:
            consequences.append(f"Potential XP reward ({task.xp_reward}) will be lost")
        
        consequences.append("This action cannot be undone")
        
        # Add warnings from safety info
        consequences.extend(safety_info.get('warnings', []))
        
        # Build alternatives list
        alternatives = []
        if task.status.name == "ACTIVE":
            alternatives.append("Mark task as 'Blocked' instead")
            alternatives.append("Mark task as 'Pending' instead")
        elif not task.is_completed:
            alternatives.append("Complete the task to earn XP")
            alternatives.append("Mark task as 'Blocked' if stuck")
        
        if task.priority.name in ["HIGH", "CRITICAL"]:
            alternatives.append("Consider the task's high priority before deleting")
        
        super().__init__(
            title=title,
            message=message,
            warning_level=warning_level,
            consequences=consequences,
            alternatives=alternatives,
            confirm_text="Delete Task",
            cancel_text="Keep Task",
            **kwargs
        )
        # Store references without using properties to avoid attribute collisions
        self._task_ref = task
        self._safety_info = safety_info


class TaskCompletionDialog(ConfirmationDialog):
    """Specialized confirmation dialog for task completion."""
    
    def __init__(self, task: Task, xp_preview: Dict[str, Any], **kwargs):
        """Initialize task completion dialog.
        
        Args:
            task: Task to be completed
            xp_preview: XP reward preview information
        """
        title = f"Complete Task: {task.title}"
        
        base_xp = xp_preview.get('base_xp', task.xp_reward)
        # XPCalculator.preview_xp_reward returns 'total_bonus', not 'bonus_xp'
        total_bonus = xp_preview.get('total_bonus', 0)
        total_xp = xp_preview.get('total_xp', base_xp)
        
        if total_bonus > 0:
            message = f"Complete '{task.title}' and earn {total_xp} XP ({base_xp} base + {total_bonus} bonus)?"
        else:
            message = f"Complete '{task.title}' and earn {total_xp} XP?"
        
        # Build consequences list
        consequences = [
            f"Task status will change to 'Completed'",
            f"You will earn {total_xp} XP",
            f"Task difficulty and status cannot be changed after completion"
        ]
        
        # Add level up information if available
        if xp_preview.get('will_level_up', False):
            new_level = xp_preview.get('new_level', 0)
            consequences.append(f"🎉 You will level up to Level {new_level}!")
        
        # Build alternatives list
        alternatives = []
        if task.status.name != "ACTIVE":
            alternatives.append("Mark task as 'Active' first to track progress")
        alternatives.append("Add notes before completing if needed")
        alternatives.append("Update task details if they've changed")
        
        super().__init__(
            title=title,
            message=message,
            warning_level="safe",
            consequences=consequences,
            alternatives=alternatives,
            confirm_text="Complete Task",
            cancel_text="Not Yet",
            **kwargs
        )
        # Store references without using properties to avoid attribute collisions
        self._task_ref = task
        self._xp_preview = xp_preview


class BulkActionDialog(ConfirmationDialog):
    """Specialized confirmation dialog for bulk actions."""
    
    def __init__(
        self,
        action: str,
        task_count: int,
        task_details: List[str],
        **kwargs
    ):
        """Initialize bulk action dialog.
        
        Args:
            action: Action being performed (e.g., "delete", "complete", "update status")
            task_count: Number of tasks affected
            task_details: List of task details for display
        """
        title = f"Bulk {action.title()}: {task_count} Tasks"
        message = f"Are you sure you want to {action} {task_count} tasks?"
        
        # Build consequences list
        consequences = [
            f"{task_count} tasks will be affected",
            f"This action will be applied to all selected tasks",
        ]
        
        if action == "delete":
            consequences.append("Deleted tasks cannot be recovered")
            warning_level = "danger"
        elif action == "complete":
            consequences.append("Completed tasks cannot be uncompleted")
            warning_level = "caution"
        else:
            warning_level = "caution"
        
        # Add task details (limited to first few)
        if task_details:
            consequences.append("Affected tasks:")
            for i, detail in enumerate(task_details[:5]):  # Show first 5
                consequences.append(f"  • {detail}")
            if len(task_details) > 5:
                consequences.append(f"  ... and {len(task_details) - 5} more")
        
        # Build alternatives list
        alternatives = [
            "Select fewer tasks for a smaller operation",
            "Review each task individually",
            "Use filters to refine your selection"
        ]
        
        super().__init__(
            title=title,
            message=message,
            warning_level=warning_level,
            consequences=consequences,
            alternatives=alternatives,
            confirm_text=f"{action.title()} All",
            cancel_text="Cancel",
            **kwargs
        )
        self.action = action
        self.task_count = task_count
        self.task_details = task_details


class DataRecoveryDialog(ConfirmationDialog):
    """Specialized confirmation dialog for data recovery operations."""
    
    def __init__(
        self,
        recovery_type: str,
        data_info: Dict[str, Any],
        **kwargs
    ):
        """Initialize data recovery dialog.
        
        Args:
            recovery_type: Type of recovery (backup_restore, corruption_fix, etc.)
            data_info: Information about the data and recovery process
        """
        recovery_titles = {
            "backup_restore": "Restore from Backup",
            "corruption_fix": "Fix Data Corruption",
            "migration": "Migrate Data Format"
        }
        
        title = recovery_titles.get(recovery_type, "Data Recovery")
        
        if recovery_type == "backup_restore":
            backup_date = data_info.get('backup_date', 'Unknown')
            message = f"Restore data from backup created on {backup_date}?"
        elif recovery_type == "corruption_fix":
            message = "Attempt to fix corrupted data files?"
        else:
            message = "Proceed with data recovery operation?"
        
        # Build consequences list
        consequences = []
        if recovery_type == "backup_restore":
            consequences.extend([
                "Current data will be replaced with backup data",
                "Recent changes may be lost",
                "Backup data will become your active data"
            ])
        elif recovery_type == "corruption_fix":
            consequences.extend([
                "Corrupted data will be repaired if possible",
                "Some data may be lost if corruption is severe",
                "A backup will be created before repair"
            ])
        
        # Add data-specific consequences
        if 'tasks_affected' in data_info:
            consequences.append(f"{data_info['tasks_affected']} tasks may be affected")
        
        if 'player_data_affected' in data_info and data_info['player_data_affected']:
            consequences.append("Player progress data may be affected")
        
        # Build alternatives list
        alternatives = [
            "Create a manual backup first",
            "Export important data before proceeding",
            "Contact support for assistance"
        ]
        
        if recovery_type == "backup_restore":
            alternatives.append("Check if multiple backups are available")
        
        super().__init__(
            title=title,
            message=message,
            warning_level="caution",
            consequences=consequences,
            alternatives=alternatives,
            confirm_text="Proceed",
            cancel_text="Cancel",
            **kwargs
        )
        self.recovery_type = recovery_type
        self.data_info = data_info