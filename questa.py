#!/usr/bin/env python3
"""
QUESTA - A Professional TUI Task Manager
Enhanced with LazyVim/LazyGit inspired design
"""

import json
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    ProgressBar,
    Select,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
)


# Data Models
class TaskDifficulty(Enum):
    EASY = ("Easy", 15)
    MEDIUM = ("Medium", 30)
    HARD = ("Hard", 50)

    def __init__(self, label: str, xp: int):
        self.label = label
        self.xp = xp


class TaskStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class Priority(Enum):
    LOW = ("Low", "#9aa0b0")
    MEDIUM = ("Medium", "#ffc107")
    HIGH = ("High", "#f44336")
    CRITICAL = ("Critical", "#f44336")

    def __init__(self, label: str, color: str):
        self.label = label
        self.color = color


@dataclass
class Task:
    id: str
    title: str
    difficulty: TaskDifficulty
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM
    completed: bool = False
    created_date: str = ""
    completed_date: Optional[str] = None
    notes: str = ""
    tags: List[str] = None
    file_path: str = ""
    estimated_time: str = ""

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class PlayerData:
    name: str = "CodeWarrior_42"
    level: int = 5
    total_xp: int = 650
    current_streak: int = 7
    tasks_completed: int = 23
    bugs_fixed: int = 12
    last_active_date: str = ""


