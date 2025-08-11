"""Journal screen for activity tracking with chronological display."""

from datetime import datetime, date, timedelta
from typing import List, Optional

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Static, Button
from textual.binding import Binding

from ..widgets.terminal_header import TerminalHeader
from ..widgets.terminal_footer import TerminalFooter
from ..widgets.terminal_panel import TerminalPanel
from ..widgets.activity_timeline import ActivityTimeline
from ..models.activity import ActivityEntry, ActivityType
from ..models.task import Task
from ..models.enums import TaskDifficulty
from ..terminal_theme import get_terminal_theme, get_ascii_generator


class JournalScreen(Screen):
    """Journal screen for viewing activity timeline and progress tracking."""
    
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("q", "quit", "Quit"),
        Binding("h", "help", "Help"),
        Binding("r", "refresh", "Refresh"),
        Binding("f", "filter", "Filter"),
    ]
    
    DEFAULT_CSS = """
    JournalScreen {
        background: #0a1543;
        color: #e0e0e0;
    }
    
    .journal-container {
        height: 100%;
        layout: vertical;
    }
    
    .journal-content {
        height: 100%;
        layout: horizontal;
    }
    
    .journal-sidebar {
        width: 25%;
        min-width: 30;
        background: #181817;
        border-right: solid #3a3a3a;
    }
    
    .journal-main {
        width: 75%;
        background: #181817;
    }
    
    .stats-panel {
        height: 40%;
        margin: 0 0 1 0;
    }
    
    .filter-panel {
        height: 60%;
    }
    
    .stats-item {
        color: #e0e0e0;
        padding: 0 1;
        margin: 0 0 1 0;
    }
    
    .stats-label {
        color: #9aa0b0;
        width: 15;
    }
    
    .stats-value {
        color: #ffc107;
        text-style: bold;
    }
    
    .filter-button {
        width: 100%;
        margin: 0 0 1 0;
        text-align: left;
    }
    
    .filter-button.active {
        background: #1b45d7;
        color: #ffffff;
    }
    
    .empty-state {
        color: #9aa0b0;
        text-style: italic;
        text-align: center;
        padding: 4;
    }
    """
    
    def __init__(self, activities: List[ActivityEntry] = None, **kwargs):
        """Initialize journal screen.
        
        Args:
            activities: List of activities to display
        """
        super().__init__(**kwargs)
        self.activities = activities or []
        self.filtered_activities = self.activities.copy()
        self.current_filter = "all"
        self.theme = get_terminal_theme()
        self.ascii_gen = get_ascii_generator()
    
    def compose(self) -> ComposeResult:
        """Compose the journal screen layout."""
        with Container(classes="journal-container"):
            # Header
            yield TerminalHeader("Quest Journal", user_name="Player")
            
            # Main content area
            with Container(classes="journal-content"):
                # Sidebar with stats and filters
                with Container(classes="journal-sidebar"):
                    # Statistics panel
                    stats_panel = TerminalPanel(
                        title="Statistics",
                        scrollable=False,
                        show_border=True
                    )
                    stats_panel.add_class("stats-panel")
                    yield stats_panel
                    
                    # Filter panel
                    filter_panel = TerminalPanel(
                        title="Filters",
                        scrollable=False,
                        show_border=True
                    )
                    filter_panel.add_class("filter-panel")
                    yield filter_panel
                
                # Main timeline area
                with Container(classes="journal-main"):
                    timeline_panel = TerminalPanel(
                        title="Activity Timeline",
                        scrollable=True,
                        show_border=True
                    )
                    yield timeline_panel
            
            # Footer
            yield TerminalFooter([
                ":back - Back",
                ":refresh - Refresh",
                ":filter - Toggle Filter",
                ":help - Help",
                ":quit - Quit"
            ])
        
        # Initialize content after compose
        self.call_after_refresh(self._initialize_content)
    
    def _initialize_content(self) -> None:
        """Initialize the screen content."""
        self._populate_statistics()
        self._populate_filters()
        self._populate_timeline()
    
    def _populate_statistics(self) -> None:
        """Populate the statistics panel."""
        stats_panel = self.query(TerminalPanel)[0]  # First panel is stats
        stats_container = stats_panel.get_content_container()
        
        # Calculate statistics
        stats = self._calculate_statistics()
        
        # Create statistics display
        stats_items = [
            ("Total Activities", str(stats['total_activities'])),
            ("Quests Completed", str(stats['quests_completed'])),
            ("Total XP Earned", str(stats['total_xp'])),
            ("Level Ups", str(stats['level_ups'])),
            ("Achievements", str(stats['achievements'])),
            ("This Week", str(stats['this_week_activities'])),
            ("Today", str(stats['today_activities'])),
        ]
        
        for label, value in stats_items:
            stats_line = f"{label}: {value}"
            stats_container.mount(Static(stats_line, classes="stats-item"))
    
    def _populate_filters(self) -> None:
        """Populate the filter panel."""
        filter_panel = self.query(TerminalPanel)[1]  # Second panel is filters
        filter_container = filter_panel.get_content_container()
        
        # Filter options
        filters = [
            ("all", "All Activities"),
            ("today", "Today"),
            ("week", "This Week"),
            ("month", "This Month"),
            ("quests", "Quests Only"),
            ("achievements", "Achievements"),
            ("level_ups", "Level Ups"),
        ]
        
        for filter_id, filter_name in filters:
            button = Button(filter_name, id=f"filter-{filter_id}", classes="filter-button")
            if filter_id == self.current_filter:
                button.add_class("active")
            filter_container.mount(button)
    
    def _populate_timeline(self) -> None:
        """Populate the timeline panel."""
        timeline_panel = self.query(TerminalPanel)[2]  # Third panel is timeline
        timeline_container = timeline_panel.get_content_container()
        
        # Clear existing content
        timeline_container.remove_children()
        
        # Create and mount timeline
        timeline = ActivityTimeline(self.filtered_activities)
        timeline_container.mount(timeline)
    
    def _calculate_statistics(self) -> dict:
        """Calculate statistics from activities."""
        now = datetime.now()
        today = now.date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        stats = {
            'total_activities': len(self.activities),
            'quests_completed': sum(1 for a in self.activities if a.is_task_completion),
            'total_xp': sum(a.xp_earned for a in self.activities),
            'level_ups': sum(1 for a in self.activities if a.is_level_up),
            'achievements': sum(1 for a in self.activities if a.is_achievement),
            'today_activities': sum(1 for a in self.activities if a.timestamp.date() == today),
            'this_week_activities': sum(1 for a in self.activities 
                                      if a.timestamp.date() >= week_start),
            'this_month_activities': sum(1 for a in self.activities 
                                       if a.timestamp.date() >= month_start),
        }
        
        return stats
    
    def _apply_filter(self, filter_type: str) -> None:
        """Apply filter to activities."""
        self.current_filter = filter_type
        now = datetime.now()
        today = now.date()
        
        if filter_type == "all":
            self.filtered_activities = self.activities.copy()
        elif filter_type == "today":
            self.filtered_activities = [a for a in self.activities 
                                      if a.timestamp.date() == today]
        elif filter_type == "week":
            week_start = today - timedelta(days=today.weekday())
            self.filtered_activities = [a for a in self.activities 
                                      if a.timestamp.date() >= week_start]
        elif filter_type == "month":
            month_start = today.replace(day=1)
            self.filtered_activities = [a for a in self.activities 
                                      if a.timestamp.date() >= month_start]
        elif filter_type == "quests":
            self.filtered_activities = [a for a in self.activities if a.is_task_completion]
        elif filter_type == "achievements":
            self.filtered_activities = [a for a in self.activities if a.is_achievement]
        elif filter_type == "level_ups":
            self.filtered_activities = [a for a in self.activities if a.is_level_up]
        
        # Update filter button states
        for button in self.query(Button):
            if button.id and button.id.startswith("filter-"):
                filter_id = button.id.replace("filter-", "")
                if filter_id == filter_type:
                    button.add_class("active")
                else:
                    button.remove_class("active")
        
        # Refresh timeline
        self._populate_timeline()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id and event.button.id.startswith("filter-"):
            filter_type = event.button.id.replace("filter-", "")
            self._apply_filter(filter_type)
    
    def action_back(self) -> None:
        """Handle back action."""
        self.app.pop_screen()
    
    def action_quit(self) -> None:
        """Handle quit action."""
        self.app.exit()
    
    def action_help(self) -> None:
        """Handle help action."""
        # For now, just show a notification instead of pushing a help screen
        self.notify("Help: Use ESC to go back, R to refresh, F to filter, Q to quit")
    
    def action_refresh(self) -> None:
        """Handle refresh action."""
        self._initialize_content()
    
    def action_filter(self) -> None:
        """Handle filter cycling action."""
        filters = ["all", "today", "week", "month", "quests", "achievements", "level_ups"]
        current_index = filters.index(self.current_filter)
        next_index = (current_index + 1) % len(filters)
        self._apply_filter(filters[next_index])
    
    def update_activities(self, activities: List[ActivityEntry]) -> None:
        """Update the screen with new activities."""
        self.activities = activities
        self.filtered_activities = activities.copy()
        self._initialize_content()
    
    def add_activity(self, activity: ActivityEntry) -> None:
        """Add a new activity to the journal."""
        self.activities.append(activity)
        # Re-sort activities by timestamp (newest first)
        self.activities.sort(key=lambda a: a.timestamp, reverse=True)
        
        # Update filtered activities if the new activity matches current filter
        if self._activity_matches_filter(activity, self.current_filter):
            self.filtered_activities.append(activity)
            self.filtered_activities.sort(key=lambda a: a.timestamp, reverse=True)
        
        # Refresh display
        self._initialize_content()
    
    def _activity_matches_filter(self, activity: ActivityEntry, filter_type: str) -> bool:
        """Check if activity matches the current filter."""
        now = datetime.now()
        today = now.date()
        
        if filter_type == "all":
            return True
        elif filter_type == "today":
            return activity.timestamp.date() == today
        elif filter_type == "week":
            week_start = today - timedelta(days=today.weekday())
            return activity.timestamp.date() >= week_start
        elif filter_type == "month":
            month_start = today.replace(day=1)
            return activity.timestamp.date() >= month_start
        elif filter_type == "quests":
            return activity.is_task_completion
        elif filter_type == "achievements":
            return activity.is_achievement
        elif filter_type == "level_ups":
            return activity.is_level_up
        
        return False


