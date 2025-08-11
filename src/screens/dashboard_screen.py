"""DashboardScreen - Focused daily work interface with today's quests and detailed view."""

from typing import List, Optional, Dict
from datetime import datetime, date
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Static, ListView, Button, Label
from textual.binding import Binding
from textual.message import Message

from ..models.task import Task
from ..models.player import PlayerData
from ..models.enums import TaskStatus, TaskDifficulty, TaskPriority
from ..data.data_manager import DataManager
from ..widgets.terminal_header import TerminalHeader
from ..widgets.terminal_footer import TerminalFooter
from ..widgets.terminal_panel import TerminalPanel
from ..widgets.task_list_item import TaskListItem
from ..widgets.feedback_system import FeedbackSystem
from ..terminal_theme import get_terminal_theme, get_ascii_generator


class TodayQuestItem(Static):
    """Widget for displaying a quest in the today's quests sidebar."""
    
    DEFAULT_CSS = """
    TodayQuestItem {
        height: 3;
        padding: 0 1;
        margin: 0 0 1 0;
        background: #181817;
        border: solid #3a3a3a;
    }
    
    TodayQuestItem:hover {
        background: #19327f;
        border: solid #1b45d7;
    }
    
    TodayQuestItem.selected {
        background: #19327f;
        border: solid #1b45d7;
        color: #ffffff;
    }
    
    .quest-title {
        color: #e0e0e0;
        text-style: bold;
        height: 1;
    }
    
    .quest-meta {
        color: #9aa0b0;
        height: 1;
    }
    
    .quest-xp {
        color: #ffc107;
        text-style: bold;
    }
    
    .priority-critical {
        color: #f44336;
    }
    
    .priority-high {
        color: #ff9800;
    }
    
    .priority-medium {
        color: #ffc107;
    }
    
    .priority-low {
        color: #9aa0b0;
    }
    """
    
    def __init__(self, task: Task, **kwargs):
        """Initialize the today quest item.
        
        Args:
            task: Task object to display
        """
        super().__init__(**kwargs)
        self.task = task
        self.can_focus = True
    
    def compose(self) -> ComposeResult:
        """Compose the quest item layout."""
        # Priority indicator and title
        priority_symbol = self._get_priority_symbol()
        title_text = f"{priority_symbol} {self.task.title[:30]}{'...' if len(self.task.title) > 30 else ''}"
        yield Static(title_text, classes=f"quest-title priority-{self.task.priority.name.lower()}")
        
        # XP and status info
        status_text = f"XP: {self.task.xp_reward} | {self.task.difficulty.display_name} | {self.task.status.value}"
        yield Static(status_text, classes="quest-meta")
    
    def _get_priority_symbol(self) -> str:
        """Get the priority symbol for the task."""
        symbols = {
            TaskPriority.CRITICAL: "🔥",
            TaskPriority.HIGH: "⚡",
            TaskPriority.MEDIUM: "●",
            TaskPriority.LOW: "○"
        }
        return symbols.get(self.task.priority, "●")
    
    def set_selected(self, selected: bool) -> None:
        """Set the selected state of the quest item."""
        if selected:
            self.add_class("selected")
        else:
            self.remove_class("selected")


