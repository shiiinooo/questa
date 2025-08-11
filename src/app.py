"""Main QUESTA application with integrated task management."""

from typing import Optional, Dict, Any
from pathlib import Path
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Header, Footer
from textual.message import Message

from .screens.welcome_screen import WelcomeScreen
from .screens.home_screen import HomeScreen
from .screens.quests_screen import QuestsScreen
from .screens.add_task_screen import AddTaskScreen
from .screens.edit_task_screen import EditTaskScreen
from .screens.character_stats_screen import CharacterStatsScreen
from .business.task_manager import TaskManager
from .data.data_manager import DataManager
from .terminal_utils import load_terminal_css


class QUESTAApp(App):
    """QUESTA - A Professional TUI Task Manager with Gamification"""

    CSS = load_terminal_css()

    def __init__(self):
        """Initialize the QUESTA application."""
        super().__init__()
        self.data_manager = DataManager()

    def on_mount(self):
        """Push the welcome screen when the app mounts."""
        self.push_screen(WelcomeScreen(self.data_manager), callback=self._on_welcome_dismissed)

    def _on_welcome_dismissed(self, result=None):
        """Handle welcome screen dismissal by showing home screen."""
        self.push_screen(HomeScreen(self.data_manager))

    def action_quit(self):
        """Global quit action"""
        self.exit()