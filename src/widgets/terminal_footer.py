"""Terminal-style footer widget for command navigation."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Static
from typing import List, Tuple, Union, Optional

try:
    from ..terminal_utils import get_terminal_formatter
except ImportError:
    from terminal_utils import get_terminal_formatter


class TerminalFooter(Widget):
    """Terminal-style footer widget with command navigation and status."""
    
    DEFAULT_CSS = """
    TerminalFooter {
        dock: bottom;
        height: 2;
        background: #0a1543;
        color: #9aa0b0;
        border-top: solid #3a3a3a;
        padding: 0 2;
    }
    
    TerminalFooter > Horizontal {
        height: 100%;
        align: center middle;
    }
    
    .footer-commands {
        color: #9aa0b0;
        text-align: left;
    }
    
    .footer-status {
        color: #9aa0b0;
        text-align: right;
    }
    
    .command-highlight {
        color: #1b45d7;
        text-style: bold;
    }
    
    .status-info {
        color: #ffc107;
    }
    """
    
    def __init__(
        self,
        commands: Optional[List[Union[str, Tuple[str, str]]]] = None,
        status_info: str = "",
        **kwargs
    ):
        """Initialize the terminal footer.
        
        Args:
            commands: List of available commands. Can be strings or (command, description) tuples
            status_info: Status information to display on the right side
        """
        super().__init__(**kwargs)
        self.commands = commands or self._get_default_commands()
        self.status_info = status_info
        self.formatter = get_terminal_formatter()
    
    def _get_default_commands(self) -> List[Tuple[str, str]]:
        """Get the default set of commands."""
        return [
            ("back", "Back"),
            ("navigate", "Navigate"),
            ("help", "Help"),
            ("quit", "Quit")
        ]
    
    def compose(self) -> ComposeResult:
        """Compose the footer layout."""
        with Horizontal():
            # Left side - Available commands
            commands_text = self._format_commands()
            yield Static(commands_text, classes="footer-commands", id="footer-commands")
            
            # Right side - Status information
            if self.status_info:
                yield Static(self.status_info, classes="footer-status", id="footer-status")
    
    def _format_commands(self) -> str:
        """Format the available commands for display."""
        formatted_commands = []
        
        for cmd in self.commands:
            if isinstance(cmd, tuple):
                command, description = cmd
                formatted_commands.append(f":{command} {description}")
            else:
                formatted_commands.append(f":{cmd}")
        
        return " | ".join(formatted_commands)
    
    def update_commands(self, commands: List[Union[str, Tuple[str, str]]]) -> None:
        """Update the available commands."""
        self.commands = commands
        commands_widget = self.query_one("#footer-commands", Static)
        commands_text = self._format_commands()
        commands_widget.update(commands_text)
    
    def update_status(self, status_info: str) -> None:
        """Update the status information."""
        self.status_info = status_info
        try:
            status_widget = self.query_one("#footer-status", Static)
            status_widget.update(status_info)
        except:
            # Status widget doesn't exist, need to recreate layout
            pass
    
    def add_command(self, command: Union[str, Tuple[str, str]]) -> None:
        """Add a new command to the footer."""
        if command not in self.commands:
            self.commands.append(command)
            self.update_commands(self.commands)
    
    def remove_command(self, command_name: str) -> None:
        """Remove a command from the footer."""
        self.commands = [
            cmd for cmd in self.commands
            if (isinstance(cmd, tuple) and cmd[0] != command_name) or
               (isinstance(cmd, str) and cmd != command_name)
        ]
        self.update_commands(self.commands)
    
    def set_screen_commands(self, screen_name: str) -> None:
        """Set commands appropriate for a specific screen."""
        screen_commands = {
            "welcome": [
                ("enter", "Continue"),
                ("quit", "Quit")
            ],
            "journal": [
                ("back", "Back"),
                ("navigate", "Navigate"),
                ("help", "Help"),
                ("quit", "Quit")
            ],
            "new_quest": [
                ("save", "Save Quest"),
                ("cancel", "Cancel"),
                ("back", "Back"),
                ("help", "Help")
            ],
            "character_stats": [
                ("back", "Back"),
                ("navigate", "Navigate"),
                ("achievements", "View Achievements"),
                ("help", "Help"),
                ("quit", "Quit")
            ],
            "all_quests": [
                ("add", "New Quest"),
                ("edit", "Edit"),
                ("complete", "Complete"),
                ("delete", "Delete"),
                ("filter", "Filter"),
                ("back", "Back"),
                ("help", "Help")
            ],
            "dashboard": [
                ("add", "New Quest"),
                ("edit", "Edit"),
                ("complete", "Complete"),
                ("journal", "Journal"),
                ("stats", "Stats"),
                ("help", "Help"),
                ("quit", "Quit")
            ]
        }
        
        commands = screen_commands.get(screen_name.lower(), self._get_default_commands())
        self.update_commands(commands)


class TerminalFooterWithHelp(TerminalFooter):
    """Extended terminal footer with help text display."""
    
    DEFAULT_CSS = """
    TerminalFooterWithHelp {
        dock: bottom;
        height: 3;
        background: #0a1543;
        color: #9aa0b0;
        border-top: solid #3a3a3a;
        padding: 1 2;
    }
    
    .footer-help-text {
        color: #9aa0b0;
        text-style: italic;
        text-align: center;
        height: 1;
    }
    
    .footer-main-row {
        height: 1;
    }
    """
    
    def __init__(
        self,
        commands: Optional[List[Union[str, Tuple[str, str]]]] = None,
        status_info: str = "",
        help_text: str = "",
        **kwargs
    ):
        """Initialize the extended terminal footer.
        
        Args:
            commands: List of available commands
            status_info: Status information to display
            help_text: Additional help text to display
        """
        super().__init__(commands, status_info, **kwargs)
        self.help_text = help_text
    
    def compose(self) -> ComposeResult:
        """Compose the extended footer layout."""
        # Help text row
        if self.help_text:
            yield Static(self.help_text, classes="footer-help-text", id="footer-help-text")
        
        # Main commands and status row
        with Horizontal(classes="footer-main-row"):
            commands_text = self._format_commands()
            yield Static(commands_text, classes="footer-commands", id="footer-commands")
            
            if self.status_info:
                yield Static(self.status_info, classes="footer-status", id="footer-status")
    
    def update_help_text(self, help_text: str) -> None:
        """Update the help text."""
        self.help_text = help_text
        try:
            help_widget = self.query_one("#footer-help-text", Static)
            help_widget.update(help_text)
        except:
            # Help widget doesn't exist
            pass
    
    def set_contextual_help(self, context: str) -> None:
        """Set contextual help text based on current context."""
        help_texts = {
            "form": "Use Tab to navigate between fields, Enter to submit",
            "list": "Use arrow keys to navigate, Enter to select, Space to toggle",
            "navigation": "Use :navigate <screen> to jump to a specific screen",
            "commands": "Type :help for a full list of available commands",
            "editing": "Use Ctrl+S to save, Ctrl+C to cancel changes"
        }
        
        help_text = help_texts.get(context, "")
        self.update_help_text(help_text)


class TerminalStatusBar(Widget):
    """Simple status bar for displaying current application state."""
    
    DEFAULT_CSS = """
    TerminalStatusBar {
        dock: bottom;
        height: 1;
        background: #181817;
        color: #9aa0b0;
        padding: 0 2;
    }
    
    TerminalStatusBar > Horizontal {
        height: 100%;
        align: center middle;
    }
    
    .status-left {
        text-align: left;
    }
    
    .status-center {
        text-align: center;
        margin: 0 2;
    }
    
    .status-right {
        text-align: right;
        margin-left: auto;
    }
    """
    
    def __init__(
        self,
        left_text: str = "",
        center_text: str = "",
        right_text: str = "",
        **kwargs
    ):
        """Initialize the status bar.
        
        Args:
            left_text: Text to display on the left
            center_text: Text to display in the center
            right_text: Text to display on the right
        """
        super().__init__(**kwargs)
        self.left_text = left_text
        self.center_text = center_text
        self.right_text = right_text
    
    def compose(self) -> ComposeResult:
        """Compose the status bar layout."""
        with Horizontal():
            if self.left_text:
                yield Static(self.left_text, classes="status-left", id="status-left")
            
            if self.center_text:
                yield Static(self.center_text, classes="status-center", id="status-center")
            
            if self.right_text:
                yield Static(self.right_text, classes="status-right", id="status-right")
    
    def update_left(self, text: str) -> None:
        """Update the left status text."""
        self.left_text = text
        try:
            widget = self.query_one("#status-left", Static)
            widget.update(text)
        except:
            pass
    
    def update_center(self, text: str) -> None:
        """Update the center status text."""
        self.center_text = text
        try:
            widget = self.query_one("#status-center", Static)
            widget.update(text)
        except:
            pass
    
    def update_right(self, text: str) -> None:
        """Update the right status text."""
        self.right_text = text
        try:
            widget = self.query_one("#status-right", Static)
            widget.update(text)
        except:
            pass