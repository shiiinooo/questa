"""Character stats screen with achievements and progression display."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid, ScrollableContainer
from textual.widgets import Static, Label, ProgressBar, Button
from textual.screen import Screen
from textual.reactive import reactive

from ..models.player import PlayerData
from ..models.achievement import get_achievement_system, AchievementCategory, Achievement
from ..data.data_manager import DataManager
from ..terminal_theme import get_terminal_theme, get_ascii_generator
from ..widgets.terminal_header import TerminalHeader
from ..widgets.terminal_footer import TerminalFooter
from ..widgets.terminal_panel import TerminalPanel


class AchievementBadge(Static):
    """Individual achievement badge with icon, title, and description."""
    
    DEFAULT_CSS = """
    AchievementBadge {
        height: 4;
        width: 1fr;
        border: solid #3a3a3a;
        padding: 1;
        margin: 0 1 1 0;
    }
    
    AchievementBadge.unlocked {
        background: #1e1e1e;
        border: solid #1b45d7;
    }
    
    AchievementBadge.locked {
        background: #181817;
        border: solid #3a3a3a;
        opacity: 0.6;
    }
    
    .badge-icon {
        color: #ffc107;
        text-style: bold;
        text-align: center;
        height: 1;
    }
    
    .badge-title {
        color: #1b45d7;
        text-style: bold;
        text-align: center;
        height: 1;
    }
    
    .badge-description {
        color: #9aa0b0;
        text-align: center;
        height: 1;
    }
    
    .badge-progress {
        color: #ffc107;
        text-align: center;
        height: 1;
    }
    
    .locked .badge-icon {
        color: #9aa0b0;
    }
    
    .locked .badge-title {
        color: #9aa0b0;
    }
    """
    
    def __init__(self, achievement: Achievement, is_unlocked: bool = False, progress: float = 0.0, **kwargs):
        super().__init__(**kwargs)
        self.achievement = achievement
        self.is_unlocked = is_unlocked
        self.progress = progress
        
        if is_unlocked:
            self.add_class("unlocked")
        else:
            self.add_class("locked")
    
    def compose(self) -> ComposeResult:
        """Compose the achievement badge."""
        # Icon
        yield Static(self.achievement.badge_icon, classes="badge-icon")
        
        # Title
        yield Static(self.achievement.name, classes="badge-title")
        
        # Description or progress
        if self.is_unlocked:
            yield Static(self.achievement.description, classes="badge-description")
        else:
            if self.progress > 0:
                progress_text = f"{int(self.progress * 100)}%"
                yield Static(progress_text, classes="badge-progress")
            else:
                yield Static("Locked", classes="badge-description")


class AchievementGrid(TerminalPanel):
    """Grid displaying achievements with filtering by category."""
    
    DEFAULT_CSS = """
    AchievementGrid {
        height: 1fr;
        border: solid #3a3a3a;
        background: #181817;
    }
    
    .achievement-filters {
        height: 3;
        dock: top;
        border-bottom: solid #3a3a3a;
        background: #0a1543;
        layout: horizontal;
        padding: 1;
    }
    
    .filter-button {
        margin: 0 1 0 0;
        min-width: 12;
        height: 1;
    }
    
    .filter-button.active {
        background: #1b45d7;
        color: #ffffff;
    }
    
    .achievements-scroll {
        height: 1fr;
        padding: 1;
    }
    
    .achievements-container {
        layout: grid;
        grid-size: 3;
        grid-gutter: 1;
        height: auto;
    }
    """
    
    current_filter = reactive(AchievementCategory.PROGRESSION)
    
    def __init__(self, player: PlayerData, **kwargs):
        super().__init__(title="Achievements", **kwargs)
        self.player = player
        self.achievement_system = get_achievement_system()
        self.unlocked_achievements = set(
            unlocked.achievement_id for unlocked in self.achievement_system.unlocked.values()
        )
    
    def compose(self) -> ComposeResult:
        """Compose the achievement grid."""
        with Container():
            # Filter buttons
            with Container(classes="achievement-filters"):
                for category in AchievementCategory:
                    button = Button(
                        category.display_name,
                        id=f"filter_{category.value}",
                        classes="filter-button"
                    )
                    if category == self.current_filter:
                        button.add_class("active")
                    yield button
            
            # Scrollable achievements grid
            with ScrollableContainer(classes="achievements-scroll"):
                with Container(classes="achievements-container", id="achievements_container"):
                    yield from self._create_achievement_badges()
    
    def _create_achievement_badges(self) -> ComposeResult:
        """Create achievement badges for the current filter."""
        achievements = self.achievement_system.get_achievements_by_category(self.current_filter)
        
        for achievement in achievements:
            is_unlocked = achievement.id in self.unlocked_achievements
            progress = 0.0
            
            if not is_unlocked:
                progress = self.achievement_system.get_progress_for_achievement(
                    achievement.id, self.player
                ) or 0.0
            
            yield AchievementBadge(achievement, is_unlocked, progress)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle filter button presses."""
        if event.button.id and event.button.id.startswith("filter_"):
            category_value = event.button.id.replace("filter_", "")
            try:
                new_filter = AchievementCategory(category_value)
                self.current_filter = new_filter
                self._update_filter_buttons()
                self._refresh_achievements()
            except ValueError:
                pass
    
    def _update_filter_buttons(self) -> None:
        """Update the active state of filter buttons."""
        for category in AchievementCategory:
            button = self.query_one(f"#filter_{category.value}", Button)
            if category == self.current_filter:
                button.add_class("active")
            else:
                button.remove_class("active")
    
    def _refresh_achievements(self) -> None:
        """Refresh the achievements display."""
        container = self.query_one("#achievements_container", Container)
        container.remove_children()
        
        achievements = self.achievement_system.get_achievements_by_category(self.current_filter)
        
        for achievement in achievements:
            is_unlocked = achievement.id in self.unlocked_achievements
            progress = 0.0
            
            if not is_unlocked:
                progress = self.achievement_system.get_progress_for_achievement(
                    achievement.id, self.player
                ) or 0.0
            
            container.mount(AchievementBadge(achievement, is_unlocked, progress))


