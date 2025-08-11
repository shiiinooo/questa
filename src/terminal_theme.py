"""Terminal theme system for QUESTA application."""

from dataclasses import dataclass
from typing import Dict, Any
from pathlib import Path


@dataclass
class TerminalTheme:
    """Terminal theme configuration with colors, fonts, and ASCII characters."""
    
    colors: Dict[str, str]
    fonts: Dict[str, str]
    ascii_chars: Dict[str, str]
    spacing: Dict[str, int]
    
    @classmethod
    def default_theme(cls) -> 'TerminalTheme':
        """Create the default terminal theme."""
        return cls(
            colors={
                # Background colors
                'background': '#0a1543',      # Dark blue background
                'surface': '#181817',         # Slightly lighter surface
                'surface_light': '#1e1e1e',   # Light surface variant
                
                # Primary colors
                'primary': '#1b45d7',         # Bright blue for headers/accents
                'secondary': '#19327f',       # Medium blue for highlights
                'accent': '#1b45d7',          # Accent color (same as primary)
                
                # Text colors
                'text': '#e0e0e0',           # Light gray text
                'text_muted': '#9aa0b0',     # Muted text
                'text_bright': '#ffffff',     # Bright white text
                
                # Status colors
                'accent_yellow': '#ffc107',   # Yellow for XP/rewards
                'accent_green': '#4caf50',    # Green for completed items
                'accent_red': '#f44336',      # Red for high priority/errors
                'accent_orange': '#ff9800',   # Orange for warnings
                
                # Border and UI elements
                'border': '#3a3a3a',         # Border color
                'border_bright': '#1b45d7',  # Bright border for focus
                'selection': '#19327f',      # Selection background
                'hover': '#19327f',          # Hover background
            },
            fonts={
                'primary': 'monospace',       # Primary monospace font
                'fallback': 'Courier New, Monaco, Consolas, monospace',
                'logo': 'monospace',          # Font for ASCII logo
            },
            ascii_chars={
                # Box drawing characters
                'box_horizontal': '─',
                'box_vertical': '│',
                'box_top_left': '┌',
                'box_top_right': '┐',
                'box_bottom_left': '└',
                'box_bottom_right': '┘',
                'box_cross': '┼',
                'box_t_down': '┬',
                'box_t_up': '┴',
                'box_t_right': '├',
                'box_t_left': '┤',
                
                # Double line box characters
                'box_double_horizontal': '═',
                'box_double_vertical': '║',
                'box_double_top_left': '╔',
                'box_double_top_right': '╗',
                'box_double_bottom_left': '╚',
                'box_double_bottom_right': '╝',
                
                # Progress and indicators
                'progress_full': '█',
                'progress_partial': '▓',
                'progress_empty': '░',
                'bullet': '•',
                'arrow_right': '→',
                'arrow_left': '←',
                'arrow_up': '↑',
                'arrow_down': '↓',
                
                # Special characters
                'star': '★',
                'diamond': '◆',
                'circle': '●',
                'square': '■',
                'triangle': '▲',
            },
            spacing={
                'panel_padding': 1,
                'content_margin': 1,
                'header_height': 3,
                'footer_height': 2,
                'sidebar_width': 25,
                'min_sidebar_width': 30,
            }
        )


