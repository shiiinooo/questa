"""Utility functions for terminal theme integration."""

from pathlib import Path
from typing import Optional
try:
    from .terminal_theme import get_terminal_theme, get_ascii_generator, get_terminal_css
except ImportError:
    from terminal_theme import get_terminal_theme, get_ascii_generator, get_terminal_css


def load_terminal_css() -> str:
    """Load the terminal CSS from file or generate it dynamically."""
    css_file = Path(__file__).parent / "terminal_styles.css"
    
    if css_file.exists():
        return css_file.read_text()
    else:
        # Fallback to generated CSS
        return get_terminal_css()


def get_questa_logo(size: str = "large") -> str:
    """Get the QUESTA ASCII art logo."""
    ascii_gen = get_ascii_generator()
    
    if size == "large":
        return ascii_gen.generate_questa_logo()
    elif size == "small":
        return ascii_gen.generate_small_logo()
    else:
        return ascii_gen.generate_questa_logo()


def create_terminal_border(width: int, height: int, title: str = "", double_line: bool = False) -> str:
    """Create a terminal-style border box."""
    ascii_gen = get_ascii_generator()
    return ascii_gen.create_border_box(width, height, title, double_line)


def create_progress_bar(progress: float, width: int = 20, show_percentage: bool = True) -> str:
    """Create a terminal-style progress bar."""
    ascii_gen = get_ascii_generator()
    return ascii_gen.create_progress_bar(progress, width, show_percentage)


def create_separator(width: int, char: Optional[str] = None) -> str:
    """Create a horizontal separator line."""
    ascii_gen = get_ascii_generator()
    return ascii_gen.create_separator(width, char)


def create_bullet_list(items: list, bullet_char: Optional[str] = None) -> str:
    """Create a bulleted list with terminal characters."""
    ascii_gen = get_ascii_generator()
    return ascii_gen.create_bullet_list(items, bullet_char)


def get_terminal_colors() -> dict:
    """Get the terminal color scheme."""
    theme = get_terminal_theme()
    return theme.colors


def get_terminal_ascii_chars() -> dict:
    """Get the terminal ASCII characters."""
    theme = get_terminal_theme()
    return theme.ascii_chars


def format_xp_display(xp: int) -> str:
    """Format XP value for terminal display."""
    return f"{xp} XP"


def get_level_title(level: int) -> str:
    """Get the title for a given level."""
    if level <= 2:
        return "Code Novice"
    elif level <= 4:
        return "Code Student"
    elif level <= 6:
        return "Code Apprentice"
    elif level <= 8:
        return "Code Journeyman"
    elif level <= 10:
        return "Code Expert"
    else:
        return "Code Master"


def format_level_display(level: int, title: str = None) -> str:
    """Format level and title for terminal display."""
    if title is None:
        title = get_level_title(level)
    return f"Level {level} - {title}"


def format_task_priority(priority: str) -> str:
    """Format task priority with terminal symbols."""
    ascii_chars = get_terminal_ascii_chars()
    
    priority_symbols = {
        "low": ascii_chars['circle'],
        "medium": ascii_chars['diamond'],
        "high": ascii_chars['triangle'],
        "critical": ascii_chars['star']
    }
    
    symbol = priority_symbols.get(priority.lower(), ascii_chars['circle'])
    return f"{symbol} {priority.upper()}"


def format_task_status(status: str) -> str:
    """Format task status with terminal symbols."""
    ascii_chars = get_terminal_ascii_chars()
    
    status_symbols = {
        "pending": ascii_chars['circle'],
        "active": ascii_chars['arrow_right'],
        "completed": ascii_chars['star'],
        "blocked": ascii_chars['square']
    }
    
    symbol = status_symbols.get(status.lower(), ascii_chars['circle'])
    return f"{symbol} {status.upper()}"


def format_difficulty_display(difficulty: str, xp_value: int) -> str:
    """Format difficulty with XP value for terminal display."""
    return f"{difficulty.upper()} ({xp_value} XP)"


class TerminalFormatter:
    """Helper class for consistent terminal formatting."""
    
    def __init__(self):
        self.theme = get_terminal_theme()
        self.ascii_gen = get_ascii_generator()
    
    def format_header(self, screen_name: str, user_name: str = "") -> str:
        """Format a terminal-style header."""
        title = f"QUESTA - {screen_name}"
        if user_name:
            # Calculate spacing to right-align user name
            header_width = 80  # Assume standard terminal width
            title_len = len(title)
            user_len = len(user_name)
            spacing = header_width - title_len - user_len - 2  # 2 for padding
            
            if spacing > 0:
                return f"{title}{' ' * spacing}{user_name}"
            else:
                return f"{title} | {user_name}"
        return title
    
    def format_footer_commands(self, commands: list) -> str:
        """Format footer commands in terminal style."""
        formatted_commands = []
        for cmd in commands:
            if isinstance(cmd, tuple):
                key, desc = cmd
                formatted_commands.append(f":{key} {desc}")
            else:
                formatted_commands.append(f":{cmd}")
        
        return " | ".join(formatted_commands)
    
    def format_panel_title(self, title: str, width: int = 40) -> str:
        """Format a panel title with terminal borders."""
        ascii_chars = self.theme.ascii_chars
        
        if len(title) + 4 < width:  # 4 for spaces and brackets
            padding = (width - len(title) - 4) // 2
            remaining = width - len(title) - 4 - padding
            return f"{ascii_chars['box_horizontal'] * padding} {title} {ascii_chars['box_horizontal'] * remaining}"
        else:
            return title
    
    def format_task_list_item(self, task_title: str, priority: str, status: str, xp: int) -> str:
        """Format a task list item for terminal display."""
        priority_symbol = format_task_priority(priority)
        status_symbol = format_task_status(status)
        xp_display = format_xp_display(xp)
        
        return f"{status_symbol} {task_title} [{priority_symbol}] ({xp_display})"
    
    def format_progress_with_label(self, label: str, current: int, total: int, width: int = 20) -> str:
        """Format a labeled progress bar."""
        progress = current / total if total > 0 else 0
        bar = self.ascii_gen.create_progress_bar(progress, width, False)
        percentage = int(progress * 100)
        return f"{label}: {bar} {current}/{total} ({percentage}%)"


# Global formatter instance
_terminal_formatter = TerminalFormatter()


def get_terminal_formatter() -> TerminalFormatter:
    """Get the global terminal formatter instance."""
    return _terminal_formatter