"""
Base agent class for CodeLens.
Provides lifecycle management, retry logic, and timeout handling.
"""

import asyncio
from typing import Any, Dict, Optional
from datetime import datetime
import structlog

from codelens.app.models.agent import AgentInput, AgentOutput, AgentStatus


class BaseAgent:
    """
    Base agent class that provides common functionality for all agents in the CodeLens system.
    Handles lifecycle management, retry logic with exponential backoff, and timeout handling.
    """

    MAX_RETRIES = 3
    DEFAULT_TIMEOUT = 120  # seconds

    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.logger = structlog.get_logger(__name__).bind(
            agent_id=agent_id,
            agent_type=agent_type
        )

    async def run(self, input_data: AgentInput) -> AgentOutput:
        """
        Execute the agent with retry logic and timeout handling.

        Args:
            input_data: The input data for the agent

        Returns:
            AgentOutput: The result of the agent execution
        """
        self.logger.info("Agent starting", attempt=1)

        for attempt in range(self.MAX_RETRIES):
            try:
                # Apply timeout to the agent execution
                async with asyncio.timeout(self.DEFAULT_TIMEOUT):
                    return await self._execute(input_data)

            except asyncio.TimeoutError:
                self.logger.warning(
                    "Agent execution timed out",
                    attempt=attempt + 1,
                    timeout=self.DEFAULT_TIMEOUT
                )
                if attempt == self.MAX_RETRIES - 1:
                    # Final attempt failed
                    return AgentOutput(
                        status=AgentStatus.FAILED,
                        error=f"Agent timed out after {self.MAX_RETRIES} attempts",
                        agent_id=self.agent_id,
                        agent_type=self.agent_type,
                        completed_at=datetime.utcnow()
                    )
                # Exponential backoff: 2^attempt seconds
                await asyncio.sleep(2 ** attempt)

            except Exception as e:
                self.logger.error(
                    "Agent execution failed",
                    attempt=attempt + 1,
                    error=str(e)
                )
                if attempt == self.MAX_RETRIES - 1:
                    # Final attempt failed
                    return AgentOutput(
                        status=AgentStatus.FAILED,
                        error=str(e),
                        agent_id=self.agent_id,
                        agent_type=self.agent_type,
                        completed_at=datetime.utcnow()
                    )
                # Exponential backoff: 2^attempt seconds
                await asyncio.sleep(2 ** attempt)

        # This should never be reached, but just in case
        return AgentOutput(
            status=AgentStatus.FAILED,
            error="Agent failed after maximum retries",
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            completed_at=datetime.utcnow()
        )

    async def _execute(self, input_data: AgentInput) -> AgentOutput:
        """
        Abstract method that must be implemented by subclasses.
        Contains the actual agent logic.

        Args:
            input_data: The input data for the agent

        Returns:
            AgentOutput: The result of the agent execution
        """
        raise NotImplementedError("Subclasses must implement _execute method")