class TodayQuestsSidebar(TerminalPanel):
    """Sidebar panel displaying today's active quests."""
    
    def __init__(self, data_manager: DataManager, **kwargs):
        """Initialize the today's quests sidebar.
        
        Args:
            data_manager: Data manager instance
        """
        super().__init__(title="Today's Quests", scrollable=True, **kwargs)
        self.data_manager = data_manager
        self.today_tasks: List[Task] = []
        self.selected_task: Optional[Task] = None
        self.quest_items: List[TodayQuestItem] = []
    
    def compose(self) -> ComposeResult:
        """Compose the sidebar layout."""
        yield from super().compose()
    
    def on_mount(self) -> None:
        """Handle mount event."""
        self.refresh_today_tasks()
    
    def refresh_today_tasks(self) -> None:
        """Refresh the list of today's tasks."""
        try:
            # Load all tasks
            all_tasks = self.data_manager.load_tasks()
            
            # Filter for today's active tasks (not completed)
            today = date.today()
            self.today_tasks = []
            
            for task in all_tasks.values():
                # Include tasks that are not completed and were created today or are active
                if (not task.is_completed and 
                    (task.created_at.date() == today or task.status == TaskStatus.ACTIVE)):
                    self.today_tasks.append(task)
            
            # Sort by priority (CRITICAL > HIGH > MEDIUM > LOW) and creation time
            priority_order = {
                TaskPriority.CRITICAL: 0,
                TaskPriority.HIGH: 1,
                TaskPriority.MEDIUM: 2,
                TaskPriority.LOW: 3
            }
            
            self.today_tasks.sort(key=lambda t: (
                priority_order.get(t.priority, 4),
                -t.created_at.timestamp()
            ))
            
            # Update the display
            self._update_quest_display()
            
        except Exception as e:
            # Handle error gracefully
            self.today_tasks = []
            self._update_quest_display()
    
    def _update_quest_display(self) -> None:
        """Update the quest items display."""
        # Clear existing content
        content_container = self.get_content_container()
        content_container.remove_children()
        self.quest_items.clear()
        
        if not self.today_tasks:
            # Show empty state
            empty_message = Static("No quests for today.\nCreate a new quest to get started!", 
                                 classes="terminal-text-muted")
            content_container.mount(empty_message)
            return
        
        # Add quest items
        for task in self.today_tasks:
            quest_item = TodayQuestItem(task)
            self.quest_items.append(quest_item)
            content_container.mount(quest_item)
        
        # Select first item by default
        if self.quest_items and not self.selected_task:
            self.select_quest(self.today_tasks[0])
    
    def select_quest(self, task: Task) -> None:
        """Select a specific quest."""
        # Update selected task
        old_selected = self.selected_task
        self.selected_task = task
        
        # Update visual selection
        for quest_item in self.quest_items:
            quest_item.set_selected(quest_item.task.id == task.id)
        
        # Notify parent about selection change
        if old_selected != task:
            self.post_message(self.QuestSelected(task))
    
    def get_selected_quest(self) -> Optional[Task]:
        """Get the currently selected quest."""
        return self.selected_task
    
    def on_click(self, event) -> None:
        """Handle click events on quest items."""
        # Find which quest item was clicked
        for quest_item in self.quest_items:
            if quest_item.get_widget_at(event.screen_x, event.screen_y)[0] == quest_item:
                self.select_quest(quest_item.task)
                break
    
    class QuestSelected(Message):
        """Message sent when a quest is selected."""
        
        def __init__(self, task: Task):
            super().__init__()
            self.task = task