class DataManager:
    """Handles saving/loading player data and tasks"""

    def __init__(self):
        self.data_file = "questa_data.json"
        self.player = PlayerData()
        self.tasks: List[Task] = []
        self.load_data()
        self._ensure_demo_data()

    def _ensure_demo_data(self):
        """Ensure we have some demo data for showcase"""
        if not self.tasks:
            demo_tasks = [
                Task(
                    id="1",
                    title="Fix auth bug",
                    difficulty=TaskDifficulty.HARD,
                    status=TaskStatus.ACTIVE,
                    priority=Priority.HIGH,
                    created_date="2025-08-05",
                    notes="Login validation failing for special characters",
                    tags=["bug", "auth", "critical"],
                    file_path="src/auth.py",
                    estimated_time="2-3 hours",
                ),
                Task(
                    id="2",
                    title="Write API tests",
                    difficulty=TaskDifficulty.MEDIUM,
                    status=TaskStatus.PENDING,
                    priority=Priority.MEDIUM,
                    created_date="2025-08-04",
                    tags=["testing"],
                    file_path="tests/api/",
                    estimated_time="1-2 hours",
                ),
                Task(
                    id="3",
                    title="Update documentation",
                    difficulty=TaskDifficulty.EASY,
                    status=TaskStatus.PENDING,
                    priority=Priority.LOW,
                    created_date="2025-08-03",
                    tags=["docs"],
                    file_path="README.md",
                    estimated_time="30 minutes",
                ),
            ]
            self.tasks.extend(demo_tasks)
            self.save_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    self.player = PlayerData(**data.get("player", {}))

                    tasks_data = data.get("tasks", [])
                    self.tasks = []
                    for task_data in tasks_data:
                        # Convert enum strings back to enums
                        task_data["difficulty"] = TaskDifficulty[
                            task_data["difficulty"]
                        ]
                        task_data["status"] = TaskStatus[task_data["status"]]
                        task_data["priority"] = Priority[task_data["priority"]]
                        self.tasks.append(Task(**task_data))
            except Exception as e:
                print(f"Error loading data: {e}")

    def save_data(self):
        try:
            tasks_data = []
            for task in self.tasks:
                task_dict = asdict(task)
                task_dict["difficulty"] = task.difficulty.name
                task_dict["status"] = task.status.name
                task_dict["priority"] = task.priority.name
                tasks_data.append(task_dict)

            data = {"player": asdict(self.player), "tasks": tasks_data}

            with open(self.data_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving data: {e}")

    def get_xp_for_next_level(self) -> int:
        """XP needed for next level"""
        return 1000  # Simplified for demo

    def get_current_level_progress(self) -> tuple[int, int]:
        """Returns (current_progress, total_needed)"""
        total_needed = self.get_xp_for_next_level()
        current_progress = self.player.total_xp % total_needed
        return (current_progress, total_needed)


# Enhanced Widgets
class StatusIndicator(Static):
    """Status dot indicator"""

    def __init__(self, status: TaskStatus):
        self.status = status
        status_symbols = {
            TaskStatus.PENDING: "●",
            TaskStatus.ACTIVE: "●",
            TaskStatus.COMPLETED: "●",
            TaskStatus.BLOCKED: "●",
        }
        super().__init__(status_symbols[status], classes=f"status-{status.value}")


class PriorityBar(Static):
    """Priority indicator bar"""

    def __init__(self, priority: Priority):
        super().__init__("", classes=f"priority-{priority.name.lower()}")


class TaskListItemEnhanced(ListItem):
    """Enhanced task list item with status and priority indicators"""

    def __init__(self, task: Task):
        self.task_data = task

        # Create status indicator
        status_indicator = StatusIndicator(task.status)

        # Create task info
        task_info = Static(
            f"{task.title}\n{task.file_path}" if task.file_path else task.title,
            classes="task-info",
        )

        # Create difficulty badge
        badge_class = f"badge-{task.difficulty.name.lower()}"
        difficulty_badge = Static(
            f"{task.difficulty.name[0]}", classes=f"difficulty-badge {badge_class}"
        )

        # Create XP indicator
        xp_label = Static(f"{task.difficulty.xp} XP", classes="xp-label")

        super().__init__(
            Horizontal(
                PriorityBar(task.priority),
                status_indicator,
                task_info,
                Vertical(difficulty_badge, xp_label, classes="task-meta"),
                classes="task-item-content",
            )
        )


# Screens
class WelcomeScreen(Screen):
    """Welcome/Splash screen"""

    BINDINGS = [
        Binding("enter", "continue", "Continue", priority=True),
        Binding("escape", "quit", "Quit"),
    ]

    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.data_manager = data_manager

    def compose(self) -> ComposeResult:
        yield Container(
            Static(
                """
 ██████╗ ██╗   ██╗███████╗███████╗████████╗ █████╗ 
██╔═══██╗██║   ██║██╔════╝██╔════╝╚══██╔══╝██╔══██╗
██║   ██║██║   ██║█████╗  █████╗     ██║   ███████║
██║▄▄ ██║██║   ██║██╔══╝  ██╔══╝     ██║   ██╔══██║
╚██████╔╝╚██████╔╝███████╗███████╗   ██║   ██║  ██║
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝
        """,
                id="logo",
            ),
            Static("Press Enter to begin your quest!", classes="center"),
            id="welcome-container",
        )

    def action_continue(self):
        self.app.push_screen(HomeScreen(self.data_manager))

    def action_quit(self):
        self.app.exit()


class HomeScreen(Screen):
    """Enhanced main dashboard with sidebar layout"""

    BINDINGS = [
        Binding("q", "show_quests", "Quests", show=True),
        Binding("l", "show_leveling", "Levels", show=True),
        Binding("j", "show_journal", "Journal", show=True),
        Binding("a", "add_task", "Add", show=True),
        Binding("enter", "complete_task", "Complete", show=True),
        Binding("escape", "quit", "Exit", show=True),
    ]

    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.data_manager = data_manager
        self.task_list = ListView(classes="quest-list focused-panel")
        self.selected_task = None

    def compose(self) -> ComposeResult:
        # Header with player info
        yield Container(
            Label("QUESTA - Dashboard", classes="screen-title"),
            Label(
                f"{self.data_manager.player.name} | Lvl {self.data_manager.player.level} | {self.data_manager.player.total_xp}/1000 XP",
                classes="player-info",
            ),
            classes="tui-header",
        )

        # Main content area
        yield Container(
            # Sidebar
            Container(
                Container(
                    Label("Today's Quests", classes="panel-header"),
                    self.task_list,
                    classes="panel-content",
                ),
                classes="tui-sidebar focused-panel",
            ),
            # Main content
            Container(
                Container(
                    Label(
                        "Quest Details - Fix auth bug",
                        classes="panel-header",
                        id="details-header",
                    ),
                    VerticalScroll(
                        Static("Difficulty: Hard (+50 XP)", id="task-difficulty"),
                        Static("File: src/auth.py", id="task-file"),
                        Static("Created: 2025-08-05 09:30", id="task-created"),
                        Static("Priority: High", id="task-priority"),
                        Static("Status: Active", id="task-status"),
                        Static(""),
                        Static("Description:", classes="detail-label"),
                        Static(
                            "Login validation is failing for users with special characters in their email addresses. Need to update regex pattern and add proper escaping.",
                            id="task-description",
                        ),
                        Static(""),
                        Static("Acceptance Criteria:", classes="detail-label"),
                        Static(
                            "• Update email validation regex\n• Add unit tests for edge cases\n• Verify OAuth flow still works",
                            id="task-criteria",
                        ),
                        Static(""),
                        Container(
                            Static(
                                "┌─────────────────┐\n│ STREAK: 7 DAYS  │\n└─────────────────┘",
                                classes="streak-box",
                            ),
                            classes="streak-container",
                        ),
                        classes="details-scroll",
                    ),
                    classes="panel-content",
                ),
                classes="tui-main",
            ),
            classes="tui-content",
        )

        # Footer with shortcuts
        yield Container(
            Label(
                "q:quests l:levels j:journal a:add enter:complete esc:quit",
                classes="shortcuts",
            ),
            Label("3 active quests", classes="status-info"),
            classes="tui-footer",
        )

    def on_mount(self):
        self.refresh_tasks()

    def refresh_tasks(self):
        """Refresh the task list with enhanced items"""
        self.task_list.clear()
        active_tasks = [t for t in self.data_manager.tasks if not t.completed]

        if not active_tasks:
            self.task_list.append(
                ListItem(Label("No active quests. Press 'A' to add one!"))
            )
        else:
            for task in active_tasks:
                self.task_list.append(TaskListItemEnhanced(task))

    def on_list_view_selected(self, event: ListView.Selected):
        """Update details panel when task is selected"""
        if hasattr(event.item, "task_data"):
            task = event.item.task_data
            self.selected_task = task
            self.update_details_panel(task)

    def update_details_panel(self, task: Task):
        """Update the details panel with task information"""
        self.query_one("#details-header").update(f"Quest Details - {task.title}")
        self.query_one("#task-difficulty").update(
            f"Difficulty: {task.difficulty.label} (+{task.difficulty.xp} XP)"
        )
        self.query_one("#task-file").update(
            f"File: {task.file_path or 'Not specified'}"
        )
        self.query_one("#task-created").update(f"Created: {task.created_date}")
        self.query_one("#task-priority").update(f"Priority: {task.priority.label}")
        self.query_one("#task-status").update(f"Status: {task.status.value.title()}")
        self.query_one("#task-description").update(
            task.notes or "No description provided"
        )

    def action_show_quests(self):
        self.app.push_screen(QuestsScreen(self.data_manager))

    def action_show_leveling(self):
        self.app.push_screen(LevelingScreen(self.data_manager))

    def action_show_journal(self):
        self.app.push_screen(JournalScreen(self.data_manager))

    def action_add_task(self):
        self.app.push_screen(
            AddTaskScreen(self.data_manager), callback=self.on_task_added
        )

    def action_complete_task(self):
        """Complete the selected task with enhanced feedback"""
        if self.selected_task and not self.selected_task.completed:
            self.selected_task.completed = True
            self.selected_task.status = TaskStatus.COMPLETED
            self.selected_task.completed_date = datetime.now().isoformat()

            # Award XP and update stats
            self.data_manager.player.total_xp += self.selected_task.difficulty.xp
            self.data_manager.player.tasks_completed += 1

            # Update streak
            today = date.today().isoformat()
            if self.data_manager.player.last_active_date != today:
                self.data_manager.player.current_streak += 1
                self.data_manager.player.last_active_date = today

            self.data_manager.save_data()

            # Show completion feedback
            self.app.push_screen(CompletionModal(self.selected_task))

            self.refresh_tasks()

    def on_task_added(self, task: Optional[Task]):
        if task:
            self.refresh_tasks()

    def action_quit(self):
        self.app.exit()


class QuestsScreen(Screen):
    """Enhanced quests screen with filters and actions"""

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("enter", "complete_task", "Complete", show=True),
        Binding("e", "edit_task", "Edit", show=True),
        Binding("d", "delete_task", "Delete", show=True),
        Binding("j,k", "navigate", "Navigate", show=False),
    ]

    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.data_manager = data_manager
        self.task_list = ListView(classes="quest-list focused-panel")
        self.current_filter = "today"
        self.selected_task = None

    def compose(self) -> ComposeResult:
        yield Container(
            Label("QUESTA - All Quests", classes="screen-title"),
            Label("Filter: today | 3 active, 12 completed", classes="filter-info"),
            classes="tui-header",
        )

        # Filter tabs
        yield Container(
            Button(
                "Today",
                variant="primary",
                classes="filter-tab active",
                id="filter-today",
            ),
            Button("All", classes="filter-tab", id="filter-all"),
            Button("Completed", classes="filter-tab", id="filter-completed"),
            Button("By Tag", classes="filter-tab", id="filter-tags"),
            classes="filter-tabs",
        )

        yield Container(
            # Sidebar with quest list
            Container(
                Container(
                    Label("Quest List", classes="panel-header"),
                    self.task_list,
                    classes="panel-content",
                ),
                classes="tui-sidebar focused-panel",
            ),
            # Actions panel
            Container(
                Container(
                    Label("Actions", classes="panel-header"),
                    Container(
                        Button("[Enter] Complete", classes="action-btn complete"),
                        Button("[e] Edit", classes="action-btn edit"),
                        Button("[d] Delete", classes="action-btn delete"),
                        classes="action-buttons",
                    ),
                    Static(""),
                    Label("Tags: #bug #auth #critical", id="task-tags"),
                    Label("Estimated Time: 2-3 hours", id="task-time"),
                    Label("Dependencies: None", id="task-deps"),
                    Static(""),
                    Label("Notes:", classes="detail-label"),
                    Static(
                        "This affects OAuth login flow. Test thoroughly before deploying.",
                        id="task-notes",
                    ),
                    classes="panel-content",
                ),
                classes="tui-main",
            ),
            classes="tui-content",
        )

        yield Container(
            Label(
                "←:back j/k:nav enter:complete e:edit d:delete /:search",
                classes="shortcuts",
            ),
            Label("Quest 1/15", classes="status-info"),
            classes="tui-footer",
        )

    def on_mount(self):
        self.refresh_tasks()

    def refresh_tasks(self):
        """Refresh task list based on current filter"""
        self.task_list.clear()

        if self.current_filter == "today":
            tasks = [t for t in self.data_manager.tasks if not t.completed]
        elif self.current_filter == "completed":
            tasks = [t for t in self.data_manager.tasks if t.completed]
        else:  # all
            tasks = self.data_manager.tasks

        for task in tasks:
            self.task_list.append(TaskListItemEnhanced(task))

    def on_list_view_selected(self, event: ListView.Selected):
        """Update action panel when task is selected"""
        if hasattr(event.item, "task_data"):
            self.selected_task = event.item.task_data
            task = self.selected_task

            # Update task details in action panel
            tags_text = (
                " ".join(f"#{tag}" for tag in task.tags) if task.tags else "None"
            )
            self.query_one("#task-tags").update(f"Tags: {tags_text}")
            self.query_one("#task-time").update(
                f"Estimated Time: {task.estimated_time or 'Not specified'}"
            )
            self.query_one("#task-deps").update(
                "Dependencies: None"
            )  # Could be enhanced
            self.query_one("#task-notes").update(task.notes or "No notes provided")

    def action_back(self):
        self.app.pop_screen()

    def action_complete_task(self):
        if self.selected_task and not self.selected_task.completed:
            self.selected_task.completed = True
            self.selected_task.status = TaskStatus.COMPLETED
            self.data_manager.save_data()
            self.refresh_tasks()

    def action_edit_task(self):
        if self.selected_task:
            self.app.push_screen(EditTaskScreen(self.data_manager, self.selected_task))

    def action_delete_task(self):
        if self.selected_task:
            self.data_manager.tasks.remove(self.selected_task)
            self.data_manager.save_data()
            self.refresh_tasks()


