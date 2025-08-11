"""WelcomeScreen - Terminal splash screen for QUESTA application."""

from textual.app import ComposeResult
from textual.containers import Vertical, Center, Container
from textual.screen import Screen
from textual.widgets import Static, Label
from textual.binding import Binding
from textual.timer import Timer

from ..data.data_manager import DataManager
from ..models.player import PlayerData
from ..terminal_utils import get_questa_logo, create_progress_bar, format_level_display, get_level_title


class WelcomeScreen(Screen):
    """Welcome screen with terminal splash interface showing QUESTA logo and player stats."""
    
    BINDINGS = [
        Binding("enter", "continue", "Continue"),
        Binding("space", "continue", "Continue"),
        Binding("escape", "continue", "Continue"),
    ]
    
    DEFAULT_CSS = """
    WelcomeScreen {
        background: #0a1543;
        color: #e0e0e0;
    }
    
    WelcomeScreen .welcome-container {
        height: 100%;
        width: 100%;
        align: center middle;
        text-align: center;
    }
    
    WelcomeScreen .logo-container {
        height: auto;
        width: auto;
        text-align: center;
        margin-bottom: 2;
    }
    
    WelcomeScreen .questa-logo {
        color: #1b45d7;
        text-style: bold;
        text-align: center;
        margin-bottom: 3;
    }
    
    WelcomeScreen .player-info {
        text-align: center;
        margin-bottom: 2;
    }
    
    WelcomeScreen .level-display {
        color: #1b45d7;
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }
    
    WelcomeScreen .xp-progress {
        color: #ffc107;
        text-align: center;
        margin-bottom: 3;
    }
    
    WelcomeScreen .continue-prompt {
        color: #9aa0b0;
        text-align: center;
        text-style: italic;
        margin-top: 2;
    }
    
    WelcomeScreen .continue-hint {
        color: #9aa0b0;
        text-align: center;
        text-style: italic;
        margin-top: 1;
    }
    """
    
    def __init__(self, data_manager: DataManager = None, **kwargs):
        """Initialize the welcome screen.
        
        Args:
            data_manager: DataManager instance for loading player data
        """
        super().__init__(**kwargs)
        self.data_manager = data_manager or DataManager()
        self.player_data: PlayerData = None
        self.auto_continue_timer: Timer | None = None
        self._pulse_timer: Timer | None = None
    
    def compose(self) -> ComposeResult:
        """Compose the welcome screen layout."""
        # Load player data
        self.player_data = self.data_manager.load_player_data()
        
        with Center(classes="welcome-container"):
            with Vertical(classes="logo-container"):
                # Large ASCII art QUESTA logo
                yield Static(self._render_logo(), classes="questa-logo")
                
                # Player level and title display
                yield Container(
                    Static(self._render_level_display(), classes="level-display"),
                    classes="player-info"
                )
                
                # XP progress bar
                yield Container(
                    Static(self._render_xp_progress(), classes="xp-progress"),
                    classes="player-info"
                )
                
                # Continue instruction
                yield Static("Press [Enter] to continue", classes="continue-prompt")
                yield Label("", classes="continue-hint", id="continue-hint")
    
    def _render_logo(self) -> str:
        """Render the QUESTA ASCII logo."""
        return get_questa_logo("large")
    
    def _render_level_display(self) -> str:
        """Render the player level and title display."""
        if not self.player_data:
            return "Level 1 - Code Novice"
        
        level = self.player_data.level
        title = get_level_title(level)
        return format_level_display(level, title)
    
    def _render_xp_progress(self) -> str:
        """Render the XP progress bar with terminal styling."""
        if not self.player_data:
            return "XP: 0 / 100 [░░░░░░░░░░░░░░░░░░░░] 0%"
        
        current_xp = self.player_data.total_xp
        current_level_xp = self.player_data.xp_for_current_level
        next_level_xp = self.player_data.xp_for_next_level
        progress = self.player_data.level_progress
        
        # Create progress bar
        progress_bar = create_progress_bar(progress, width=20, show_percentage=False)
        percentage = int(progress * 100)
        
        # Format XP display
        xp_in_level = current_xp - current_level_xp
        xp_needed_for_level = next_level_xp - current_level_xp
        
        return f"XP: {xp_in_level} / {xp_needed_for_level} {progress_bar} {percentage}%"
    
    def on_mount(self) -> None:
        """Handle screen mount event."""
        # Start auto-continue timer (10 seconds for splash screen)
        self.auto_continue_timer = self.set_timer(10.0, self.action_continue)
        
        # Start pulsing hint animation
        self._start_pulse_animation()
    
    def _start_pulse_animation(self) -> None:
        """Start the pulsing animation for the continue hint."""
        def toggle_hint():
            try:
                hint_label = self.query_one("#continue-hint", Label)
                current_text = hint_label.renderable
                if current_text == "":
                    hint_label.update("(or wait to continue automatically)")
                else:
                    hint_label.update("")
            except Exception:
                pass  # Ignore errors if screen is being torn down
        
        # Pulse every 2 seconds
        try:
            self._pulse_timer = self.set_interval(2.0, toggle_hint)
        except Exception:
            self._pulse_timer = None
    
    def action_continue(self) -> None:
        """Continue to the main application."""
        # Cancel auto-continue timer if it exists
        if self.auto_continue_timer:
            self.auto_continue_timer.stop()
            self.auto_continue_timer = None
        
        # Dismiss this screen to continue to home
        self.dismiss()
    
    def on_key(self, event) -> None:
        """Handle any key press to continue."""
        self.action_continue()
    
    def on_unmount(self) -> None:
        """Handle screen unmount event."""
        # Clean up timers
        if self.auto_continue_timer:
            self.auto_continue_timer.stop()
            self.auto_continue_timer = None
        if self._pulse_timer:
            try:
                self._pulse_timer.stop()
            except Exception:
                pass
            self._pulse_timer = None