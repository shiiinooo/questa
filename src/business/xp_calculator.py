"""XP calculation logic with difficulty-based rewards and bonus systems."""

from typing import Optional
from datetime import datetime, timedelta

from ..models.enums import TaskDifficulty
from ..models.task import Task
from ..models.player import PlayerData


class XPCalculator:
    """XP calculation with difficulty-based rewards and bonus logic."""
    
    # Bonus multipliers
    STREAK_BONUS_THRESHOLD = 3  # Minimum streak for bonus
    STREAK_BONUS_MULTIPLIER = 0.1  # 10% bonus per streak level
    MAX_STREAK_BONUS = 0.5  # Maximum 50% bonus
    
    DAILY_COMPLETION_BONUS = 5  # Flat bonus for completing tasks same day
    WEEKLY_COMPLETION_BONUS = 10  # Flat bonus for completing multiple tasks in a week
    
    # Priority multipliers
    PRIORITY_MULTIPLIERS = {
        'LOW': 1.0,
        'MEDIUM': 1.0,
        'HIGH': 1.1,  # 10% bonus for high priority
        'CRITICAL': 1.2  # 20% bonus for critical priority
    }
    
    @classmethod
    def calculate_base_xp(cls, difficulty: TaskDifficulty) -> int:
        """Calculate base XP from task difficulty.
        
        Args:
            difficulty: Task difficulty level
            
        Returns:
            int: Base XP amount
        """
        return difficulty.xp_value
    
    @classmethod
    def calculate_priority_bonus(cls, task: Task) -> float:
        """Calculate priority-based XP multiplier.
        
        Args:
            task: Task to calculate bonus for
            
        Returns:
            float: Priority multiplier (1.0 = no bonus)
        """
        priority_name = task.priority.name
        return cls.PRIORITY_MULTIPLIERS.get(priority_name, 1.0)
    
    @classmethod
    def calculate_streak_bonus(cls, player: PlayerData) -> float:
        """Calculate streak-based XP multiplier.
        
        Args:
            player: Player data with streak information
            
        Returns:
            float: Streak multiplier (1.0 = no bonus)
        """
        if player.current_streak < cls.STREAK_BONUS_THRESHOLD:
            return 1.0
        
        # Calculate bonus based on streak length
        streak_levels = player.current_streak - cls.STREAK_BONUS_THRESHOLD + 1
        bonus = min(streak_levels * cls.STREAK_BONUS_MULTIPLIER, cls.MAX_STREAK_BONUS)
        
        return 1.0 + bonus
    
    @classmethod
    def calculate_completion_bonus(cls, task: Task, player: PlayerData) -> int:
        """Calculate flat completion bonuses.
        
        Args:
            task: Completed task
            player: Player data
            
        Returns:
            int: Flat bonus XP amount
        """
        bonus = 0
        now = datetime.now()
        
        # Daily completion bonus - if task was created and completed same day
        if (task.created_at.date() == now.date()):
            bonus += cls.DAILY_COMPLETION_BONUS
        
        # Weekly completion bonus - if player has completed multiple tasks this week
        if player.last_activity:
            days_since_last = (now - player.last_activity).days
            if days_since_last <= 7 and player.current_streak >= 2:
                bonus += cls.WEEKLY_COMPLETION_BONUS
        
        return bonus
    
    @classmethod
    def calculate_bonus_xp(cls, task: Task, player: PlayerData) -> int:
        """Calculate total bonus XP for task completion.
        
        Args:
            task: Task being completed
            player: Current player data
            
        Returns:
            int: Total bonus XP amount
        """
        base_xp = cls.calculate_base_xp(task.difficulty)
        
        # Calculate multiplier bonuses
        priority_multiplier = cls.calculate_priority_bonus(task)
        streak_multiplier = cls.calculate_streak_bonus(player)
        
        # Apply multipliers to base XP
        multiplied_xp = base_xp * priority_multiplier * streak_multiplier
        multiplier_bonus = int(multiplied_xp - base_xp)
        
        # Calculate flat bonuses
        flat_bonus = cls.calculate_completion_bonus(task, player)
        
        return multiplier_bonus + flat_bonus
    
    @classmethod
    def calculate_total_xp(cls, task: Task, player: PlayerData) -> int:
        """Calculate total XP reward for task completion.
        
        Args:
            task: Task being completed
            player: Current player data
            
        Returns:
            int: Total XP reward (base + bonuses)
        """
        base_xp = cls.calculate_base_xp(task.difficulty)
        bonus_xp = cls.calculate_bonus_xp(task, player)
        
        return base_xp + bonus_xp
    
    @classmethod
    def calculate_level(cls, total_xp: int) -> int:
        """Calculate player level from total XP.
        
        Args:
            total_xp: Total XP accumulated
            
        Returns:
            int: Player level
        """
        # Use the same formula as PlayerData.level property
        if total_xp <= 0:
            return 1
        return int((total_xp / 100) ** 0.5) + 1
    
    @classmethod
    def calculate_xp_for_level(cls, level: int) -> int:
        """Calculate XP required to reach a specific level.
        
        Args:
            level: Target level
            
        Returns:
            int: XP required for that level
        """
        if level <= 1:
            return 0
        return (level - 1) ** 2 * 100
    
    @classmethod
    def calculate_xp_to_next_level(cls, current_xp: int) -> int:
        """Calculate XP needed to reach next level.
        
        Args:
            current_xp: Current XP amount
            
        Returns:
            int: XP needed for next level
        """
        current_level = cls.calculate_level(current_xp)
        next_level_xp = cls.calculate_xp_for_level(current_level + 1)
        
        return next_level_xp - current_xp
    
    @classmethod
    def preview_xp_reward(cls, task: Task, player: PlayerData) -> dict:
        """Preview XP reward breakdown for a task.
        
        Args:
            task: Task to preview reward for
            player: Current player data
            
        Returns:
            dict: Detailed XP breakdown
        """
        base_xp = cls.calculate_base_xp(task.difficulty)
        priority_multiplier = cls.calculate_priority_bonus(task)
        streak_multiplier = cls.calculate_streak_bonus(player)
        flat_bonus = cls.calculate_completion_bonus(task, player)
        total_xp = cls.calculate_total_xp(task, player)
        
        return {
            'base_xp': base_xp,
            'priority_multiplier': priority_multiplier,
            'streak_multiplier': streak_multiplier,
            'multiplier_bonus': int(base_xp * priority_multiplier * streak_multiplier - base_xp),
            'flat_bonus': flat_bonus,
            'total_bonus': total_xp - base_xp,
            'total_xp': total_xp,
            'breakdown': {
                'difficulty': f"{task.difficulty.display_name} ({base_xp} XP)",
                'priority': f"{task.priority.value} ({priority_multiplier:.1f}x)",
                'streak': f"{player.current_streak} tasks ({streak_multiplier:.1f}x)",
                'completion_bonus': f"{flat_bonus} XP"
            }
        }
    
    @classmethod
    def calculate_difficulty_adjustment(cls, current_difficulty: TaskDifficulty, 
                                      new_difficulty: TaskDifficulty) -> int:
        """Calculate XP adjustment when task difficulty changes.
        
        Args:
            current_difficulty: Current task difficulty
            new_difficulty: New task difficulty
            
        Returns:
            int: XP difference (positive = increase, negative = decrease)
        """
        current_xp = cls.calculate_base_xp(current_difficulty)
        new_xp = cls.calculate_base_xp(new_difficulty)
        
        return new_xp - current_xp