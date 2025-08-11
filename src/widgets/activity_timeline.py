"""Activity timeline widgets for journal screen."""

from datetime import datetime, date
from typing import List, Dict, Optional
from collections import defaultdict

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widget import Widget
from textual.widgets import Static, Label
from textual.containers import ScrollableContainer

from ..models.activity import ActivityEntry, ActivityType
from ..terminal_theme import get_terminal_theme, get_ascii_generator


class ActivityItem(Widget):
    """Individual activity item widget with terminal styling."""
    
    DEFAULT_CSS = """
    ActivityItem {
        height: auto;
        padding: 1;
        margin: 0 0 1 0;
        background: #181817;
        border-left: thick #3a3a3a;
    }
    
    ActivityItem:hover {
        background: #19327f;
        border-left: thick #1b45d7;
    }
    
    ActivityItem.task-completion {
        border-left: thick #4caf50;
    }
    
    ActivityItem.level-up {
        border-left: thick #1b45d7;
        background: #1e1e1e;
    }
    
    ActivityItem.achievement {
        border-left: thick #ffc107;
        background: #1e1e1e;
    }
    
    .activity-time {
        color: #9aa0b0;
        width: 8;
        text-align: right;
    }
    
    .activity-content {
        margin: 0 0 0 2;
    }
    
    .activity-description {
        color: #e0e0e0;
        text-style: bold;
    }
    
    .activity-xp {
        color: #ffc107;
        text-style: bold;
    }
    
    .activity-difficulty {
        text-style: bold;
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
    
    .activity-level-up {
        color: #1b45d7;
        text-style: bold;
        background: #1e1e1e;
    }
    
    .activity-achievement {
        color: #ffc107;
        text-style: bold;
    }
    
    .achievement-badge {
        color: #ffc107;
        text-style: bold;
        background: #1e1e1e;
    }
    
    .activity-meta {
        color: #9aa0b0;
        text-style: italic;
    }
    """
    
    def __init__(self, activity: ActivityEntry, **kwargs):
        """Initialize activity item widget.
        
        Args:
            activity: ActivityEntry to display
        """
        super().__init__(**kwargs)
        self.activity = activity
        self.theme = get_terminal_theme()
        self.ascii_gen = get_ascii_generator()
        
        # Add CSS class based on activity type
        if activity.is_task_completion:
            self.add_class("task-completion")
        elif activity.is_level_up:
            self.add_class("level-up")
        elif activity.is_achievement:
            self.add_class("achievement")
    
    def compose(self) -> ComposeResult:
        """Compose the activity item layout."""
        with Horizontal():
            # Time column
            yield Static(self.activity.time_str, classes="activity-time")
            
            # Content column
            with Vertical(classes="activity-content"):
                # Main description with type-specific styling
                if self.activity.is_task_completion:
                    yield from self._create_task_completion_content()
                elif self.activity.is_level_up:
                    yield from self._create_level_up_content()
                elif self.activity.is_achievement:
                    yield from self._create_achievement_content()
                else:
                    yield Static(self.activity.description, classes="activity-description")
    
    def _create_task_completion_content(self) -> ComposeResult:
        """Create content for task completion activity."""
        difficulty = self.activity.difficulty
        task_title = self.activity.task_title or self.activity.description
        
        # Task title with bullet point
        with Horizontal():
            yield Static(f"{self.ascii_gen.theme.ascii_chars['bullet']} ", classes="activity-description")
            yield Static(task_title, classes="activity-description")
        
        # Difficulty and XP on second line with proper indentation
        with Horizontal():
            yield Static("  ", classes="activity-description")  # Indentation
            
            if difficulty:
                difficulty_class = f"difficulty-{difficulty.name.lower()}"
                difficulty_text = f"[{difficulty.display_name}]"
                yield Static(difficulty_text, classes=f"activity-difficulty {difficulty_class}")
                yield Static(" ", classes="activity-description")  # Spacer
            
            if self.activity.xp_earned > 0:
                xp_text = f"+{self.activity.xp_earned} XP"
                yield Static(xp_text, classes="activity-xp")
    
    def _create_level_up_content(self) -> ComposeResult:
        """Create content for level up activity with prominent display."""
        level_info = self.activity.level_info
        
        # Create prominent level up display
        star_char = self.ascii_gen.theme.ascii_chars['star']
        arrow_char = self.ascii_gen.theme.ascii_chars['arrow_right']
        
        if level_info:
            old_level = level_info['old_level']
            new_level = level_info['new_level']
            
            # Main level up announcement
            level_text = f"{star_char} LEVEL UP! {star_char}"
            yield Static(level_text, classes="activity-level-up")
            
            # Level progression details
            progression_text = f"  Level {old_level} {arrow_char} Level {new_level}"
            yield Static(progression_text, classes="activity-level-up")
            
            # Total XP if available
            if 'total_xp' in self.activity.metadata:
                total_xp = self.activity.metadata['total_xp']
                xp_text = f"  Total XP: {total_xp}"
                yield Static(xp_text, classes="activity-meta")
        else:
            level_text = f"{star_char} {self.activity.description}"
            yield Static(level_text, classes="activity-level-up")
    
    def _create_achievement_content(self) -> ComposeResult:
        """Create content for achievement activity with special badge formatting."""
        achievement_info = self.activity.achievement_info
        
        if achievement_info:
            badge_icon = achievement_info.get('badge_icon', '★')
            achievement_name = achievement_info.get('achievement_name', '')
            achievement_desc = achievement_info.get('achievement_description', '')
            
            # Achievement header with badge
            with Horizontal():
                yield Static(f"{badge_icon} ACHIEVEMENT UNLOCKED! {badge_icon}", classes="achievement-badge")
            
            # Achievement name
            with Horizontal():
                yield Static("  ", classes="activity-achievement")  # Indentation
                yield Static(achievement_name, classes="activity-achievement")
            
            # Achievement description
            if achievement_desc:
                with Horizontal():
                    yield Static("  ", classes="activity-meta")  # Indentation
                    yield Static(f'"{achievement_desc}"', classes="activity-meta")
        else:
            # Fallback for achievements without detailed info
            star_char = self.ascii_gen.theme.ascii_chars['star']
            yield Static(f"{star_char} {self.activity.description}", classes="activity-achievement")


