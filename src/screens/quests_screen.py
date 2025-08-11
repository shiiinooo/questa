"""AllQuestsScreen - Enhanced terminal-style task management and overview screen."""

from typing import List, Optional, Dict, Any
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import (
    Button, Header, Footer, Label, ListView, Static, 
    Select, Input, Checkbox, TabbedContent, TabPane
)
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from datetime import datetime, date

from ..models.task import Task
from ..models.enums import TaskStatus, TaskDifficulty, TaskPriority
from ..data.data_manager import DataManager
from ..widgets.task_list_item import TaskListItem
from ..widgets.confirmation_dialog import TaskDeletionDialog
from ..widgets.feedback_system import FeedbackSystem
from ..widgets.terminal_panel import TerminalPanel, TerminalSplitPanel
from ..widgets.priority_indicator import PriorityIndicator, DifficultyIndicator
from ..widgets.status_badge import StatusBadge
from ..terminal_theme import get_terminal_theme, get_ascii_generator


class TerminalQuestListItem(Widget):
    """Terminal-styled quest list item with priority indicators and XP values."""
    
    DEFAULT_CSS = """
    TerminalQuestListItem {
        height: 3;
        padding: 0 1;
        border-bottom: solid #3a3a3a;
        background: #181817;
    }
    
    TerminalQuestListItem:hover {
        background: #19327f;
    }
    
    TerminalQuestListItem.selected {
        background: #19327f;
        border-left: thick #1b45d7;
    }
    
    .quest-indicators {
        width: 8;
        dock: left;
        padding: 0 1;
    }
    
    .quest-content {
        padding: 0 1;
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
        height: 1;
    }
    
    .quest-tags {
        color: #1b45d7;
        height: 1;
    }
    
    /* Filter tabs styling */
    .filter-tabs-container {
        margin: 0 0 1 0;
        padding: 1;
        border-bottom: solid #3a3a3a;
    }
    
    .tab-buttons {
        height: 1;
        margin: 0 0 1 0;
    }
    
    .tab-button {
        background: #3a3a3a;
        color: #9aa0b0;
        border: none;
        margin: 0 1 0 0;
        padding: 0 1;
    }
    
    .tab-button.active {
        background: #1b45d7;
        color: #ffffff;
        text-style: bold;
    }
    
    .tab-button:hover {
        background: #19327f;
        color: #ffffff;
    }
    
    .filter-content {
        padding: 1 0;
    }
    
    .hidden {
        display: none;
    }
    
    .tag-buttons {
        margin: 1 0 0 0;
    }
    
    .tag-button {
        background: #181817;
        color: #1b45d7;
        border: solid #1b45d7;
        margin: 0 1 0 0;
        padding: 0 1;
    }
    
    .tag-button:hover {
        background: #1b45d7;
        color: #ffffff;
    }
    
    /* Quest detail styling */
    .quest-detail-header {
        margin: 0 0 1 0;
        padding: 1;
        border-bottom: solid #3a3a3a;
    }
    
    .quest-badges {
        margin: 1 0 0 0;
        height: 1;
    }
    
    .tag-display {
        margin: 0;
    }
    
    .tag-display-button {
        background: #181817;
        color: #1b45d7;
        border: solid #1b45d7;
        margin: 0 1 0 0;
        padding: 0 1;
        height: 1;
    }
    
    .tag-display-button:hover {
        background: #1b45d7;
        color: #ffffff;
    }
    
    .action-buttons {
        margin: 0;
    }
    
    .primary-button {
        background: #1b45d7;
        color: #ffffff;
        border: solid #1b45d7;
        margin: 0 1 0 0;
        padding: 0 2;
    }
    
    .primary-button:hover {
        background: #19327f;
    }
    
    .secondary-button {
        background: #3a3a3a;
        color: #e0e0e0;
        border: solid #3a3a3a;
        margin: 0 1 0 0;
        padding: 0 2;
    }
    
    .secondary-button:hover {
        background: #19327f;
        color: #ffffff;
    }
    """
    
    def __init__(self, task: Task, **kwargs):
        """Initialize the terminal quest list item."""
        super().__init__(**kwargs)
        self.task = task
        self.selected = False
        self.theme = get_terminal_theme()
        self.ascii_chars = get_ascii_generator().theme.ascii_chars
    
    def compose(self) -> ComposeResult:
        """Compose the quest list item layout."""
        with Horizontal():
            # Priority and status indicators
            with Vertical(classes="quest-indicators"):
                yield PriorityIndicator(self.task.priority, show_text=False)
                yield StatusBadge(self.task.status)
                yield DifficultyIndicator(self.task.difficulty, show_xp=False)
            
            # Quest content
            with Vertical(classes="quest-content"):
                # Title with status symbol
                status_symbol = self._get_status_symbol()
                yield Label(f"{status_symbol} {self.task.title}", classes="quest-title")
                
                # Meta information
                created_date = self.task.created_at.strftime("%m/%d")
                meta_text = f"Created: {created_date} | Difficulty: {self.task.difficulty.value}"
                yield Label(meta_text, classes="quest-meta")
                
                # XP value prominently displayed
                xp_text = f"🏆 {self.task.xp_reward} XP"
                yield Label(xp_text, classes="quest-xp")
                
                # Tags if present
                if self.task.tags:
                    tags_text = f"Tags: {', '.join(self.task.tags[:3])}"  # Show first 3 tags
                    if len(self.task.tags) > 3:
                        tags_text += f" +{len(self.task.tags) - 3} more"
                    yield Label(tags_text, classes="quest-tags")
    
    def _get_status_symbol(self) -> str:
        """Get the terminal symbol for the task status."""
        symbols = {
            TaskStatus.PENDING: self.ascii_chars.get('circle', '●'),
            TaskStatus.ACTIVE: self.ascii_chars.get('arrow_right', '→'),
            TaskStatus.COMPLETED: self.ascii_chars.get('star', '★'),
            TaskStatus.BLOCKED: self.ascii_chars.get('square', '■')
        }
        return symbols.get(self.task.status, '●')
    
    def set_selected(self, selected: bool) -> None:
        """Set the selection state."""
        self.selected = selected
        if selected:
            self.add_class("selected")
        else:
            self.remove_class("selected")
    
    def on_click(self) -> None:
        """Handle click events."""
        self.post_message(self.QuestSelected(self.task))
    
    class QuestSelected(Message):
        """Message sent when a quest is selected."""
        def __init__(self, task: Task):
            super().__init__()
            self.task = task