class LevelingScreen(Screen):
    """Enhanced leveling screen with professional layout"""

    BINDINGS = [Binding("escape", "back", "Back", show=True)]

    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.data_manager = data_manager

    def compose(self) -> ComposeResult:
        player = self.data_manager.player

        yield Container(
            Label("QUESTA - Character Stats", classes="screen-title"),
            Label(f"Level {player.level} - Code Apprentice", classes="level-subtitle"),
            classes="tui-header",
        )

        yield Container(
            # Left sidebar with level progress
            Container(
                Container(
                    Label("Level Progress", classes="panel-header"),
                    Container(
                        ProgressBar(
                            total=1000, show_percentage=False, classes="level-progress"
                        ),
                        Static("650 / 1000 XP", classes="xp-text"),
                        Static(
                            "350 XP to Level 6\n(Code Journeyman)",
                            classes="next-level-info",
                        ),
                        classes="progress-container",
                    ),
                    Container(
                        Container(
                            Static("23\nCOMPLETED", classes="stat-box"),
                            classes="stat-item",
                        ),
                        Container(
                            Static("1,250\nTOTAL XP", classes="stat-box"),
                            classes="stat-item",
                        ),
                        Container(
                            Static("7\nSTREAK", classes="stat-box"), classes="stat-item"
                        ),
                        Container(
                            Static("12\nBUGS FIXED", classes="stat-box"),
                            classes="stat-item",
                        ),
                        classes="stats-grid",
                    ),
                    classes="panel-content",
                ),
                classes="tui-sidebar focused-panel",
            ),
            # Main content with achievements
            Container(
                Container(
                    Label("Achievements & Badges", classes="panel-header"),
                    Container(
                        # Unlocked badges
                        Container(
                            Static(
                                "[B]\nBug Slayer\nFixed 10+ bugs",
                                classes="badge unlocked",
                            ),
                            Static(
                                "[D]\nDocumenter\nUpdated 5+ docs",
                                classes="badge unlocked",
                            ),
                            Static(
                                "[S]\nStreak Master\n7 day streak",
                                classes="badge unlocked",
                            ),
                            classes="badge-row",
                        ),
                        Container(
                            Static(
                                "[F]\nSpeed Demon\n3 tasks in 1 day",
                                classes="badge locked",
                            ),
                            Static(
                                "[P]\nPerfectionist\n20 hard tasks",
                                classes="badge locked",
                            ),
                            Static(
                                "[M]\nCode Master\nReach Level 10",
                                classes="badge locked",
                            ),
                            classes="badge-row",
                        ),
                        classes="badges-grid",
                    ),
                    Static(""),
                    Container(
                        Label("Level Progression", classes="detail-label"),
                        Static(
                            "Level 1-2: Code Novice (0-100 XP)\n"
                            "Level 3-4: Code Student (101-400 XP)\n"
                            "Level 5-6: Code Apprentice (401-1000 XP) ← Current\n"
                            "Level 7-8: Code Journeyman (1001-2000 XP)\n"
                            "Level 9-10: Code Expert (2001-4000 XP)\n"
                            "Level 11+: Code Master (4000+ XP)",
                            classes="progression-text",
                        ),
                        classes="progression-info",
                    ),
                    classes="panel-content",
                ),
                classes="tui-main",
            ),
            classes="tui-content",
        )

        yield Container(
            Label("←:back j/k:navigate ?:help", classes="shortcuts"),
            Label("3/6 badges unlocked", classes="status-info"),
            classes="tui-footer",
        )

    def on_mount(self):
        # Set progress bar value
        progress_bar = self.query_one(ProgressBar)
        progress_bar.advance(650)

    def action_back(self):
        self.app.pop_screen()


class JournalScreen(Screen):
    """Enhanced journal screen with activity history"""

    BINDINGS = [Binding("escape", "back", "Back", show=True)]

    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.data_manager = data_manager

    def compose(self) -> ComposeResult:
        yield Container(
            Label("QUESTA - Quest Journal", classes="screen-title"),
            Label("Last 7 days • 185 XP earned", classes="journal-subtitle"),
            classes="tui-header",
        )

        yield Container(
            Container(
                Label("Recent Activity", classes="panel-header"),
                VerticalScroll(
                    Container(
                        Static("2025-08-05 • Monday", classes="journal-date"),
                        Static(
                            "+50 XP • 2 quests completed", classes="journal-summary"
                        ),
                        Static(
                            "• [HARD] Fixed authentication bug (+50 XP)\n• [EASY] Updated API documentation (+15 XP)",
                            classes="journal-details",
                        ),
                        classes="journal-entry",
                    ),
                    Container(
                        Static("2025-08-04 • Sunday", classes="journal-date"),
                        Static("+30 XP • 1 quest completed", classes="journal-summary"),
                        Static(
                            "• [MEDIUM] Wrote unit tests for user service (+30 XP)",
                            classes="journal-details",
                        ),
                        classes="journal-entry",
                    ),
                    Container(
                        Static("2025-08-03 • Saturday", classes="journal-date"),
                        Static(
                            "+45 XP • 3 quests • [BADGE] Achievement unlocked",
                            classes="journal-summary",
                        ),
                        Static(
                            '• [MEDIUM] Refactored database queries (+30 XP)\n• [EASY] Updated README documentation (+15 XP)\n• [BADGE] Unlocked "Documenter" achievement',
                            classes="journal-details",
                        ),
                        classes="journal-entry",
                    ),
                    Container(
                        Static("2025-08-02 • Friday", classes="journal-date"),
                        Static(
                            "+65 XP • [LEVEL UP] Now Level 5", classes="journal-summary"
                        ),
                        Static(
                            "• [HARD] Fixed critical security vulnerability (+50 XP)\n• [EASY] Added proper error handling (+15 XP)\n• [LEVEL UP] Advanced to Code Apprentice (Level 5)",
                            classes="journal-details",
                        ),
                        classes="journal-entry",
                    ),
                    classes="journal-scroll",
                ),
                classes="panel-content",
            ),
            classes="journal-container",
        )

        yield Container(
            Label("←:back j/k:scroll g/G:top/bottom /:search", classes="shortcuts"),
            Label("Showing last 30 days", classes="status-info"),
            classes="tui-footer",
        )

    def action_back(self):
        self.app.pop_screen()