class DailyActivityGroup(Widget):
    """Widget for displaying activities grouped by date."""
    
    DEFAULT_CSS = """
    DailyActivityGroup {
        height: auto;
        margin: 0 0 2 0;
        background: #181817;
        border: solid #3a3a3a;
        padding: 1;
    }
    
    .daily-header {
        dock: top;
        height: 3;
        background: #0a1543;
        color: #1b45d7;
        text-style: bold;
        padding: 1;
        border-bottom: solid #3a3a3a;
        margin: 0 0 1 0;
    }
    
    .daily-date {
        color: #1b45d7;
        text-style: bold;
        text-align: center;
    }
    
    .daily-day-of-week {
        color: #9aa0b0;
        text-align: center;
    }
    
    .daily-summary {
        color: #ffc107;
        text-align: center;
    }
    
    .daily-activities {
        padding: 0;
    }
    
    .no-activities {
        color: #9aa0b0;
        text-style: italic;
        text-align: center;
        padding: 2;
    }
    """
    
    def __init__(self, date_obj: date, activities: List[ActivityEntry], **kwargs):
        """Initialize daily activity group.
        
        Args:
            date_obj: Date for this group
            activities: List of activities for this date
        """
        super().__init__(**kwargs)
        self.date_obj = date_obj
        self.activities = sorted(activities, key=lambda a: a.timestamp, reverse=True)
        self.theme = get_terminal_theme()
        self.ascii_gen = get_ascii_generator()
    
    def compose(self) -> ComposeResult:
        """Compose the daily activity group layout."""
        # Header with date and summary
        with Container(classes="daily-header"):
            yield Static(self.date_obj.strftime("%B %d, %Y"), classes="daily-date")
            yield Static(self.date_obj.strftime("%A"), classes="daily-day-of-week")
            yield Static(self._get_daily_summary(), classes="daily-summary")
        
        # Activities list
        with Container(classes="daily-activities"):
            if self.activities:
                for activity in self.activities:
                    yield ActivityItem(activity)
            else:
                yield Static("No activities recorded", classes="no-activities")
    
    def _get_daily_summary(self) -> str:
        """Get summary text for the day."""
        total_xp = sum(activity.xp_earned for activity in self.activities)
        quest_count = sum(1 for activity in self.activities if activity.is_task_completion)
        level_ups = sum(1 for activity in self.activities if activity.is_level_up)
        achievements = sum(1 for activity in self.activities if activity.is_achievement)
        
        summary_parts = []
        
        if quest_count > 0:
            summary_parts.append(f"{quest_count} quest{'s' if quest_count != 1 else ''}")
        
        if total_xp > 0:
            summary_parts.append(f"{total_xp} XP")
        
        if level_ups > 0:
            summary_parts.append(f"{level_ups} level up{'s' if level_ups != 1 else ''}")
        
        if achievements > 0:
            summary_parts.append(f"{achievements} achievement{'s' if achievements != 1 else ''}")
        
        if summary_parts:
            return " • ".join(summary_parts)
        else:
            return "No activity"