class AllQuestsScreen(Screen):
    """Enhanced terminal-style quests screen with filtering and detailed view."""

    BINDINGS = [
        Binding("n", "new_task", "New Quest", show=True),
        Binding("e", "edit_task", "Edit", show=True),
        Binding("d", "delete_task", "Delete", show=True),
        Binding("c", "complete_task", "Complete", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("1", "filter_today", "Today", show=True),
        Binding("2", "filter_all", "All", show=True),
        Binding("3", "filter_completed", "Completed", show=True),
        Binding("4", "filter_by_tag", "By Tag", show=True),
        Binding("up", "select_previous", "Previous", show=True),
        Binding("down", "select_next", "Next", show=True),
        Binding("enter", "view_details", "Details", show=True),
        Binding("escape", "back", "Back", show=True),
    ]

    # Reactive properties
    current_filter = reactive("all")
    search_query = reactive("")
    selected_tag = reactive("")

    def __init__(self, data_manager: DataManager, **kwargs):
        """Initialize the all quests screen."""
        super().__init__(**kwargs)
        self.data_manager = data_manager
        self.all_tasks: List[Task] = []
        self.filtered_tasks: List[Task] = []
        self.selected_task: Optional[Task] = None
        self.selected_index = 0
        self.feedback_system = FeedbackSystem()
        self.theme = get_terminal_theme()
        self.ascii_generator = get_ascii_generator()

    def compose(self) -> ComposeResult:
        """Compose the all quests screen layout."""
        # Terminal header
        with Container(classes="terminal-header"):
            yield Static("QUESTA - All Quests", classes="screen-title")
            player_info = f"Level {self.data_manager.player.level} - {self.data_manager.player.title}"
            yield Static(player_info, classes="user-context")
        
        # Main content with split panel layout
        with Container(classes="terminal-content"):
            # Left panel: Quest list with filter tabs
            with TerminalPanel(title="Quest List", scrollable=True) as quest_panel:
                quest_panel.styles.width = "60%"
                yield self._compose_filter_tabs()
                yield self._compose_quest_list()
            
            # Right panel: Quest details
            with TerminalPanel(title="Quest Details", scrollable=True) as details_panel:
                details_panel.styles.width = "40%"
                yield self._compose_quest_details()
        
        # Terminal footer with commands
        with Container(classes="terminal-footer"):
            commands = ":1-Today :2-All :3-Completed :4-ByTag :n-New :e-Edit :d-Delete :c-Complete :back"
            yield Static(commands, classes="navigation-commands")
        
        yield self.feedback_system

    def _compose_filter_tabs(self) -> ComposeResult:
        """Compose the filter tabs for quest display."""
        with Container(classes="filter-tabs-container"):
            # Tab buttons
            with Horizontal(classes="tab-buttons"):
                yield Button("1. Today", action="filter_today", classes="tab-button", id="tab-today")
                yield Button("2. All", action="filter_all", classes="tab-button active", id="tab-all")
                yield Button("3. Completed", action="filter_completed", classes="tab-button", id="tab-completed")
                yield Button("4. By Tag", action="filter_by_tag", classes="tab-button", id="tab-by-tag")
            
            # Filter content area
            with Container(classes="filter-content", id="filter-content"):
                # Search input (always visible)
                yield Input(placeholder="Search quests...", id="general-search", classes="terminal-input")
                
                # Tag-specific search (shown when by-tag is active)
                with Container(id="tag-filter-container", classes="hidden"):
                    yield Input(placeholder="Enter tag to filter...", id="tag-search", classes="terminal-input")
                    yield self._compose_available_tags()
    
    def _compose_available_tags(self) -> ComposeResult:
        """Compose the available tags display."""
        # Get all unique tags from tasks
        all_tags = set()
        for task in self.all_tasks:
            all_tags.update(task.tags)
        
        if all_tags:
            yield Static("Available tags:", classes="terminal-text-muted")
            # Display tags as clickable buttons
            with Horizontal(classes="tag-buttons"):
                for tag in sorted(all_tags):
                    yield Button(f"#{tag}", action=f"select_tag_{tag}", classes="tag-button")
        else:
            yield Static("No tags available", classes="terminal-text-muted")
    
    def _compose_quest_list(self) -> ComposeResult:
        """Compose the quest list with terminal styling."""
        with VerticalScroll(id="quest-list-container"):
            # Quest count display
            count_text = f"Showing {len(self.filtered_tasks)} of {len(self.all_tasks)} quests"
            yield Static(count_text, classes="terminal-text-muted", id="quest-count")
            
            # Quest list items
            with Container(id="quest-list"):
                for task in self.filtered_tasks:
                    yield TerminalQuestListItem(task)
    
    def _compose_quest_details(self) -> ComposeResult:
        """Compose the detailed quest view panel."""
        if self.selected_task:
            yield self._render_quest_details(self.selected_task)
        else:
            with Vertical():
                yield Static("Select a quest to view details", classes="terminal-text-muted")
                yield Static("", classes="terminal-text")
                yield Static("Use ↑/↓ to navigate quests", classes="terminal-text-muted")
                yield Static("Press Enter to view details", classes="terminal-text-muted")
    
    def _render_quest_details(self, task: Task) -> ComposeResult:
        """Render comprehensive quest information with terminal styling."""
        # Quest header with status and priority indicators
        with Container(classes="quest-detail-header"):
            status_symbol = self._get_status_symbol(task.status)
            yield Static(f"{status_symbol} {task.title}", classes="terminal-title")
            
            # Status badges row
            with Horizontal(classes="quest-badges"):
                yield StatusBadge(task.status)
                yield PriorityIndicator(task.priority, show_text=True)
                yield DifficultyIndicator(task.difficulty, show_xp=True)
        
        # Quest metadata panel
        with TerminalPanel(title="Quest Information", scrollable=False):
            # XP reward prominently displayed
            yield Static(f"🏆 XP Reward: {task.xp_reward}", classes="xp-value")
            
            # Time information
            created_date = task.created_at.strftime("%Y-%m-%d %H:%M")
            yield Static(f"📅 Created: {created_date}", classes="terminal-text")
            
            if task.status == TaskStatus.COMPLETED and hasattr(task, 'completed_at'):
                completed_date = task.completed_at.strftime("%Y-%m-%d %H:%M")
                yield Static(f"✅ Completed: {completed_date}", classes="terminal-text")
            
            # Estimated time if available
            if hasattr(task, 'estimated_time') and task.estimated_time:
                yield Static(f"⏱️ Estimated Time: {task.estimated_time}", classes="terminal-text")
            
            # File paths if available
            if hasattr(task, 'file_paths') and task.file_paths:
                yield Static("📁 Files:", classes="terminal-highlight")
                for file_path in task.file_paths:
                    yield Static(f"  • {file_path}", classes="terminal-text-muted")
        
        # Description panel
        if task.description:
            with TerminalPanel(title="Description", scrollable=True):
                yield Static(task.description, classes="terminal-text")
        
        # Tags panel
        if task.tags:
            with TerminalPanel(title="Tags", scrollable=False):
                with Horizontal(classes="tag-display"):
                    for tag in task.tags:
                        yield Button(f"#{tag}", classes="tag-display-button")
        
        # Dependencies panel (if available)
        if hasattr(task, 'dependencies') and task.dependencies:
            with TerminalPanel(title="Dependencies", scrollable=False):
                for dep in task.dependencies:
                    yield Static(f"• {dep}", classes="terminal-text")
        
        # Assignee information (if available)
        if hasattr(task, 'assignee') and task.assignee:
            with TerminalPanel(title="Assignment", scrollable=False):
                yield Static(f"👤 Assignee: {task.assignee}", classes="terminal-text")
        
        # Notes panel
        if task.notes:
            with TerminalPanel(title="Notes", scrollable=True):
                yield Static(task.notes, classes="terminal-text")
        
        # Creation history panel
        with TerminalPanel(title="History", scrollable=False):
            yield Static(f"📝 Created: {created_date}", classes="terminal-text-muted")
            
            # Priority changes (if tracked)
            if hasattr(task, 'priority_history') and task.priority_history:
                yield Static("Priority changes:", classes="terminal-text-muted")
                for change in task.priority_history[-3:]:  # Show last 3 changes
                    yield Static(f"  • {change}", classes="terminal-text-muted")
            
            # Work start times (if tracked)
            if hasattr(task, 'work_sessions') and task.work_sessions:
                yield Static("Recent work sessions:", classes="terminal-text-muted")
                for session in task.work_sessions[-3:]:  # Show last 3 sessions
                    yield Static(f"  • {session}", classes="terminal-text-muted")
        
        # Action buttons panel
        with TerminalPanel(title="Actions", scrollable=False):
            with Horizontal(classes="action-buttons"):
                if task.status != TaskStatus.COMPLETED:
                    yield Button("✅ Complete", action="complete_task", classes="primary-button")
                    if task.status == TaskStatus.PENDING:
                        yield Button("▶️ Start", action="start_task", classes="primary-button")
                    elif task.status == TaskStatus.ACTIVE:
                        yield Button("⏸️ Pause", action="pause_task", classes="secondary-button")
                
                yield Button("✏️ Edit", action="edit_task", classes="secondary-button")
                yield Button("🗑️ Delete", action="delete_task", classes="secondary-button")
                
                # Additional actions
                if task.status == TaskStatus.BLOCKED:
                    yield Button("🔓 Unblock", action="unblock_task", classes="primary-button")
    
    def _get_status_symbol(self, status: TaskStatus) -> str:
        """Get the terminal symbol for the task status."""
        symbols = {
            TaskStatus.PENDING: self.ascii_generator.theme.ascii_chars.get('circle', '●'),
            TaskStatus.ACTIVE: self.ascii_generator.theme.ascii_chars.get('arrow_right', '→'),
            TaskStatus.COMPLETED: self.ascii_generator.theme.ascii_chars.get('star', '★'),
            TaskStatus.BLOCKED: self.ascii_generator.theme.ascii_chars.get('square', '■')
        }
        return symbols.get(status, '●')

    def _compose_filter_panel(self) -> ComposeResult:
        """Compose the filter and sort panel."""
        with Container(classes="filter-panel"):
            yield Label("Filters & Sort", classes="panel-header")
            
            with Container(classes="panel-content"):
                # Search
                yield Label("Search:", classes="filter-label")
                yield Input(placeholder="Search tasks...", id="search-input")
                
                # Status filter
                yield Label("Status:", classes="filter-label")
                yield Select(
                    options=[
                        ("all", "All Statuses"),
                        ("pending", "Pending"),
                        ("active", "Active"),
                        ("completed", "Completed"),
                        ("blocked", "Blocked")
                    ],
                    value="all",
                    id="status-filter"
                )
                
                # Difficulty filter
                yield Label("Difficulty:", classes="filter-label")
                yield Select(
                    options=[
                        ("all", "All Difficulties"),
                        ("easy", "Easy"),
                        ("medium", "Medium"),
                        ("hard", "Hard")
                    ],
                    value="all",
                    id="difficulty-filter"
                )
                
                # Priority filter
                yield Label("Priority:", classes="filter-label")
                yield Select(
                    options=[
                        ("all", "All Priorities"),
                        ("low", "Low"),
                        ("medium", "Medium"),
                        ("high", "High"),
                        ("critical", "Critical")
                    ],
                    value="all",
                    id="priority-filter"
                )
                
                # Sort options
                yield Label("Sort by:", classes="filter-label")
                yield Select(
                    options=[
                        ("priority", "Priority"),
                        ("difficulty", "Difficulty"),
                        ("created", "Created Date"),
                        ("title", "Title")
                    ],
                    value="priority",
                    id="sort-select"
                )
                
                # Action buttons
                yield Button("Apply Filters", action="apply_filters", classes="filter-button")
                yield Button("Clear Filters", action="clear_filters", classes="filter-button")

    def _compose_task_list(self) -> ComposeResult:
        """Compose the task list panel."""
        with Container(classes="task-list-panel"):
            yield Label("Tasks", classes="panel-header")
            
            with Container(classes="panel-content"):
                # Task count
                yield Label(f"Showing {len(self.filtered_tasks)} of {len(self.all_tasks)} tasks", 
                           classes="task-count")
                
                # Task list
                yield ListView(
                    *[TaskListItem(task) for task in self.filtered_tasks],
                    classes="task-list"
                )

    def _compose_task_details(self) -> ComposeResult:
        """Compose the task details panel."""
        with Container(classes="task-details-panel"):
            yield Label("Task Details", classes="panel-header")
            
            with Container(classes="panel-content"):
                if self.selected_task:
                    yield self._render_task_details(self.selected_task)
                else:
                    yield Label("Select a task to view details", classes="no-selection")

    def _render_task_details(self, task: Task) -> ComposeResult:
        """Render detailed information about a selected task."""
        yield Label(task.title, classes="task-title")
        yield Label(f"Status: {task.status.value}", classes="task-meta")
        yield Label(f"Priority: {task.priority.value}", classes="task-meta")
        yield Label(f"Difficulty: {task.difficulty.value}", classes="task-meta")
        yield Label(f"XP Reward: {task.xp_reward}", classes="task-meta")
        yield Label(f"Created: {task.created_date}", classes="task-meta")
        
        if task.notes:
            yield Label("Notes:", classes="task-meta")
            yield Label(task.notes, classes="task-notes")
        
        if task.tags:
            yield Label(f"Tags: {', '.join(task.tags)}", classes="task-meta")

    def on_mount(self) -> None:
        """Handle screen mount event."""
        self.refresh_tasks()

    def refresh_tasks(self) -> None:
        """Refresh the task list from the data manager."""
        try:
            # Load all tasks
            self.all_tasks = self.data_manager.tasks.copy()
            
            # Apply current filters
            self._apply_filters()
            
            # Update the quest list
            self._update_quest_list()
            
            # Update quest count
            self._update_quest_count()
            
            # Update status
            self.feedback_system.show_info(f"Loaded {len(self.filtered_tasks)} quests")
            
        except Exception as e:
            self.feedback_system.show_error(f"Error refreshing quests: {e}")
    
    def _update_quest_list(self) -> None:
        """Update the quest list display."""
        try:
            quest_list_container = self.query_one("#quest-list", Container)
            quest_list_container.remove_children()
            
            for i, task in enumerate(self.filtered_tasks):
                quest_item = TerminalQuestListItem(task)
                if i == self.selected_index and self.selected_task:
                    quest_item.set_selected(True)
                quest_list_container.mount(quest_item)
        except Exception as e:
            self.feedback_system.show_error(f"Error updating quest list: {e}")
    
    def _update_quest_count(self) -> None:
        """Update the quest count display."""
        try:
            count_text = f"Showing {len(self.filtered_tasks)} of {len(self.all_tasks)} quests"
            count_widget = self.query_one("#quest-count", Static)
            count_widget.update(count_text)
        except:
            pass

    def _apply_filters(self) -> None:
        """Apply current filters to the task list with enhanced search functionality."""
        self.filtered_tasks = self.all_tasks.copy()
        
        # Apply filter based on current tab
        if self.current_filter == "today":
            today = date.today()
            self.filtered_tasks = [
                task for task in self.filtered_tasks
                if (task.status in [TaskStatus.ACTIVE, TaskStatus.PENDING] and
                    (task.created_at.date() == today or 
                     task.status == TaskStatus.ACTIVE))  # Include active tasks regardless of date
            ]
        elif self.current_filter == "completed":
            self.filtered_tasks = [
                task for task in self.filtered_tasks
                if task.status == TaskStatus.COMPLETED
            ]
        elif self.current_filter == "by-tag":
            if self.selected_tag:
                tag_query = self.selected_tag.lower().strip()
                if tag_query:
                    self.filtered_tasks = [
                        task for task in self.filtered_tasks
                        if any(tag_query in tag.lower() for tag in task.tags)
                    ]
        
        # Apply general search filter (works across all tabs)
        if self.search_query:
            query = self.search_query.lower().strip()
            if query:
                self.filtered_tasks = [
                    task for task in self.filtered_tasks
                    if (query in task.title.lower() or 
                        query in task.description.lower() or
                        any(query in tag.lower() for tag in task.tags) or
                        query in task.notes.lower() if task.notes else False)
                ]
        
        # Apply sorting (priority-based by default)
        self._sort_tasks()
        
        # Update filter statistics
        self._update_filter_stats()
    
    def _update_filter_stats(self) -> None:
        """Update filter statistics display."""
        total_tasks = len(self.all_tasks)
        filtered_count = len(self.filtered_tasks)
        
        # Calculate statistics by filter type
        stats_text = f"Showing {filtered_count} of {total_tasks} quests"
        
        if self.current_filter == "today":
            active_today = len([t for t in self.filtered_tasks if t.status == TaskStatus.ACTIVE])
            pending_today = len([t for t in self.filtered_tasks if t.status == TaskStatus.PENDING])
            stats_text += f" ({active_today} active, {pending_today} pending)"
        elif self.current_filter == "completed":
            total_xp = sum(task.xp_reward for task in self.filtered_tasks)
            stats_text += f" (Total XP earned: {total_xp})"
        elif self.current_filter == "by-tag" and self.selected_tag:
            stats_text += f" with tag '#{self.selected_tag}'"
        
        # Update the display
        try:
            count_widget = self.query_one("#quest-count", Static)
            count_widget.update(stats_text)
        except:
            pass

    def _sort_tasks(self) -> None:
        """Sort tasks with priority-based sorting for terminal display."""
        # Sort by priority (high to low), then by XP reward (high to low), then by creation date (newest first)
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        
        self.filtered_tasks.sort(key=lambda t: (
            priority_order.get(t.priority.name, 4),  # Priority first
            -t.xp_reward,  # Higher XP first
            -t.created_at.timestamp()  # Newer tasks first
        ))

    def on_terminal_quest_list_item_quest_selected(self, event: TerminalQuestListItem.QuestSelected) -> None:
        """Handle quest selection in the list."""
        self.selected_task = event.task
        # Find the index of the selected task
        for i, task in enumerate(self.filtered_tasks):
            if task.id == self.selected_task.id:
                self.selected_index = i
                break
        
        # Update selection display
        self._update_selection_display()
        self.refresh()
    
    def _update_selection_display(self) -> None:
        """Update the visual selection in the quest list."""
        try:
            quest_items = self.query(TerminalQuestListItem)
            for i, item in enumerate(quest_items):
                item.set_selected(i == self.selected_index)
        except:
            pass

    def action_filter_today(self) -> None:
        """Filter to show today's quests."""
        self.current_filter = "today"
        self._update_tab_buttons("tab-today")
        self._hide_tag_filter()
        self._apply_filters()
        self._update_quest_list()
        self._update_quest_count()
        self.feedback_system.show_info("Showing today's active quests")
    
    def action_filter_all(self) -> None:
        """Filter to show all quests."""
        self.current_filter = "all"
        self._update_tab_buttons("tab-all")
        self._hide_tag_filter()
        self._apply_filters()
        self._update_quest_list()
        self._update_quest_count()
        self.feedback_system.show_info("Showing all quests")
    
    def action_filter_completed(self) -> None:
        """Filter to show completed quests."""
        self.current_filter = "completed"
        self._update_tab_buttons("tab-completed")
        self._hide_tag_filter()
        self._apply_filters()
        self._update_quest_list()
        self._update_quest_count()
        self.feedback_system.show_info("Showing completed quests")
    
    def action_filter_by_tag(self) -> None:
        """Filter quests by tag."""
        self.current_filter = "by-tag"
        self._update_tab_buttons("tab-by-tag")
        self._show_tag_filter()
        self._apply_filters()
        self._update_quest_list()
        self._update_quest_count()
        # Focus on the tag search input
        try:
            tag_input = self.query_one("#tag-search", Input)
            tag_input.focus()
        except:
            pass
        self.feedback_system.show_info("Enter tag to filter by")
    
    def _update_tab_buttons(self, active_tab_id: str) -> None:
        """Update the visual state of tab buttons."""
        tab_ids = ["tab-today", "tab-all", "tab-completed", "tab-by-tag"]
        for tab_id in tab_ids:
            try:
                button = self.query_one(f"#{tab_id}", Button)
                if tab_id == active_tab_id:
                    button.add_class("active")
                else:
                    button.remove_class("active")
            except:
                pass
    
    def _show_tag_filter(self) -> None:
        """Show the tag filter container."""
        try:
            container = self.query_one("#tag-filter-container", Container)
            container.remove_class("hidden")
        except:
            pass
    
    def _hide_tag_filter(self) -> None:
        """Hide the tag filter container."""
        try:
            container = self.query_one("#tag-filter-container", Container)
            container.add_class("hidden")
        except:
            pass
    
    def action_view_details(self) -> None:
        """View details of the selected quest."""
        if not self.selected_task:
            self.feedback_system.show_warning("Please select a quest to view details")
            return
        
        # Refresh the details panel
        self.refresh()
    
    def on_mount(self) -> None:
        """Handle screen mount event."""
        self.refresh_tasks()
        # Select first task if available
        if self.filtered_tasks:
            self.selected_task = self.filtered_tasks[0]
            self.selected_index = 0
            self._update_selection_display()
    
    def action_back(self) -> None:
        """Go back to the previous screen."""
        self.app.pop_screen()

    def action_complete_task(self) -> None:
        """Complete the selected quest."""
        if not self.selected_task:
            self.feedback_system.show_warning("Please select a quest to complete")
            return
        
        if self.selected_task.status == TaskStatus.COMPLETED:
            self.feedback_system.show_warning("Quest is already completed")
            return
        
        # Mark task as completed
        self.selected_task.status = TaskStatus.COMPLETED
        self.selected_task.completed = True
        
        # Set completion time if supported
        if hasattr(self.selected_task, 'completed_at'):
            self.selected_task.completed_at = datetime.now()
        
        # Calculate XP earned
        xp_earned = self.selected_task.xp_reward
        
        # Update player stats
        player = self.data_manager.player
        player.total_xp += xp_earned
        player.tasks_completed += 1
        
        # Save data
        self.data_manager.save_data()
        
        # Show completion feedback
        self.feedback_system.show_success(
            f"Quest completed! 🏆 +{xp_earned} XP earned"
        )
        
        # Refresh the quest list and details
        self.refresh_tasks()
        self.refresh()
    
    def action_start_task(self) -> None:
        """Start working on the selected quest."""
        if not self.selected_task:
            self.feedback_system.show_warning("Please select a quest to start")
            return
        
        if self.selected_task.status == TaskStatus.ACTIVE:
            self.feedback_system.show_warning("Quest is already active")
            return
        
        # Set task as active
        self.selected_task.status = TaskStatus.ACTIVE
        
        # Track work session start if supported
        if hasattr(self.selected_task, 'work_sessions'):
            if not self.selected_task.work_sessions:
                self.selected_task.work_sessions = []
            self.selected_task.work_sessions.append(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Save data
        self.data_manager.save_data()
        
        # Show feedback
        self.feedback_system.show_success(f"Started working on: {self.selected_task.title}")
        
        # Refresh display
        self.refresh_tasks()
        self.refresh()
    
    def action_pause_task(self) -> None:
        """Pause the selected quest."""
        if not self.selected_task:
            self.feedback_system.show_warning("Please select a quest to pause")
            return
        
        if self.selected_task.status != TaskStatus.ACTIVE:
            self.feedback_system.show_warning("Quest is not currently active")
            return
        
        # Set task as pending
        self.selected_task.status = TaskStatus.PENDING
        
        # Track work session pause if supported
        if hasattr(self.selected_task, 'work_sessions'):
            if not self.selected_task.work_sessions:
                self.selected_task.work_sessions = []
            self.selected_task.work_sessions.append(f"Paused: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Save data
        self.data_manager.save_data()
        
        # Show feedback
        self.feedback_system.show_info(f"Paused work on: {self.selected_task.title}")
        
        # Refresh display
        self.refresh_tasks()
        self.refresh()
    
    def action_unblock_task(self) -> None:
        """Unblock the selected quest."""
        if not self.selected_task:
            self.feedback_system.show_warning("Please select a quest to unblock")
            return
        
        if self.selected_task.status != TaskStatus.BLOCKED:
            self.feedback_system.show_warning("Quest is not currently blocked")
            return
        
        # Set task as pending
        self.selected_task.status = TaskStatus.PENDING
        
        # Save data
        self.data_manager.save_data()
        
        # Show feedback
        self.feedback_system.show_success(f"Unblocked quest: {self.selected_task.title}")
        
        # Refresh display
        self.refresh_tasks()
        self.refresh()

    def action_edit_task(self) -> None:
        """Edit the selected task."""
        if not self.selected_task:
            self.feedback_system.show_warning("Please select a task to edit")
            return
        
        from .edit_task_screen import EditTaskScreen
        self.app.push_screen(EditTaskScreen(self.data_manager, self.selected_task))

    def action_delete_task(self) -> None:
        """Delete the selected task."""
        if not self.selected_task:
            self.feedback_system.show_warning("Please select a task to delete")
            return
        
        # Post message for testability
        self.post_message(self.DeleteTaskRequested(self.selected_task))
        
        # Show confirmation dialog
        self.app.push_screen(TaskDeletionDialog(self.selected_task))

    def action_new_task(self) -> None:
        """Create a new task."""
        from .add_task_screen import AddTaskScreen
        self.app.push_screen(AddTaskScreen(self.data_manager))

    def action_refresh(self) -> None:
        """Refresh the task list."""
        self.refresh_tasks()

    def action_toggle_sort(self) -> None:
        """Toggle between sort options."""
        sort_options = ["priority", "difficulty", "created", "title"]
        current_index = sort_options.index(self.sort_by)
        next_index = (current_index + 1) % len(sort_options)
        self.sort_by = sort_options[next_index]
        self._apply_filters()
        self.refresh()

    def action_toggle_filter(self) -> None:
        """Toggle filter panel visibility."""
        self.show_filters = not self.show_filters
        filter_panel = self.query_one(".filter-panel", Container)
        if filter_panel:
            filter_panel.styles.display = "block" if self.show_filters else "none"

    def action_select_previous(self) -> None:
        """Select the previous quest in the list."""
        if self.filtered_tasks and self.selected_index > 0:
            self.selected_index -= 1
            self.selected_task = self.filtered_tasks[self.selected_index]
            self._update_selection_display()
            self.refresh()

    def action_select_next(self) -> None:
        """Select the next quest in the list."""
        if self.filtered_tasks and self.selected_index < len(self.filtered_tasks) - 1:
            self.selected_index += 1
            self.selected_task = self.filtered_tasks[self.selected_index]
            self._update_selection_display()
            self.refresh()

    def action_activate_task(self) -> None:
        """Activate/deactivate the selected task."""
        if not self.selected_task:
            return
        
        if self.selected_task.status == TaskStatus.ACTIVE:
            self.selected_task.status = TaskStatus.PENDING
            self.feedback_system.show_info("Task deactivated")
        elif self.selected_task.status == TaskStatus.PENDING:
            self.selected_task.status = TaskStatus.ACTIVE
            self.feedback_system.show_info("Task activated")
        
        # Save data
        self.data_manager.save_data()
        
        # Refresh the display
        self.refresh()

    def action_apply_filters(self) -> None:
        """Apply the current filter settings."""
        # Get values from form controls
        search_input = self.query_one("#search-input", Input)
        if search_input:
            self.search_query = search_input.value
        
        status_filter = self.query_one("#status-filter", Select)
        if status_filter:
            self.filter_status = status_filter.value
        
        difficulty_filter = self.query_one("#difficulty-filter", Select)
        if difficulty_filter:
            self.filter_difficulty = difficulty_filter.value
        
        priority_filter = self.query_one("#priority-filter", Select)
        if priority_filter:
            self.filter_priority = priority_filter.value
        
        sort_select = self.query_one("#sort-select", Select)
        if sort_select:
            self.sort_by = sort_select.value
        
        # Apply filters
        self._apply_filters()
        self.refresh()
        
        self.feedback_system.show_info("Filters applied")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes for search and tag filtering."""
        if event.input.id == "general-search":
            self.search_query = event.value
            self._apply_filters()
            self._update_quest_list()
            self._update_quest_count()
        elif event.input.id == "tag-search":
            self.selected_tag = event.value
            if self.current_filter == "by-tag":
                self._apply_filters()
                self._update_quest_list()
                self._update_quest_count()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses for tag selection."""
        button_id = event.button.id
        if button_id and button_id.startswith("select_tag_"):
            tag = button_id.replace("select_tag_", "")
            self.selected_tag = tag
            # Update the tag search input
            try:
                tag_input = self.query_one("#tag-search", Input)
                tag_input.value = tag
            except:
                pass
            
            if self.current_filter == "by-tag":
                self._apply_filters()
                self._update_quest_list()
                self._update_quest_count()
                self.feedback_system.show_info(f"Filtering by tag: #{tag}")
    
    def _get_available_tags(self) -> List[str]:
        """Get all available tags from tasks."""
        all_tags = set()
        for task in self.all_tasks:
            all_tags.update(task.tags)
        return sorted(all_tags)

    def _handle_error(self, error: Exception, context: str = "Unknown") -> None:
        """Handle errors with user-friendly messages."""
        error_message = str(error)
        
        if "validation error" in error_message.lower() or "invalid" in error_message.lower():
            self._update_status_message(f"Validation error: {error_message}", error=True)
        elif "not found" in error_message.lower():
            self._update_status_message(f"Task not found: {error_message}", error=True)
        elif "permission" in error_message.lower() or "access" in error_message.lower():
            self._update_status_message(f"Permission denied: {error_message}", error=True)
        else:
            self._update_status_message(f"Error in {context}: {error_message}", error=True)

    def _update_status_message(self, message: str, error: bool = False) -> None:
        """Update the status message in the footer."""
        footer = self.query_one(Footer)
        if footer:
            if error:
                footer.update(f"Error: {message}")
            else:
                footer.update(message)

    # Custom messages for testability
    class DeleteTaskRequested(Message):
        """Message sent when task deletion is requested."""
        def __init__(self, task: Task):
            super().__init__()
            self.task = task