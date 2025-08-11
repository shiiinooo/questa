"""Terminal-style panel widget with ASCII borders and scrollable content."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widget import Widget
from textual.widgets import Static
from textual.containers import ScrollableContainer
from typing import Optional, Union, List, Tuple

try:
    from ..terminal_utils import get_terminal_formatter, get_terminal_ascii_chars
except ImportError:
    from terminal_utils import get_terminal_formatter, get_terminal_ascii_chars


class TerminalPanel(Widget):
    """Reusable terminal-style panel with ASCII borders and optional header."""
    
    DEFAULT_CSS = """
    TerminalPanel {
        background: #181817;
        border: solid #3a3a3a;
        padding: 0;
        margin: 1;
    }
    
    TerminalPanel.focused {
        border: solid #1b45d7;
    }
    
    .panel-header {
        dock: top;
        height: 1;
        background: #0a1543;
        color: #1b45d7;
        text-style: bold;
        padding: 0 1;
        border-bottom: solid #3a3a3a;
    }
    
    .panel-content {
        padding: 1;
        height: 100%;
        background: #181817;
    }
    
    .panel-title {
        color: #1b45d7;
        text-style: bold;
        text-align: center;
    }
    
    .panel-border-top {
        color: #3a3a3a;
        height: 1;
        dock: top;
    }
    
    .panel-border-bottom {
        color: #3a3a3a;
        height: 1;
        dock: bottom;
    }
    
    .panel-scrollable {
        height: 100%;
        scrollbar-gutter: stable;
    }
    """
    
    def __init__(
        self,
        title: str = "",
        scrollable: bool = True,
        show_border: bool = True,
        border_style: str = "single",  # "single", "double", "thick"
        focusable: bool = True,
        **kwargs
    ):
        """Initialize the terminal panel.
        
        Args:
            title: Panel title to display in header
            scrollable: Whether the content area should be scrollable
            show_border: Whether to show ASCII-style borders
            border_style: Style of border ("single", "double", "thick")
            focusable: Whether the panel can receive focus
        """
        super().__init__(**kwargs)
        self.title = title
        self.scrollable = scrollable
        self.show_border = show_border
        self.border_style = border_style
        self.can_focus = focusable
        self.formatter = get_terminal_formatter()
        self.ascii_chars = get_terminal_ascii_chars()
    
    def compose(self) -> ComposeResult:
        """Compose the panel layout."""
        # Optional ASCII border top
        if self.show_border:
            border_top = self._create_border_line("top")
            yield Static(border_top, classes="panel-border-top")
        
        # Panel header with title
        if self.title:
            yield Static(self.title, classes="panel-header panel-title", id="panel-header")
        
        # Content area
        if self.scrollable:
            with ScrollableContainer(classes="panel-content panel-scrollable", id="panel-content"):
                yield Container(id="panel-inner-content")
        else:
            yield Container(classes="panel-content", id="panel-content")
        
        # Optional ASCII border bottom
        if self.show_border:
            border_bottom = self._create_border_line("bottom")
            yield Static(border_bottom, classes="panel-border-bottom")
    
    def _create_border_line(self, position: str) -> str:
        """Create an ASCII border line."""
        # For now, return a simple line - can be enhanced with full ASCII box drawing
        chars = self.ascii_chars
        
        if self.border_style == "double":
            char = chars['box_double_horizontal']
        elif self.border_style == "thick":
            char = chars['progress_full']
        else:
            char = chars['box_horizontal']
        
        # Create a line of appropriate length (will be styled by CSS)
        return char * 50  # Default width, will be adjusted by CSS
    
    def update_title(self, title: str) -> None:
        """Update the panel title."""
        self.title = title
        try:
            header_widget = self.query_one("#panel-header", Static)
            header_widget.update(title)
        except:
            # Header doesn't exist
            pass
    
    def get_content_container(self) -> Container:
        """Get the content container for adding child widgets."""
        if self.scrollable:
            return self.query_one("#panel-inner-content", Container)
        else:
            return self.query_one("#panel-content", Container)
    
    def add_content(self, widget: Widget) -> None:
        """Add a widget to the panel content."""
        content_container = self.get_content_container()
        content_container.mount(widget)
    
    def clear_content(self) -> None:
        """Clear all content from the panel."""
        content_container = self.get_content_container()
        content_container.remove_children()
    
    def set_focus_style(self, focused: bool) -> None:
        """Update the panel's focus styling."""
        if focused:
            self.add_class("focused")
        else:
            self.remove_class("focused")


