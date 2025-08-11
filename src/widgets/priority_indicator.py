"""Priority indicator widget with visual symbols and colors."""

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static
from typing import Optional

try:
    from ..models.enums import TaskPriority
    from ..terminal_utils import get_terminal_ascii_chars
except ImportError:
    from models.enums import TaskPriority
    from terminal_utils import get_terminal_ascii_chars


class PriorityIndicator(Widget):
    """Widget that displays priority with appropriate symbol and color."""
    
    DEFAULT_CSS = """
    PriorityIndicator {
        width: auto;
        height: 1;
    }
    
    .priority-low {
        color: #9aa0b0;
    }
    
    .priority-medium {
        color: #ffc107;
    }
    
    .priority-high {
        color: #ff9800;
    }
    
    .priority-critical {
        color: #f44336;
        text-style: bold;
    }
    
    .priority-symbol {
        text-style: bold;
    }
    """
    
    def __init__(
        self,
        priority: TaskPriority,
        show_text: bool = True,
        show_multiplier: bool = False,
        **kwargs
    ):
        """Initialize the priority indicator.
        
        Args:
            priority: The task priority to display
            show_text: Whether to show the priority text
            show_multiplier: Whether to show the XP multiplier
        """
        super().__init__(**kwargs)
        self.priority = priority
        self.show_text = show_text
        self.show_multiplier = show_multiplier
        self.ascii_chars = get_terminal_ascii_chars()
    
    def compose(self) -> ComposeResult:
        """Compose the priority indicator."""
        display_text = self._get_display_text()
        css_class = self._get_css_class()
        
        yield Static(display_text, classes=f"priority-symbol {css_class}")
    
    def _get_display_text(self) -> str:
        """Get the display text for the priority."""
        # Priority symbols
        symbols = {
            TaskPriority.LOW: self.ascii_chars.get('circle', '●'),
            TaskPriority.MEDIUM: self.ascii_chars.get('diamond', '◆'),
            TaskPriority.HIGH: self.ascii_chars.get('triangle', '▲'),
            TaskPriority.CRITICAL: self.ascii_chars.get('star', '★')
        }
        
        # XP multipliers
        multipliers = {
            TaskPriority.LOW: 0.8,
            TaskPriority.MEDIUM: 1.0,
            TaskPriority.HIGH: 1.3,
            TaskPriority.CRITICAL: 1.6
        }
        
        symbol = symbols.get(self.priority, '◆')
        text_parts = [symbol]
        
        if self.show_text:
            text_parts.append(self.priority.value)
        
        if self.show_multiplier:
            multiplier = multipliers.get(self.priority, 1.0)
            text_parts.append(f"({multiplier:.1f}x)")
        
        return " ".join(text_parts)
    
    def _get_css_class(self) -> str:
        """Get the CSS class for the priority."""
        return f"priority-{self.priority.value.lower()}"
    
    def update_priority(self, priority: TaskPriority) -> None:
        """Update the displayed priority."""
        self.priority = priority
        
        # Update the static widget
        static_widget = self.query_one(Static)
        if static_widget:
            display_text = self._get_display_text()
            css_class = self._get_css_class()
            
            static_widget.update(display_text)
            # Remove old priority classes
            for p in TaskPriority:
                static_widget.remove_class(f"priority-{p.value.lower()}")
            # Add new priority class
            static_widget.add_class(css_class)


class DifficultyIndicator(Widget):
    """Widget that displays difficulty with appropriate color and XP value."""
    
    DEFAULT_CSS = """
    DifficultyIndicator {
        width: auto;
        height: 1;
    }
    
    .difficulty-easy {
        color: #4caf50;
    }
    
    .difficulty-medium {
        color: #ffc107;
    }
    
    .difficulty-hard {
        color: #f44336;
        text-style: bold;
    }
    
    .difficulty-symbol {
        text-style: bold;
    }
    """
    
    def __init__(
        self,
        difficulty,  # TaskDifficulty enum
        show_xp: bool = True,
        **kwargs
    ):
        """Initialize the difficulty indicator.
        
        Args:
            difficulty: The task difficulty to display
            show_xp: Whether to show the XP value
        """
        super().__init__(**kwargs)
        self.difficulty = difficulty
        self.show_xp = show_xp
    
    def compose(self) -> ComposeResult:
        """Compose the difficulty indicator."""
        display_text = self._get_display_text()
        css_class = self._get_css_class()
        
        yield Static(display_text, classes=f"difficulty-symbol {css_class}")
    
    def _get_display_text(self) -> str:
        """Get the display text for the difficulty."""
        text_parts = [self.difficulty.display_name]
        
        if self.show_xp:
            text_parts.append(f"({self.difficulty.xp_value} XP)")
        
        return " ".join(text_parts)
    
    def _get_css_class(self) -> str:
        """Get the CSS class for the difficulty."""
        return f"difficulty-{self.difficulty.display_name.lower()}"
    
    def update_difficulty(self, difficulty) -> None:
        """Update the displayed difficulty."""
        self.difficulty = difficulty
        
        # Update the static widget
        static_widget = self.query_one(Static)
        if static_widget:
            display_text = self._get_display_text()
            css_class = self._get_css_class()
            
            static_widget.update(display_text)
            # Remove old difficulty classes
            static_widget.remove_class("difficulty-easy")
            static_widget.remove_class("difficulty-medium")
            static_widget.remove_class("difficulty-hard")
            # Add new difficulty class
            static_widget.add_class(css_class)