class ActivityTimeline(Widget):
    """Main activity timeline widget with chronological display."""
    
    DEFAULT_CSS = """
    ActivityTimeline {
        height: 100%;
        background: #181817;
    }
    
    .timeline-header {
        dock: top;
        height: 3;
        background: #0a1543;
        color: #1b45d7;
        text-style: bold;
        padding: 1;
        border-bottom: solid #3a3a3a;
        text-align: center;
    }
    
    .timeline-content {
        height: 100%;
        padding: 1;
        scrollbar-gutter: stable;
    }
    
    .timeline-empty {
        color: #9aa0b0;
        text-style: italic;
        text-align: center;
        padding: 4;
    }
    
    .timeline-loading {
        color: #1b45d7;
        text-align: center;
        padding: 4;
    }
    """
    
    def __init__(self, activities: List[ActivityEntry] = None, **kwargs):
        """Initialize activity timeline.
        
        Args:
            activities: List of activities to display
        """
        super().__init__(**kwargs)
        self.activities = activities or []
        self.theme = get_terminal_theme()
        self.ascii_gen = get_ascii_generator()
    
    def compose(self) -> ComposeResult:
        """Compose the activity timeline layout."""
        # Header
        yield Static("Quest Journal - Activity Timeline", classes="timeline-header")
        
        # Scrollable content
        with ScrollableContainer(classes="timeline-content", id="timeline-content"):
            yield Container(id="timeline-activities")
        
        # Load initial activities
        self.call_after_refresh(self._populate_timeline)
    
    def _populate_timeline(self) -> None:
        """Populate the timeline with activity groups."""
        container = self.query_one("#timeline-activities", Container)
        container.remove_children()
        
        if not self.activities:
            container.mount(Static("No activities recorded yet. Complete some quests to see your progress!", 
                                 classes="timeline-empty"))
            return
        
        # Group activities by date
        activities_by_date = self._group_activities_by_date()
        
        # Create daily groups in reverse chronological order (newest first)
        for date_obj in sorted(activities_by_date.keys(), reverse=True):
            daily_activities = activities_by_date[date_obj]
            daily_group = DailyActivityGroup(date_obj, daily_activities)
            container.mount(daily_group)
    
    def _group_activities_by_date(self) -> Dict[date, List[ActivityEntry]]:
        """Group activities by date."""
        activities_by_date = defaultdict(list)
        
        for activity in self.activities:
            activity_date = activity.timestamp.date()
            activities_by_date[activity_date].append(activity)
        
        return dict(activities_by_date)
    
    def update_activities(self, activities: List[ActivityEntry]) -> None:
        """Update the timeline with new activities."""
        self.activities = activities
        self._populate_timeline()
    
    def add_activity(self, activity: ActivityEntry) -> None:
        """Add a new activity to the timeline."""
        self.activities.append(activity)
        # Re-sort activities by timestamp (newest first)
        self.activities.sort(key=lambda a: a.timestamp, reverse=True)
        self._populate_timeline()
    
    def clear_activities(self) -> None:
        """Clear all activities from the timeline."""
        self.activities = []
        self._populate_timeline()
    
    def get_activities_for_date(self, date_obj: date) -> List[ActivityEntry]:
        """Get activities for a specific date."""
        return [activity for activity in self.activities 
                if activity.timestamp.date() == date_obj]
    
    def get_recent_activities(self, days: int = 7) -> List[ActivityEntry]:
        """Get activities from the last N days."""
        cutoff_date = datetime.now().date() - __import__('datetime').timedelta(days=days)
        return [activity for activity in self.activities 
                if activity.timestamp.date() >= cutoff_date]