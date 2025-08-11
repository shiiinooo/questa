#!/usr/bin/env python3
"""Test script for the journal screen and activity timeline."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from datetime import datetime, timedelta
from textual.app import App

from src.models.activity import ActivityEntry, ActivityType
from src.models.enums import TaskDifficulty
from src.screens.journal_screen import JournalScreen, create_sample_activities


class TestJournalApp(App):
    """Test application for the journal screen."""
    
    def on_mount(self) -> None:
        """Initialize the app with sample data."""
        # Create sample activities
        activities = create_sample_activities()
        
        # Add some additional test activities
        now = datetime.now()
        
        # Add more varied activities
        activities.extend([
            ActivityEntry.create_task_completion(
                "Refactor database queries", TaskDifficulty.HARD, 50, "task-5"
            ),
            ActivityEntry.create_achievement(
                "Speed Demon", "Completed 5 tasks in one day", "⚡"
            ),
            ActivityEntry(
                timestamp=now - timedelta(days=2),
                activity_type=ActivityType.TASK_COMPLETED,
                description="Write unit tests",
                xp_earned=30,
                metadata={
                    'task_title': "Write unit tests",
                    'difficulty': TaskDifficulty.MEDIUM.name,
                    'task_id': "task-6"
                }
            ),
            ActivityEntry.create_level_up(3, 4, 400),
        ])
        
        # Sort activities by timestamp (newest first)
        activities.sort(key=lambda a: a.timestamp, reverse=True)
        
        # Push the journal screen
        journal_screen = JournalScreen(activities)
        self.push_screen(journal_screen)


if __name__ == "__main__":
    app = TestJournalApp()
    app.run()