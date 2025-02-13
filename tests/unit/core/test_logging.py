# tests/unit/test_core/test_logging.py
"""
Test suite for the sequence-aware logging system.

Status: CURRENT
Version: 1.0
Last Updated: 2025-02-11
Superseded By: N/A
Historical Context: Initial test implementation for sequence-aware logging during Base Camp 1.
"""

import pytest
import logging
from datetime import datetime
from src.core.logging import (
    ExecutionContext,
    SequenceAwareJsonFormatter,
    SequenceAwareLogManager
)

@pytest.fixture
def log_manager():
    """Provide a fresh log manager for each test."""
    return SequenceAwareLogManager()

@pytest.fixture
def capture_logs(caplog):
    """Capture logs with the proper format."""
    caplog.set_level(logging.INFO)
    return caplog

def test_execution_context_creation():
    """Test that execution context is created with proper attributes."""
    context = ExecutionContext(
        task_id="test_task",
        sequence_id="test_sequence",
        parent_sequence_id=None,
        step_number=0,
        tool_name=None,
        reason="Test execution",
        start_time=datetime.utcnow()
    )
    
    assert context.task_id == "test_task"
    assert context.sequence_id == "test_sequence"
    assert context.parent_sequence_id is None
    assert context.step_number == 0
    assert context.tool_name is None
    assert context.reason == "Test execution"
    assert isinstance(context.start_time, datetime)
    assert context.end_time is None

def test_task_sequence_context(log_manager, capture_logs):
    """Test that task sequence properly manages context."""
    with log_manager.task_sequence("test_task", "Test operation") as context:
        assert context.task_id == "test_task"
        assert context.parent_sequence_id is None
        assert "Starting task sequence" in capture_logs.text
        
        # Verify context is accessible
        log_manager.log_with_context(logging.INFO, "Test message")
        
    assert "Completed task sequence" in capture_logs.text
    assert context.end_time is not None

def test_nested_tool_sequence(log_manager, capture_logs):
    """Test that tool sequences properly nest within task sequences."""
    with log_manager.task_sequence("test_task", "Test operation") as task_context:
        with log_manager.tool_sequence("test_tool", "Tool operation") as tool_context:
            assert tool_context.parent_sequence_id == task_context.sequence_id
            assert tool_context.tool_name == "test_tool"
            assert "Starting tool sequence" in capture_logs.text
            
            log_manager.log_with_context(logging.INFO, "Tool message")
            
        assert "Completed tool sequence" in capture_logs.text
        assert tool_context.end_time is not None

def test_tool_sequence_requires_task(log_manager):
    """Test that tool sequences cannot be created without a task sequence."""
    with pytest.raises(RuntimeError) as exc_info:
        with log_manager.tool_sequence("test_tool", "Tool operation"):
            pass
    assert "Tool sequence must be within a task sequence" in str(exc_info.value)

def test_json_formatter():
    """Test that the JSON formatter includes all required fields."""
    formatter = SequenceAwareJsonFormatter()
    logger = logging.getLogger("test_logger")
    
    # Create a log record with execution context
    context = ExecutionContext(
        task_id="test_task",
        sequence_id="test_sequence",
        parent_sequence_id=None,
        step_number=0,
        tool_name=None,
        reason="Test execution",
        start_time=datetime.utcnow()
    )
    
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test_file.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    record.execution_context = context
    
    # Format the record
    formatted = formatter.format(record)
    
    # Verify all required fields are present
    assert "task_id" in formatted
    assert "sequence_id" in formatted
    assert "timestamp" in formatted
    assert "date" in formatted
    assert "time" in formatted
    assert "sequence_start_time" in formatted

def test_concurrent_task_sequences(log_manager):
    """Test that task sequences maintain separate contexts in different threads."""
    import threading
    import queue
    
    results = queue.Queue()
    
    def run_task(task_id):
        with log_manager.task_sequence(task_id, f"Task {task_id}"):
            context = getattr(log_manager._context_storage, 'context', None)
            results.put((task_id, context.sequence_id if context else None))
    
    # Create and run two threads
    thread1 = threading.Thread(target=run_task, args=("task1",))
    thread2 = threading.Thread(target=run_task, args=("task2",))
    
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    
    # Collect results
    results_list = []
    while not results.empty():
        results_list.append(results.get())
    
    # Verify each task had its own context
    assert len(results_list) == 2
    assert results_list[0][0] != results_list[1][0]  # Different task IDs
    assert results_list[0][1] != results_list[1][1]  # Different sequence IDs