class TerminalPanelWithBorder(TerminalPanel):
    """Terminal panel with full ASCII box drawing borders."""
    
    DEFAULT_CSS = """
    TerminalPanelWithBorder {
        background: #181817;
        padding: 0;
        margin: 1;
    }
    
    TerminalPanelWithBorder.focused {
        background: #1e1e1e;
    }
    
    .ascii-border {
        color: #3a3a3a;
        text-style: bold;
    }
    
    .ascii-border.focused {
        color: #1b45d7;
    }
    
    .border-content {
        padding: 1;
        background: #181817;
    }
    """
    
    def __init__(
        self,
        title: str = "",
        width: int = 40,
        height: int = 10,
        scrollable: bool = True,
        **kwargs
    ):
        """Initialize the bordered terminal panel.
        
        Args:
            title: Panel title
            width: Panel width in characters
            height: Panel height in lines
            scrollable: Whether content should be scrollable
        """
        super().__init__(title, scrollable, show_border=False, **kwargs)
        self.panel_width = width
        self.panel_height = height
    
    def compose(self) -> ComposeResult:
        """Compose the panel with full ASCII borders."""
        # Create the full ASCII border box
        border_box = self._create_full_border()
        yield Static(border_box, classes="ascii-border", id="ascii-border")
        
        # Content area inside the border
        if self.scrollable:
            with ScrollableContainer(classes="border-content panel-scrollable", id="panel-content"):
                yield Container(id="panel-inner-content")
        else:
            yield Container(classes="border-content", id="panel-content")
    
    def _create_full_border(self) -> str:
        """Create a full ASCII box border with optional title."""
        chars = self.ascii_chars
        
        # Top border
        if self.title:
            title_len = len(self.title)
            if title_len + 4 < self.panel_width:  # 4 for spaces and brackets
                padding = (self.panel_width - title_len - 4) // 2
                remaining = self.panel_width - title_len - 4 - padding
                top_line = (chars['box_top_left'] + 
                           chars['box_horizontal'] * padding + 
                           f" {self.title} " + 
                           chars['box_horizontal'] * remaining + 
                           chars['box_top_right'])
            else:
                top_line = (chars['box_top_left'] + 
                           chars['box_horizontal'] * (self.panel_width - 2) + 
                           chars['box_top_right'])
        else:
            top_line = (chars['box_top_left'] + 
                       chars['box_horizontal'] * (self.panel_width - 2) + 
                       chars['box_top_right'])
        
        # Middle lines (empty for content)
        middle_lines = []
        for _ in range(self.panel_height - 2):
            middle_lines.append(chars['box_vertical'] + 
                              " " * (self.panel_width - 2) + 
                              chars['box_vertical'])
        
        # Bottom border
        bottom_line = (chars['box_bottom_left'] + 
                      chars['box_horizontal'] * (self.panel_width - 2) + 
                      chars['box_bottom_right'])
        
        return "\n".join([top_line] + middle_lines + [bottom_line])