# Helper functions for creating sample activities (for testing)
def create_sample_activities() -> List[ActivityEntry]:
    """Create sample activities for testing the journal screen."""
    activities = []
    now = datetime.now()
    
    # Today's activities
    activities.append(ActivityEntry.create_task_completion(
        "Fix login bug", TaskDifficulty.MEDIUM, 30, "task-1"
    ))
    
    activities.append(ActivityEntry.create_task_completion(
        "Update documentation", TaskDifficulty.EASY, 15, "task-2"
    ))
    
    activities.append(ActivityEntry.create_level_up(4, 5, 500))
    
    # Yesterday's activities
    yesterday = now - timedelta(days=1)
    activities.append(ActivityEntry(
        timestamp=yesterday,
        activity_type=ActivityType.TASK_COMPLETED,
        description="Implement user authentication",
        xp_earned=50,
        metadata={
            'task_title': "Implement user authentication",
            'difficulty': TaskDifficulty.HARD.name,
            'task_id': "task-3"
        }
    ))
    
    activities.append(ActivityEntry.create_achievement(
        "Bug Hunter", "Fixed 10 bugs", "🐛"
    ))
    
    # Last week's activities
    last_week = now - timedelta(days=7)
    activities.append(ActivityEntry(
        timestamp=last_week,
        activity_type=ActivityType.TASK_COMPLETED,
        description="Setup CI/CD pipeline",
        xp_earned=50,
        metadata={
            'task_title': "Setup CI/CD pipeline",
            'difficulty': TaskDifficulty.HARD.name,
            'task_id': "task-4"
        }
    ))
    
    return activities