class StatisticsPanel(TerminalPanel):
    """Panel displaying player statistics and metrics."""
    
    DEFAULT_CSS = """
    StatisticsPanel {
        height: 1fr;
        border: solid #3a3a3a;
        background: #181817;
        margin: 1 0 0 0;
    }
    
    .stats-grid {
        layout: grid;
        grid-size: 2;
        grid-gutter: 1;
        padding: 1;
        height: auto;
    }
    
    .stat-item {
        height: 3;
        border: solid #3a3a3a;
        padding: 1;
        background: #0a1543;
    }
    
    .stat-label {
        color: #1b45d7;
        text-style: bold;
        height: 1;
    }
    
    .stat-value {
        color: #ffc107;
        text-style: bold;
        text-align: center;
        height: 1;
    }
    
    .stat-detail {
        color: #9aa0b0;
        text-align: center;
        height: 1;
    }
    
    .difficulty-breakdown {
        layout: horizontal;
        height: 1;
        margin: 1 0 0 0;
    }
    
    .difficulty-stat {
        width: 1fr;
        text-align: center;
        margin: 0 1;
    }
    
    .difficulty-easy {
        color: #4caf50;
    }
    
    .difficulty-medium {
        color: #ffc107;
    }
    
    .difficulty-hard {
        color: #f44336;
    }
    """
    
    def __init__(self, player: PlayerData, **kwargs):
        super().__init__(title="Statistics", **kwargs)
        self.player = player
    
    def compose(self) -> ComposeResult:
        """Compose the statistics panel."""
        with Container():
            with Container(classes="stats-grid"):
                # Total XP
                with Container(classes="stat-item"):
                    yield Static("Total XP", classes="stat-label")
                    yield Static(f"{self.player.total_xp:,}", classes="stat-value")
                    yield Static("Experience Points", classes="stat-detail")
                
                # Tasks Completed
                with Container(classes="stat-item"):
                    yield Static("Tasks Completed", classes="stat-label")
                    yield Static(str(self.player.tasks_completed), classes="stat-value")
                    yield Static("Total Quests", classes="stat-detail")
                
                # Current Streak
                with Container(classes="stat-item"):
                    yield Static("Current Streak", classes="stat-label")
                    yield Static(str(self.player.current_streak), classes="stat-value")
                    yield Static("Consecutive Tasks", classes="stat-detail")
                
                # Current Level
                with Container(classes="stat-item"):
                    yield Static("Current Level", classes="stat-label")
                    yield Static(str(self.player.level), classes="stat-value")
                    yield Static(f"{self.player.xp_to_next_level} XP to next", classes="stat-detail")
            
            # Difficulty breakdown
            yield Static("Task Completion by Difficulty", classes="stat-label")
            with Container(classes="difficulty-breakdown"):
                with Container(classes="difficulty-stat"):
                    yield Static("Easy", classes="difficulty-easy")
                    yield Static(str(self.player.easy_tasks_completed), classes="difficulty-easy")
                
                with Container(classes="difficulty-stat"):
                    yield Static("Medium", classes="difficulty-medium")
                    yield Static(str(self.player.medium_tasks_completed), classes="difficulty-medium")
                
                with Container(classes="difficulty-stat"):
                    yield Static("Hard", classes="difficulty-hard")
                    yield Static(str(self.player.hard_tasks_completed), classes="difficulty-hard")