class AddTaskScreen(Screen):
    """Enhanced add task screen with professional form layout"""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("ctrl+s", "save", "Save", show=True),
    ]

    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.data_manager = data_manager

    def compose(self) -> ComposeResult:
        yield Container(
            Label("QUESTA - New Quest", classes="screen-title"),
            Label("Fill details and press Ctrl+S to save", classes="form-subtitle"),
            classes="tui-header",
        )

        yield Container(
            Container(
                Label("Quest Details", classes="panel-header"),
                VerticalScroll(
                    Container(
                        Label("Title *", classes="form-label"),
                        Input(
                            placeholder="e.g., Fix memory leak in image processor",
                            id="title-input",
                        ),
                        classes="form-row",
                    ),
                    Container(
                        Label("Difficulty *", classes="form-label"),
                        Select(
                            [
                                (
                                    "Easy (+15 XP) - Quick fixes, simple tasks",
                                    TaskDifficulty.EASY,
                                ),
                                (
                                    "Medium (+30 XP) - Moderate complexity",
                                    TaskDifficulty.MEDIUM,
                                ),
                                (
                                    "Hard (+50 XP) - Complex problems, major features",
                                    TaskDifficulty.HARD,
                                ),
                            ],
                            value=TaskDifficulty.MEDIUM,
                            id="difficulty-select",
                        ),
                        classes="form-row",
                    ),
                    Container(
                        Label("Priority", classes="form-label"),
                        Select(
                            [
                                ("Low", Priority.LOW),
                                ("Medium", Priority.MEDIUM),
                                ("High", Priority.HIGH),
                                ("Critical", Priority.CRITICAL),
                            ],
                            value=Priority.MEDIUM,
                            id="priority-select",
                        ),
                        classes="form-row",
                    ),
                    Container(
                        Label("Files/Paths", classes="form-label"),
                        Input(placeholder="e.g., src/utils/image.py", id="files-input"),
                        classes="form-row",
                    ),
                    Container(
                        Label("Tags (space-separated)", classes="form-label"),
                        Input(
                            placeholder="e.g., memory leak performance", id="tags-input"
                        ),
                        classes="form-row",
                    ),
                    Container(
                        Label("Estimated Time", classes="form-label"),
                        Select(
                            [
                                ("Not specified", ""),
                                ("15 minutes", "15m"),
                                ("30 minutes", "30m"),
                                ("1 hour", "1h"),
                                ("2 hours", "2h"),
                                ("4 hours", "4h"),
                                ("Full day", "1d"),
                            ],
                            id="time-select",
                        ),
                        classes="form-row",
                    ),
                    Container(
                        Label("Description", classes="form-label"),
                        TextArea(
                            text="",
                            id="description-input",
                        ),
                        classes="form-row large",
                    ),
                    classes="form-scroll",
                ),
                classes="panel-content",
            ),
            classes="form-container",
        )

        yield Container(
            Label(
                "Ctrl+S:save Ctrl+C:cancel Tab:next field Shift+Tab:prev field",
                classes="shortcuts",
            ),
            Label("Quest will award XP based on difficulty", classes="status-info"),
            classes="tui-footer",
        )

    def action_save(self):
        title = self.query_one("#title-input", Input).value.strip()
        if not title:
            return

        difficulty = (
            self.query_one("#difficulty-select", Select).value or TaskDifficulty.MEDIUM
        )
        priority = self.query_one("#priority-select", Select).value or Priority.MEDIUM
        file_path = self.query_one("#files-input", Input).value.strip()
        tags_str = self.query_one("#tags-input", Input).value.strip()
        estimated_time = self.query_one("#time-select", Select).value or ""
        description = self.query_one("#description-input", TextArea).text.strip()

        tags = tags_str.split() if tags_str else []

        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            difficulty=difficulty,
            priority=priority,
            created_date=datetime.now().strftime("%Y-%m-%d"),
            notes=description,
            tags=tags,
            file_path=file_path,
            estimated_time=estimated_time,
        )

        self.data_manager.tasks.append(task)
        self.data_manager.save_data()
        self.dismiss(task)

    def action_cancel(self):
        self.dismiss(None)


class EditTaskScreen(Screen):
    """Edit existing task screen"""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("ctrl+s", "save", "Save", show=True),
    ]

    def __init__(self, data_manager: DataManager, task: Task):
        super().__init__()
        self.data_manager = data_manager
        self.task = task

    def compose(self) -> ComposeResult:
        yield Container(
            Label("QUESTA - Edit Quest", classes="screen-title"),
            Label(f"Editing: {self.task.title}", classes="form-subtitle"),
            classes="tui-header",
        )

        yield Container(
            Container(
                Label("Quest Details", classes="panel-header"),
                VerticalScroll(
                    Container(
                        Label("Title *", classes="form-label"),
                        Input(value=self.task.title, id="title-input"),
                        classes="form-row",
                    ),
                    Container(
                        Label("Difficulty *", classes="form-label"),
                        Select(
                            [
                                ("Easy (+15 XP)", TaskDifficulty.EASY),
                                ("Medium (+30 XP)", TaskDifficulty.MEDIUM),
                                ("Hard (+50 XP)", TaskDifficulty.HARD),
                            ],
                            value=self.task.difficulty,
                            id="difficulty-select",
                        ),
                        classes="form-row",
                    ),
                    Container(
                        Label("Priority", classes="form-label"),
                        Select(
                            [
                                ("Low", Priority.LOW),
                                ("Medium", Priority.MEDIUM),
                                ("High", Priority.HIGH),
                                ("Critical", Priority.CRITICAL),
                            ],
                            value=self.task.priority,
                            id="priority-select",
                        ),
                        classes="form-row",
                    ),
                    Container(
                        Label("Description", classes="form-label"),
                        TextArea(text=self.task.notes, id="description-input"),
                        classes="form-row large",
                    ),
                    classes="form-scroll",
                ),
                classes="panel-content",
            ),
            classes="form-container",
        )

        yield Container(
            Label("Ctrl+S:save Ctrl+C:cancel", classes="shortcuts"),
            Label("", classes="status-info"),
            classes="tui-footer",
        )

    def action_save(self):
        title = self.query_one("#title-input", Input).value.strip()
        if not title:
            return

        self.task.title = title
        self.task.difficulty = self.query_one("#difficulty-select", Select).value
        self.task.priority = self.query_one("#priority-select", Select).value
        self.task.notes = self.query_one("#description-input", TextArea).text.strip()

        self.data_manager.save_data()
        self.dismiss(self.task)

    def action_cancel(self):
        self.dismiss(None)


class CompletionModal(ModalScreen):
    """Modal shown when a task is completed"""

    def __init__(self, task: Task):
        super().__init__()
        self.task = task

    def compose(self) -> ComposeResult:
        yield Container(
            Static("Quest Completed!", classes="completion-title"),
            Static(""),
            Static(f"[✓] {self.task.title}", classes="completed-task"),
            Static(f"+{self.task.difficulty.xp} XP gained!", classes="xp-gained"),
            Static(""),
            Static("[STREAK] Streak continues: 8 days", classes="streak-info"),
            Static(""),
            Button("Continue", variant="primary", id="continue-btn"),
            classes="completion-modal",
        )

    def on_button_pressed(self, event: Button.Pressed):
        self.dismiss()


class LevelUpModal(ModalScreen):
    """Modal shown when player levels up"""

    def __init__(self, new_level: int, xp_gained: int):
        super().__init__()
        self.new_level = new_level
        self.xp_gained = xp_gained

    def compose(self) -> ComposeResult:
        yield Container(
            Static("[LEVEL UP]", classes="level-up-title"),
            Static(""),
            Static(f"You reached Level {self.new_level}!", classes="level-up-text"),
            Static(f"Gained {self.xp_gained} XP", classes="xp-text"),
            Static(""),
            Button("Continue", variant="primary", id="continue-btn"),
            classes="level-up-modal",
        )

    def on_button_pressed(self, event: Button.Pressed):
        self.dismiss()


