"""Unit tests for XPCalculator with comprehensive calculation scenarios."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from src.business.xp_calculator import XPCalculator
from src.models.enums import TaskDifficulty, TaskPriority, TaskStatus
from src.models.task import Task
from src.models.player import PlayerData


class TestXPCalculator:
    """Test XPCalculator calculation methods."""
    
    def test_calculate_base_xp(self):
        """Test base XP calculation from difficulty."""
        assert XPCalculator.calculate_base_xp(TaskDifficulty.EASY) == 15
        assert XPCalculator.calculate_base_xp(TaskDifficulty.MEDIUM) == 30
        assert XPCalculator.calculate_base_xp(TaskDifficulty.HARD) == 50
    
    def test_calculate_priority_bonus_no_bonus(self):
        """Test priority bonus calculation with no bonus priorities."""
        task = Mock()
        task.priority.name = 'LOW'
        assert XPCalculator.calculate_priority_bonus(task) == 1.0
        
        task.priority.name = 'MEDIUM'
        assert XPCalculator.calculate_priority_bonus(task) == 1.0
    
    def test_calculate_priority_bonus_with_bonus(self):
        """Test priority bonus calculation with bonus priorities."""
        task = Mock()
        task.priority.name = 'HIGH'
        assert XPCalculator.calculate_priority_bonus(task) == 1.1
        
        task.priority.name = 'CRITICAL'
        assert XPCalculator.calculate_priority_bonus(task) == 1.2
    
    def test_calculate_streak_bonus_no_streak(self):
        """Test streak bonus calculation with no streak."""
        player = PlayerData(current_streak=0)
        assert XPCalculator.calculate_streak_bonus(player) == 1.0
        
        player = PlayerData(current_streak=2)
        assert XPCalculator.calculate_streak_bonus(player) == 1.0
    
    def test_calculate_streak_bonus_with_streak(self):
        """Test streak bonus calculation with active streak."""
        player = PlayerData(current_streak=3)
        expected = 1.0 + 0.1  # 10% bonus for first streak level
        assert XPCalculator.calculate_streak_bonus(player) == expected
        
        player = PlayerData(current_streak=5)
        expected = 1.0 + (3 * 0.1)  # 30% bonus for 3 streak levels
        assert XPCalculator.calculate_streak_bonus(player) == expected
    
    def test_calculate_streak_bonus_max_cap(self):
        """Test streak bonus calculation with maximum cap."""
        player = PlayerData(current_streak=10)
        expected = 1.0 + 0.5  # Capped at 50% bonus
        assert XPCalculator.calculate_streak_bonus(player) == expected
    
    def test_calculate_completion_bonus_same_day(self):
        """Test completion bonus for same-day task completion."""
        now = datetime.now()
        task = Mock()
        task.created_at = now
        
        player = PlayerData()
        
        bonus = XPCalculator.calculate_completion_bonus(task, player)
        assert bonus == 5  # Daily completion bonus
    
    def test_calculate_completion_bonus_different_day(self):
        """Test completion bonus for different-day task completion."""
        yesterday = datetime.now() - timedelta(days=1)
        task = Mock()
        task.created_at = yesterday
        
        player = PlayerData()
        
        bonus = XPCalculator.calculate_completion_bonus(task, player)
        assert bonus == 0  # No daily bonus
    
    def test_calculate_completion_bonus_weekly_streak(self):
        """Test completion bonus with weekly streak."""
        now = datetime.now()
        task = Mock()
        task.created_at = now
        
        player = PlayerData(
            current_streak=3,
            last_activity=now - timedelta(days=3)
        )
        
        bonus = XPCalculator.calculate_completion_bonus(task, player)
        expected = 5 + 10  # Daily + weekly bonus
        assert bonus == expected
    
    def test_calculate_completion_bonus_no_weekly_streak(self):
        """Test completion bonus without qualifying weekly streak."""
        now = datetime.now()
        task = Mock()
        task.created_at = now
        
        # Too long since last activity
        player = PlayerData(
            current_streak=3,
            last_activity=now - timedelta(days=8)
        )
        
        bonus = XPCalculator.calculate_completion_bonus(task, player)
        assert bonus == 5  # Only daily bonus
        
        # Not enough streak
        player = PlayerData(
            current_streak=1,
            last_activity=now - timedelta(days=3)
        )
        
        bonus = XPCalculator.calculate_completion_bonus(task, player)
        assert bonus == 5  # Only daily bonus
    
    def test_calculate_bonus_xp_comprehensive(self):
        """Test comprehensive bonus XP calculation."""
        task = Mock()
        task.difficulty = TaskDifficulty.MEDIUM  # 30 base XP
        task.priority.name = 'HIGH'  # 1.1x multiplier
        task.created_at = datetime.now()  # Same day = 5 bonus
        
        player = PlayerData(
            current_streak=4,  # 1.2x multiplier
            last_activity=datetime.now() - timedelta(days=2)  # Weekly bonus = 10
        )
        
        bonus_xp = XPCalculator.calculate_bonus_xp(task, player)
        
        # Base XP: 30
        # Multipliers: 1.1 * 1.2 = 1.32
        # Multiplied XP: 30 * 1.32 = 39.6
        # Multiplier bonus: 39.6 - 30 = 9.6 -> 9 (int)
        # Flat bonus: 5 (daily) + 10 (weekly) = 15
        # Total bonus: 9 + 15 = 24
        expected = 9 + 15
        assert bonus_xp == expected
    
    def test_calculate_total_xp(self):
        """Test total XP calculation."""
        task = Mock()
        task.difficulty = TaskDifficulty.EASY  # 15 base XP
        task.priority.name = 'LOW'  # 1.0x multiplier
        task.created_at = datetime.now() - timedelta(days=1)  # No daily bonus
        
        player = PlayerData(current_streak=0)  # No streak bonus
        
        total_xp = XPCalculator.calculate_total_xp(task, player)
        assert total_xp == 15  # Just base XP
    
    def test_calculate_level(self):
        """Test level calculation from XP."""
        assert XPCalculator.calculate_level(0) == 1
        assert XPCalculator.calculate_level(100) == 2
        assert XPCalculator.calculate_level(400) == 3
        assert XPCalculator.calculate_level(900) == 4
    
    def test_calculate_xp_for_level(self):
        """Test XP required for specific levels."""
        assert XPCalculator.calculate_xp_for_level(1) == 0
        assert XPCalculator.calculate_xp_for_level(2) == 100
        assert XPCalculator.calculate_xp_for_level(3) == 400
        assert XPCalculator.calculate_xp_for_level(4) == 900
    
    def test_calculate_xp_to_next_level(self):
        """Test XP needed to reach next level."""
        assert XPCalculator.calculate_xp_to_next_level(0) == 100  # Level 1 -> 2
        assert XPCalculator.calculate_xp_to_next_level(50) == 50   # Level 1 -> 2
        assert XPCalculator.calculate_xp_to_next_level(150) == 250 # Level 2 -> 3
        assert XPCalculator.calculate_xp_to_next_level(500) == 400 # Level 3 -> 4
    
    def test_preview_xp_reward(self):
        """Test XP reward preview with detailed breakdown."""
        task = Mock()
        task.difficulty = TaskDifficulty.MEDIUM  # 30 base XP
        task.priority = Mock()
        task.priority.name = 'HIGH'  # 1.1x multiplier
        task.priority.value = 'High'
        task.created_at = datetime.now()  # Same day = 5 bonus
        
        player = PlayerData(
            current_streak=3,  # 1.1x multiplier
            last_activity=datetime.now() - timedelta(days=2)  # Weekly bonus = 10
        )
        
        preview = XPCalculator.preview_xp_reward(task, player)
        
        assert preview['base_xp'] == 30
        assert preview['priority_multiplier'] == 1.1
        assert preview['streak_multiplier'] == 1.1
        assert preview['flat_bonus'] == 15  # 5 daily + 10 weekly
        assert 'breakdown' in preview
        assert 'Medium (30 XP)' in preview['breakdown']['difficulty']
        assert 'High (1.1x)' in preview['breakdown']['priority']
        assert '3 tasks (1.1x)' in preview['breakdown']['streak']
        assert '15 XP' in preview['breakdown']['completion_bonus']
    
    def test_calculate_difficulty_adjustment(self):
        """Test XP adjustment when difficulty changes."""
        # Easy to Medium: +15 XP
        adjustment = XPCalculator.calculate_difficulty_adjustment(
            TaskDifficulty.EASY, TaskDifficulty.MEDIUM
        )
        assert adjustment == 15
        
        # Hard to Easy: -35 XP
        adjustment = XPCalculator.calculate_difficulty_adjustment(
            TaskDifficulty.HARD, TaskDifficulty.EASY
        )
        assert adjustment == -35
        
        # Same difficulty: 0 XP
        adjustment = XPCalculator.calculate_difficulty_adjustment(
            TaskDifficulty.MEDIUM, TaskDifficulty.MEDIUM
        )
        assert adjustment == 0
    
    def test_edge_cases_negative_values(self):
        """Test edge cases with negative or zero values."""
        # Negative XP should still return level 1
        assert XPCalculator.calculate_level(-100) == 1
        
        # Zero streak should return 1.0 multiplier
        player = PlayerData(current_streak=0)
        assert XPCalculator.calculate_streak_bonus(player) == 1.0
    
    def test_real_world_scenario(self):
        """Test realistic task completion scenario."""
        # Create a real task (not mock)
        task = Task(
            title="Implement user authentication",
            difficulty=TaskDifficulty.HARD,
            priority=TaskPriority.CRITICAL,
            status=TaskStatus.PENDING
        )
        
        # Player with some progress
        player = PlayerData(
            total_xp=250,
            tasks_completed=8,
            current_streak=5
        )
        
        # Calculate total XP
        total_xp = XPCalculator.calculate_total_xp(task, player)
        
        # Should be base (50) + priority bonus + streak bonus
        # Base: 50, Priority: 1.2x, Streak: 1.3x
        # Multiplied: 50 * 1.2 * 1.3 = 78
        # No flat bonuses (different day, no recent activity)
        assert total_xp >= 50  # At least base XP
        assert total_xp > 50   # Should have bonuses
    
    def test_bonus_calculation_precision(self):
        """Test that bonus calculations handle floating point precision correctly."""
        task = Mock()
        task.difficulty = TaskDifficulty.MEDIUM  # 30 XP
        task.priority.name = 'HIGH'  # 1.1x
        task.created_at = datetime.now() - timedelta(days=1)  # No daily bonus
        
        player = PlayerData(
            current_streak=4,  # 1.2x
            last_activity=None  # No weekly bonus
        )
        
        bonus_xp = XPCalculator.calculate_bonus_xp(task, player)
        
        # 30 * 1.1 * 1.2 = 39.6, bonus = 39.6 - 30 = 9.6 -> 9 (int conversion)
        assert isinstance(bonus_xp, int)
        assert bonus_xp == 9