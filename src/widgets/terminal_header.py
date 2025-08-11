"""Terminal-style header widget for QUESTA application."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Static
from typing import Optional

try:
    from ..terminal_utils import get_terminal_formatter
except ImportError:
    from terminal_utils import get_terminal_formatter


class TerminalHeader(Widget):
    """Terminal-style header widget with QUESTA branding and navigation."""
    
    DEFAULT_CSS = """
    TerminalHeader {
        dock: top;
        height: 3;
        background: #0a1543;
        color: #1b45d7;
        border-bottom: solid #3a3a3a;
    }
    
    TerminalHeader > Horizontal {
        height: 100%;
        align: center middle;
    }
    
    .header-title {
        color: #1b45d7;
        text-style: bold;
        text-align: left;
    }
    
    .header-tabs {
        color: #9aa0b0;
        text-align: center;
        margin: 0 2;
    }
    
    .header-user {
        color: #9aa0b0;
        text-align: right;
    }
    
    .active-tab {
        color: #1b45d7;
        text-style: bold;
    }
    """
    
    def __init__(
        self,
        screen_name: str = "",
        user_name: str = "",
        active_tab: int = 1,
        show_tabs: bool = True,
        **kwargs
    ):
        """Initialize the terminal header.
        
        Args:
            screen_name: Name of the current screen
            user_name: Current user name to display
            active_tab: Currently active tab number (1-6)
            show_tabs: Whether to show tab navigation indicators
        """
        super().__init__(**kwargs)
        self.screen_name = screen_name
        self.user_name = user_name
        self.active_tab = active_tab
        self.show_tabs = show_tabs
        self.formatter = get_terminal_formatter()
    
    def compose(self) -> ComposeResult:
        """Compose the header layout."""
        with Horizontal():
            # Left side - QUESTA title and screen name
            title_text = f"QUESTA - {self.screen_name}" if self.screen_name else "QUESTA"
            yield Static(title_text, classes="header-title", id="header-title")
            
            # Center - Tab navigation indicators (if enabled)
            if self.show_tabs:
                tabs_text = self._format_tab_indicators()
                yield Static(tabs_text, classes="header-tabs", id="header-tabs")
            
            # Right side - User context
            if self.user_name:
                yield Static(self.user_name, classes="header-user", id="header-user")
    
    def _format_tab_indicators(self) -> str:
        """Format the tab navigation indicators."""
        tabs = []
        for i in range(1, 7):  # Tabs 1-6 as shown in mockups
            if i == self.active_tab:
                tabs.append(f"[{i}]")
            else:
                tabs.append(f" {i} ")
        
        return " ".join(tabs)
    
    def update_screen_name(self, screen_name: str) -> None:
        """Update the screen name in the header."""
        self.screen_name = screen_name
        title_widget = self.query_one("#header-title", Static)
        title_text = f"QUESTA - {screen_name}" if screen_name else "QUESTA"
        title_widget.update(title_text)
    
    def update_user_name(self, user_name: str) -> None:
        """Update the user name in the header."""
        self.user_name = user_name
        try:
            user_widget = self.query_one("#header-user", Static)
            user_widget.update(user_name)
        except:
            # User widget doesn't exist, need to recreate layout
            pass
    
    def update_active_tab(self, tab_number: int) -> None:
        """Update the active tab indicator."""
        if 1 <= tab_number <= 6:
            self.active_tab = tab_number
            if self.show_tabs:
                try:
                    tabs_widget = self.query_one("#header-tabs", Static)
                    tabs_text = self._format_tab_indicators()
                    tabs_widget.update(tabs_text)
                except:
                    # Tabs widget doesn't exist
                    pass
    
    def set_tab_visibility(self, visible: bool) -> None:
        """Show or hide the tab navigation indicators."""
        self.show_tabs = visible
        try:
            tabs_widget = self.query_one("#header-tabs", Static)
            if visible:
                tabs_widget.display = True
                tabs_widget.update(self._format_tab_indicators())
            else:
                tabs_widget.display = False
        except:
            # Tabs widget doesn't exist, will be handled on next compose
            pass


class TerminalHeaderSimple(Widget):
    """Simplified terminal header without tabs for specific screens."""
    
    DEFAULT_CSS = """
    TerminalHeaderSimple {
        dock: top;
        height: 2;
        background: #0a1543;
        color: #1b45d7;
        border-bottom: solid #3a3a3a;
        padding: 0 2;
    }
    
    TerminalHeaderSimple > Horizontal {
        height: 100%;
        align: center middle;
    }
    
    .simple-header-title {
        color: #1b45d7;
        text-style: bold;
        text-align: left;
    }
    
    .simple-header-user {
        color: #9aa0b0;
        text-align: right;
    }
    """
    
    def __init__(
        self,
        screen_name: str = "",
        user_name: str = "",
        **kwargs
    ):
        """Initialize the simple terminal header.
        
        Args:
            screen_name: Name of the current screen
            user_name: Current user name to display
        """
        super().__init__(**kwargs)
        self.screen_name = screen_name
        self.user_name = user_name
    
    def compose(self) -> ComposeResult:
        """Compose the simple header layout."""
        with Horizontal():
            # Left side - QUESTA title and screen name
            title_text = f"QUESTA - {self.screen_name}" if self.screen_name else "QUESTA"
            yield Static(title_text, classes="simple-header-title", id="simple-header-title")
            
            # Right side - User context
            if self.user_name:
                yield Static(self.user_name, classes="simple-header-user", id="simple-header-user")
    
    def update_screen_name(self, screen_name: str) -> None:
        """Update the screen name in the header."""
        self.screen_name = screen_name
        title_widget = self.query_one("#simple-header-title", Static)
        title_text = f"QUESTA - {screen_name}" if screen_name else "QUESTA"
        title_widget.update(title_text)
    
    def update_user_name(self, user_name: str) -> None:
        """Update the user name in the header."""
        self.user_name = user_name
        try:
            user_widget = self.query_one("#simple-header-user", Static)
            user_widget.update(user_name)
        except:
            # User widget doesn't exist
            pass