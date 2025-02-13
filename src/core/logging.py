# src/core/logging.py
"""
Enhanced Sequence-Aware Logging System

Status: CURRENT
Version: 1.0
Last Updated: 2025-02-11
Superseded By: N/A
Historical Context: Initial implementation of sequence-aware logging system during Base Camp 1.
This module provides the foundation for tracking agent decisions and tool interactions.

This module implements a sequence-aware logging system that tracks the execution flow
of AI agent operations. It supports hierarchical task tracking, tool execution monitoring,
and business intelligence integration through structured logging formats.
"""

from typing import Dict, Any, Optional
import uuid
from contextlib import contextmanager
from datetime import datetime
import logging
from pythonjsonlogger import jsonlogger
from dataclasses import dataclass
import threading
from src.config import get_settings

@dataclass
class ExecutionContext:
    """
    Tracks the context of an agent's execution sequence.
    
    This creates a breadcrumb trail of agent actions and their rationale, enabling
    both real-time monitoring and post-execution analysis.
    
    Attributes:
        task_id: Unique identifier for the overall task
        sequence_id: Unique identifier for this specific sequence
        parent_sequence_id: ID of the parent sequence for nested operations
        step_number: Position in the sequence
        tool_name: Name of the tool being used (if applicable)
        reason: Explanation for why this step was chosen
        start_time: When this sequence began
        end_time: When this sequence completed (if finished)
    """
    task_id: str
    sequence_id: str
    parent_sequence_id: Optional[str]
    step_number: int
    tool_name: Optional[str]
    reason: Optional[str]
    start_time: datetime
    end_time: Optional[datetime] = None

class SequenceAwareJsonFormatter(jsonlogger.JsonFormatter):
    """
    Enhanced JSON formatter that understands execution sequences.
    
    This formatter extends the standard JSON formatter to include:
    - Detailed timing information for analysis
    - Execution context for tracing agent decisions
    - Standardized fields for BI tool integration
    """
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp fields for time-series analysis
        now = datetime.utcnow()
        log_record.update({
            'timestamp': now.isoformat(),
            'date': now.date().isoformat(),
            'time': now.time().isoformat(),
            'hour': now.hour,
            'day_of_week': now.weekday(),
            'month': now.month,
            'year': now.year,
        })
        
        # Add execution context if available
        if hasattr(record, 'execution_context'):
            context = record.execution_context
            log_record.update({
                'task_id': context.task_id,
                'sequence_id': context.sequence_id,
                'parent_sequence_id': context.parent_sequence_id,
                'step_number': context.step_number,
                'tool_name': context.tool_name,
                'reason': context.reason,
                'sequence_start_time': context.start_time.isoformat(),
                'sequence_end_time': context.end_time.isoformat() if context.end_time else None,
            })

class SequenceAwareLogManager:
    """
    Enhanced LogManager that tracks execution sequences.
    
    This manager provides context managers for tracking task and tool sequences,
    enabling hierarchical logging of agent operations with proper context maintenance.
    """
    
    def __init__(self):
        """Initialize the log manager with thread-local storage for context."""
        self.logger = logging.getLogger('ai_agent')
        self._context_storage = threading.local()
        self._configure_logging()
    
    def _configure_logging(self):
        """Configure the logging system with sequence-aware formatting."""
        handler = logging.StreamHandler()
        formatter = SequenceAwareJsonFormatter()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Set log level from configuration
        settings = get_settings()
        self.logger.setLevel(getattr(logging, settings.logging.LOG_LEVEL))
    
    @contextmanager
    def task_sequence(self, task_id: str, description: str):
        """
        Create a context manager for tracking a main task sequence.
        
        Args:
            task_id: Unique identifier for the task
            description: Human-readable description of the task
            
        Example:
            with log_manager.task_sequence("query_123", "Process user question") as seq:
                # Do main task work
        """
        sequence_id = str(uuid.uuid4())
        context = ExecutionContext(
            task_id=task_id,
            sequence_id=sequence_id,
            parent_sequence_id=None,
            step_number=0,
            tool_name=None,
            reason=description,
            start_time=datetime.utcnow()
        )
        
        self._context_storage.context = context
        self.logger.info(f"Starting task sequence: {description}", 
                        extra={'execution_context': context})
        
        try:
            yield context
        finally:
            context.end_time = datetime.utcnow()
            self.logger.info(f"Completed task sequence: {description}", 
                           extra={'execution_context': context})
            self._context_storage.context = None
    
    @contextmanager
    def tool_sequence(self, tool_name: str, reason: str):
        """
        Create a context manager for tracking a tool's execution within a sequence.
        
        Args:
            tool_name: Name of the tool being used
            reason: Explanation of why this tool was chosen
            
        Example:
            with log_manager.task_sequence("query_123", "Process question") as main_seq:
                with log_manager.tool_sequence("web_search", "Find information") as tool_seq:
                    # Do tool-specific work
        """
        parent_context = getattr(self._context_storage, 'context', None)
        if not parent_context:
            raise RuntimeError("Tool sequence must be within a task sequence")
        
        sequence_id = str(uuid.uuid4())
        context = ExecutionContext(
            task_id=parent_context.task_id,
            sequence_id=sequence_id,
            parent_sequence_id=parent_context.sequence_id,
            step_number=parent_context.step_number + 1,
            tool_name=tool_name,
            reason=reason,
            start_time=datetime.utcnow()
        )
        
        previous_context = self._context_storage.context
        self._context_storage.context = context
        self.logger.info(f"Starting tool sequence: {tool_name}", 
                        extra={'execution_context': context})
        
        try:
            yield context
        finally:
            context.end_time = datetime.utcnow()
            self.logger.info(f"Completed tool sequence: {tool_name}", 
                           extra={'execution_context': context})
            self._context_storage.context = previous_context
    
    def log_with_context(self, level: int, msg: str, **kwargs):
        """
        Log a message with the current execution context.
        
        Args:
            level: Logging level (e.g., logging.INFO)
            msg: Message to log
            **kwargs: Additional logging context
        """
        context = getattr(self._context_storage, 'context', None)
        extra = kwargs.get('extra', {})
        if context:
            extra['execution_context'] = context
        self.logger.log(level, msg, extra=extra)

# Global instance for application-wide use
log_manager = SequenceAwareLogManager()