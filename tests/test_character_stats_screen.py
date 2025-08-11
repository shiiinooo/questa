"""Tests for CharacterStatsScreen and achievement system."""

import pytest
from unittest.mock import Mock, patch

from src.screens.character_stats_screen import CharacterStatsScreen, LevelProgressPanel, AchievementGrid, StatisticsPanel
from src.models.player import PlayerData
from src.models.achievement import get_achievement_system, AchievementCategory


class TestCharacterStatsScreen:
    """Test CharacterStatsScreen functionality."""
    
    def test_screen_initialization(self):
        """Test that CharacterStatsScreen initializes correctly."""
        with patch('src.screens.character_stats_screen.DataManager') as mock_data_manager:
            mock_data_manager.return_value.load_player_data.return_value = PlayerData()
            
            screen = CharacterStatsScreen()
            
            assert screen.data_manager is not None
            assert screen.player is not None
            assert screen.achievement_system is not None
            assert screen.theme is not None


class TestLevelProgressPanel:
    """Test LevelProgressPanel functionality."""
    
    def test_level_progress_panel_initialization(self):
        """Test that LevelProgressPanel initializes with player data."""
        player = PlayerData(total_xp=500, tasks_completed=10)
        panel = LevelProgressPanel(player)
        
        assert panel.player == player
        assert panel.ascii_gen is not None
    
    def test_get_level_title(self):
        """Test level title generation for different levels."""
        # Test different level ranges
        test_cases = [
            (1, "Novice Coder"),
            (3, "Junior Developer"),
            (5, "Code Apprentice"),
            (10, "Code Journeyman"),
            (15, "Senior Developer"),
            (20, "Code Master"),
            (25, "Code Master")  # Max title
        ]
        
        for level_xp, expected_title in test_cases:
            # Calculate XP needed for this level (level = floor(sqrt(xp/100)) + 1)
            if level_xp == 1:
                xp = 0
            else:
                xp = (level_xp - 1) ** 2 * 100
            
            player = PlayerData(total_xp=xp)
            panel = LevelProgressPanel(player)
            
            assert panel._get_level_title() == expected_title


class TestAchievementSystem:
    """Test achievement system functionality."""
    
    def test_achievement_system_initialization(self):
        """Test that achievement system initializes with default achievements."""
        achievement_system = get_achievement_system()
        
        assert len(achievement_system.achievements) > 0
        assert len(achievement_system.unlocked) == 0  # Initially no achievements unlocked
    
    def test_check_new_unlocks_first_task(self):
        """Test that completing first task unlocks 'First Steps' achievement."""
        achievement_system = get_achievement_system()
        achievement_system.unlocked.clear()  # Reset for test
        
        player = PlayerData(tasks_completed=1, total_xp=50)
        newly_unlocked = achievement_system.check_new_unlocks(player)
        
        # Should unlock "First Steps"
        assert len(newly_unlocked) >= 1
        first_steps = next((a for a in newly_unlocked if a.id == "first_steps"), None)
        assert first_steps is not None
        assert first_steps.name == "First Steps"
    
    def test_check_new_unlocks_multiple_achievements(self):
        """Test unlocking multiple achievements at once."""
        achievement_system = get_achievement_system()
        achievement_system.unlocked.clear()  # Reset for test
        
        # Player with stats that should unlock multiple achievements
        player = PlayerData(
            total_xp=1250,  # Should unlock XP Collector
            tasks_completed=25,  # Should unlock Task Warrior
            current_streak=8,  # Should unlock On Fire
            easy_tasks_completed=12,
            medium_tasks_completed=8,
            hard_tasks_completed=5  # Should unlock Dedication
        )
        
        newly_unlocked = achievement_system.check_new_unlocks(player)
        
        # Should unlock multiple achievements
        assert len(newly_unlocked) >= 4
        
        unlocked_ids = {a.id for a in newly_unlocked}
        expected_ids = {"first_steps", "task_warrior", "on_fire", "xp_collector", "dedication"}
        
        # Check that expected achievements are unlocked
        assert expected_ids.issubset(unlocked_ids)
    
    def test_get_progress_for_achievement(self):
        """Test progress calculation for achievements."""
        achievement_system = get_achievement_system()
        achievement_system.unlocked.clear()  # Reset for test
        
        player = PlayerData(tasks_completed=5, total_xp=500)
        
        # Test progress for Task Warrior (needs 10 tasks)
        progress = achievement_system.get_progress_for_achievement("task_warrior", player)
        assert progress == 0.5  # 5/10 = 50%
        
        # Test progress for XP Collector (needs 1000 XP)
        progress = achievement_system.get_progress_for_achievement("xp_collector", player)
        assert progress == 0.5  # 500/1000 = 50%
    
    def test_get_achievements_by_category(self):
        """Test filtering achievements by category."""
        achievement_system = get_achievement_system()
        
        progression_achievements = achievement_system.get_achievements_by_category(AchievementCategory.PROGRESSION)
        completion_achievements = achievement_system.get_achievements_by_category(AchievementCategory.COMPLETION)
        streak_achievements = achievement_system.get_achievements_by_category(AchievementCategory.STREAK)
        
        assert len(progression_achievements) > 0
        assert len(completion_achievements) > 0
        assert len(streak_achievements) > 0
        
        # Verify categories are correct
        for achievement in progression_achievements:
            assert achievement.category == AchievementCategory.PROGRESSION
        
        for achievement in completion_achievements:
            assert achievement.category == AchievementCategory.COMPLETION


