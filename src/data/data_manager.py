"""Data persistence manager for tasks and player data with atomic operations and backup support."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

from ..models.task import Task
from ..models.player import PlayerData
from ..models.enums import TaskDifficulty, TaskPriority, TaskStatus


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataPersistenceError(Exception):
    """Raised when data save/load operations fail."""
    pass


class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass


class DataMigrationError(Exception):
    """Raised when data migration fails."""
    pass


class DataManager:
    """Manages data persistence for tasks and player data with atomic operations and backup support."""
    
    CURRENT_VERSION = "1.0"
    BACKUP_SUFFIX = ".backup"
    
    def __init__(self, data_dir: Path = Path("data")):
        """Initialize DataManager with specified data directory.
        
        Args:
            data_dir: Directory to store data files
        """
        self.data_dir = Path(data_dir)
        self.tasks_file = self.data_dir / "tasks.json"
        self.player_file = self.data_dir / "player.json"
        
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"DataManager initialized with data directory: {self.data_dir}")
    
    def save_tasks(self, tasks: Dict[str, Task]) -> bool:
        """Save tasks to JSON file with atomic operation and backup.
        
        Args:
            tasks: Dictionary of task ID to Task objects
            
        Returns:
            bool: True if save successful, False otherwise
            
        Raises:
            DataPersistenceError: If save operation fails
        """
        try:
            # Create backup if file exists
            if self.tasks_file.exists():
                self._create_backup(self.tasks_file)
            
            # Prepare data structure
            tasks_data = {
                "tasks": {task_id: task.to_dict() for task_id, task in tasks.items()},
                "version": self.CURRENT_VERSION,
                "last_modified": datetime.now().isoformat()
            }
            
            # Atomic write using temporary file
            temp_file = self.tasks_file.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, indent=2, ensure_ascii=False)
            
            # Atomic move
            temp_file.replace(self.tasks_file)
            
            logger.info(f"Successfully saved {len(tasks)} tasks to {self.tasks_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save tasks: {e}")
            raise DataPersistenceError(f"Failed to save tasks: {e}") from e
    
    def load_tasks(self) -> Dict[str, Task]:
        """Load tasks from JSON file with error handling and validation.
        
        Returns:
            Dict[str, Task]: Dictionary of task ID to Task objects
            
        Raises:
            DataPersistenceError: If load operation fails
            DataValidationError: If data validation fails
        """
        try:
            if not self.tasks_file.exists():
                logger.info("Tasks file does not exist, returning empty dictionary")
                return {}
            
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate data structure
            self._validate_tasks_data(data)
            
            # Handle migration if needed
            if data.get("version") != self.CURRENT_VERSION:
                data = self._migrate_tasks_data(data)
            
            # Convert to Task objects
            tasks = {}
            for task_id, task_data in data.get("tasks", {}).items():
                try:
                    task = Task.from_dict(task_data)
                    tasks[task_id] = task
                except Exception as e:
                    logger.warning(f"Failed to load task {task_id}: {e}")
                    continue
            
            logger.info(f"Successfully loaded {len(tasks)} tasks from {self.tasks_file}")
            return tasks
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in tasks file: {e}")
            # Try to recover from backup
            if self._restore_from_backup(self.tasks_file):
                return self.load_tasks()  # Recursive call after restore
            raise DataPersistenceError(f"Invalid JSON in tasks file: {e}") from e
            
        except Exception as e:
            logger.error(f"Failed to load tasks: {e}")
            raise DataPersistenceError(f"Failed to load tasks: {e}") from e
    
    def save_player_data(self, player_data: PlayerData) -> bool:
        """Save player data to JSON file with atomic operation and backup.
        
        Args:
            player_data: PlayerData object to save
            
        Returns:
            bool: True if save successful, False otherwise
            
        Raises:
            DataPersistenceError: If save operation fails
        """
        try:
            # Create backup if file exists
            if self.player_file.exists():
                self._create_backup(self.player_file)
            
            # Prepare data structure
            player_file_data = {
                "player": player_data.to_dict(),
                "statistics": player_data.get_statistics(),
                "version": self.CURRENT_VERSION,
                "last_modified": datetime.now().isoformat()
            }
            
            # Atomic write using temporary file
            temp_file = self.player_file.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(player_file_data, f, indent=2, ensure_ascii=False)
            
            # Atomic move
            temp_file.replace(self.player_file)
            
            logger.info(f"Successfully saved player data to {self.player_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save player data: {e}")
            raise DataPersistenceError(f"Failed to save player data: {e}") from e
    
    def load_player_data(self) -> PlayerData:
        """Load player data from JSON file with error handling and defaults.
        
        Returns:
            PlayerData: Player data object with defaults if file doesn't exist
            
        Raises:
            DataPersistenceError: If load operation fails
            DataValidationError: If data validation fails
        """
        try:
            if not self.player_file.exists():
                logger.info("Player file does not exist, returning default PlayerData")
                return PlayerData()
            
            with open(self.player_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate data structure
            self._validate_player_data(data)
            
            # Handle migration if needed
            if data.get("version") != self.CURRENT_VERSION:
                data = self._migrate_player_data(data)
            
            # Convert to PlayerData object
            player_data = PlayerData.from_dict(data.get("player", {}))
            
            logger.info(f"Successfully loaded player data from {self.player_file}")
            return player_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in player file: {e}")
            # Try to recover from backup
            if self._restore_from_backup(self.player_file):
                return self.load_player_data()  # Recursive call after restore
            # Return default if recovery fails
            logger.warning("Using default player data due to JSON error")
            return PlayerData()
            
        except Exception as e:
            logger.error(f"Failed to load player data: {e}")
            raise DataPersistenceError(f"Failed to load player data: {e}") from e
    
    def _validate_tasks_data(self, data: dict) -> None:
        """Validate tasks data structure.
        
        Args:
            data: Tasks data dictionary
            
        Raises:
            DataValidationError: If data structure is invalid
        """
        if not isinstance(data, dict):
            raise DataValidationError("Tasks data must be a dictionary")
        
        if "tasks" not in data:
            raise DataValidationError("Tasks data missing 'tasks' key")
        
        if not isinstance(data["tasks"], dict):
            raise DataValidationError("Tasks data 'tasks' must be a dictionary")
        
        # Validate individual task entries
        for task_id, task_data in data["tasks"].items():
            if not isinstance(task_data, dict):
                raise DataValidationError(f"Task {task_id} data must be a dictionary")
            
            required_fields = ["id", "title", "difficulty", "priority", "status"]
            for field in required_fields:
                if field not in task_data:
                    raise DataValidationError(f"Task {task_id} missing required field: {field}")
    
    def _validate_player_data(self, data: dict) -> None:
        """Validate player data structure.
        
        Args:
            data: Player data dictionary
            
        Raises:
            DataValidationError: If data structure is invalid
        """
        if not isinstance(data, dict):
            raise DataValidationError("Player data must be a dictionary")
        
        if "player" not in data:
            raise DataValidationError("Player data missing 'player' key")
        
        if not isinstance(data["player"], dict):
            raise DataValidationError("Player data 'player' must be a dictionary")
        
        # Validate player fields
        player_data = data["player"]
        numeric_fields = ["total_xp", "tasks_completed", "current_streak"]
        for field in numeric_fields:
            if field in player_data and not isinstance(player_data[field], int):
                raise DataValidationError(f"Player field {field} must be an integer")
    
    def _migrate_tasks_data(self, data: dict) -> dict:
        """Migrate tasks data to current version.
        
        Args:
            data: Tasks data dictionary
            
        Returns:
            dict: Migrated tasks data
        """
        # For now, just update version - add migration logic as needed
        migrated_data = data.copy()
        migrated_data["version"] = self.CURRENT_VERSION
        migrated_data["last_modified"] = datetime.now().isoformat()
        
        logger.info(f"Migrated tasks data to version {self.CURRENT_VERSION}")
        return migrated_data
    
    def _migrate_player_data(self, data: dict) -> dict:
        """Migrate player data to current version.
        
        Args:
            data: Player data dictionary
            
        Returns:
            dict: Migrated player data
        """
        # For now, just update version - add migration logic as needed
        migrated_data = data.copy()
        migrated_data["version"] = self.CURRENT_VERSION
        migrated_data["last_modified"] = datetime.now().isoformat()
        
        logger.info(f"Migrated player data to version {self.CURRENT_VERSION}")
        return migrated_data
    
    def create_backup(self) -> bool:
        """Create backup of all data files.
        
        Returns:
            bool: True if backup successful, False otherwise
        """
        try:
            success = True
            
            if self.tasks_file.exists():
                success &= self._create_backup(self.tasks_file)
            
            if self.player_file.exists():
                success &= self._create_backup(self.player_file)
            
            logger.info(f"Backup creation {'successful' if success else 'failed'}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    def _create_backup(self, file_path: Path) -> bool:
        """Create backup of specified file.
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            bool: True if backup successful, False otherwise
        """
        try:
            backup_path = file_path.with_suffix(file_path.suffix + self.BACKUP_SUFFIX)
            shutil.copy2(file_path, backup_path)
            logger.debug(f"Created backup: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
            return False
    
    def _restore_from_backup(self, file_path: Path) -> bool:
        """Restore file from backup.
        
        Args:
            file_path: Path to file to restore
            
        Returns:
            bool: True if restore successful, False otherwise
        """
        try:
            backup_path = file_path.with_suffix(file_path.suffix + self.BACKUP_SUFFIX)
            
            if not backup_path.exists():
                logger.warning(f"No backup found for {file_path}")
                return False
            
            shutil.copy2(backup_path, file_path)
            logger.info(f"Restored {file_path} from backup")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore {file_path} from backup: {e}")
            return False