class ASCIIArtGenerator:
    """Utility class for generating ASCII art and terminal graphics."""
    
    def __init__(self, theme: TerminalTheme):
        self.theme = theme
    
    def generate_questa_logo(self) -> str:
        """Generate the QUESTA ASCII art logo in block/pixelated style."""
        return """
██████╗ ██╗   ██╗███████╗███████╗████████╗ █████╗ 
██╔═══██╗██║   ██║██╔════╝██╔════╝╚══██╔══╝██╔══██╗
██║   ██║██║   ██║█████╗  ███████╗   ██║   ███████║
██║▄▄ ██║██║   ██║██╔══╝  ╚════██║   ██║   ██╔══██║
╚██████╔╝╚██████╔╝███████╗███████║   ██║   ██║  ██║
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝
"""
    
    def generate_small_logo(self) -> str:
        """Generate a smaller QUESTA logo for headers."""
        return """
██████╗ ██╗   ██╗███████╗███████╗████████╗ █████╗ 
██╔═══██╗██║   ██║██╔════╝██╔════╝╚══██╔══╝██╔══██╗
██║▄▄ ██║██║   ██║█████╗  ███████╗   ██║   ███████║
╚██████╔╝╚██████╔╝███████╗███████║   ██║   ██║  ██║
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝
"""
    
    def create_border_box(self, width: int, height: int, title: str = "", double_line: bool = False) -> str:
        """Create a bordered box with optional title."""
        chars = self.theme.ascii_chars
        
        if double_line:
            h_char = chars['box_double_horizontal']
            v_char = chars['box_double_vertical']
            tl_char = chars['box_double_top_left']
            tr_char = chars['box_double_top_right']
            bl_char = chars['box_double_bottom_left']
            br_char = chars['box_double_bottom_right']
        else:
            h_char = chars['box_horizontal']
            v_char = chars['box_vertical']
            tl_char = chars['box_top_left']
            tr_char = chars['box_top_right']
            bl_char = chars['box_bottom_left']
            br_char = chars['box_bottom_right']
        
        # Create top border
        if title:
            title_len = len(title)
            if title_len + 4 < width:  # 4 for spaces and brackets
                padding = (width - title_len - 4) // 2
                top_line = tl_char + h_char * padding + f" {title} " + h_char * (width - padding - title_len - 3) + tr_char
            else:
                top_line = tl_char + h_char * (width - 2) + tr_char
        else:
            top_line = tl_char + h_char * (width - 2) + tr_char
        
        # Create middle lines
        middle_lines = [v_char + " " * (width - 2) + v_char for _ in range(height - 2)]
        
        # Create bottom border
        bottom_line = bl_char + h_char * (width - 2) + br_char
        
        return "\n".join([top_line] + middle_lines + [bottom_line])
    
    def create_progress_bar(self, progress: float, width: int = 20, show_percentage: bool = True) -> str:
        """Create a terminal-style progress bar."""
        chars = self.theme.ascii_chars
        filled_width = int(progress * width)
        
        bar = (chars['progress_full'] * filled_width + 
               chars['progress_empty'] * (width - filled_width))
        
        if show_percentage:
            percentage = f"{int(progress * 100):3d}%"
            return f"[{bar}] {percentage}"
        else:
            return f"[{bar}]"
    
    def create_separator(self, width: int, char: str = None) -> str:
        """Create a horizontal separator line."""
        if char is None:
            char = self.theme.ascii_chars['box_horizontal']
        return char * width
    
    def create_bullet_list(self, items: list, bullet_char: str = None) -> str:
        """Create a bulleted list with terminal characters."""
        if bullet_char is None:
            bullet_char = self.theme.ascii_chars['bullet']
        
        return "\n".join([f"{bullet_char} {item}" for item in items])