class TerminalSplitPanel(Widget):
    """Terminal panel with horizontal or vertical split layout."""
    
    DEFAULT_CSS = """
    TerminalSplitPanel {
        background: #181817;
        border: solid #3a3a3a;
        padding: 0;
        margin: 1;
    }
    
    .split-left, .split-right {
        background: #181817;
        padding: 1;
    }
    
    .split-top, .split-bottom {
        background: #181817;
        padding: 1;
    }
    
    .split-divider {
        color: #3a3a3a;
        background: #0a1543;
    }
    
    .split-divider-vertical {
        width: 1;
        dock: left;
    }
    
    .split-divider-horizontal {
        height: 1;
        dock: top;
    }
    """
    
    def __init__(
        self,
        orientation: str = "horizontal",  # "horizontal" or "vertical"
        split_ratio: float = 0.5,
        left_title: str = "",
        right_title: str = "",
        **kwargs
    ):
        """Initialize the split panel.
        
        Args:
            orientation: Split orientation ("horizontal" or "vertical")
            split_ratio: Ratio of the split (0.0 to 1.0)
            left_title: Title for left/top panel
            right_title: Title for right/bottom panel
        """
        super().__init__(**kwargs)
        self.orientation = orientation
        self.split_ratio = split_ratio
        self.left_title = left_title
        self.right_title = right_title
        self.ascii_chars = get_terminal_ascii_chars()
    
    def compose(self) -> ComposeResult:
        """Compose the split panel layout."""
        if self.orientation == "horizontal":
            with Horizontal():
                # Left panel
                left_panel = TerminalPanel(
                    title=self.left_title,
                    scrollable=True,
                    show_border=False
                )
                left_panel.styles.width = f"{int(self.split_ratio * 100)}%"
                yield left_panel
                
                # Divider
                divider_char = self.ascii_chars['box_vertical']
                yield Static(divider_char, classes="split-divider split-divider-vertical")
                
                # Right panel
                right_panel = TerminalPanel(
                    title=self.right_title,
                    scrollable=True,
                    show_border=False
                )
                right_panel.styles.width = f"{int((1 - self.split_ratio) * 100)}%"
                yield right_panel
        else:
            with Vertical():
                # Top panel
                top_panel = TerminalPanel(
                    title=self.left_title,
                    scrollable=True,
                    show_border=False
                )
                top_panel.styles.height = f"{int(self.split_ratio * 100)}%"
                yield top_panel
                
                # Divider
                divider_char = self.ascii_chars['box_horizontal']
                yield Static(divider_char, classes="split-divider split-divider-horizontal")
                
                # Bottom panel
                bottom_panel = TerminalPanel(
                    title=self.right_title,
                    scrollable=True,
                    show_border=False
                )
                bottom_panel.styles.height = f"{int((1 - self.split_ratio) * 100)}%"
                yield bottom_panel
    
    def get_left_panel(self) -> TerminalPanel:
        """Get the left/top panel."""
        panels = self.query(TerminalPanel)
        return panels[0] if panels else None
    
    def get_right_panel(self) -> TerminalPanel:
        """Get the right/bottom panel."""
        panels = self.query(TerminalPanel)
        return panels[1] if len(panels) > 1 else None


class TerminalTabPanel(Widget):
    """Terminal panel with tab navigation."""
    
    DEFAULT_CSS = """
    TerminalTabPanel {
        background: #181817;
        border: solid #3a3a3a;
        padding: 0;
        margin: 1;
    }
    
    .tab-header {
        dock: top;
        height: 1;
        background: #0a1543;
        border-bottom: solid #3a3a3a;
        padding: 0 1;
    }
    
    .tab-button {
        color: #9aa0b0;
        margin: 0 1;
    }
    
    .tab-button.active {
        color: #1b45d7;
        text-style: bold;
    }
    
    .tab-content {
        padding: 1;
        height: 100%;
    }
    """
    
    def __init__(
        self,
        tabs: List[Tuple[str, str]] = None,  # (tab_id, tab_title)
        active_tab: str = "",
        **kwargs
    ):
        """Initialize the tab panel.
        
        Args:
            tabs: List of (tab_id, tab_title) tuples
            active_tab: ID of the initially active tab
        """
        super().__init__(**kwargs)
        self.tabs = tabs or []
        self.active_tab = active_tab or (self.tabs[0][0] if self.tabs else "")
        self.tab_contents = {}
    
    def compose(self) -> ComposeResult:
        """Compose the tab panel layout."""
        # Tab header
        with Horizontal(classes="tab-header"):
            for tab_id, tab_title in self.tabs:
                classes = "tab-button"
                if tab_id == self.active_tab:
                    classes += " active"
                yield Static(f"[{tab_title}]", classes=classes, id=f"tab-{tab_id}")
        
        # Tab content area
        yield Container(classes="tab-content", id="tab-content")
    
    def add_tab(self, tab_id: str, tab_title: str, content: Widget = None) -> None:
        """Add a new tab."""
        self.tabs.append((tab_id, tab_title))
        if content:
            self.tab_contents[tab_id] = content
    
    def set_active_tab(self, tab_id: str) -> None:
        """Set the active tab."""
        if tab_id in [tab[0] for tab in self.tabs]:
            self.active_tab = tab_id
            # Update tab button styles
            for tab_button_id, tab_title in self.tabs:
                try:
                    button = self.query_one(f"#tab-{tab_button_id}", Static)
                    if tab_button_id == tab_id:
                        button.add_class("active")
                    else:
                        button.remove_class("active")
                except:
                    pass
            
            # Update content
            self._update_tab_content()
    
    def _update_tab_content(self) -> None:
        """Update the displayed tab content."""
        content_container = self.query_one("#tab-content", Container)
        content_container.remove_children()
        
        if self.active_tab in self.tab_contents:
            content_container.mount(self.tab_contents[self.active_tab])
    
    def get_active_tab(self) -> str:
        """Get the currently active tab ID."""
        return self.active_tab