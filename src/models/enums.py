"""Core enumerations for the task management system."""

from enum import Enum
from typing import Tuple


class TaskDifficulty(Enum):
    """Task difficulty levels with associated XP rewards."""
    
    EASY = ("Easy", 15)
    MEDIUM = ("Medium", 30)
    HARD = ("Hard", 50)
    
    def __init__(self, display_name: str, xp_value: int):
        self.display_name = display_name
        self.xp_value = xp_value
    
    def __str__(self) -> str:
        return self.display_name


class TaskPriority(Enum):
    """Task priority levels."""
    
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"
    
    def __str__(self) -> str:
        return self.value


class TaskStatus(Enum):
    """Task status states with transition rules."""
    
    PENDING = "Pending"
    ACTIVE = "Active"
    BLOCKED = "Blocked"
    COMPLETED = "Completed"
    
    def __str__(self) -> str:
        return self.value
    
    def can_transition_to(self, new_status: 'TaskStatus') -> bool:
        """Check if transition to new status is allowed."""
        valid_transitions = {
            TaskStatus.PENDING: {TaskStatus.ACTIVE, TaskStatus.BLOCKED, TaskStatus.COMPLETED},
            TaskStatus.ACTIVE: {TaskStatus.PENDING, TaskStatus.BLOCKED, TaskStatus.COMPLETED},
            TaskStatus.BLOCKED: {TaskStatus.PENDING, TaskStatus.ACTIVE, TaskStatus.COMPLETED},
            TaskStatus.COMPLETED: set()  # No transitions allowed from completed
        }
        
        return new_status in valid_transitions.get(self, set())