# Main App with Enhanced CSS
class QUESTAApp(App):
    """Enhanced QUESTA application with professional styling"""

    CSS = """
    /* Base Styling */
    Screen {
        background: #181817;
        color: #e0e0e0;
    }
    
    /* Welcome Screen (Original) */
    #welcome-container {
        height: 100%;
        align: center middle;
        text-align: center;
    }
    
    #logo {
        color: #1b45d7;
        text-align: center;
    }
    
    .center {
        text-align: center;
        color: #19327f;
    }
    
    /* Header and Footer */
    .tui-header {
        background: #0a1543;
        height: 3;
        dock: top;
        padding: 0 2;
        border-bottom: solid #3a3a3a;
    }
    
    .tui-footer {
        background: #0a1543;
        height: 2;
        dock: bottom;
        padding: 0 2;
        border-top: solid #3a3a3a;
    }
    
    .screen-title {
        color: #1b45d7;
        text-style: bold;
    }
    
    .player-info, .filter-info, .journal-subtitle, .form-subtitle {
        color: #9aa0b0;
        text-align: right;
    }
    
    .shortcuts {
        color: #9aa0b0;
    }
    
    .status-info {
        color: #9aa0b0;
        text-align: right;
    }
    
    /* Layout */
    .tui-content {
        layout: horizontal;
    }
    
    .tui-sidebar {
        width: 25%;
        min-width: 30;
        border-right: solid #3a3a3a;
        background: #181817;
    }
    
    .tui-main {
        background: #181817;
    }
    
    .focused-panel {
        border: solid #1b45d7;
    }
    
    /* Panels */
    .panel-header {
        background: #0a1543;
        color: #1b45d7;
        text-style: bold;
        padding: 0 1;
        dock: top;
        height: 1;
        border-bottom: solid #3a3a3a;
    }
    
    .panel-content {
        padding: 1;
        height: 100%;
    }
    
    /* Task List Items */
    .task-item-content {
        layout: horizontal;
        height: auto;
    }
    
    .task-info {
        width: 1fr;
        margin-left: 1;
    }
    
    .task-meta {
        layout: vertical;
        width: auto;
        align: center middle;
    }
    
    /* Status Indicators */
    .status-pending { color: #9aa0b0; }
    .status-active { color: #1b45d7; }
    .status-completed { color: #4caf50; }
    .status-blocked { color: #f44336; }
    
    /* Priority Bars */
    .priority-low {
        width: 1;
        background: #9aa0b0;
    }
    
    .priority-medium {
        width: 1;
        background: #ffc107;
    }
    
    .priority-high, .priority-critical {
        width: 1;
        background: #f44336;
    }
    
    /* Difficulty Badges */
    .difficulty-badge {
        text-align: center;
        text-style: bold;
        width: 3;
        height: 1;
    }
    
    .badge-easy { background: #4caf50; }
    .badge-medium { background: #ffc107; color: black; }
    .badge-hard { background: #f44336; }
    
    .xp-label {
        text-align: center;
        color: #9aa0b0;
        width: 3;
    }
    
    /* List Item States */
    ListView > ListItem {
        background: #181817;
        color: #e0e0e0;
    }
    
    ListView > ListItem:hover {
        background: #19327f 20%;
    }
    
    ListView > ListItem.-highlighted {
        background: #1b45d7;
        color: white;
    }
    
    /* Details Panel */
    .detail-label {
        color: #1b45d7;
        text-style: bold;
        margin: 1 0 0 0;
    }
    
    .streak-container {
        text-align: center;
        margin: 2 0;
    }
    
    .streak-box {
        color: #ffc107;
        text-style: bold;
    }
    
    /* Filter Tabs */
    .filter-tabs {
        layout: horizontal;
        dock: top;
        height: 1;
        border-bottom: solid #3a3a3a;
    }
    
    .filter-tab {
        border: none;
        border-right: solid #3a3a3a;
        background: #181817;
        color: #9aa0b0;
    }
    
    .filter-tab.active, .filter-tab:hover {
        background: #0a1543;
        color: #1b45d7;
    }
    
    /* Action Buttons */
    .action-buttons {
        layout: vertical;
        margin: 1 0;
    }
    
    .action-btn {
        margin: 0 0 1 0;
        border: solid #3a3a3a;
        background: #181817;
    }
    
    .action-btn.complete { border: solid #4caf50; color: #4caf50; }
    .action-btn.edit { border: solid #ffc107; color: #ffc107; }
    .action-btn.delete { border: solid #f44336; color: #f44336; }
    
    /* Leveling Screen */
    .level-progress {
        margin: 1 0;
    }
    
    .xp-text {
        text-align: center;
        margin: 1 0;
        color: #9aa0b0;
    }
    
    .next-level-info {
        text-align: center;
        color: #9aa0b0;
    }
    
    .stats-grid {
        layout: grid;
        grid-size: 2 2;
        grid-gutter: 1;
        margin: 2 0;
    }
    
    .stat-item {
        border: solid #3a3a3a;
        background: #0a1543;
        padding: 1;
        text-align: center;
    }
    
    .stat-box {
        text-align: center;
    }
    
    /* Badges */
    .badges-grid {
        layout: vertical;
        margin: 1 0;
    }
    
    .badge-row {
        layout: horizontal;
        margin: 0 0 1 0;
    }
    
    .badge {
        border: solid #3a3a3a;
        background: #0a1543;
        padding: 1;
        text-align: center;
        margin: 0 1 0 0;
        width: 1fr;
    }
    
    .badge.unlocked {
        border: solid #1b45d7;
        background: #19327f;
    }
    
    .badge.locked {
        opacity: 30%;
    }
    
    .progression-info {
        border: solid #3a3a3a;
        background: #0a1543;
        padding: 1;
        margin: 1 0;
    }
    
    .progression-text {
        color: #9aa0b0;
    }
    
    /* Journal */
    .journal-container {
        width: 100%;
    }
    
    .journal-entry {
        border-left: thick #4caf50;
        padding-left: 1;
        margin: 1 0;
    }
    
    .journal-date {
        color: #9aa0b0;
    }
    
    .journal-summary {
        color: #1b45d7;
        text-style: bold;
    }
    
    .journal-details {
        color: #9aa0b0;
        margin: 1 0 0 0;
    }
    
    /* Forms */
    .form-container {
        width: 100%;
    }
    
    .form-row {
        margin: 1 0;
    }
    
    .form-row.large {
        margin: 2 0;
    }
    
    .form-label {
        color: #1b45d7;
        margin: 0 0 1 0;
    }
    
    Input, Select, TextArea {
        background: #0a1543;
        border: solid #3a3a3a;
        color: #e0e0e0;
    }
    
    Input:focus, Select:focus, TextArea:focus {
        border: solid #1b45d7;
    }
    
    /* Modals */
    .completion-modal, .level-up-modal {
        background: #0a1543;
        border: thick #1b45d7;
        width: 50;
        height: 15;
        text-align: center;
        padding: 2;
    }
    
    .completion-title, .level-up-title {
        color: #4caf50;
        text-style: bold;
    }
    
    .completed-task {
        color: #1b45d7;
    }
    
    .xp-gained {
        color: #ffc107;
        text-style: bold;
    }
    
    .streak-info {
        color: #ffc107;
    }
    
    .level-up-text {
        color: #1b45d7;
        text-style: bold;
    }
    
    /* Progress Bars */
    ProgressBar > .bar--bar {
        color: #021fa0;
    }
    
    ProgressBar > .bar--complete {
        background: #1b45d7;
    }
    
    /* Buttons */
    Button {
        margin: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()

    def on_mount(self):
        self.push_screen(WelcomeScreen(self.data_manager))


class StatsScreen(Screen):
    """Detailed statistics screen"""

    BINDINGS = [Binding("escape", "back", "Back", show=True)]

    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.data_manager = data_manager

    def compose(self) -> ComposeResult:
        player = self.data_manager.player
        completed_tasks = [t for t in self.data_manager.tasks if t.completed]

        # Calculate additional stats
        easy_completed = len(
            [t for t in completed_tasks if t.difficulty == TaskDifficulty.EASY]
        )
        medium_completed = len(
            [t for t in completed_tasks if t.difficulty == TaskDifficulty.MEDIUM]
        )
        hard_completed = len(
            [t for t in completed_tasks if t.difficulty == TaskDifficulty.HARD]
        )

        yield Container(
            Label("QUESTA - Detailed Statistics", classes="screen-title"),
            Label(
                f"Player: {player.name} | Total Sessions: {len(completed_tasks)}",
                classes="stats-subtitle",
            ),
            classes="tui-header",
        )

        yield Container(
            Container(
                Container(
                    Label("Performance Metrics", classes="panel-header"),
                    Container(
                        Static(
                            f"Total XP Earned: {player.total_xp}", classes="stat-line"
                        ),
                        Static(
                            f"Average XP per Task: {player.total_xp // max(1, player.tasks_completed)}",
                            classes="stat-line",
                        ),
                        Static(f"Current Level: {player.level}", classes="stat-line"),
                        Static(
                            f"Tasks Completed: {player.tasks_completed}",
                            classes="stat-line",
                        ),
                        Static(
                            f"Current Streak: {player.current_streak} days",
                            classes="stat-line",
                        ),
                        Static(f"Bugs Fixed: {player.bugs_fixed}", classes="stat-line"),
                        Static(""),
                        Label("Task Breakdown by Difficulty:", classes="detail-label"),
                        Static(
                            f"Easy Tasks: {easy_completed} ({easy_completed * 15} XP)",
                            classes="difficulty-stat easy",
                        ),
                        Static(
                            f"Medium Tasks: {medium_completed} ({medium_completed * 30} XP)",
                            classes="difficulty-stat medium",
                        ),
                        Static(
                            f"Hard Tasks: {hard_completed} ({hard_completed * 50} XP)",
                            classes="difficulty-stat hard",
                        ),
                        classes="stats-content",
                    ),
                    classes="panel-content",
                ),
                classes="stats-panel",
            ),
            classes="stats-container",
        )

        yield Container(
            Label("←:back", classes="shortcuts"),
            Label(
                f"Showing stats for {len(self.data_manager.tasks)} total quests",
                classes="status-info",
            ),
            classes="tui-footer",
        )

    def action_back(self):
        self.app.pop_screen()


class SearchScreen(Screen):
    """Search and filter tasks screen"""

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("enter", "search", "Search", show=True),
    ]

    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.data_manager = data_manager
        self.results_list = ListView(classes="search-results")

    def compose(self) -> ComposeResult:
        yield Container(
            Label("QUESTA - Search Quests", classes="screen-title"),
            Label("Search by title, tags, or file path", classes="search-subtitle"),
            classes="tui-header",
        )

        yield Container(
            Container(
                Container(
                    Label("Search Query", classes="panel-header"),
                    Container(
                        Input(placeholder="Enter search terms...", id="search-input"),
                        Static(""),
                        Label("Filter Options:", classes="detail-label"),
                        Container(
                            Button("All", classes="filter-btn active", id="filter-all"),
                            Button("Active", classes="filter-btn", id="filter-active"),
                            Button(
                                "Completed", classes="filter-btn", id="filter-completed"
                            ),
                            classes="filter-buttons",
                        ),
                        classes="search-controls",
                    ),
                    classes="panel-content",
                ),
                classes="search-panel",
            ),
            Container(
                Container(
                    Label("Search Results", classes="panel-header"),
                    self.results_list,
                    classes="panel-content",
                ),
                classes="results-panel",
            ),
            classes="search-content",
        )

        yield Container(
            Label("←:back enter:search", classes="shortcuts"),
            Label("0 results", id="results-count", classes="status-info"),
            classes="tui-footer",
        )

    def on_input_changed(self, event: Input.Changed):
        """Auto-search as user types"""
        if event.input.id == "search-input":
            self.perform_search(event.value)

    def perform_search(self, query: str):
        """Perform search and update results"""
        if not query.strip():
            self.results_list.clear()
            self.query_one("#results-count").update("0 results")
            return

        query_lower = query.lower()
        results = []

        for task in self.data_manager.tasks:
            # Search in title, notes, tags, and file_path
            searchable_text = (
                f"{task.title} {task.notes} {' '.join(task.tags)} {task.file_path}"
            ).lower()

            if query_lower in searchable_text:
                results.append(task)

        # Update results list
        self.results_list.clear()
        for task in results:
            self.results_list.append(TaskListItemEnhanced(task))

        # Update count
        self.query_one("#results-count").update(f"{len(results)} results")

    def action_back(self):
        self.app.pop_screen()

    def action_search(self):
        query = self.query_one("#search-input", Input).value
        self.perform_search(query)


class SettingsScreen(Screen):
    """Settings and configuration screen"""

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("ctrl+s", "save", "Save", show=True),
    ]

    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.data_manager = data_manager

    def compose(self) -> ComposeResult:
        yield Container(
            Label("QUESTA - Settings", classes="screen-title"),
            Label(
                "Configure your development environment", classes="settings-subtitle"
            ),
            classes="tui-header",
        )

        yield Container(
            Container(
                Container(
                    Label("Player Settings", classes="panel-header"),
                    Container(
                        Container(
                            Label("Player Name", classes="form-label"),
                            Input(
                                value=self.data_manager.player.name, id="player-name"
                            ),
                            classes="form-row",
                        ),
                        Container(
                            Label("Default Difficulty", classes="form-label"),
                            Select(
                                [
                                    ("Easy", TaskDifficulty.EASY),
                                    ("Medium", TaskDifficulty.MEDIUM),
                                    ("Hard", TaskDifficulty.HARD),
                                ],
                                value=TaskDifficulty.MEDIUM,
                                id="default-difficulty",
                            ),
                            classes="form-row",
                        ),
                        Container(
                            Label("Auto-save Interval", classes="form-label"),
                            Select(
                                [
                                    ("Every change", "immediate"),
                                    ("Every 5 minutes", "5min"),
                                    ("Every 10 minutes", "10min"),
                                    ("Manual only", "manual"),
                                ],
                                id="autosave-interval",
                            ),
                            classes="form-row",
                        ),
                        classes="settings-form",
                    ),
                    classes="panel-content",
                ),
                classes="settings-panel",
            ),
            Container(
                Container(
                    Label("Data Management", classes="panel-header"),
                    Container(
                        Button("Export Data", classes="data-btn", id="export-btn"),
                        Button("Import Data", classes="data-btn", id="import-btn"),
                        Button(
                            "Reset All Data", classes="data-btn danger", id="reset-btn"
                        ),
                        Static(""),
                        Label("Statistics:", classes="detail-label"),
                        Static(
                            f"Total Tasks: {len(self.data_manager.tasks)}",
                            classes="stat-line",
                        ),
                        Static(
                            f"Data File: {self.data_manager.data_file}",
                            classes="stat-line",
                        ),
                        classes="data-management",
                    ),
                    classes="panel-content",
                ),
                classes="data-panel",
            ),
            classes="settings-content",
        )

        yield Container(
            Label("←:back ctrl+s:save", classes="shortcuts"),
            Label("Settings will be saved automatically", classes="status-info"),
            classes="tui-footer",
        )

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "export-btn":
            self.export_data()
        elif event.button.id == "import-btn":
            self.import_data()
        elif event.button.id == "reset-btn":
            self.reset_data()

    def export_data(self):
        """Export data to JSON file"""
        export_file = f"questa_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(export_file, "w") as f:
                tasks_data = []
                for task in self.data_manager.tasks:
                    task_dict = asdict(task)
                    task_dict["difficulty"] = task.difficulty.name
                    task_dict["status"] = task.status.name
                    task_dict["priority"] = task.priority.name
                    tasks_data.append(task_dict)

                data = {
                    "player": asdict(self.data_manager.player),
                    "tasks": tasks_data,
                    "export_date": datetime.now().isoformat(),
                }
                json.dump(data, f, indent=2)

            self.app.push_screen(InfoModal(f"Data exported to {export_file}"))
        except Exception as e:
            self.app.push_screen(InfoModal(f"Export failed: {str(e)}"))

    def import_data(self):
        """Import data from JSON file"""
        # This would typically open a file dialog, but for TUI we'll just show info
        self.app.push_screen(
            InfoModal("Import feature: Place JSON file as 'import.json' and restart")
        )

    def reset_data(self):
        """Reset all data"""
        self.app.push_screen(
            ConfirmModal("Are you sure you want to reset all data?", self.confirm_reset)
        )

    def confirm_reset(self, confirmed: bool):
        if confirmed:
            # Reset player data
            self.data_manager.player = PlayerData()
            self.data_manager.tasks = []
            self.data_manager.save_data()
            self.app.push_screen(InfoModal("All data has been reset"))

    def action_save(self):
        """Save settings"""
        player_name = self.query_one("#player-name", Input).value.strip()
        if player_name:
            self.data_manager.player.name = player_name
            self.data_manager.save_data()

    def action_back(self):
        self.action_save()  # Auto-save on exit
        self.app.pop_screen()


class InfoModal(ModalScreen):
    """Simple info modal"""

    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        yield Container(
            Static("Information", classes="modal-title"),
            Static(""),
            Static(self.message, classes="modal-message"),
            Static(""),
            Button("OK", variant="primary", id="ok-btn"),
            classes="info-modal",
        )

    def on_button_pressed(self, event: Button.Pressed):
        self.dismiss()


class ConfirmModal(ModalScreen):
    """Confirmation modal"""

    def __init__(self, message: str, callback=None):
        super().__init__()
        self.message = message
        self.callback = callback

    def compose(self) -> ComposeResult:
        yield Container(
            Static("Confirm Action", classes="modal-title"),
            Static(""),
            Static(self.message, classes="modal-message"),
            Static(""),
            Container(
                Button("Yes", variant="error", id="yes-btn"),
                Button("No", variant="primary", id="no-btn"),
                classes="modal-buttons",
            ),
            classes="confirm-modal",
        )

    def on_button_pressed(self, event: Button.Pressed):
        if self.callback:
            self.callback(event.button.id == "yes-btn")
        self.dismiss()


class HelpScreen(Screen):
    """Help and keyboard shortcuts screen"""

    BINDINGS = [Binding("escape", "back", "Back", show=True)]

    def compose(self) -> ComposeResult:
        yield Container(
            Label("QUESTA - Help & Shortcuts", classes="screen-title"),
            Label("Keyboard shortcuts and usage guide", classes="help-subtitle"),
            classes="tui-header",
        )

        yield Container(
            VerticalScroll(
                Container(
                    Label("Global Shortcuts", classes="help-section-title"),
                    Static("ESC        - Go back / Exit", classes="help-item"),
                    Static("Ctrl+C     - Quit application", classes="help-item"),
                    Static("?          - Show this help screen", classes="help-item"),
                    Static(""),
                    Label("Home Screen", classes="help-section-title"),
                    Static("q          - Open Quests screen", classes="help-item"),
                    Static("l          - Open Leveling screen", classes="help-item"),
                    Static("j          - Open Journal screen", classes="help-item"),
                    Static("a          - Add new task", classes="help-item"),
                    Static("ENTER      - Complete selected task", classes="help-item"),
                    Static(""),
                    Label("Quest Management", classes="help-section-title"),
                    Static("ENTER      - Complete task", classes="help-item"),
                    Static("e          - Edit task", classes="help-item"),
                    Static("d          - Delete task", classes="help-item"),
                    Static("j/k        - Navigate up/down", classes="help-item"),
                    Static("/          - Search tasks", classes="help-item"),
                    Static(""),
                    Label("Forms", classes="help-section-title"),
                    Static("TAB        - Next field", classes="help-item"),
                    Static("Shift+TAB  - Previous field", classes="help-item"),
                    Static("Ctrl+S     - Save", classes="help-item"),
                    Static("Ctrl+C     - Cancel", classes="help-item"),
                    Static(""),
                    Label("Task Difficulty & XP", classes="help-section-title"),
                    Static(
                        "Easy       - 15 XP  (Quick fixes, documentation)",
                        classes="help-item",
                    ),
                    Static(
                        "Medium     - 30 XP  (Features, moderate complexity)",
                        classes="help-item",
                    ),
                    Static(
                        "Hard       - 50 XP  (Complex problems, major features)",
                        classes="help-item",
                    ),
                    Static(""),
                    Label("Leveling System", classes="help-section-title"),
                    Static("Level 1-2  - Code Novice", classes="help-item"),
                    Static("Level 3-4  - Code Student", classes="help-item"),
                    Static("Level 5-6  - Code Apprentice", classes="help-item"),
                    Static("Level 7-8  - Code Journeyman", classes="help-item"),
                    Static("Level 9-10 - Code Expert", classes="help-item"),
                    Static("Level 11+  - Code Master", classes="help-item"),
                    classes="help-content",
                ),
                classes="help-scroll",
            ),
            classes="help-container",
        )

        yield Container(
            Label("←:back", classes="shortcuts"),
            Label("QUESTA v1.0 - Professional TUI Task Manager", classes="status-info"),
            classes="tui-footer",
        )

    def action_back(self):
        self.app.pop_screen()


# Enhanced HomeScreen with additional navigation options
class HomeScreenEnhanced(HomeScreen):
    """Enhanced home screen with more options"""

    BINDINGS = [
        Binding("q", "show_quests", "Quests", show=True),
        Binding("l", "show_leveling", "Levels", show=True),
        Binding("j", "show_journal", "Journal", show=True),
        Binding("a", "add_task", "Add", show=True),
        Binding("s", "show_stats", "Stats", show=True),
        Binding("ctrl+f", "show_search", "Search", show=True),
        Binding("ctrl+comma", "show_settings", "Settings", show=False),
        Binding("question_mark", "show_help", "Help", show=False),
        Binding("enter", "complete_task", "Complete", show=True),
        Binding("escape", "quit", "Exit", show=True),
    ]

    def action_show_stats(self):
        self.app.push_screen(StatsScreen(self.data_manager))

    def action_show_search(self):
        self.app.push_screen(SearchScreen(self.data_manager))

    def action_show_settings(self):
        self.app.push_screen(SettingsScreen(self.data_manager))

    def action_show_help(self):
        self.app.push_screen(HelpScreen())


# Main App with Enhanced Features
class QUESTAApp(App):
    """Enhanced QUESTA application with full feature set"""

    CSS = """
    /* Base Styling */
    Screen {
        background: #181817;
        color: #e0e0e0;
    }
    
    /* Welcome Screen (Original) */
    #welcome-container {
        height: 100%;
        align: center middle;
        text-align: center;
    }
    
    #logo {
        color: #1b45d7;
        text-align: center;
    }
    
    .center {
        text-align: center;
        color: #19327f;
    }
    
    /* Header and Footer */
    .tui-header {
        background: #0a1543;
        height: 3;
        dock: top;
        padding: 0 2;
        border-bottom: solid #3a3a3a;
    }
    
    .tui-footer {
        background: #0a1543;
        height: 2;
        dock: bottom;
        padding: 0 2;
        border-top: solid #3a3a3a;
    }
    
    .screen-title {
        color: #1b45d7;
        text-style: bold;
    }
    
    .player-info, .filter-info, .journal-subtitle, .form-subtitle, 
    .search-subtitle, .settings-subtitle, .help-subtitle, .stats-subtitle {
        color: #9aa0b0;
        text-align: right;
    }
    
    .shortcuts {
        color: #9aa0b0;
    }
    
    .status-info {
        color: #9aa0b0;
        text-align: right;
    }
    
    /* Layout */
    .tui-content {
        layout: horizontal;
    }
    
    .tui-sidebar {
        width: 25%;
        min-width: 30;
        border-right: solid #3a3a3a;
        background: #181817;
    }
    
    .tui-main {
        background: #181817;
    }
    
    .focused-panel {
        border: solid #1b45d7;
    }
    
    /* Additional Layouts for New Screens */
    .search-content, .settings-content {
        layout: horizontal;
    }
    
    .search-panel, .settings-panel, .data-panel, .stats-panel {
        width: 50%;
        border-right: solid #3a3a3a;
    }
    
    .results-panel {
        width: 50%;
    }
    
    .help-container, .stats-container, .journal-container {
        width: 100%;
    }
    
    /* Panels */
    .panel-header {
        background: #0a1543;
        color: #1b45d7;
        text-style: bold;
        padding: 0 1;
        dock: top;
        height: 1;
        border-bottom: solid #3a3a3a;
    }
    
    .panel-content {
        padding: 1;
        height: 100%;
    }
    
    /* Task List Items */
    .task-item-content {
        layout: horizontal;
        height: auto;
    }
    
    .task-info {
        width: 1fr;
        margin-left: 1;
    }
    
    .task-meta {
        layout: vertical;
        width: auto;
        align: center middle;
    }
    
    /* Status Indicators */
    .status-pending { color: #9aa0b0; }
    .status-active { color: #1b45d7; }
    .status-completed { color: #4caf50; }
    .status-blocked { color: #f44336; }
    
    /* Priority Bars */
    .priority-low {
        width: 1;
        background: #9aa0b0;
    }
    
    .priority-medium {
        width: 1;
        background: #ffc107;
    }
    
    .priority-high, .priority-critical {
        width: 1;
        background: #f44336;
    }
    
    /* Difficulty Badges and Stats */
    .difficulty-badge {
        text-align: center;
        text-style: bold;
        width: 3;
        height: 1;
    }
    
    .badge-easy, .difficulty-stat.easy { background: #4caf50; }
    .badge-medium, .difficulty-stat.medium { background: #ffc107; color: black; }
    .badge-hard, .difficulty-stat.hard { background: #f44336; }
    
    .xp-label {
        text-align: center;
        color: #9aa0b0;
        width: 3;
    }
    
    /* List Item States */
    ListView > ListItem {
        background: #181817;
        color: #e0e0e0;
    }
    
    ListView > ListItem:hover {
        background: #19327f 20%;
    }
    
    ListView > ListItem.-highlighted {
        background: #1b45d7;
        color: white;
    }
    
    /* Details Panel */
    .detail-label {
        color: #1b45d7;
        text-style: bold;
        margin: 1 0 0 0;
    }
    
    .streak-container {
        text-align: center;
        margin: 2 0;
    }
    
    .streak-box {
        color: #ffc107;
        text-style: bold;
    }
    
    /* Filter Tabs and Buttons */
    .filter-tabs {
        layout: horizontal;
        dock: top;
        height: 1;
        border-bottom: solid #3a3a3a;
    }
    
    .filter-tab, .filter-btn {
        border: none;
        border-right: solid #3a3a3a;
        background: #181817;
        color: #9aa0b0;
    }
    
    .filter-tab.active, .filter-tab:hover, .filter-btn.active, .filter-btn:hover {
        background: #0a1543;
        color: #1b45d7;
    }
    
    .filter-buttons {
        layout: horizontal;
        margin: 1 0;
    }
    
    /* Action Buttons */
    .action-buttons {
        layout: vertical;
        margin: 1 0;
    }
    
    .action-btn {
        margin: 0 0 1 0;
        border: solid #3a3a3a;
        background: #181817;
    }
    
    .action-btn.complete { border: solid #4caf50; color: #4caf50; }
    .action-btn.edit { border: solid #ffc107; color: #ffc107; }
    .action-btn.delete { border: solid #f44336; color: #f44336; }
    
    /* Data Management Buttons */
    .data-btn {
        margin: 0 0 1 0;
        background: #0a1543;
        border: solid #3a3a3a;
    }
    
    .data-btn.danger {
        border: solid #f44336;
        color: #f44336;
    }
    
    /* Stats and Help */
    .stat-line, .help-item {
        margin: 0 0 1 0;
        padding: 0 0 0 1;
    }
    
    .help-section-title {
        color: #1b45d7;
        text-style: bold;
        margin: 2 0 1 0;
    }
    
    .help-item {
        color: #9aa0b0;
    }
    
    /* Leveling Screen */
    .level-progress {
        margin: 1 0;
    }
    
    .xp-text {
        text-align: center;
        margin: 1 0;
        color: #9aa0b0;
    }
    
    .next-level-info {
        text-align: center;
        color: #9aa0b0;
    }
    
    .stats-grid {
        layout: grid;
        grid-size: 2 2;
        grid-gutter: 1;
        margin: 2 0;
    }
    
    .stat-item {
        border: solid #3a3a3a;
        background: #0a1543;
        padding: 1;
        text-align: center;
    }
    
    .stat-box {
        text-align: center;
    }
    
    /* Badges */
    .badges-grid {
        layout: vertical;
        margin: 1 0;
    }
    
    .badge-row {
        layout: horizontal;
        margin: 0 0 1 0;
    }
    
    .badge {
        border: solid #3a3a3a;
        background: #0a1543;
        padding: 1;
        text-align: center;
        margin: 0 1 0 0;
        width: 1fr;
    }
    
    .badge.unlocked {
        border: solid #1b45d7;
        background: #19327f;
    }
    
    .badge.locked {
        opacity: 30%;
    }
    
    .progression-info {
        border: solid #3a3a3a;
        background: #0a1543;
        padding: 1;
        margin: 1 0;
    }
    
    .progression-text {
        color: #9aa0b0;
    }
    
    /* Journal */
    .journal-entry {
        border-left: thick #4caf50;
        padding-left: 1;
        margin: 1 0;
    }
    
    .journal-date {
        color: #9aa0b0;
    }
    
    .journal-summary {
        color: #1b45d7;
        text-style: bold;
    }
    
    .journal-details {
        color: #9aa0b0;
        margin: 1 0 0 0;
    }
    
    /* Forms */
    .form-container {
        width: 100%;
    }
    
    .form-row {
        margin: 1 0;
    }
    
    .form-row.large {
        margin: 2 0;
    }
    
    .form-label {
        color: #1b45d7;
        margin: 0 0 1 0;
    }
    
    Input, Select, TextArea {
        background: #0a1543;
        border: solid #3a3a3a;
        color: #e0e0e0;
    }
    
    Input:focus, Select:focus, TextArea:focus {
        border: solid #1b45d7;
    }
    
    /* Modals */
    .completion-modal, .level-up-modal, .info-modal, .confirm-modal {
        background: #0a1543;
        border: thick #1b45d7;
        width: 50;
        height: auto;
        text-align: center;
        padding: 2;
    }
    
    .completion-title, .level-up-title, .modal-title {
        color: #1b45d7;
        text-style: bold;
    }
    
    .completed-task {
        color: #1b45d7;
    }
    
    .xp-gained {
        color: #ffc107;
        text-style: bold;
    }
    
    .streak-info {
        color: #ffc107;
    }
    
    .level-up-text {
        color: #1b45d7;
        text-style: bold;
    }
    
    .modal-message {
        color: #e0e0e0;
    }
    
    .modal-buttons {
        layout: horizontal;
        margin: 1 0 0 0;
    }
    
    /* Progress Bars */
    ProgressBar > .bar--bar {
        color: #021fa0;
    }
    
    ProgressBar > .bar--complete {
        background: #1b45d7;
    }
    
    /* Buttons */
    Button {
        margin: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()

    def on_mount(self):
        self.push_screen(WelcomeScreen(self.data_manager))

    def action_quit(self):
        """Global quit action"""
        self.exit()


if __name__ == "__main__":
    app = QUESTAApp()
    app.run()