class StreakAndActionsPanel(TerminalPanel):
    """Panel for displaying streak information and quick actions."""
    
    def __init__(self, data_manager: DataManager, **kwargs):
        """Initialize the streak and actions panel.
        
        Args:
            data_manager: Data manager instance
        """
        super().__init__(title="Progress & Quick Actions", scrollable=False, **kwargs)
        self.data_manager = data_manager
        self.player_data: Optional[PlayerData] = None
        self.ascii_generator = get_ascii_generator()
    
    def update_player_data(self, player_data: PlayerData) -> None:
        """Update the player data and refresh display.
        
        Args:
            player_data: Updated player data
        """
        self.player_data = player_data
        self._refresh_content()
    
    def _refresh_content(self) -> None:
        """Refresh the panel content."""
        content_container = self.get_content_container()
        content_container.remove_children()
        
        if not self.player_data:
            # Show loading state
            loading_message = Static(
                "Loading player data...",
                classes="terminal-text-muted"
            )
            content_container.mount(loading_message)
            return
        
        # Create horizontal layout for streak info and actions
        with Horizontal():
            # Left side - Streak and progress info
            streak_container = Container()
            streak_container.styles.width = "60%"
            
            # Current streak display
            streak_text = f"🔥 Current Streak: {self.player_data.current_streak} days"
            streak_widget = Static(streak_text, classes="streak-info terminal-highlight")
            streak_container.mount(streak_widget)
            
            # Daily progress
            today_tasks = self._get_today_completed_tasks()
            progress_text = f"📋 Today: {today_tasks} quests completed"
            progress_widget = Static(progress_text, classes="terminal-text")
            streak_container.mount(progress_widget)
            
            # Level and XP info
            level_text = f"⭐ Level {self.player_data.level} | XP: {self.player_data.total_xp}"
            level_widget = Static(level_text, classes="level-info")
            streak_container.mount(level_widget)
            
            # XP progress bar
            progress_bar = self._create_xp_progress_bar()
            streak_container.mount(progress_bar)
            
            content_container.mount(streak_container)
            
            # Right side - Quick action buttons
            actions_container = Container()
            actions_container.styles.width = "40%"
            
            # Quick action buttons
            add_button = Button("➕ New Quest", id="quick-add", classes="action-button")
            actions_container.mount(add_button)
            
            complete_button = Button("✅ Complete", id="quick-complete", classes="action-button")
            actions_container.mount(complete_button)
            
            journal_button = Button("📖 Journal", id="quick-journal", classes="action-button")
            actions_container.mount(journal_button)
            
            stats_button = Button("📊 Stats", id="quick-stats", classes="action-button")
            actions_container.mount(stats_button)
            
            content_container.mount(actions_container)
    
    def _get_today_completed_tasks(self) -> int:
        """Get the number of tasks completed today."""
        try:
            all_tasks = self.data_manager.load_tasks()
            today = date.today()
            
            completed_today = 0
            for task in all_tasks.values():
                if (task.is_completed and 
                    task.completed_at and 
                    task.completed_at.date() == today):
                    completed_today += 1
            
            return completed_today
        except:
            return 0
    
    def _create_xp_progress_bar(self) -> Static:
        """Create a terminal-style XP progress bar."""
        if not self.player_data:
            return Static("", classes="terminal-text")
        
        # Calculate progress to next level
        current_level_xp = self.player_data.current_level_xp
        xp_for_next_level = self.player_data.xp_for_next_level - self.player_data.xp_for_current_level
        
        if xp_for_next_level <= 0:
            progress = 1.0
        else:
            progress = current_level_xp / xp_for_next_level
        
        # Create ASCII progress bar
        progress_bar = self.ascii_generator.create_progress_bar(
            progress, 
            width=25, 
            show_percentage=False
        )
        
        progress_text = f"{progress_bar} {current_level_xp}/{xp_for_next_level} XP"
        return Static(progress_text, classes="progress-bar-terminal xp-value")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        
        if button_id == "quick-add":
            self.post_message(self.QuickAction("add_task"))
        elif button_id == "quick-complete":
            self.post_message(self.QuickAction("complete_task"))
        elif button_id == "quick-journal":
            self.post_message(self.QuickAction("show_journal"))
        elif button_id == "quick-stats":
            self.post_message(self.QuickAction("show_stats"))
    
    class QuickAction(Message):
        """Message sent when a quick action is triggered."""
        
        def __init__(self, action: str):
            super().__init__()
            self.action = action