class LevelProgressPanel(TerminalPanel):
    """Panel displaying current level progress with terminal-style XP bar."""
    
    DEFAULT_CSS = """
    LevelProgressPanel {
        height: 8;
        border: solid #3a3a3a;
        background: #181817;
    }
    
    .level-title {
        color: #1b45d7;
        text-style: bold;
        text-align: center;
        margin: 0 0 1 0;
    }
    
    .level-info {
        color: #e0e0e0;
        text-align: center;
        margin: 0 0 1 0;
    }
    
    .xp-progress {
        margin: 1 2;
    }
    
    .xp-numbers {
        color: #ffc107;
        text-style: bold;
        text-align: center;
        margin: 1 0 0 0;
    }
    
    .progress-bar-container {
        height: 1;
        margin: 0 2;
    }
    """
    
    def __init__(self, player: PlayerData, **kwargs):
        super().__init__(title="Level Progress", **kwargs)
        self.player = player
        self.ascii_gen = get_ascii_generator()
    
    def compose(self) -> ComposeResult:
        """Compose the level progress panel."""
        with Container():
            # Level title and current level
            level_title = self._get_level_title()
            yield Static(f"Level {self.player.level} - {level_title}", classes="level-title")
            
            # XP progress bar
            with Container(classes="progress-bar-container"):
                progress_bar = ProgressBar(
                    total=100,
                    show_bar=True,
                    show_percentage=False,
                    show_eta=False
                )
                progress_bar.advance(int(self.player.level_progress * 100))
                yield progress_bar
            
            # XP numbers
            current_level_xp = self.player.current_level_xp
            xp_needed = self.player.xp_to_next_level
            total_for_next = self.player.xp_for_next_level - self.player.xp_for_current_level
            
            xp_text = f"{current_level_xp}/{total_for_next} XP ({xp_needed} needed)"
            yield Static(xp_text, classes="xp-numbers")
            
            # Progress percentage
            percentage = int(self.player.level_progress * 100)
            yield Static(f"Progress: {percentage}%", classes="level-info")
    
    def _get_level_title(self) -> str:
        """Get the title for the current level."""
        level = self.player.level
        
        if level >= 20:
            return "Code Master"
        elif level >= 15:
            return "Senior Developer"
        elif level >= 10:
            return "Code Journeyman"
        elif level >= 5:
            return "Code Apprentice"
        elif level >= 3:
            return "Junior Developer"
        else:
            return "Novice Coder"


class CharacterStatsScreen(Screen):
    """Character stats screen showing level progression, achievements, and statistics."""
    
    BINDINGS = [
        ("escape", "back", "Back"),
        ("q", "quit", "Quit"),
        ("h", "help", "Help"),
    ]
    
    DEFAULT_CSS = """
    CharacterStatsScreen {
        background: #0a1543;
        color: #e0e0e0;
    }
    
    .stats-container {
        layout: vertical;
        height: 100%;
    }
    
    .stats-content {
        layout: horizontal;
        height: 1fr;
    }
    
    .left-column {
        width: 30%;
        margin: 1;
    }
    
    .right-column {
        width: 70%;
        margin: 1;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_manager = DataManager()
        self.player = self.data_manager.load_player_data()
        self.achievement_system = get_achievement_system()
        self.theme = get_terminal_theme()
    
    def compose(self) -> ComposeResult:
        """Compose the character stats screen."""
        with Container(classes="stats-container"):
            # Header
            yield TerminalHeader("Character Stats")
            
            # Main content
            with Container(classes="stats-content"):
                with Container(classes="left-column"):
                    # Level progress panel
                    yield LevelProgressPanel(self.player)
                    
                    # Statistics panel
                    yield StatisticsPanel(self.player)
                
                with Container(classes="right-column"):
                    # Achievement grid
                    yield AchievementGrid(self.player)
            
            # Footer
            yield TerminalFooter()
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
    
    def action_help(self) -> None:
        """Show help information."""
        self.app.push_screen("help")