class XPCalculatorWidget(Widget):
    """Widget that shows detailed XP calculation breakdown."""
    
    DEFAULT_CSS = """
    XPCalculatorWidget {
        background: #181817;
        border: solid #ffc107;
        padding: 1;
        margin: 1 0;
        height: auto;
    }
    
    .xp-total {
        color: #ffc107;
        text-style: bold;
        text-align: center;
    }
    
    .xp-breakdown {
        color: #9aa0b0;
        text-align: center;
        margin: 1 0 0 0;
    }
    
    .xp-formula {
        color: #e0e0e0;
        text-align: center;
        margin: 1 0 0 0;
    }
    """
    
    def __init__(
        self,
        difficulty=None,
        priority=None,
        **kwargs
    ):
        """Initialize the XP calculator widget.
        
        Args:
            difficulty: Task difficulty enum
            priority: Task priority enum
        """
        super().__init__(**kwargs)
        self.difficulty = difficulty
        self.priority = priority
    
    def compose(self) -> ComposeResult:
        """Compose the XP calculator widget."""
        yield Static("", id="xp-total", classes="xp-total")
        yield Static("", id="xp-breakdown", classes="xp-breakdown")
        yield Static("", id="xp-formula", classes="xp-formula")
        
        # Initial calculation
        self._update_calculation()
    
    def _update_calculation(self) -> None:
        """Update the XP calculation display."""
        if not self.difficulty or not self.priority:
            self._show_placeholder()
            return
        
        try:
            # Calculate XP
            base_xp = self.difficulty.xp_value
            
            priority_multipliers = {
                TaskPriority.LOW: 0.8,
                TaskPriority.MEDIUM: 1.0,
                TaskPriority.HIGH: 1.3,
                TaskPriority.CRITICAL: 1.6
            }
            
            multiplier = priority_multipliers.get(self.priority, 1.0)
            total_xp = int(base_xp * multiplier)
            
            # Priority symbols
            priority_symbols = {
                TaskPriority.LOW: "●",
                TaskPriority.MEDIUM: "◆",
                TaskPriority.HIGH: "▲",
                TaskPriority.CRITICAL: "★"
            }
            
            symbol = priority_symbols.get(self.priority, "◆")
            
            # Update displays
            total_widget = self.query_one("#xp-total", Static)
            total_widget.update(f"🏆 Total XP Reward: {total_xp} XP")
            
            breakdown_widget = self.query_one("#xp-breakdown", Static)
            breakdown_widget.update(
                f"{self.difficulty.display_name} ({base_xp} XP) × "
                f"{symbol} {self.priority.value} ({multiplier:.1f}x)"
            )
            
            formula_widget = self.query_one("#xp-formula", Static)
            formula_widget.update(f"Formula: {base_xp} × {multiplier:.1f} = {total_xp} XP")
            
        except Exception as e:
            self._show_error()
    
    def _show_placeholder(self) -> None:
        """Show placeholder text when difficulty or priority is not set."""
        try:
            total_widget = self.query_one("#xp-total", Static)
            total_widget.update("🏆 Select difficulty and priority to calculate XP")
            
            breakdown_widget = self.query_one("#xp-breakdown", Static)
            breakdown_widget.update("XP = Base Difficulty × Priority Multiplier")
            
            formula_widget = self.query_one("#xp-formula", Static)
            formula_widget.update("Easy: 15 XP | Medium: 30 XP | Hard: 50 XP")
        except:
            pass
    
    def _show_error(self) -> None:
        """Show error message when calculation fails."""
        try:
            total_widget = self.query_one("#xp-total", Static)
            total_widget.update("❌ Error calculating XP")
            
            breakdown_widget = self.query_one("#xp-breakdown", Static)
            breakdown_widget.update("Unable to calculate XP breakdown")
            
            formula_widget = self.query_one("#xp-formula", Static)
            formula_widget.update("")
        except:
            pass
    
    def update_values(self, difficulty=None, priority=None) -> None:
        """Update the difficulty and priority values."""
        if difficulty is not None:
            self.difficulty = difficulty
        if priority is not None:
            self.priority = priority
        
        self._update_calculation()
    
    def get_calculated_xp(self) -> int:
        """Get the currently calculated XP value."""
        if not self.difficulty or not self.priority:
            return 0
        
        base_xp = self.difficulty.xp_value
        priority_multipliers = {
            TaskPriority.LOW: 0.8,
            TaskPriority.MEDIUM: 1.0,
            TaskPriority.HIGH: 1.3,
            TaskPriority.CRITICAL: 1.6
        }
        
        multiplier = priority_multipliers.get(self.priority, 1.0)
        return int(base_xp * multiplier)