class QuestDetailsPanel(TerminalPanel):
    """Panel for displaying detailed quest information."""
    
    def __init__(self, **kwargs):
        """Initialize the quest details panel."""
        super().__init__(title="Quest Details", scrollable=True, **kwargs)
        self.current_task: Optional[Task] = None
        self.ascii_generator = get_ascii_generator()
    
    def update_quest(self, task: Optional[Task]) -> None:
        """Update the displayed quest details.
        
        Args:
            task: Task to display, or None to show empty state
        """
        self.current_task = task
        self._refresh_content()
    
    def _refresh_content(self) -> None:
        """Refresh the panel content."""
        content_container = self.get_content_container()
        content_container.remove_children()
        
        if not self.current_task:
            # Show empty state
            empty_message = Static(
                "Select a quest from the sidebar to view details",
                classes="terminal-text-muted"
            )
            content_container.mount(empty_message)
            return
        
        # Quest title and basic info
        title_widget = Static(
            self.current_task.title,
            classes="terminal-title"
        )
        content_container.mount(title_widget)
        
        # Separator
        separator = Static(
            self.ascii_generator.create_separator(50),
            classes="ascii-border"
        )
        content_container.mount(separator)
        
        # Quest metadata in organized sections
        # Basic Information Section
        basic_info = self._create_basic_info_section()
        content_container.mount(basic_info)
        
        # Description Section
        if self.current_task.notes:
            desc_section = self._create_description_section()
            content_container.mount(desc_section)
        
        # Acceptance Criteria Section (if available in notes)
        criteria_section = self._create_acceptance_criteria_section()
        if criteria_section:
            content_container.mount(criteria_section)
        
        # Timestamps Section
        timestamps_section = self._create_timestamps_section()
        content_container.mount(timestamps_section)
    
    def _create_basic_info_section(self) -> Container:
        """Create the basic information section."""
        section = Container()
        
        # Section header
        header = Static("Basic Information", classes="terminal-highlight")
        section.mount(header)
        
        # Difficulty with XP
        difficulty_text = f"Difficulty: {self.current_task.difficulty.display_name} (XP: {self.current_task.xp_reward})"
        difficulty_widget = Static(difficulty_text, classes=f"difficulty-{self.current_task.difficulty.name.lower()}")
        section.mount(difficulty_widget)
        
        # Priority
        priority_symbol = self._get_priority_symbol()
        priority_text = f"Priority: {priority_symbol} {self.current_task.priority.value}"
        priority_widget = Static(priority_text, classes=f"priority-{self.current_task.priority.name.lower()}")
        section.mount(priority_widget)
        
        # Status
        status_text = f"Status: {self.current_task.status.value}"
        status_widget = Static(status_text, classes=f"status-{self.current_task.status.name.lower()}")
        section.mount(status_widget)
        
        # Add spacing
        section.mount(Static("", classes="terminal-text"))
        
        return section
    
    def _create_description_section(self) -> Container:
        """Create the description section."""
        section = Container()
        
        # Section header
        header = Static("Description", classes="terminal-highlight")
        section.mount(header)
        
        # Description text
        desc_widget = Static(self.current_task.notes, classes="terminal-text")
        section.mount(desc_widget)
        
        # Add spacing
        section.mount(Static("", classes="terminal-text"))
        
        return section
    
    def _create_acceptance_criteria_section(self) -> Optional[Container]:
        """Create the acceptance criteria section if criteria are found in notes."""
        if not self.current_task.notes:
            return None
        
        # Look for acceptance criteria patterns in notes
        notes_lines = self.current_task.notes.split('\n')
        criteria_lines = []
        in_criteria_section = False
        
        for line in notes_lines:
            line_lower = line.lower().strip()
            if 'acceptance criteria' in line_lower or 'criteria:' in line_lower:
                in_criteria_section = True
                continue
            elif in_criteria_section:
                if line.strip().startswith(('-', '*', '•', '1.', '2.', '3.')):
                    criteria_lines.append(line.strip())
                elif line.strip() == '':
                    continue
                else:
                    # End of criteria section
                    break
        
        if not criteria_lines:
            return None
        
        section = Container()
        
        # Section header
        header = Static("Acceptance Criteria", classes="terminal-highlight")
        section.mount(header)
        
        # Criteria list
        for criterion in criteria_lines:
            # Format as bullet point if not already
            if not criterion.startswith(('•', '-', '*')):
                criterion = f"• {criterion}"
            
            criteria_widget = Static(criterion, classes="terminal-text")
            section.mount(criteria_widget)
        
        # Add spacing
        section.mount(Static("", classes="terminal-text"))
        
        return section
    
    def _create_timestamps_section(self) -> Container:
        """Create the timestamps section."""
        section = Container()
        
        # Section header
        header = Static("Timeline", classes="terminal-highlight")
        section.mount(header)
        
        # Created date
        created_text = f"Created: {self.current_task.created_at.strftime('%Y-%m-%d %H:%M')}"
        created_widget = Static(created_text, classes="terminal-text-muted")
        section.mount(created_widget)
        
        # Completed date (if applicable)
        if self.current_task.completed_at:
            completed_text = f"Completed: {self.current_task.completed_at.strftime('%Y-%m-%d %H:%M')}"
            completed_widget = Static(completed_text, classes="terminal-text-muted")
            section.mount(completed_widget)
        
        return section
    
    def _get_priority_symbol(self) -> str:
        """Get the priority symbol for the task."""
        symbols = {
            TaskPriority.CRITICAL: "🔥",
            TaskPriority.HIGH: "⚡",
            TaskPriority.MEDIUM: "●",
            TaskPriority.LOW: "○"
        }
        return symbols.get(self.current_task.priority, "●")


