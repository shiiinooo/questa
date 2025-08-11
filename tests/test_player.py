"""Tests for PlayerData model."""

import pytest
from datetime import datetime
from src.models.player import PlayerData


class TestPlayerData:
    """Test PlayerData model."""
    
    def test_player_creation_with_defaults(self):
        """Test creating player with default values."""
        player = PlayerData()
        
        assert player.total_xp == 0
        assert player.tasks_completed == 0
        assert player.current_streak == 0
        assert player.last_activity is None
        assert player.easy_tasks_completed == 0
        assert player.medium_tasks_completed == 0
        assert player.hard_tasks_completed == 0
    
    def test_player_creation_with_values(self):
        """Test creating player with specific values."""
        last_activity = datetime.now()
        player = PlayerData(
            total_xp=150,
            tasks_completed=10,
            current_streak=5,
            last_activity=last_activity,
            easy_tasks_completed=6,
            medium_tasks_completed=3,
            hard_tasks_completed=1
        )
        
        assert player.total_xp == 150
        assert player.tasks_completed == 10
        assert player.current_streak == 5
        assert player.last_activity == last_activity
        assert player.easy_tasks_completed == 6
        assert player.medium_tasks_completed == 3
        assert player.hard_tasks_completed == 1
    
    def test_player_validation(self):
        """Test player data validation."""
        # Negative total XP should raise error
        with pytest.raises(ValueError, match="Total XP cannot be negative"):
            PlayerData(total_xp=-10)
        
        # Negative tasks completed should raise error
        with pytest.raises(ValueError, match="Tasks completed cannot be negative"):
            PlayerData(tasks_completed=-1)
        
        # Negative streak should raise error
        with pytest.raises(ValueError, match="Current streak cannot be negative"):
            PlayerData(current_streak=-1)
    
    def test_level_calculation(self):
        """Test player level calculation."""
        player = PlayerData()
        
        # Level 1 with 0 XP
        assert player.level == 1
        
        # Level 1 with small XP
        player.total_xp = 50
        assert player.level == 1
        
        # Level 2 at 100 XP
        player.total_xp = 100
        assert player.level == 2
        
        # Level 3 at 400 XP
        player.total_xp = 400
        assert player.level == 3
        
        # Level 4 at 900 XP
        player.total_xp = 900
        assert player.level == 4
        
        # Level 10 at 8100 XP
        player.total_xp = 8100
        assert player.level == 10
    
    def test_xp_calculations(self):
        """Test XP calculation properties."""
        player = PlayerData(total_xp=250)  # Level 2
        
        assert player.level == 2
        assert player.xp_for_current_level == 100  # Level 2 starts at 100 XP
        assert player.xp_for_next_level == 400     # Level 3 starts at 400 XP
        assert player.xp_to_next_level == 150      # 400 - 250 = 150
    
    def test_level_progress(self):
        """Test level progress calculation."""
        player = PlayerData()
        
        # At level 1 with 0 XP
        player.total_xp = 0
        assert player.level_progress == 0.0
        
        # At level 1 with 50 XP (halfway to level 2)
        player.total_xp = 50
        assert player.level_progress == 0.5
        
        # At level 1 with 99 XP (almost level 2)
        player.total_xp = 99
        assert abs(player.level_progress - 0.99) < 0.01
        
        # At level 2 with 100 XP (start of level 2)
        player.total_xp = 100
        assert player.level_progress == 0.0
        
        # At level 2 with 250 XP (halfway to level 3)
        player.total_xp = 250
        assert player.level_progress == 0.5
    
    def test_add_xp(self):
        """Test adding XP and level up detection."""
        player = PlayerData(total_xp=50)
        
        # Add XP without level up
        new_level, level_up = player.add_xp(30)
        assert player.total_xp == 80
        assert new_level == 1
        assert not level_up
        
        # Add XP with level up
        new_level, level_up = player.add_xp(50)  # Total becomes 130
        assert player.total_xp == 130
        assert new_level == 2
        assert level_up
        
        # Cannot add negative XP
        with pytest.raises(ValueError, match="XP amount cannot be negative"):
            player.add_xp(-10)
    
    def test_complete_task(self):
        """Test task completion tracking."""
        player = PlayerData()
        
        # Complete easy task
        new_level, level_up = player.complete_task(15, "easy")
        
        assert player.total_xp == 15
        assert player.tasks_completed == 1
        assert player.easy_tasks_completed == 1
        assert player.medium_tasks_completed == 0
        assert player.hard_tasks_completed == 0
        assert player.current_streak == 1
        assert isinstance(player.last_activity, datetime)
        assert new_level == 1
        assert not level_up
        
        # Complete medium task
        new_level, level_up = player.complete_task(30, "medium")
        
        assert player.total_xp == 45
        assert player.tasks_completed == 2
        assert player.easy_tasks_completed == 1
        assert player.medium_tasks_completed == 1
        assert player.hard_tasks_completed == 0
        assert player.current_streak == 2
        
        # Complete hard task with level up
        new_level, level_up = player.complete_task(50, "hard")
        
        assert player.total_xp == 95
        assert player.tasks_completed == 3
        assert player.easy_tasks_completed == 1
        assert player.medium_tasks_completed == 1
        assert player.hard_tasks_completed == 1
        assert player.current_streak == 3
        
        # Complete another task to trigger level up
        new_level, level_up = player.complete_task(15, "easy")
        
        assert player.total_xp == 110
        assert new_level == 2
        assert level_up
    
    def test_reset_streak(self):
        """Test streak reset functionality."""
        player = PlayerData(current_streak=5)
        
        player.reset_streak()
        assert player.current_streak == 0
    
    def test_get_statistics(self):
        """Test statistics summary."""
        last_activity = datetime.now()
        player = PlayerData(
            total_xp=250,
            tasks_completed=10,
            current_streak=3,
            last_activity=last_activity,
            easy_tasks_completed=6,
            medium_tasks_completed=3,
            hard_tasks_completed=1
        )
        
        stats = player.get_statistics()
        
        expected_keys = {
            'level', 'total_xp', 'xp_to_next_level', 'level_progress',
            'tasks_completed', 'current_streak', 'easy_tasks_completed',
            'medium_tasks_completed', 'hard_tasks_completed', 'last_activity'
        }
        assert set(stats.keys()) == expected_keys
        
        assert stats['level'] == 2
        assert stats['total_xp'] == 250
        assert stats['xp_to_next_level'] == 150
        assert stats['level_progress'] == 0.5
        assert stats['tasks_completed'] == 10
        assert stats['current_streak'] == 3
        assert stats['easy_tasks_completed'] == 6
        assert stats['medium_tasks_completed'] == 3
        assert stats['hard_tasks_completed'] == 1
        assert stats['last_activity'] == last_activity.isoformat()
    
    def test_player_serialization(self):
        """Test player to_dict and from_dict methods."""
        last_activity = datetime.now()
        original_player = PlayerData(
            total_xp=300,
            tasks_completed=15,
            current_streak=7,
            last_activity=last_activity,
            easy_tasks_completed=8,
            medium_tasks_completed=5,
            hard_tasks_completed=2
        )
        
        # Convert to dict
        player_dict = original_player.to_dict()
        
        expected_keys = {
            'total_xp', 'tasks_completed', 'current_streak', 'last_activity',
            'easy_tasks_completed', 'medium_tasks_completed', 'hard_tasks_completed'
        }
        assert set(player_dict.keys()) == expected_keys
        
        assert player_dict['total_xp'] == 300
        assert player_dict['tasks_completed'] == 15
        assert player_dict['current_streak'] == 7
        assert player_dict['last_activity'] == last_activity.isoformat()
        assert player_dict['easy_tasks_completed'] == 8
        assert player_dict['medium_tasks_completed'] == 5
        assert player_dict['hard_tasks_completed'] == 2
        
        # Convert back from dict
        restored_player = PlayerData.from_dict(player_dict)
        
        assert restored_player.total_xp == original_player.total_xp
        assert restored_player.tasks_completed == original_player.tasks_completed
        assert restored_player.current_streak == original_player.current_streak
        assert restored_player.last_activity == original_player.last_activity
        assert restored_player.easy_tasks_completed == original_player.easy_tasks_completed
        assert restored_player.medium_tasks_completed == original_player.medium_tasks_completed
        assert restored_player.hard_tasks_completed == original_player.hard_tasks_completed
    
    def test_player_serialization_with_none_activity(self):
        """Test serialization when last_activity is None."""
        player = PlayerData(total_xp=100)
        
        player_dict = player.to_dict()
        assert player_dict['last_activity'] is None
        
        restored_player = PlayerData.from_dict(player_dict)
        assert restored_player.last_activity is None