"""
Permission and safety management system for secure automation.
"""

import asyncio
import json
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from loguru import logger
from pydantic import BaseModel

from ..utils.config import Config


class PermissionLevel(Enum):
    """Permission levels for different actions."""
    
    SAFE = "safe"          # Safe actions that don't modify system
    MODERATE = "moderate"  # Actions that modify user data
    RISKY = "risky"       # Actions that could affect system security


class ActionType(Enum):
    """Types of automation actions."""
    
    SCREEN_CAPTURE = "screen_capture"
    MOUSE_CLICK = "mouse_click"
    KEYBOARD_INPUT = "keyboard_input"
    FILE_ACCESS = "file_access"
    SYSTEM_COMMAND = "system_command"


class PermissionRequest(BaseModel):
    """Permission request model."""
    
    action: str
    action_type: ActionType
    permission_level: PermissionLevel
    parameters: Dict[str, Any]
    timestamp: float
    user_approved: Optional[bool] = None
    auto_approved: bool = False


class PermissionManager:
    """Manages permissions and safety for automation actions."""
    
    def __init__(self, config: Config):
        """Initialize permission manager.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self._approved_actions: Set[str] = set()
        self._denied_actions: Set[str] = set()
        self._session_permissions: Dict[str, bool] = {}
        
        # Action classification
        self._action_classifications = {
            "capture_screen": (ActionType.SCREEN_CAPTURE, PermissionLevel.SAFE),
            "click_element": (ActionType.MOUSE_CLICK, PermissionLevel.MODERATE),
            "type_text": (ActionType.KEYBOARD_INPUT, PermissionLevel.MODERATE),
            "press_key": (ActionType.KEYBOARD_INPUT, PermissionLevel.MODERATE),
            "scroll": (ActionType.MOUSE_CLICK, PermissionLevel.SAFE),
            "analyze_screen": (ActionType.SCREEN_CAPTURE, PermissionLevel.SAFE),
            "find_text": (ActionType.SCREEN_CAPTURE, PermissionLevel.SAFE),
            "detect_elements": (ActionType.SCREEN_CAPTURE, PermissionLevel.SAFE),
        }
        
        # Rate limiting
        self._action_history: List[float] = []
        
        logger.info("PermissionManager initialized")
    
    async def initialize(self) -> None:
        """Initialize permission manager asynchronously."""
        try:
            # Load saved permissions if available
            await self._load_saved_permissions()
            
            logger.info("PermissionManager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize PermissionManager: {e}")
            raise
    
    async def _load_saved_permissions(self) -> None:
        """Load saved permissions from file."""
        try:
            permissions_file = Path("configs/permissions.json")
            
            if permissions_file.exists():
                with open(permissions_file, 'r') as f:
                    saved_data = json.load(f)
                
                self._approved_actions = set(saved_data.get("approved_actions", []))
                self._denied_actions = set(saved_data.get("denied_actions", []))
                
                logger.info(f"Loaded {len(self._approved_actions)} approved and {len(self._denied_actions)} denied actions")
            
        except Exception as e:
            logger.warning(f"Could not load saved permissions: {e}")
    
    async def _save_permissions(self) -> None:
        """Save current permissions to file."""
        try:
            permissions_file = Path("configs/permissions.json")
            permissions_file.parent.mkdir(exist_ok=True)
            
            save_data = {
                "approved_actions": list(self._approved_actions),
                "denied_actions": list(self._denied_actions),
                "last_updated": time.time()
            }
            
            with open(permissions_file, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            logger.debug("Permissions saved to file")
            
        except Exception as e:
            logger.error(f"Failed to save permissions: {e}")
    
    def _classify_action(self, action: str, parameters: Dict[str, Any]) -> tuple[ActionType, PermissionLevel]:
        """Classify an action to determine its type and permission level.
        
        Args:
            action: Action name
            parameters: Action parameters
            
        Returns:
            Tuple of (action_type, permission_level)
        """
        # Get base classification
        if action in self._action_classifications:
            action_type, base_level = self._action_classifications[action]
        else:
            # Default to risky for unknown actions
            action_type, base_level = ActionType.SYSTEM_COMMAND, PermissionLevel.RISKY
        
        # Adjust permission level based on parameters
        permission_level = base_level
        
        # Elevate permission level for sensitive parameters
        if action == "type_text":
            text = parameters.get("text", "")
            # Check for potentially sensitive text
            sensitive_keywords = ["password", "secret", "key", "token", "sudo", "admin"]
            if any(keyword in text.lower() for keyword in sensitive_keywords):
                permission_level = PermissionLevel.RISKY
        
        elif action == "click_element":
            # Check if clicking on system areas
            x, y = parameters.get("x", 0), parameters.get("y", 0)
            # Check automation bounds
            if not self._check_coordinates_in_bounds(x, y):
                permission_level = PermissionLevel.RISKY
        
        return action_type, permission_level
    
    def _check_coordinates_in_bounds(self, x: int, y: int) -> bool:
        """Check if coordinates are within automation bounds.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if coordinates are within bounds
        """
        bounds = self.config.safety.automation_bounds
        if bounds is None:
            return True  # No bounds set, allow all coordinates
        
        return (
            bounds["x"] <= x <= bounds["x"] + bounds["width"] and
            bounds["y"] <= y <= bounds["y"] + bounds["height"]
        )
    
    def _check_rate_limit(self) -> bool:
        """Check if current action is within rate limits.
        
        Returns:
            True if action is allowed by rate limiting
        """
        current_time = time.time()
        
        # Remove actions older than 1 minute
        self._action_history = [
            t for t in self._action_history 
            if current_time - t < 60
        ]
        
        # Check rate limit
        return len(self._action_history) < self.config.safety.max_actions_per_minute
    
    async def _request_user_permission(
        self,
        permission_request: PermissionRequest
    ) -> bool:
        """Request permission from user (simplified implementation).
        
        Args:
            permission_request: Permission request details
            
        Returns:
            True if user approved the action
        """
        # This is a simplified implementation
        # In a real application, you would show a UI dialog or use other means
        # to get user confirmation
        
        logger.warning(
            f"Permission required for {permission_request.action} "
            f"({permission_request.permission_level.value}): {permission_request.parameters}"
        )
        
        # For now, auto-approve safe actions and deny risky ones
        if permission_request.permission_level == PermissionLevel.SAFE:
            logger.info(f"Auto-approving safe action: {permission_request.action}")
            return True
        elif permission_request.permission_level == PermissionLevel.MODERATE:
            # In production, this would show a user prompt
            logger.warning(f"Auto-approving moderate action: {permission_request.action}")
            return True
        else:  # RISKY
            logger.error(f"Denying risky action: {permission_request.action}")
            return False
    
    async def request_permission(
        self,
        action: str,
        parameters: Dict[str, Any]
    ) -> bool:
        """Request permission to perform an action.
        
        Args:
            action: Action to perform
            parameters: Action parameters
            
        Returns:
            True if permission is granted
        """
        try:
            # Check if permissions are disabled
            if not self.config.safety.require_confirmation:
                return True
            
            # Check rate limiting first
            if not self._check_rate_limit():
                logger.warning(f"Rate limit exceeded for action: {action}")
                return False
            
            # Create action signature for caching
            action_signature = f"{action}:{hash(str(sorted(parameters.items())))}"
            
            # Check session permissions cache
            if action_signature in self._session_permissions:
                return self._session_permissions[action_signature]
            
            # Check permanently approved/denied actions
            if action_signature in self._approved_actions:
                self._session_permissions[action_signature] = True
                return True
            
            if action_signature in self._denied_actions:
                self._session_permissions[action_signature] = False
                return False
            
            # Classify the action
            action_type, permission_level = self._classify_action(action, parameters)
            
            # Create permission request
            permission_request = PermissionRequest(
                action=action,
                action_type=action_type,
                permission_level=permission_level,
                parameters=parameters,
                timestamp=time.time()
            )
            
            # Request user permission
            approved = await self._request_user_permission(permission_request)
            
            # Cache the decision
            self._session_permissions[action_signature] = approved
            
            if approved:
                # Record the action time for rate limiting
                self._action_history.append(time.time())
                
                # Optionally save to permanent approvals for safe actions
                if permission_level == PermissionLevel.SAFE:
                    self._approved_actions.add(action_signature)
                    await self._save_permissions()
            else:
                # Save to permanent denials for risky actions
                if permission_level == PermissionLevel.RISKY:
                    self._denied_actions.add(action_signature)
                    await self._save_permissions()
            
            logger.info(
                f"Permission {'granted' if approved else 'denied'} for {action} "
                f"({permission_level.value})"
            )
            
            return approved
            
        except Exception as e:
            logger.error(f"Permission request failed: {e}")
            # Fail securely - deny permission on error
            return False
    
    async def is_action_allowed(
        self,
        action: str,
        parameters: Dict[str, Any]
    ) -> bool:
        """Check if an action is allowed without requesting permission.
        
        Args:
            action: Action to check
            parameters: Action parameters
            
        Returns:
            True if action is allowed
        """
        try:
            # Check if permissions are disabled
            if not self.config.safety.require_confirmation:
                return True
            
            # Check rate limiting
            if not self._check_rate_limit():
                return False
            
            # Create action signature
            action_signature = f"{action}:{hash(str(sorted(parameters.items())))}"
            
            # Check session cache
            if action_signature in self._session_permissions:
                return self._session_permissions[action_signature]
            
            # Check permanent permissions
            if action_signature in self._approved_actions:
                return True
            
            if action_signature in self._denied_actions:
                return False
            
            # Classify action and auto-approve safe ones
            action_type, permission_level = self._classify_action(action, parameters)
            
            if permission_level == PermissionLevel.SAFE:
                return True
            
            # For moderate and risky actions, require explicit permission
            return False
            
        except Exception as e:
            logger.error(f"Action check failed: {e}")
            return False
    
    async def revoke_permission(
        self,
        action: str,
        parameters: Dict[str, Any]
    ) -> bool:
        """Revoke permission for a specific action.
        
        Args:
            action: Action to revoke
            parameters: Action parameters
            
        Returns:
            True if permission was revoked
        """
        try:
            action_signature = f"{action}:{hash(str(sorted(parameters.items())))}"
            
            # Remove from all permission stores
            self._session_permissions.pop(action_signature, None)
            self._approved_actions.discard(action_signature)
            self._denied_actions.add(action_signature)
            
            # Save changes
            await self._save_permissions()
            
            logger.info(f"Revoked permission for {action}")
            return True
            
        except Exception as e:
            logger.error(f"Permission revocation failed: {e}")
            return False
    
    async def clear_session_permissions(self) -> None:
        """Clear all session permissions (requires re-approval)."""
        self._session_permissions.clear()
        logger.info("Session permissions cleared")
    
    async def get_permission_status(self) -> Dict[str, Any]:
        """Get current permission status.
        
        Returns:
            Permission status summary
        """
        return {
            "require_confirmation": self.config.safety.require_confirmation,
            "rate_limit": self.config.safety.max_actions_per_minute,
            "automation_bounds": self.config.safety.automation_bounds,
            "session_permissions": len(self._session_permissions),
            "approved_actions": len(self._approved_actions),
            "denied_actions": len(self._denied_actions),
            "recent_actions": len(self._action_history)
        }
    
    async def emergency_lockdown(self) -> None:
        """Emergency lockdown - deny all future actions."""
        logger.critical("EMERGENCY LOCKDOWN ACTIVATED")
        
        # Clear all permissions
        self._session_permissions.clear()
        self._approved_actions.clear()
        
        # Set a flag to deny all future actions
        # This could be implemented as a configuration change
        # For now, we'll clear the action history to trigger rate limiting
        self._action_history = [time.time()] * self.config.safety.max_actions_per_minute
        
        await self._save_permissions()
    
    async def cleanup(self) -> None:
        """Cleanup permission manager resources."""
        try:
            # Save current permissions
            await self._save_permissions()
            
            # Clear in-memory data
            self._session_permissions.clear()
            self._action_history.clear()
            
            logger.info("PermissionManager cleaned up")
            
        except Exception as e:
            logger.error(f"Permission manager cleanup failed: {e}")