class DashboardScreen(Screen):
    """Dashboard screen for focused daily work with today's quests and detailed view."""
    
    BINDINGS = [
        Binding("q", "show_quests", "All Quests", show=True),
        Binding("a", "add_task", "Add Quest", show=True),
        Binding("j", "show_journal", "Journal", show=True),
        Binding("s", "show_stats", "Stats", show=True),
        Binding("enter", "complete_task", "Complete", show=True),
        Binding("e", "edit_task", "Edit", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("escape", "quit", "Quit", show=True),
    ]
    
    def __init__(self, data_manager: DataManager, **kwargs):
        """Initialize the dashboard screen.
        
        Args:
            data_manager: Data manager instance
        """
        super().__init__(**kwargs)
        self.data_manager = data_manager
        self.selected_task: Optional[Task] = None
        self.player_data: Optional[PlayerData] = None
        self.feedback_system = FeedbackSystem()
        self.quest_details_panel: Optional[QuestDetailsPanel] = None
        self.streak_actions_panel: Optional[StreakAndActionsPanel] = None
    
    def compose(self) -> ComposeResult:
        """Compose the dashboard screen layout."""
        # Terminal header
        yield TerminalHeader(
            screen_name="Dashboard",
            user_name="Player",  # TODO: Get from player data
            active_tab=1,
            show_tabs=True
        )
        
        # Main content area
        with Container(classes="terminal-content"):
            # Left sidebar - Today's quests
            self.today_sidebar = TodayQuestsSidebar(
                self.data_manager,
                classes="terminal-sidebar"
            )
            self.today_sidebar.styles.width = "30%"
            yield self.today_sidebar
            
            # Main content area - Quest details
            with Container(classes="terminal-main"):
                yield from self._compose_main_content()
        
        # Terminal footer
        yield TerminalFooter(
            commands=[
                ("add", "New Quest"),
                ("edit", "Edit"),
                ("complete", "Complete"),
                ("journal", "Journal"),
                ("stats", "Stats"),
                ("help", "Help"),
                ("quit", "Quit")
            ],
            status_info="Dashboard - Focus on today's work"
        )
        
        # Feedback system
        yield self.feedback_system
    
    def _compose_main_content(self) -> ComposeResult:
        """Compose the main content area."""
        # Main quest details panel
        self.quest_details_panel = QuestDetailsPanel(classes="focused-panel")
        self.quest_details_panel.styles.height = "70%"
        yield self.quest_details_panel
        
        # Streak indicator and quick actions panel
        self.streak_actions_panel = StreakAndActionsPanel(self.data_manager)
        self.streak_actions_panel.styles.height = "30%"
        yield self.streak_actions_panel
    
    def on_mount(self) -> None:
        """Handle screen mount event."""
        self.load_player_data()
        self.today_sidebar.refresh_today_tasks()
    
    def load_player_data(self) -> None:
        """Load player data."""
        try:
            self.player_data = self.data_manager.load_player_data()
            
            # Update the streak and actions panel
            if self.streak_actions_panel:
                self.streak_actions_panel.update_player_data(self.player_data)
                
        except Exception as e:
            self.feedback_system.show_error(f"Failed to load player data: {e}")
    
    def on_today_quests_sidebar_quest_selected(self, message: TodayQuestsSidebar.QuestSelected) -> None:
        """Handle quest selection from the sidebar."""
        self.selected_task = message.task
        
        # Update the quest details panel
        if self.quest_details_panel:
            self.quest_details_panel.update_quest(message.task)
        
        self.feedback_system.show_info(f"Selected quest: {message.task.title}")
    
    def on_streak_and_actions_panel_quick_action(self, message: StreakAndActionsPanel.QuickAction) -> None:
        """Handle quick action messages from the streak and actions panel."""
        action = message.action
        
        if action == "add_task":
            self.action_add_task()
        elif action == "complete_task":
            self.action_complete_task()
        elif action == "show_journal":
            self.action_show_journal()
        elif action == "show_stats":
            self.action_show_stats()
    
    def action_add_task(self) -> None:
        """Open the add task screen."""
        from .new_quest_screen import NewQuestScreen
        self.app.push_screen(NewQuestScreen(self.data_manager))
    
    def action_show_quests(self) -> None:
        """Navigate to the all quests screen."""
        from .quests_screen import QuestsScreen
        self.app.push_screen(QuestsScreen(self.data_manager))
    
    def action_show_journal(self) -> None:
        """Navigate to the journal screen."""
        from .journal_screen import JournalScreen
        self.app.push_screen(JournalScreen(self.data_manager))
    
    def action_show_stats(self) -> None:
        """Navigate to the character stats screen."""
        from .character_stats_screen import CharacterStatsScreen
        self.app.push_screen(CharacterStatsScreen())
    
    def action_complete_task(self) -> None:
        """Complete the selected task."""
        if not self.selected_task:
            self.feedback_system.show_warning("Please select a quest to complete")
            return
        
        if self.selected_task.is_completed:
            self.feedback_system.show_warning("Quest is already completed")
            return
        
        try:
            # Complete the task
            xp_earned = self.selected_task.complete()
            
            # Update player stats
            if self.player_data:
                self.player_data.total_xp += xp_earned
                self.player_data.tasks_completed += 1
                self.data_manager.save_player_data(self.player_data)
            
            # Save task data
            all_tasks = self.data_manager.load_tasks()
            all_tasks[self.selected_task.id] = self.selected_task
            self.data_manager.save_tasks(all_tasks)
            
            # Show success feedback
            self.feedback_system.show_success(
                f"Quest completed! +{xp_earned} XP earned"
            )
            
            # Refresh the sidebar
            self.today_sidebar.refresh_today_tasks()
            
        except Exception as e:
            self.feedback_system.show_error(f"Failed to complete quest: {e}")
    
    def action_edit_task(self) -> None:
        """Edit the selected task."""
        if not self.selected_task:
            self.feedback_system.show_warning("Please select a quest to edit")
            return
        
        from .edit_task_screen import EditTaskScreen
        self.app.push_screen(EditTaskScreen(self.data_manager, self.selected_task))
    
    def action_refresh(self) -> None:
        """Refresh the dashboard data."""
        self.load_player_data()
        self.today_sidebar.refresh_today_tasks()
        self.feedback_system.show_info("Dashboard refreshed")
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()