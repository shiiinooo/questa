"""Player data model with level calculation and progress tracking."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import math


@dataclass
class PlayerData:
    """Player data with level calculation and progress tracking."""
    
    total_xp: int = 0
    tasks_completed: int = 0
    current_streak: int = 0
    last_activity: Optional[datetime] = None
    easy_tasks_completed: int = 0
    medium_tasks_completed: int = 0
    hard_tasks_completed: int = 0
    
    def __post_init__(self):
        """Validate player data after initialization."""
        if self.total_xp < 0:
            raise ValueError("Total XP cannot be negative")
        if self.tasks_completed < 0:
            raise ValueError("Tasks completed cannot be negative")
        if self.current_streak < 0:
            raise ValueError("Current streak cannot be negative")
    
    @property
    def level(self) -> int:
        """Calculate player level based on total XP.
        
        Level formula: level = floor(sqrt(total_xp / 100)) + 1
        This creates a progression where each level requires more XP than the last.
        """
        if self.total_xp <= 0:
            return 1
        return int(math.sqrt(self.total_xp / 100)) + 1
    
    @property
    def xp_for_current_level(self) -> int:
        """Calculate XP required to reach current level."""
        if self.level <= 1:
            return 0
        return (self.level - 1) ** 2 * 100
    
    @property
    def xp_for_next_level(self) -> int:
        """Calculate XP required to reach next level."""
        return self.level ** 2 * 100
    
    @property
    def xp_to_next_level(self) -> int:
        """Calculate XP needed to reach next level."""
        return self.xp_for_next_level - self.total_xp
    
    @property
    def current_level_xp(self) -> int:
        """Calculate XP earned within current level."""
        return self.total_xp - self.xp_for_current_level
    
    @property
    def level_progress(self) -> float:
        """Calculate progress towards next level as percentage (0.0 to 1.0)."""
        current_level_xp = self.xp_for_current_level
        next_level_xp = self.xp_for_next_level
        level_xp_range = next_level_xp - current_level_xp
        
        if level_xp_range <= 0:
            return 1.0
        
        progress_in_level = self.total_xp - current_level_xp
        return min(1.0, max(0.0, progress_in_level / level_xp_range))
    
    def add_xp(self, xp_amount: int) -> tuple[int, bool]:
        """Add XP and return (new_level, level_up_occurred)."""
        if xp_amount < 0:
            raise ValueError("XP amount cannot be negative")
        
        old_level = self.level
        self.total_xp += xp_amount
        new_level = self.level
        
        return new_level, new_level > old_level
    
    def complete_task(self, xp_earned: int, difficulty_name: str) -> tuple[int, bool]:
        """Record task completion and return (new_level, level_up_occurred)."""
        self.tasks_completed += 1
        self.last_activity = datetime.now()
        
        # Update difficulty-specific counters
        difficulty_lower = difficulty_name.lower()
        if difficulty_lower == 'easy':
            self.easy_tasks_completed += 1
        elif difficulty_lower == 'medium':
            self.medium_tasks_completed += 1
        elif difficulty_lower == 'hard':
            self.hard_tasks_completed += 1
        
        # Update streak (simplified - could be enhanced with date logic)
        self.current_streak += 1
        
        return self.add_xp(xp_earned)
    
    def reset_streak(self) -> None:
        """Reset the current streak to 0."""
        self.current_streak = 0
    
    def get_statistics(self) -> dict:
        """Get player statistics summary."""
        return {
            'level': self.level,
            'total_xp': self.total_xp,
            'xp_to_next_level': self.xp_to_next_level,
            'level_progress': self.level_progress,
            'tasks_completed': self.tasks_completed,
            'current_streak': self.current_streak,
            'easy_tasks_completed': self.easy_tasks_completed,
            'medium_tasks_completed': self.medium_tasks_completed,
            'hard_tasks_completed': self.hard_tasks_completed,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None
        }
    
    def to_dict(self) -> dict:
        """Convert player data to dictionary for JSON serialization."""
        return {
            'total_xp': self.total_xp,
            'tasks_completed': self.tasks_completed,
            'current_streak': self.current_streak,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'easy_tasks_completed': self.easy_tasks_completed,
            'medium_tasks_completed': self.medium_tasks_completed,
            'hard_tasks_completed': self.hard_tasks_completed
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PlayerData':
        """Create player data from dictionary (JSON deserialization)."""
        return cls(
            total_xp=data.get('total_xp', 0),
            tasks_completed=data.get('tasks_completed', 0),
            current_streak=data.get('current_streak', 0),
            last_activity=datetime.fromisoformat(data['last_activity']) if data.get('last_activity') else None,
            easy_tasks_completed=data.get('easy_tasks_completed', 0),
            medium_tasks_completed=data.get('medium_tasks_completed', 0),
            hard_tasks_completed=data.get('hard_tasks_completed', 0)
        )