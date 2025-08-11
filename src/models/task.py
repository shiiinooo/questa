"""Task model with validation and business logic."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

from .enums import TaskDifficulty, TaskPriority, TaskStatus


@dataclass
class Task:
    """Task model with validation and business logic methods."""
    
    title: str
    difficulty: TaskDifficulty
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    notes: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate task data after initialization."""
        self._validate_title()
        self._calculate_xp_reward()
    
    def _validate_title(self) -> None:
        """Validate task title requirements."""
        if not self.title or not self.title.strip():
            raise ValueError("Task title cannot be empty")
        
        if len(self.title.strip()) > 200:
            raise ValueError("Task title cannot exceed 200 characters")
        
        # Clean up title
        self.title = self.title.strip()
    
    def _calculate_xp_reward(self) -> None:
        """Calculate XP reward based on difficulty."""
        self.xp_reward = self.difficulty.xp_value
    
    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == TaskStatus.COMPLETED
    
    @property
    def is_active(self) -> bool:
        """Check if task is active."""
        return self.status == TaskStatus.ACTIVE
    
    @property
    def is_blocked(self) -> bool:
        """Check if task is blocked."""
        return self.status == TaskStatus.BLOCKED
    
    def complete(self) -> int:
        """Mark task as completed and return XP earned."""
        if self.is_completed:
            raise ValueError("Task is already completed")
        
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        return self.xp_reward
    
    def can_transition_to(self, new_status: TaskStatus) -> bool:
        """Check if task can transition to new status."""
        return self.status.can_transition_to(new_status)
    
    def update_status(self, new_status: TaskStatus) -> None:
        """Update task status with validation."""
        if not self.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {self.status} to {new_status}")
        
        # Handle completion
        if new_status == TaskStatus.COMPLETED and not self.is_completed:
            self.completed_at = datetime.now()
        elif new_status != TaskStatus.COMPLETED and self.is_completed:
            # If moving away from completed, clear completion timestamp
            self.completed_at = None
        
        self.status = new_status
    
    def update_difficulty(self, new_difficulty: TaskDifficulty) -> None:
        """Update task difficulty and recalculate XP reward."""
        if self.is_completed:
            raise ValueError("Cannot change difficulty of completed task")
        
        self.difficulty = new_difficulty
        self._calculate_xp_reward()
    
    def to_dict(self) -> dict:
        """Convert task to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'difficulty': self.difficulty.name,
            'priority': self.priority.name,
            'status': self.status.name,
            'notes': self.notes,
            'xp_reward': self.xp_reward,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """Create task from dictionary (JSON deserialization)."""
        task = cls(
            id=data['id'],
            title=data['title'],
            difficulty=TaskDifficulty[data['difficulty']],
            priority=TaskPriority[data['priority']],
            status=TaskStatus[data['status']],
            notes=data.get('notes'),
            created_at=datetime.fromisoformat(data['created_at']),
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None
        )
        task.xp_reward = data['xp_reward']
        return task