class TerminalStyleGenerator:
    """Generate CSS styles for terminal theme."""
    
    def __init__(self, theme: TerminalTheme):
        self.theme = theme
    
    def generate_css(self) -> str:
        """Generate complete CSS for terminal theme."""
        colors = self.theme.colors
        fonts = self.theme.fonts
        spacing = self.theme.spacing
        
        return f"""
/* QUESTA Terminal Theme - Complete Override */

/* Base Application Styling */
App {{
    background: {colors['background']};
    color: {colors['text']};
}}

Screen {{
    background: {colors['background']};
    color: {colors['text']};
}}

/* Typography - Note: Textual doesn't support font-family in CSS */

/* Headers and Navigation */
.terminal-header {{
    background: {colors['background']};
    color: {colors['primary']};
    height: {spacing['header_height']};
    dock: top;
    padding: 0 2;
    border-bottom: solid {colors['border']};
}}

.terminal-footer {{
    background: {colors['background']};
    color: {colors['text_muted']};
    height: {spacing['footer_height']};
    dock: bottom;
    padding: 0 2;
    border-top: solid {colors['border']};
}}

.screen-title {{
    color: {colors['primary']};
    text-style: bold;
}}

.user-context {{
    color: {colors['text_muted']};
    text-align: right;
}}

.navigation-commands {{
    color: {colors['text_muted']};
}}

/* Panels and Containers */
.terminal-panel {{
    background: {colors['surface']};
    border: solid {colors['border']};
    padding: {spacing['panel_padding']};
    margin: {spacing['content_margin']};
}}

.terminal-panel-header {{
    background: {colors['background']};
    color: {colors['primary']};
    text-style: bold;
    padding: 0 1;
    dock: top;
    height: 1;
    border-bottom: solid {colors['border']};
}}

.terminal-panel-content {{
    padding: 1;
    height: 100%;
}}

.focused-panel {{
    border: solid {colors['border_bright']};
}}

/* Layout */
.terminal-content {{
    layout: horizontal;
}}

.terminal-sidebar {{
    width: {spacing['sidebar_width']}%;
    min-width: {spacing['min_sidebar_width']};
    border-right: solid {colors['border']};
    background: {colors['surface']};
}}

.terminal-main {{
    background: {colors['surface']};
}}

/* Text Styles */
.terminal-text {{
    color: {colors['text']};
}}

.terminal-text-muted {{
    color: {colors['text_muted']};
}}

.terminal-text-bright {{
    color: {colors['text_bright']};
}}

.terminal-title {{
    color: {colors['primary']};
    text-style: bold;
    text-align: center;
}}

.terminal-subtitle {{
    color: {colors['text_muted']};
    text-align: center;
}}

.terminal-highlight {{
    color: {colors['primary']};
    text-style: bold;
}}

/* Form Elements */
Input {{
    background: {colors['background']};
    color: {colors['text']};
    border: solid {colors['border']};
}}

Input:focus {{
    border: solid {colors['border_bright']};
}}

Select {{
    background: {colors['background']};
    color: {colors['text']};
    border: solid {colors['border']};
}}

Select:focus {{
    border: solid {colors['border_bright']};
}}

TextArea {{
    background: {colors['background']};
    color: {colors['text']};
    border: solid {colors['border']};
}}

TextArea:focus {{
    border: solid {colors['border_bright']};
}}

.form-label {{
    color: {colors['primary']};
    text-style: bold;
    margin: 0 0 1 0;
}}

.form-error {{
    color: {colors['accent_red']};
    text-style: italic;
}}

.form-help {{
    color: {colors['text_muted']};
    text-style: italic;
}}

/* Buttons */
Button {{
    background: {colors['primary']};
    color: {colors['text_bright']};
    border: solid {colors['primary']};
    margin: 1;
}}

Button:hover {{
    background: {colors['secondary']};
}}

Button:focus {{
    border: solid {colors['text_bright']};
}}

/* Progress Bars */
ProgressBar {{
    background: {colors['surface_light']};
}}

ProgressBar > .bar--bar {{
    color: {colors['background']};
}}

ProgressBar > .bar--complete {{
    background: {colors['primary']};
}}

/* Task Status Colors */
.status-pending {{
    color: {colors['text_muted']};
}}

.status-active {{
    color: {colors['primary']};
}}

.status-completed {{
    color: {colors['accent_green']};
}}

.status-blocked {{
    color: {colors['accent_red']};
}}

/* Priority Colors */
.priority-low {{
    color: {colors['text_muted']};
}}

.priority-medium {{
    color: {colors['accent_yellow']};
}}

.priority-high {{
    color: {colors['accent_orange']};
}}

.priority-critical {{
    color: {colors['accent_red']};
}}

/* Difficulty Colors */
.difficulty-easy {{
    color: {colors['accent_green']};
}}

.difficulty-medium {{
    color: {colors['accent_yellow']};
}}

.difficulty-hard {{
    color: {colors['accent_red']};
}}

/* XP and Rewards */
.xp-value {{
    color: {colors['accent_yellow']};
    text-style: bold;
}}

.level-info {{
    color: {colors['primary']};
    text-style: bold;
}}

.streak-info {{
    color: {colors['accent_yellow']};
}}

/* Selection and Hover States */
.selected {{
    background: {colors['selection']};
    color: {colors['text_bright']};
}}

.hover {{
    background: {colors['hover']};
}}

/* Task List Items */
.task-item {{
    padding: 1;
    border-bottom: solid {colors['border']};
}}

.task-item:hover {{
    background: {colors['hover']};
}}

.task-title {{
    color: {colors['text']};
    text-style: bold;
}}

.task-meta {{
    color: {colors['text_muted']};
}}

/* Modals and Dialogs */
.terminal-modal {{
    background: {colors['background']};
    border: thick {colors['border_bright']};
    text-align: center;
    padding: 2;
}}

.modal-title {{
    color: {colors['primary']};
    text-style: bold;
}}

.modal-message {{
    color: {colors['text']};
}}

.modal-buttons {{
    layout: horizontal;
    margin: 1 0 0 0;
}}

/* Messages and Notifications */
.success-message {{
    color: {colors['accent_green']};
    background: {colors['surface']};
    border: solid {colors['accent_green']};
}}

.error-message {{
    color: {colors['accent_red']};
    background: {colors['surface']};
    border: solid {colors['accent_red']};
}}

.warning-message {{
    color: {colors['accent_orange']};
    background: {colors['surface']};
    border: solid {colors['accent_orange']};
}}

.info-message {{
    color: {colors['primary']};
    background: {colors['surface']};
    border: solid {colors['primary']};
}}

/* Welcome Screen Specific */
#welcome-container {{
    height: 100%;
    align: center middle;
    text-align: center;
}}

#logo {{
    color: {colors['primary']};
    text-align: center;
}}

.center {{
    text-align: center;
    color: {colors['secondary']};
}}

/* ASCII Art and Special Elements */
.ascii-art {{
    color: {colors['primary']};
    text-style: bold;
}}

.ascii-border {{
    color: {colors['border']};
}}

.progress-bar-terminal {{
    color: {colors['accent_yellow']};
}}
"""


# Global theme instance
_terminal_theme = TerminalTheme.default_theme()
_ascii_generator = ASCIIArtGenerator(_terminal_theme)
_style_generator = TerminalStyleGenerator(_terminal_theme)


def get_terminal_theme() -> TerminalTheme:
    """Get the current terminal theme."""
    return _terminal_theme


def get_ascii_generator() -> ASCIIArtGenerator:
    """Get the ASCII art generator."""
    return _ascii_generator


def get_style_generator() -> TerminalStyleGenerator:
    """Get the terminal style generator."""
    return _style_generator


def get_terminal_css() -> str:
    """Get the complete terminal CSS."""
    return _style_generator.generate_css()