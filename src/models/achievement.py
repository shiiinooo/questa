"""Achievement system models for QUESTA application."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

from .player import PlayerData


class AchievementCategory(Enum):
    """Categories for organizing achievements."""
    
    PROGRESSION = "progression"
    COMPLETION = "completion"
    STREAK = "streak"
    DIFFICULTY = "difficulty"
    SPECIAL = "special"
    
    @property
    def display_name(self) -> str:
        """Get display name for the category."""
        return self.value.title()


@dataclass
class Achievement:
    """Achievement definition with unlock conditions."""
    
    id: str
    name: str
    description: str
    category: AchievementCategory
    badge_icon: str = "★"
    unlock_condition: Optional[Callable[[PlayerData], bool]] = None
    unlock_threshold: Optional[int] = None
    is_hidden: bool = False  # Hidden until unlocked
    
    def __post_init__(self):
        """Validate achievement after initialization."""
        if not self.id.strip():
            raise ValueError("Achievement ID cannot be empty")
        if not self.name.strip():
            raise ValueError("Achievement name cannot be empty")
        if not self.description.strip():
            raise ValueError("Achievement description cannot be empty")
    
    def check_unlock(self, player: PlayerData) -> bool:
        """Check if this achievement should be unlocked for the player."""
        if self.unlock_condition:
            return self.unlock_condition(player)
        return False
    
    def to_dict(self) -> dict:
        """Convert achievement to dictionary (excluding callable)."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'badge_icon': self.badge_icon,
            'unlock_threshold': self.unlock_threshold,
            'is_hidden': self.is_hidden
        }


@dataclass
class UnlockedAchievement:
    """Record of an unlocked achievement."""
    
    achievement_id: str
    unlocked_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'achievement_id': self.achievement_id,
            'unlocked_at': self.unlocked_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UnlockedAchievement':
        """Create from dictionary."""
        return cls(
            achievement_id=data['achievement_id'],
            unlocked_at=datetime.fromisoformat(data['unlocked_at'])
        )


