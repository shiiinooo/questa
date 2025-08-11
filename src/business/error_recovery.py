"""Error recovery mechanisms with graceful degradation and data backup."""

import logging
import shutil
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime
from pathlib import Path
import json

from ..data.data_manager import DataManager, DataPersistenceError
from ..models.task import Task
from ..models.player import PlayerData
from .error_handler import ErrorHandler, UserFriendlyError, ErrorCategory, ErrorSeverity


# Configure logging
logger = logging.getLogger(__name__)


class RecoveryResult:
    """Result of a recovery operation."""
    
    def __init__(
        self,
        success: bool,
        message: str,
        recovered_data: Optional[Dict[str, Any]] = None,
        warnings: Optional[List[str]] = None,
        actions_taken: Optional[List[str]] = None
    ):
        """Initialize recovery result.
        
        Args:
            success: Whether recovery was successful
            message: Human-readable result message
            recovered_data: Any data that was recovered
            warnings: List of warnings about the recovery
            actions_taken: List of actions taken during recovery
        """
        self.success = success
        self.message = message
        self.recovered_data = recovered_data or {}
        self.warnings = warnings or []
        self.actions_taken = actions_taken or []
        self.timestamp = datetime.now()


class ErrorRecoveryManager:
    """Manager for error recovery operations with graceful degradation."""
    
    def __init__(self, data_manager: DataManager):
        """Initialize error recovery manager.
        
        Args:
            data_manager: DataManager instance for data operations
        """
        self.data_manager = data_manager
        self.recovery_log: List[Dict[str, Any]] = []
        
        # Recovery strategies registry
        self.recovery_strategies: Dict[str, Callable] = {
            'data_corruption': self._recover_from_corruption,
            'save_failure': self._recover_from_save_failure,
            'load_failure': self._recover_from_load_failure,
            'backup_failure': self._recover_from_backup_failure,
            'permission_error': self._recover_from_permission_error,
            'disk_space_error': self._recover_from_disk_space_error,
            'validation_error': self._recover_from_validation_error,
            'state_error': self._recover_from_state_error
        }
    
    def attempt_recovery(
        self,
        error_type: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> RecoveryResult:
        """Attempt to recover from an error.
        
        Args:
            error_type: Type of error to recover from
            error: The original error
            context: Additional context for recovery
            
        Returns:
            RecoveryResult: Result of the recovery attempt
        """
        context = context or {}
        
        logger.info(f"Attempting recovery from {error_type}: {error}")
        
        # Log the recovery attempt
        recovery_attempt = {
            'error_type': error_type,
            'error_message': str(error),
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        self.recovery_log.append(recovery_attempt)
        
        try:
            # Get recovery strategy
            if error_type in self.recovery_strategies:
                strategy = self.recovery_strategies[error_type]
                result = strategy(error, context)
            else:
                result = self._generic_recovery(error, context)
            
            # Log the result
            recovery_attempt['result'] = {
                'success': result.success,
                'message': result.message,
                'warnings': result.warnings,
                'actions_taken': result.actions_taken
            }
            
            logger.info(f"Recovery {'succeeded' if result.success else 'failed'}: {result.message}")
            return result
            
        except Exception as recovery_error:
            logger.error(f"Recovery attempt failed: {recovery_error}", exc_info=True)
            
            recovery_attempt['result'] = {
                'success': False,
                'message': f"Recovery failed: {recovery_error}",
                'warnings': [],
                'actions_taken': []
            }
            
            return RecoveryResult(
                success=False,
                message=f"Recovery failed: {recovery_error}",
                warnings=["Recovery mechanism itself failed"],
                actions_taken=["Logged recovery failure"]
            )
    
    def _recover_from_corruption(self, error: Exception, context: Dict[str, Any]) -> RecoveryResult:
        """Recover from data corruption.
        
        Args:
            error: The corruption error
            context: Recovery context
            
        Returns:
            RecoveryResult: Recovery result
        """
        actions_taken = []
        warnings = []
        recovered_data = {}
        
        try:
            # Step 1: Create emergency backup of corrupted files
            corrupted_files = context.get('corrupted_files', [])
            if not corrupted_files:
                # Try to identify corrupted files
                corrupted_files = self._identify_corrupted_files()
            
            for file_path in corrupted_files:
                if Path(file_path).exists():
                    backup_path = Path(file_path).with_suffix('.corrupted.backup')
                    shutil.copy2(file_path, backup_path)
                    actions_taken.append(f"Backed up corrupted file: {file_path}")
            
            # Step 2: Attempt to restore from backup
            backup_restored = False
            
            # Try to restore tasks
            if self.data_manager.tasks_file.with_suffix('.json.backup').exists():
                try:
                    backup_path = self.data_manager.tasks_file.with_suffix('.json.backup')
                    shutil.copy2(backup_path, self.data_manager.tasks_file)
                    
                    # Verify the restored file
                    tasks = self.data_manager.load_tasks()
                    recovered_data['tasks'] = len(tasks)
                    actions_taken.append("Restored tasks from backup")
                    backup_restored = True
                    
                except Exception as e:
                    warnings.append(f"Failed to restore tasks from backup: {e}")
            
            # Try to restore player data
            if self.data_manager.player_file.with_suffix('.json.backup').exists():
                try:
                    backup_path = self.data_manager.player_file.with_suffix('.json.backup')
                    shutil.copy2(backup_path, self.data_manager.player_file)
                    
                    # Verify the restored file
                    player_data = self.data_manager.load_player_data()
                    recovered_data['player_data'] = True
                    actions_taken.append("Restored player data from backup")
                    backup_restored = True
                    
                except Exception as e:
                    warnings.append(f"Failed to restore player data from backup: {e}")
            
            # Step 3: If no backup available, try to salvage data
            if not backup_restored:
                salvaged_data = self._salvage_corrupted_data(corrupted_files)
                if salvaged_data:
                    recovered_data.update(salvaged_data)
                    actions_taken.append("Salvaged partial data from corrupted files")
                else:
                    # Last resort: create empty files with proper structure
                    self._create_empty_data_files()
                    actions_taken.append("Created new empty data files")
                    warnings.append("All data was lost - starting with empty files")
            
            success = backup_restored or bool(recovered_data)
            message = "Data corruption recovery completed"
            
            if not success:
                message = "Data corruption recovery failed - starting with empty data"
                warnings.append("Unable to recover any data from corruption")
            
            return RecoveryResult(
                success=success,
                message=message,
                recovered_data=recovered_data,
                warnings=warnings,
                actions_taken=actions_taken
            )
            
        except Exception as e:
            logger.error(f"Corruption recovery failed: {e}", exc_info=True)
            return RecoveryResult(
                success=False,
                message=f"Corruption recovery failed: {e}",
                warnings=["Recovery process encountered errors"],
                actions_taken=actions_taken
            )
    
    def _recover_from_save_failure(self, error: Exception, context: Dict[str, Any]) -> RecoveryResult:
        """Recover from save operation failure.
        
        Args:
            error: The save failure error
            context: Recovery context
            
        Returns:
            RecoveryResult: Recovery result
        """
        actions_taken = []
        warnings = []
        
        try:
            # Check disk space
            data_dir = self.data_manager.data_dir
            if data_dir.exists():
                try:
                    stat = shutil.disk_usage(data_dir)
                    free_space = stat.free
                    if free_space < 1024 * 1024:  # Less than 1MB
                        warnings.append("Low disk space detected")
                        actions_taken.append("Identified disk space issue")
                        
                        # Try to clean up temporary files
                        temp_files = list(data_dir.glob("*.tmp"))
                        for temp_file in temp_files:
                            try:
                                temp_file.unlink()
                                actions_taken.append(f"Removed temporary file: {temp_file.name}")
                            except:
                                pass
                except:
                    warnings.append("Could not check disk space")
            
            # Check file permissions
            try:
                test_file = data_dir / "permission_test.tmp"
                test_file.write_text("test")
                test_file.unlink()
                actions_taken.append("Verified write permissions")
            except Exception as perm_error:
                warnings.append(f"Permission issue detected: {perm_error}")
                return RecoveryResult(
                    success=False,
                    message="Save failed due to permission issues",
                    warnings=warnings,
                    actions_taken=actions_taken
                )
            
            # Try alternative save location
            alt_data_dir = data_dir.parent / "data_backup"
            alt_data_dir.mkdir(exist_ok=True)
            
            try:
                # Create alternative data manager
                alt_data_manager = DataManager(alt_data_dir)
                
                # Try to save to alternative location
                tasks_data = context.get('tasks_data', {})
                player_data = context.get('player_data')
                
                if tasks_data:
                    alt_data_manager.save_tasks(tasks_data)
                    actions_taken.append(f"Saved tasks to alternative location: {alt_data_dir}")
                
                if player_data:
                    alt_data_manager.save_player_data(player_data)
                    actions_taken.append(f"Saved player data to alternative location: {alt_data_dir}")
                
                warnings.append(f"Data saved to alternative location: {alt_data_dir}")
                
                return RecoveryResult(
                    success=False,
                    message="Save failed - used alternative location temporarily",
                    warnings=warnings,
                    actions_taken=actions_taken
                )
                
            except Exception as alt_error:
                warnings.append(f"Alternative save location failed: {alt_error}")
            
            # If all else fails, keep data in memory
            warnings.append("Data kept in memory only - save when possible")
            actions_taken.append("Preserved data in memory")
            
            return RecoveryResult(
                success=False,
                message="Save failed - data preserved in memory",
                warnings=warnings,
                actions_taken=actions_taken
            )
            
        except Exception as e:
            logger.error(f"Save failure recovery failed: {e}", exc_info=True)
            return RecoveryResult(
                success=False,
                message=f"Save failure recovery failed: {e}",
                warnings=["Recovery process encountered errors"],
                actions_taken=actions_taken
            )
    
    def _recover_from_load_failure(self, error: Exception, context: Dict[str, Any]) -> RecoveryResult:
        """Recover from load operation failure.
        
        Args:
            error: The load failure error
            context: Recovery context
            
        Returns:
            RecoveryResult: Recovery result
        """
        actions_taken = []
        warnings = []
        recovered_data = {}
        
        try:
            # Try to load from backup files
            backup_loaded = False
            
            # Try tasks backup
            tasks_backup = self.data_manager.tasks_file.with_suffix('.json.backup')
            if tasks_backup.exists():
                try:
                    with open(tasks_backup, 'r') as f:
                        tasks_data = json.load(f)
                    
                    # Validate the backup data
                    if 'tasks' in tasks_data:
                        recovered_data['tasks_count'] = len(tasks_data['tasks'])
                        actions_taken.append("Loaded tasks from backup")
                        backup_loaded = True
                    
                except Exception as e:
                    warnings.append(f"Tasks backup is also corrupted: {e}")
            
            # Try player data backup
            player_backup = self.data_manager.player_file.with_suffix('.json.backup')
            if player_backup.exists():
                try:
                    with open(player_backup, 'r') as f:
                        player_data = json.load(f)
                    
                    # Validate the backup data
                    if 'player' in player_data:
                        recovered_data['player_data'] = True
                        actions_taken.append("Loaded player data from backup")
                        backup_loaded = True
                    
                except Exception as e:
                    warnings.append(f"Player data backup is also corrupted: {e}")
            
            # If no backup available, create default data
            if not backup_loaded:
                self._create_empty_data_files()
                actions_taken.append("Created default empty data files")
                warnings.append("No backup available - starting with empty data")
                recovered_data['default_created'] = True
            
            return RecoveryResult(
                success=True,
                message="Load failure recovered",
                recovered_data=recovered_data,
                warnings=warnings,
                actions_taken=actions_taken
            )
            
        except Exception as e:
            logger.error(f"Load failure recovery failed: {e}", exc_info=True)
            return RecoveryResult(
                success=False,
                message=f"Load failure recovery failed: {e}",
                warnings=["Recovery process encountered errors"],
                actions_taken=actions_taken
            )
    
    def _recover_from_backup_failure(self, error: Exception, context: Dict[str, Any]) -> RecoveryResult:
        """Recover from backup operation failure.
        
        Args:
            error: The backup failure error
            context: Recovery context
            
        Returns:
            RecoveryResult: Recovery result
        """
        actions_taken = []
        warnings = []
        
        try:
            # Continue with the original operation despite backup failure
            warnings.append("Backup failed - proceeding without backup")
            actions_taken.append("Logged backup failure")
            
            # Try to create backup in alternative location
            alt_backup_dir = self.data_manager.data_dir.parent / "emergency_backup"
            alt_backup_dir.mkdir(exist_ok=True)
            
            try:
                # Copy current data files to alternative backup location
                if self.data_manager.tasks_file.exists():
                    alt_tasks_backup = alt_backup_dir / f"tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    shutil.copy2(self.data_manager.tasks_file, alt_tasks_backup)
                    actions_taken.append(f"Created emergency tasks backup: {alt_tasks_backup}")
                
                if self.data_manager.player_file.exists():
                    alt_player_backup = alt_backup_dir / f"player_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    shutil.copy2(self.data_manager.player_file, alt_player_backup)
                    actions_taken.append(f"Created emergency player backup: {alt_player_backup}")
                
                return RecoveryResult(
                    success=True,
                    message="Backup failure recovered with emergency backup",
                    warnings=warnings,
                    actions_taken=actions_taken
                )
                
            except Exception as alt_error:
                warnings.append(f"Emergency backup also failed: {alt_error}")
                
                return RecoveryResult(
                    success=False,
                    message="Backup failure - no backup created",
                    warnings=warnings,
                    actions_taken=actions_taken
                )
            
        except Exception as e:
            logger.error(f"Backup failure recovery failed: {e}", exc_info=True)
            return RecoveryResult(
                success=False,
                message=f"Backup failure recovery failed: {e}",
                warnings=["Recovery process encountered errors"],
                actions_taken=actions_taken
            )
    
    def _recover_from_permission_error(self, error: Exception, context: Dict[str, Any]) -> RecoveryResult:
        """Recover from permission errors.
        
        Args:
            error: The permission error
            context: Recovery context
            
        Returns:
            RecoveryResult: Recovery result
        """
        actions_taken = []
        warnings = []
        
        try:
            # Try to use alternative data directory in user's home
            import os
            home_dir = Path.home()
            alt_data_dir = home_dir / ".questa_data"
            alt_data_dir.mkdir(exist_ok=True)
            
            try:
                # Test write permissions in alternative directory
                test_file = alt_data_dir / "permission_test.tmp"
                test_file.write_text("test")
                test_file.unlink()
                
                actions_taken.append(f"Found alternative data directory: {alt_data_dir}")
                warnings.append(f"Using alternative data directory due to permissions: {alt_data_dir}")
                
                return RecoveryResult(
                    success=True,
                    message="Permission error recovered with alternative directory",
                    recovered_data={'alt_data_dir': str(alt_data_dir)},
                    warnings=warnings,
                    actions_taken=actions_taken
                )
                
            except Exception as alt_error:
                warnings.append(f"Alternative directory also has permission issues: {alt_error}")
                
                # Last resort: use temporary directory
                import tempfile
                temp_dir = Path(tempfile.gettempdir()) / "questa_temp_data"
                temp_dir.mkdir(exist_ok=True)
                
                warnings.append(f"Using temporary directory (data will be lost on restart): {temp_dir}")
                actions_taken.append(f"Using temporary directory: {temp_dir}")
                
                return RecoveryResult(
                    success=True,
                    message="Permission error recovered with temporary directory",
                    recovered_data={'temp_data_dir': str(temp_dir)},
                    warnings=warnings,
                    actions_taken=actions_taken
                )
            
        except Exception as e:
            logger.error(f"Permission error recovery failed: {e}", exc_info=True)
            return RecoveryResult(
                success=False,
                message=f"Permission error recovery failed: {e}",
                warnings=["Recovery process encountered errors"],
                actions_taken=actions_taken
            )
    
    def _recover_from_disk_space_error(self, error: Exception, context: Dict[str, Any]) -> RecoveryResult:
        """Recover from disk space errors.
        
        Args:
            error: The disk space error
            context: Recovery context
            
        Returns:
            RecoveryResult: Recovery result
        """
        actions_taken = []
        warnings = []
        
        try:
            # Clean up temporary files
            temp_files_cleaned = 0
            data_dir = self.data_manager.data_dir
            
            if data_dir.exists():
                # Remove .tmp files
                for tmp_file in data_dir.glob("*.tmp"):
                    try:
                        tmp_file.unlink()
                        temp_files_cleaned += 1
                    except:
                        pass
                
                # Remove old backup files (keep only the most recent)
                backup_files = list(data_dir.glob("*.backup"))
                if len(backup_files) > 2:  # Keep 2 most recent
                    backup_files.sort(key=lambda f: f.stat().st_mtime)
                    for old_backup in backup_files[:-2]:
                        try:
                            old_backup.unlink()
                            temp_files_cleaned += 1
                        except:
                            pass
            
            if temp_files_cleaned > 0:
                actions_taken.append(f"Cleaned up {temp_files_cleaned} temporary files")
            
            # Try to compress data files
            try:
                import gzip
                
                # Compress old backup files
                for backup_file in data_dir.glob("*.backup"):
                    if backup_file.stat().st_size > 1024:  # Only compress files > 1KB
                        compressed_file = backup_file.with_suffix('.backup.gz')
                        with open(backup_file, 'rb') as f_in:
                            with gzip.open(compressed_file, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        backup_file.unlink()
                        actions_taken.append(f"Compressed backup file: {backup_file.name}")
                
            except Exception as compress_error:
                warnings.append(f"Could not compress files: {compress_error}")
            
            # Check if we have enough space now
            try:
                stat = shutil.disk_usage(data_dir)
                free_space = stat.free
                if free_space > 1024 * 1024:  # More than 1MB
                    return RecoveryResult(
                        success=True,
                        message="Disk space error recovered by cleanup",
                        warnings=warnings,
                        actions_taken=actions_taken
                    )
                else:
                    warnings.append("Still low on disk space after cleanup")
            except:
                warnings.append("Could not verify disk space after cleanup")
            
            # If still very low on space, consider it a failure
            if temp_files_cleaned == 0:
                return RecoveryResult(
                    success=False,
                    message="Disk space error - no cleanup possible",
                    warnings=warnings,
                    actions_taken=actions_taken
                )
            
            # If still low on space, suggest alternative location
            warnings.append("Consider moving data to a location with more space")
            actions_taken.append("Provided disk space recommendations")
            
            return RecoveryResult(
                success=False,
                message="Disk space error - cleanup helped but more space needed",
                warnings=warnings,
                actions_taken=actions_taken
            )
            
        except Exception as e:
            logger.error(f"Disk space error recovery failed: {e}", exc_info=True)
            return RecoveryResult(
                success=False,
                message=f"Disk space error recovery failed: {e}",
                warnings=["Recovery process encountered errors"],
                actions_taken=actions_taken
            )
    
    def _recover_from_validation_error(self, error: Exception, context: Dict[str, Any]) -> RecoveryResult:
        """Recover from validation errors.
        
        Args:
            error: The validation error
            context: Recovery context
            
        Returns:
            RecoveryResult: Recovery result
        """
        actions_taken = []
        warnings = []
        recovered_data = {}
        
        try:
            # Try to sanitize and fix the data
            invalid_data = context.get('invalid_data', {})
            
            if invalid_data:
                # Attempt to fix common validation issues
                fixed_data = self._sanitize_invalid_data(invalid_data)
                
                if fixed_data != invalid_data:
                    recovered_data['fixed_data'] = fixed_data
                    actions_taken.append("Sanitized invalid data")
                    
                    return RecoveryResult(
                        success=True,
                        message="Validation error recovered by data sanitization",
                        recovered_data=recovered_data,
                        warnings=warnings,
                        actions_taken=actions_taken
                    )
            
            # If can't fix data, provide helpful error message
            warnings.append("Data could not be automatically fixed")
            actions_taken.append("Provided validation error details")
            
            return RecoveryResult(
                success=False,
                message="Validation error - manual correction required",
                warnings=warnings,
                actions_taken=actions_taken
            )
            
        except Exception as e:
            logger.error(f"Validation error recovery failed: {e}", exc_info=True)
            return RecoveryResult(
                success=False,
                message=f"Validation error recovery failed: {e}",
                warnings=["Recovery process encountered errors"],
                actions_taken=actions_taken
            )
    
    def _recover_from_state_error(self, error: Exception, context: Dict[str, Any]) -> RecoveryResult:
        """Recover from state errors.
        
        Args:
            error: The state error
            context: Recovery context
            
        Returns:
            RecoveryResult: Recovery result
        """
        actions_taken = []
        warnings = []
        
        try:
            # State errors usually can't be automatically recovered
            # But we can provide helpful guidance
            
            error_msg = str(error).lower()
            
            if 'already completed' in error_msg:
                warnings.append("Task is already completed - no action needed")
                actions_taken.append("Verified task completion status")
                
                return RecoveryResult(
                    success=True,
                    message="State error - task already in desired state",
                    warnings=warnings,
                    actions_taken=actions_taken
                )
            
            elif 'cannot transition' in error_msg:
                warnings.append("Invalid status transition attempted")
                actions_taken.append("Provided valid transition options")
                
                # Suggest valid transitions based on context
                current_status = context.get('current_status')
                if current_status:
                    from ..models.enums import TaskStatus
                    valid_transitions = []
                    for status in TaskStatus:
                        if current_status.can_transition_to(status):
                            valid_transitions.append(status.value)
                    
                    if valid_transitions:
                        warnings.append(f"Valid transitions from {current_status.value}: {', '.join(valid_transitions)}")
                    else:
                        warnings.append(f"Valid transitions from {current_status.value}: none")
                
                return RecoveryResult(
                    success=False,
                    message="State error - invalid transition",
                    warnings=warnings,
                    actions_taken=actions_taken
                )
            
            # Generic state error
            warnings.append("State error cannot be automatically recovered")
            actions_taken.append("Logged state error details")
            
            return RecoveryResult(
                success=False,
                message="State error - manual intervention required",
                warnings=warnings,
                actions_taken=actions_taken
            )
            
        except Exception as e:
            logger.error(f"State error recovery failed: {e}", exc_info=True)
            return RecoveryResult(
                success=False,
                message=f"State error recovery failed: {e}",
                warnings=["Recovery process encountered errors"],
                actions_taken=actions_taken
            )
    
    def _generic_recovery(self, error: Exception, context: Dict[str, Any]) -> RecoveryResult:
        """Generic recovery for unknown error types.
        
        Args:
            error: The unknown error
            context: Recovery context
            
        Returns:
            RecoveryResult: Recovery result
        """
        actions_taken = ["Logged unknown error type"]
        warnings = ["Unknown error type - limited recovery options"]
        
        # Try to preserve any data in context
        preserved_data = {}
        if 'tasks_data' in context:
            preserved_data['tasks_preserved'] = True
            actions_taken.append("Preserved task data in memory")
        
        if 'player_data' in context:
            preserved_data['player_data_preserved'] = True
            actions_taken.append("Preserved player data in memory")
        
        return RecoveryResult(
            success=bool(preserved_data),
            message="Generic recovery - data preserved where possible",
            recovered_data=preserved_data,
            warnings=warnings,
            actions_taken=actions_taken
        )
    
    def _identify_corrupted_files(self) -> List[str]:
        """Identify potentially corrupted data files.
        
        Returns:
            List of file paths that may be corrupted
        """
        corrupted_files = []
        
        # Check tasks file
        if self.data_manager.tasks_file.exists():
            try:
                with open(self.data_manager.tasks_file, 'r') as f:
                    json.load(f)
            except json.JSONDecodeError:
                corrupted_files.append(str(self.data_manager.tasks_file))
        
        # Check player file
        if self.data_manager.player_file.exists():
            try:
                with open(self.data_manager.player_file, 'r') as f:
                    json.load(f)
            except json.JSONDecodeError:
                corrupted_files.append(str(self.data_manager.player_file))
        
        return corrupted_files
    
    def _salvage_corrupted_data(self, corrupted_files: List[str]) -> Dict[str, Any]:
        """Attempt to salvage data from corrupted files.
        
        Args:
            corrupted_files: List of corrupted file paths
            
        Returns:
            Dictionary of salvaged data
        """
        salvaged_data = {}
        
        for file_path in corrupted_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Try to extract partial JSON data
                # Look for complete JSON objects within the corrupted data
                import re
                
                # Find task objects
                task_pattern = r'"[a-f0-9-]{36}"\s*:\s*\{[^}]*"id"\s*:\s*"[a-f0-9-]{36}"[^}]*\}'
                task_matches = re.findall(task_pattern, content)
                
                if task_matches:
                    salvaged_data['partial_tasks'] = len(task_matches)
                
                # Find player data
                if '"total_xp"' in content:
                    xp_match = re.search(r'"total_xp"\s*:\s*(\d+)', content)
                    if xp_match:
                        salvaged_data['total_xp'] = int(xp_match.group(1))
                
            except Exception as e:
                logger.warning(f"Could not salvage data from {file_path}: {e}")
        
        return salvaged_data
    
    def _create_empty_data_files(self) -> None:
        """Create empty data files with proper structure."""
        try:
            # Create empty tasks file
            empty_tasks = {
                "tasks": {},
                "version": "1.0",
                "last_modified": datetime.now().isoformat()
            }
            
            with open(self.data_manager.tasks_file, 'w') as f:
                json.dump(empty_tasks, f, indent=2)
            
            # Create empty player file
            empty_player = {
                "player": {
                    "total_xp": 0,
                    "tasks_completed": 0,
                    "current_streak": 0,
                    "last_activity": None
                },
                "statistics": {
                    "easy_tasks_completed": 0,
                    "medium_tasks_completed": 0,
                    "hard_tasks_completed": 0,
                    "total_xp_earned": 0
                },
                "version": "1.0",
                "last_modified": datetime.now().isoformat()
            }
            
            with open(self.data_manager.player_file, 'w') as f:
                json.dump(empty_player, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to create empty data files: {e}")
            raise
    
    def _sanitize_invalid_data(self, invalid_data: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to sanitize invalid data.
        
        Args:
            invalid_data: The invalid data to sanitize
            
        Returns:
            Sanitized data dictionary
        """
        sanitized = invalid_data.copy()
        
        # Fix common issues
        if 'title' in sanitized:
            if not isinstance(sanitized['title'], str):
                sanitized['title'] = str(sanitized['title'])
            sanitized['title'] = sanitized['title'].strip()
            if not sanitized['title']:
                sanitized['title'] = "Untitled Task"
        
        # Fix notes type
        if 'notes' in sanitized and not isinstance(sanitized['notes'], (str, type(None))):
            sanitized['notes'] = str(sanitized['notes'])
        
        # Fix enum values
        if 'difficulty' in sanitized:
            if isinstance(sanitized['difficulty'], str):
                try:
                    from ..models.enums import TaskDifficulty
                    sanitized['difficulty'] = TaskDifficulty[sanitized['difficulty'].upper()]
                except KeyError:
                    sanitized['difficulty'] = TaskDifficulty.MEDIUM
        
        if 'priority' in sanitized:
            if isinstance(sanitized['priority'], str):
                try:
                    from ..models.enums import TaskPriority
                    sanitized['priority'] = TaskPriority[sanitized['priority'].upper()]
                except KeyError:
                    sanitized['priority'] = TaskPriority.MEDIUM
        
        if 'status' in sanitized:
            if isinstance(sanitized['status'], str):
                try:
                    from ..models.enums import TaskStatus
                    sanitized['status'] = TaskStatus[sanitized['status'].upper()]
                except KeyError:
                    sanitized['status'] = TaskStatus.PENDING
        
        return sanitized
    
    def get_recovery_log(self) -> List[Dict[str, Any]]:
        """Get the recovery operation log.
        
        Returns:
            List of recovery log entries
        """
        return self.recovery_log.copy()
    
    def clear_recovery_log(self) -> None:
        """Clear the recovery operation log."""
        self.recovery_log.clear()