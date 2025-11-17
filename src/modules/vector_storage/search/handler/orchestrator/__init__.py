"""
Search Workflow Orchestrator Module

Coordinates the multi-stage search workflow with isolated, testable stages.

Public API:
    SearchWorkflowOrchestrator - Main orchestrator class
"""

from .orchestrator import SearchWorkflowOrchestrator

__all__ = ["SearchWorkflowOrchestrator"]

# Stages and utilities are importable but not in __all__ (advanced users only)
from . import stages
from . import utils