class TestAchievementGrid:
    """Test AchievementGrid functionality."""
    
    def test_achievement_grid_initialization(self):
        """Test that AchievementGrid initializes correctly."""
        player = PlayerData(total_xp=500, tasks_completed=10)
        grid = AchievementGrid(player)
        
        assert grid.player == player
        assert grid.achievement_system is not None
        assert grid.current_filter == AchievementCategory.PROGRESSION


class TestStatisticsPanel:
    """Test StatisticsPanel functionality."""
    
    def test_statistics_panel_initialization(self):
        """Test that StatisticsPanel initializes with player data."""
        player = PlayerData(
            total_xp=1250,
            tasks_completed=25,
            current_streak=8,
            easy_tasks_completed=12,
            medium_tasks_completed=8,
            hard_tasks_completed=5
        )
        
        panel = StatisticsPanel(player)
        assert panel.player == player
        
        # Verify player data is accessible
        assert panel.player.total_xp == 1250
        assert panel.player.tasks_completed == 25
        assert panel.player.current_streak == 8
        assert panel.player.easy_tasks_completed == 12
        assert panel.player.medium_tasks_completed == 8
        assert panel.player.hard_tasks_completed == 5


class TestAchievementBadge:
    """Test AchievementBadge functionality."""
    
    def test_achievement_badge_unlocked(self):
        """Test achievement badge for unlocked achievement."""
        from src.screens.character_stats_screen import AchievementBadge
        from src.models.achievement import Achievement, AchievementCategory
        
        achievement = Achievement(
            id="test_achievement",
            name="Test Achievement",
            description="A test achievement",
            category=AchievementCategory.PROGRESSION,
            badge_icon="🏆"
        )
        
        badge = AchievementBadge(achievement, is_unlocked=True)
        
        assert badge.achievement == achievement
        assert badge.is_unlocked == True
        assert badge.progress == 0.0
        assert badge.has_class("unlocked")
        assert not badge.has_class("locked")
    
    def test_achievement_badge_locked_with_progress(self):
        """Test achievement badge for locked achievement with progress."""
        from src.screens.character_stats_screen import AchievementBadge
        from src.models.achievement import Achievement, AchievementCategory
        
        achievement = Achievement(
            id="test_achievement",
            name="Test Achievement",
            description="A test achievement",
            category=AchievementCategory.COMPLETION,
            badge_icon="⭐"
        )
        
        badge = AchievementBadge(achievement, is_unlocked=False, progress=0.75)
        
        assert badge.achievement == achievement
        assert badge.is_unlocked == False
        assert badge.progress == 0.75
        assert not badge.has_class("unlocked")
        assert badge.has_class("locked")