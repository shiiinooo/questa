"""HomeScreen - Main dashboard for QUESTA application."""

from typing import List, Optional
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button, Header, Footer, Label, ListView, Static, 
    ProgressBar, TabbedContent, TabPane
)
from textual.binding import Binding
from textual.message import Message

from ..models.task import Task
from ..models.enums import TaskStatus, TaskDifficulty, TaskPriority
from ..data.data_manager import DataManager
from ..widgets.task_list_item import TaskListItem
from ..widgets.status_badge import StatusBadge
from ..widgets.priority_indicator import PriorityIndicator
from ..widgets.feedback_system import FeedbackSystem


class HomeScreen(Screen):
    """Main dashboard with task overview and management."""

    BINDINGS = [
        Binding("q", "show_quests", "Quests", show=True),
        Binding("a", "add_task", "Add Task", show=True),
        Binding("l", "show_leveling", "Stats", show=True),
        Binding("enter", "complete_task", "Complete", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("escape", "quit", "Quit", show=True),
    ]

    def __init__(self, data_manager: DataManager, **kwargs):
        """Initialize the home screen."""
        super().__init__(**kwargs)
        self.data_manager = data_manager
        self.active_tasks: List[Task] = []
        self.selected_task: Optional[Task] = None
        self.feedback_system = FeedbackSystem()

    def compose(self) -> ComposeResult:
        """Compose the home screen layout."""
        # Header with player info
        yield Header(show_clock=True)
        
        # Main content area
        with Container(classes="tui-content"):
            # Left sidebar with player stats
            with Container(classes="tui-sidebar"):
                yield from self._compose_player_panel()
                yield from self._compose_quick_actions()
            
            # Main content area
            with Container(classes="tui-main"):
                yield from self._compose_task_overview()
                yield from self._compose_task_details()
        
        # Footer with shortcuts
        yield Footer()
        
        # Feedback system
        yield self.feedback_system

    def _compose_player_panel(self) -> ComposeResult:
        """Compose the player stats panel."""
        player = self.data_manager.load_player_data()
        
        with Container(classes="player-panel"):
            yield Label("Player Stats", classes="panel-header")
            
            with Container(classes="panel-content"):
                yield Label(f"Level: {player.level}", classes="player-info")
                yield Label(f"Total XP: {player.total_xp}", classes="player-info")
                
                # XP Progress
                current_level_xp = player.current_level_xp
                xp_for_next_level = player.xp_for_next_level - player.xp_for_current_level
                progress_percent = (player.level_progress * 100) if player.level_progress > 0 else 0
                
                yield Label(f"XP: {current_level_xp}/{xp_for_next_level}", classes="player-info")
                yield ProgressBar(total=xp_for_next_level, value=current_level_xp, show_fraction=False)
                yield Label(f"{progress_percent:.1f}% to next level", classes="player-info")
                
                yield Label(f"Tasks Completed: {player.tasks_completed}", classes="player-info")
                yield Label(f"Current Streak: {player.current_streak} days", classes="player-info")

    def _compose_quick_actions(self) -> ComposeResult:
        """Compose the quick actions panel."""
        with Container(classes="actions-panel"):
            yield Label("Quick Actions", classes="panel-header")
            
            with Container(classes="panel-content"):
                yield Button("View Quests (Q)", action="show_quests", classes="action-button")
                yield Button("Add Task (A)", action="add_task", classes="action-button")
                yield Button("Complete Task (Enter)", action="complete_task", classes="action-button")
                yield Button("Refresh (R)", action="refresh", classes="action-button")

    def _compose_task_overview(self) -> ComposeResult:
        """Compose the task overview panel."""
        with Container(classes="task-overview"):
            yield Label("Active Tasks", classes="panel-header")
            
            with Container(classes="panel-content"):
                # Task list
                yield ListView(
                    *[TaskListItem(task) for task in self.active_tasks],
                    classes="task-list"
                )

    def _compose_task_details(self) -> ComposeResult:
        """Compose the task details panel."""
        with Container(classes="task-details"):
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
            # Get active tasks (not completed)
            all_tasks = self.data_manager.load_tasks()
            self.active_tasks = [task for task in all_tasks.values() if not task.completed]
            
            # Sort by priority (LOW<MEDIUM<HIGH<CRITICAL) and creation date (newest first)
            priority_order = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
            self.active_tasks.sort(key=lambda t: (
                priority_order.index(t.priority.name) if t.priority.name in priority_order else len(priority_order),
                -t.created_at.timestamp()
            ))
            
            # Update the task list
            task_list = self.query_one(".task-list", ListView)
            if task_list:
                task_list.clear()
                for task in self.active_tasks:
                    task_list.append(TaskListItem(task))
            
            # Update status
            self._update_status_message(f"Loaded {len(self.active_tasks)} active tasks")
            
        except Exception as e:
            self._update_status_message(f"Error refreshing tasks: {e}", error=True)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle task selection in the list."""
        if event.item and isinstance(event.item, TaskListItem):
            self.selected_task = event.item.task
            self.refresh()

    def update_details_panel(self, task: Task) -> None:
        """Update the details panel with a specific task."""
        self.selected_task = task
        self.refresh()

    def action_show_quests(self) -> None:
        """Navigate to the quests screen."""
        from .quests_screen import QuestsScreen
        self.app.push_screen(QuestsScreen(self.data_manager))

    def action_show_leveling(self) -> None:
        """Show character stats and achievements screen."""
        from .character_stats_screen import CharacterStatsScreen
        self.app.push_screen(CharacterStatsScreen())

    def action_show_journal(self) -> None:
        """Show activity journal."""
        # TODO: Implement journal screen
        self.feedback_system.show_info("Journal screen coming soon!")

    def action_add_task(self) -> None:
        """Open the add task screen."""
        from .add_task_screen import AddTaskScreen
        self.app.push_screen(AddTaskScreen(self.data_manager))

    def action_complete_task(self) -> None:
        """Complete the selected task."""
        if not self.selected_task:
            self.feedback_system.show_warning("Please select a task to complete")
            return
        
        if self.selected_task.status == TaskStatus.COMPLETED:
            self.feedback_system.show_warning("Task is already completed")
            return
        
        # Mark task as completed
        self.selected_task.status = TaskStatus.COMPLETED
        self.selected_task.completed = True
        
        # Calculate XP earned
        xp_earned = self.selected_task.xp_reward
        
        # Update player stats
        player = self.data_manager.load_player_data()
        player.total_xp += xp_earned
        player.tasks_completed += 1
        
        # Save data
        self.data_manager.save_player_data(player)
        
        # Show completion feedback
        self.feedback_system.show_success(
            f"Task completed! +{xp_earned} XP earned"
        )
        
        # Refresh the task list
        self.refresh_tasks()
        self.selected_task = None

    def on_task_added(self, task: Optional[Task]) -> None:
        """Handle task creation events."""
        if task:
            self.feedback_system.show_success(f"Task '{task.title}' created successfully!")
            self.refresh_tasks()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def _update_status_message(self, message: str, error: bool = False) -> None:
        """Update the status message in the footer."""
        footer = self.query_one(Footer)
        if footer:
            if error:
                footer.update(f"Error: {message}")
            else:
                footer.update(message)