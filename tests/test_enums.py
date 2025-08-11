"""Tests for core enumerations."""

import pytest
from src.models.enums import TaskDifficulty, TaskPriority, TaskStatus


class TestTaskDifficulty:
    """Test TaskDifficulty enum."""
    
    def test_difficulty_values(self):
        """Test that difficulty enum has correct values and XP mappings."""
        assert TaskDifficulty.EASY.display_name == "Easy"
        assert TaskDifficulty.EASY.xp_value == 15
        
        assert TaskDifficulty.MEDIUM.display_name == "Medium"
        assert TaskDifficulty.MEDIUM.xp_value == 30
        
        assert TaskDifficulty.HARD.display_name == "Hard"
        assert TaskDifficulty.HARD.xp_value == 50
    
    def test_difficulty_string_representation(self):
        """Test string representation of difficulty."""
        assert str(TaskDifficulty.EASY) == "Easy"
        assert str(TaskDifficulty.MEDIUM) == "Medium"
        assert str(TaskDifficulty.HARD) == "Hard"
    
    def test_difficulty_enum_members(self):
        """Test that all expected difficulty levels exist."""
        difficulties = list(TaskDifficulty)
        assert len(difficulties) == 3
        assert TaskDifficulty.EASY in difficulties
        assert TaskDifficulty.MEDIUM in difficulties
        assert TaskDifficulty.HARD in difficulties


class TestTaskPriority:
    """Test TaskPriority enum."""
    
    def test_priority_values(self):
        """Test that priority enum has correct values."""
        assert TaskPriority.LOW.value == "Low"
        assert TaskPriority.MEDIUM.value == "Medium"
        assert TaskPriority.HIGH.value == "High"
        assert TaskPriority.CRITICAL.value == "Critical"
    
    def test_priority_string_representation(self):
        """Test string representation of priority."""
        assert str(TaskPriority.LOW) == "Low"
        assert str(TaskPriority.MEDIUM) == "Medium"
        assert str(TaskPriority.HIGH) == "High"
        assert str(TaskPriority.CRITICAL) == "Critical"
    
    def test_priority_enum_members(self):
        """Test that all expected priority levels exist."""
        priorities = list(TaskPriority)
        assert len(priorities) == 4
        assert TaskPriority.LOW in priorities
        assert TaskPriority.MEDIUM in priorities
        assert TaskPriority.HIGH in priorities
        assert TaskPriority.CRITICAL in priorities


class TestTaskStatus:
    """Test TaskStatus enum."""
    
    def test_status_values(self):
        """Test that status enum has correct values."""
        assert TaskStatus.PENDING.value == "Pending"
        assert TaskStatus.ACTIVE.value == "Active"
        assert TaskStatus.BLOCKED.value == "Blocked"
        assert TaskStatus.COMPLETED.value == "Completed"
    
    def test_status_string_representation(self):
        """Test string representation of status."""
        assert str(TaskStatus.PENDING) == "Pending"
        assert str(TaskStatus.ACTIVE) == "Active"
        assert str(TaskStatus.BLOCKED) == "Blocked"
        assert str(TaskStatus.COMPLETED) == "Completed"
    
    def test_status_enum_members(self):
        """Test that all expected status values exist."""
        statuses = list(TaskStatus)
        assert len(statuses) == 4
        assert TaskStatus.PENDING in statuses
        assert TaskStatus.ACTIVE in statuses
        assert TaskStatus.BLOCKED in statuses
        assert TaskStatus.COMPLETED in statuses
    
    def test_valid_status_transitions(self):
        """Test valid status transitions."""
        # From PENDING
        assert TaskStatus.PENDING.can_transition_to(TaskStatus.ACTIVE)
        assert TaskStatus.PENDING.can_transition_to(TaskStatus.BLOCKED)
        assert TaskStatus.PENDING.can_transition_to(TaskStatus.COMPLETED)
        assert not TaskStatus.PENDING.can_transition_to(TaskStatus.PENDING)
        
        # From ACTIVE
        assert TaskStatus.ACTIVE.can_transition_to(TaskStatus.PENDING)
        assert TaskStatus.ACTIVE.can_transition_to(TaskStatus.BLOCKED)
        assert TaskStatus.ACTIVE.can_transition_to(TaskStatus.COMPLETED)
        assert not TaskStatus.ACTIVE.can_transition_to(TaskStatus.ACTIVE)
        
        # From BLOCKED
        assert TaskStatus.BLOCKED.can_transition_to(TaskStatus.PENDING)
        assert TaskStatus.BLOCKED.can_transition_to(TaskStatus.ACTIVE)
        assert TaskStatus.BLOCKED.can_transition_to(TaskStatus.COMPLETED)
        assert not TaskStatus.BLOCKED.can_transition_to(TaskStatus.BLOCKED)
        
        # From COMPLETED - no transitions allowed
        assert not TaskStatus.COMPLETED.can_transition_to(TaskStatus.PENDING)
        assert not TaskStatus.COMPLETED.can_transition_to(TaskStatus.ACTIVE)
        assert not TaskStatus.COMPLETED.can_transition_to(TaskStatus.BLOCKED)
        assert not TaskStatus.COMPLETED.can_transition_to(TaskStatus.COMPLETED)