class AchievementSystem:
    """Achievement system for tracking and unlocking achievements."""
    
    def __init__(self):
        self.achievements: Dict[str, Achievement] = {}
        self.unlocked: Dict[str, UnlockedAchievement] = {}
        self._initialize_achievements()
    
    def _initialize_achievements(self):
        """Initialize the default achievement set."""
        achievements = [
            # Progression achievements
            Achievement(
                id="first_steps",
                name="First Steps",
                description="Complete your first task",
                category=AchievementCategory.PROGRESSION,
                badge_icon="🚀",
                unlock_condition=lambda p: p.tasks_completed >= 1
            ),
            Achievement(
                id="level_5",
                name="Code Apprentice",
                description="Reach level 5",
                category=AchievementCategory.PROGRESSION,
                badge_icon="⭐",
                unlock_condition=lambda p: p.level >= 5,
                unlock_threshold=5
            ),
            Achievement(
                id="level_10",
                name="Code Journeyman",
                description="Reach level 10",
                category=AchievementCategory.PROGRESSION,
                badge_icon="🌟",
                unlock_condition=lambda p: p.level >= 10,
                unlock_threshold=10
            ),
            Achievement(
                id="level_20",
                name="Code Master",
                description="Reach level 20",
                category=AchievementCategory.PROGRESSION,
                badge_icon="💫",
                unlock_condition=lambda p: p.level >= 20,
                unlock_threshold=20
            ),
            
            # Completion achievements
            Achievement(
                id="task_warrior",
                name="Task Warrior",
                description="Complete 10 tasks",
                category=AchievementCategory.COMPLETION,
                badge_icon="⚔️",
                unlock_condition=lambda p: p.tasks_completed >= 10,
                unlock_threshold=10
            ),
            Achievement(
                id="task_champion",
                name="Task Champion",
                description="Complete 50 tasks",
                category=AchievementCategory.COMPLETION,
                badge_icon="🏆",
                unlock_condition=lambda p: p.tasks_completed >= 50,
                unlock_threshold=50
            ),
            Achievement(
                id="task_legend",
                name="Task Legend",
                description="Complete 100 tasks",
                category=AchievementCategory.COMPLETION,
                badge_icon="👑",
                unlock_condition=lambda p: p.tasks_completed >= 100,
                unlock_threshold=100
            ),
            
            # Streak achievements
            Achievement(
                id="on_fire",
                name="On Fire",
                description="Maintain a 5-task streak",
                category=AchievementCategory.STREAK,
                badge_icon="🔥",
                unlock_condition=lambda p: p.current_streak >= 5,
                unlock_threshold=5
            ),
            Achievement(
                id="unstoppable",
                name="Unstoppable",
                description="Maintain a 10-task streak",
                category=AchievementCategory.STREAK,
                badge_icon="⚡",
                unlock_condition=lambda p: p.current_streak >= 10,
                unlock_threshold=10
            ),
            Achievement(
                id="legendary_streak",
                name="Legendary Streak",
                description="Maintain a 25-task streak",
                category=AchievementCategory.STREAK,
                badge_icon="🌪️",
                unlock_condition=lambda p: p.current_streak >= 25,
                unlock_threshold=25
            ),
            
            # Difficulty achievements
            Achievement(
                id="easy_rider",
                name="Easy Rider",
                description="Complete 20 easy tasks",
                category=AchievementCategory.DIFFICULTY,
                badge_icon="🌱",
                unlock_condition=lambda p: p.easy_tasks_completed >= 20,
                unlock_threshold=20
            ),
            Achievement(
                id="challenge_seeker",
                name="Challenge Seeker",
                description="Complete 15 medium tasks",
                category=AchievementCategory.DIFFICULTY,
                badge_icon="⚖️",
                unlock_condition=lambda p: p.medium_tasks_completed >= 15,
                unlock_threshold=15
            ),
            Achievement(
                id="hard_mode",
                name="Hard Mode",
                description="Complete 10 hard tasks",
                category=AchievementCategory.DIFFICULTY,
                badge_icon="💎",
                unlock_condition=lambda p: p.hard_tasks_completed >= 10,
                unlock_threshold=10
            ),
            
            # Special achievements
            Achievement(
                id="xp_collector",
                name="XP Collector",
                description="Earn 1000 total XP",
                category=AchievementCategory.SPECIAL,
                badge_icon="💰",
                unlock_condition=lambda p: p.total_xp >= 1000,
                unlock_threshold=1000
            ),
            Achievement(
                id="dedication",
                name="Dedication",
                description="Complete tasks across multiple difficulty levels",
                category=AchievementCategory.SPECIAL,
                badge_icon="🎯",
                unlock_condition=lambda p: (
                    p.easy_tasks_completed >= 5 and 
                    p.medium_tasks_completed >= 5 and 
                    p.hard_tasks_completed >= 5
                )
            ),
        ]
        
        for achievement in achievements:
            self.achievements[achievement.id] = achievement
    
    def check_new_unlocks(self, player: PlayerData) -> List[Achievement]:
        """Check for newly unlocked achievements."""
        newly_unlocked = []
        
        for achievement in self.achievements.values():
            if (achievement.id not in self.unlocked and 
                achievement.check_unlock(player)):
                
                self.unlocked[achievement.id] = UnlockedAchievement(achievement.id)
                newly_unlocked.append(achievement)
        
        return newly_unlocked
    
    def get_unlocked_achievements(self) -> List[Achievement]:
        """Get all unlocked achievements."""
        return [
            self.achievements[achievement_id] 
            for achievement_id in self.unlocked.keys()
            if achievement_id in self.achievements
        ]
    
    def get_locked_achievements(self) -> List[Achievement]:
        """Get all locked achievements (excluding hidden ones)."""
        return [
            achievement for achievement in self.achievements.values()
            if (achievement.id not in self.unlocked and not achievement.is_hidden)
        ]
    
    def get_achievements_by_category(self, category: AchievementCategory) -> List[Achievement]:
        """Get all achievements in a specific category."""
        return [
            achievement for achievement in self.achievements.values()
            if achievement.category == category
        ]
    
    def get_progress_for_achievement(self, achievement_id: str, player: PlayerData) -> Optional[float]:
        """Get progress towards an achievement (0.0 to 1.0)."""
        if achievement_id not in self.achievements:
            return None
        
        achievement = self.achievements[achievement_id]
        if achievement.id in self.unlocked:
            return 1.0
        
        if not achievement.unlock_threshold:
            return 0.0
        
        # Calculate progress based on achievement type
        current_value = 0
        
        if achievement.category == AchievementCategory.PROGRESSION:
            current_value = player.level
        elif achievement.category == AchievementCategory.COMPLETION:
            current_value = player.tasks_completed
        elif achievement.category == AchievementCategory.STREAK:
            current_value = player.current_streak
        elif achievement.category == AchievementCategory.DIFFICULTY:
            if "easy" in achievement.id.lower():
                current_value = player.easy_tasks_completed
            elif "medium" in achievement.id.lower():
                current_value = player.medium_tasks_completed
            elif "hard" in achievement.id.lower():
                current_value = player.hard_tasks_completed
        elif achievement.category == AchievementCategory.SPECIAL:
            if "xp" in achievement.id.lower():
                current_value = player.total_xp
        
        return min(1.0, current_value / achievement.unlock_threshold)
    
    def to_dict(self) -> dict:
        """Convert achievement system to dictionary for serialization."""
        return {
            'unlocked': {
                achievement_id: unlocked.to_dict()
                for achievement_id, unlocked in self.unlocked.items()
            }
        }
    
    def from_dict(self, data: dict):
        """Load achievement system from dictionary."""
        if 'unlocked' in data:
            self.unlocked = {
                achievement_id: UnlockedAchievement.from_dict(unlocked_data)
                for achievement_id, unlocked_data in data['unlocked'].items()
            }


# Global achievement system instance
_achievement_system = AchievementSystem()


def get_achievement_system() -> AchievementSystem:
    """Get the global achievement system instance."""
    return _achievement_system