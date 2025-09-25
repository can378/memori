"""
MemoryManager - Modular memory management system for Memori

This is a working implementation that coordinates interceptors and provides
a clean interface for memory management operations.
"""

import uuid
from typing import Any, Dict, List, Optional

from loguru import logger

# Interceptor system removed - using LiteLLM native callbacks only

from dotenv import load_dotenv
import os
load_dotenv()
DB_URL = os.getenv("POSTGRE_DB_URL")

class MemoryManager:
    """
    Modular memory management system that coordinates interceptors,
    memory processing, and context injection.

    This class provides a clean interface for memory operations while
    maintaining backward compatibility with the existing Memori system.
    """

    def __init__(
        self,
        database_connect: str = DB_URL,
        template: str = "basic",
        mem_prompt: Optional[str] = None,
        conscious_ingest: bool = False,
        auto_ingest: bool = False,
        namespace: Optional[str] = None,
        shared_memory: bool = False,
        memory_filters: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        verbose: bool = False,
        provider_config: Optional[Any] = None,
        # Additional parameters for compatibility
        openai_api_key: Optional[str] = None,
        api_key: Optional[str] = None,
        api_type: Optional[str] = None,
        base_url: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        azure_deployment: Optional[str] = None,
        api_version: Optional[str] = None,
        azure_ad_token: Optional[str] = None,
        organization: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the MemoryManager.

        Args:
            database_connect: Database connection string
            template: Memory template to use
            mem_prompt: Optional memory prompt
            conscious_ingest: Enable conscious memory ingestion
            auto_ingest: Enable automatic memory ingestion
            namespace: Optional namespace for memory isolation
            shared_memory: Enable shared memory across agents
            memory_filters: Optional memory filters
            user_id: Optional user identifier
            verbose: Enable verbose logging
            provider_config: Provider configuration
            **kwargs: Additional parameters for forward compatibility
        """
        self.database_connect = database_connect
        self.template = template
        self.mem_prompt = mem_prompt
        self.conscious_ingest = conscious_ingest
        self.auto_ingest = auto_ingest
        self.namespace = namespace
        self.shared_memory = shared_memory
        self.memory_filters = memory_filters or []
        self.user_id = user_id
        self.verbose = verbose
        self.provider_config = provider_config

        # Store additional configuration
        self.openai_api_key = openai_api_key
        self.api_key = api_key
        self.api_type = api_type
        self.base_url = base_url
        self.azure_endpoint = azure_endpoint
        self.azure_deployment = azure_deployment
        self.api_version = api_version
        self.azure_ad_token = azure_ad_token
        self.organization = organization
        self.kwargs = kwargs

        # self._session_id = str(uuid.uuid4())
        self._session_id = "dkskdkskksk"
        self._enabled = False

        # LiteLLM native callback manager
        self.litellm_callback_manager = None

        logger.info(f"MemoryManager initialized with session: {self._session_id}")

    def set_memori_instance(self, memori_instance):
        """Set the parent Memori instance for memory management."""
        self.memori_instance = memori_instance

        # Initialize LiteLLM callback manager
        try:
            from ..integrations.litellm_integration import setup_litellm_callbacks

            self.litellm_callback_manager = setup_litellm_callbacks(memori_instance)
            if self.litellm_callback_manager:
                logger.debug("LiteLLM callback manager initialized")
            else:
                logger.warning("Failed to initialize LiteLLM callback manager")
        except ImportError as e:
            logger.warning(f"Could not initialize LiteLLM callback manager: {e}")

        logger.debug("MemoryManager configured with Memori instance")

    def enable(self, interceptors: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Enable memory recording using LiteLLM native callbacks.

        Args:
            interceptors: Legacy parameter (ignored, using LiteLLM callbacks)

        Returns:
            Dict containing enablement results
        """
        if self._enabled:
            return {
                "success": True,
                "message": "Already enabled",
                "enabled_interceptors": ["litellm_native"],
            }

        if interceptors is None:
            interceptors = ["litellm_native"]  # Only LiteLLM native callbacks supported

        try:
            # Enable LiteLLM native callback system
            if (
                self.litellm_callback_manager
                and not self.litellm_callback_manager.is_registered
            ):
                success = self.litellm_callback_manager.register_callbacks()
                if not success:
                    return {
                        "success": False,
                        "message": "Failed to register LiteLLM callbacks",
                    }
            elif not self.litellm_callback_manager:
                logger.warning("No LiteLLM callback manager available")

            self._enabled = True

            logger.info("MemoryManager enabled with LiteLLM native callbacks")

            return {
                "success": True,
                "message": "Enabled LiteLLM native callback system",
                "enabled_interceptors": ["litellm_native"],
            }
        except Exception as e:
            logger.error(f"Failed to enable MemoryManager: {e}")
            return {"success": False, "message": str(e)}

    def disable(self) -> Dict[str, Any]:
        """
        Disable memory recording using LiteLLM native callbacks.

        Returns:
            Dict containing disable results
        """
        if not self._enabled:
            return {"success": True, "message": "Already disabled"}

        try:
            # Disable LiteLLM native callback system
            if (
                self.litellm_callback_manager
                and self.litellm_callback_manager.is_registered
            ):
                success = self.litellm_callback_manager.unregister_callbacks()
                if not success:
                    logger.warning("Failed to unregister LiteLLM callbacks")

            self._enabled = False

            logger.info("MemoryManager disabled")

            return {
                "success": True,
                "message": "MemoryManager disabled successfully (LiteLLM native callbacks)",
            }
        except Exception as e:
            logger.error(f"Failed to disable MemoryManager: {e}")
            return {"success": False, "message": str(e)}

    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of memory recording system.

        Returns:
            Dict containing memory system status information
        """
        callback_status = "inactive"
        if self.litellm_callback_manager:
            if self.litellm_callback_manager.is_registered:
                callback_status = "active"
            else:
                callback_status = "available_but_not_registered"
        else:
            callback_status = "unavailable"

        return {
            "litellm_native": {
                "enabled": self._enabled,
                "status": callback_status,
                "method": "litellm_callbacks",
                "session_id": self._session_id,
                "callback_manager": self.litellm_callback_manager is not None,
            }
        }

    def get_health(self) -> Dict[str, Any]:
        """
        Get health check of the memory management system.

        Returns:
            Dict containing health information
        """
        return {
            "session_id": self._session_id,
            "enabled": self._enabled,
            "namespace": self.namespace,
            "user_id": self.user_id,
            "litellm_callback_manager": self.litellm_callback_manager is not None,
            "litellm_callbacks_registered": (
                self.litellm_callback_manager.is_registered
                if self.litellm_callback_manager
                else False
            ),
            "memory_filters": len(self.memory_filters),
            "conscious_ingest": self.conscious_ingest,
            "auto_ingest": self.auto_ingest,
            "database_connect": self.database_connect,
            "template": self.template,
        }

    # === BACKWARD COMPATIBILITY PROPERTIES ===

    @property
    def session_id(self) -> str:
        """Get session ID for backward compatibility."""
        return self._session_id

    @property
    def enabled(self) -> bool:
        """Check if enabled for backward compatibility."""
        return self._enabled

    # === PLACEHOLDER METHODS FOR FUTURE MODULAR COMPONENTS ===

    def record_conversation(
        self,
        user_input: str,
        ai_output: str,
        model: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Record a conversation (placeholder for future implementation).

        Returns:
            Placeholder conversation ID
        """
        logger.info(f"Recording conversation (placeholder): {user_input[:50]}...")
        return str(uuid.uuid4())

    def search_memories(
        self,
        query: str,
        limit: int = 5,
        memory_types: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        min_importance: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search memories (placeholder for future implementation).

        Returns:
            Empty list (placeholder)
        """
        logger.info(f"Searching memories (placeholder): {query}")
        return []

    def cleanup(self):
        """Cleanup resources."""
        try:
            if self._enabled:
                self.disable()

            # Clean up callback manager
            if self.litellm_callback_manager:
                self.litellm_callback_manager.unregister_callbacks()
                self.litellm_callback_manager = None

            logger.info("MemoryManager cleanup completed")
        except Exception as e:
            logger.error(f"Error during MemoryManager cleanup: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()

    def __del__(self):
        """Destructor - ensure cleanup."""
        try:
            self.cleanup()
        except:
            pass
