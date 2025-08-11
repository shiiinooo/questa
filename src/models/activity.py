"""Activity entry model for journal tracking."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from .enums import TaskDifficulty


class ActivityType(Enum):
    """Types of activities that can be logged."""
    
    TASK_COMPLETED = "task_completed"
    LEVEL_UP = "level_up"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    STREAK_MILESTONE = "streak_milestone"
    
    def __str__(self) -> str:
        return self.value


@dataclass
class ActivityEntry:
    """Activity entry for journal tracking with chronological display."""
    
    id: str = field(default_factory=lambda: str(__import__('uuid').uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    activity_type: ActivityType = ActivityType.TASK_COMPLETED
    description: str = ""
    xp_earned: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate activity entry after initialization."""
        if not self.description.strip():
            raise ValueError("Activity description cannot be empty")
        
        if self.xp_earned < 0:
            raise ValueError("XP earned cannot be negative")
        
        # Clean up description
        self.description = self.description.strip()
    
    @property
    def date_str(self) -> str:
        """Get formatted date string."""
        return self.timestamp.strftime("%Y-%m-%d")
    
    @property
    def time_str(self) -> str:
        """Get formatted time string."""
        return self.timestamp.strftime("%H:%M")
    
    @property
    def day_of_week(self) -> str:
        """Get day of week string."""
        return self.timestamp.strftime("%A")
    
    @property
    def is_task_completion(self) -> bool:
        """Check if this is a task completion activity."""
        return self.activity_type == ActivityType.TASK_COMPLETED
    
    @property
    def is_level_up(self) -> bool:
        """Check if this is a level up activity."""
        return self.activity_type == ActivityType.LEVEL_UP
    
    @property
    def is_achievement(self) -> bool:
        """Check if this is an achievement unlock activity."""
        return self.activity_type == ActivityType.ACHIEVEMENT_UNLOCKED
    
    @property
    def difficulty(self) -> Optional[TaskDifficulty]:
        """Get task difficulty if this is a task completion."""
        if self.is_task_completion and 'difficulty' in self.metadata:
            try:
                return TaskDifficulty[self.metadata['difficulty']]
            except (KeyError, ValueError):
                return None
        return None
    
    @property
    def task_title(self) -> Optional[str]:
        """Get task title if this is a task completion."""
        if self.is_task_completion:
            return self.metadata.get('task_title', self.description)
        return None
    
    @property
    def level_info(self) -> Optional[Dict[str, int]]:
        """Get level information if this is a level up."""
        if self.is_level_up:
            return {
                'old_level': self.metadata.get('old_level', 0),
                'new_level': self.metadata.get('new_level', 0)
            }
        return None
    
    @property
    def achievement_info(self) -> Optional[Dict[str, str]]:
        """Get achievement information if this is an achievement unlock."""
        if self.is_achievement:
            return {
                'achievement_name': self.metadata.get('achievement_name', ''),
                'achievement_description': self.metadata.get('achievement_description', ''),
                'badge_icon': self.metadata.get('badge_icon', '★')
            }
        return None
    
    def to_dict(self) -> dict:
        """Convert activity entry to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'activity_type': self.activity_type.value,
            'description': self.description,
            'xp_earned': self.xp_earned,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ActivityEntry':
        """Create activity entry from dictionary (JSON deserialization)."""
        return cls(
            id=data['id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            activity_type=ActivityType(data['activity_type']),
            description=data['description'],
            xp_earned=data['xp_earned'],
            metadata=data.get('metadata', {})
        )
    
    @classmethod
    def create_task_completion(
        cls,
        task_title: str,
        difficulty: TaskDifficulty,
        xp_earned: int,
        task_id: str = ""
    ) -> 'ActivityEntry':
        """Create a task completion activity entry."""
        return cls(
            activity_type=ActivityType.TASK_COMPLETED,
            description=f"Completed task: {task_title}",
            xp_earned=xp_earned,
            metadata={
                'task_title': task_title,
                'difficulty': difficulty.name,
                'task_id': task_id
            }
        )
    
    @classmethod
    def create_level_up(
        cls,
        old_level: int,
        new_level: int,
        total_xp: int
    ) -> 'ActivityEntry':
        """Create a level up activity entry."""
        return cls(
            activity_type=ActivityType.LEVEL_UP,
            description=f"Level up! Reached level {new_level}",
            xp_earned=0,  # Level up doesn't give additional XP
            metadata={
                'old_level': old_level,
                'new_level': new_level,
                'total_xp': total_xp
            }
        )
    
    @classmethod
    def create_achievement(
        cls,
        achievement_name: str,
        achievement_description: str,
        badge_icon: str = "★"
    ) -> 'ActivityEntry':
        """Create an achievement unlock activity entry."""
        return cls(
            activity_type=ActivityType.ACHIEVEMENT_UNLOCKED,
            description=f"Achievement unlocked: {achievement_name}",
            xp_earned=0,  # Achievements don't give XP directly
            metadata={
                'achievement_name': achievement_name,
                'achievement_description': achievement_description,
                'badge_icon': badge_icon
            }
        )