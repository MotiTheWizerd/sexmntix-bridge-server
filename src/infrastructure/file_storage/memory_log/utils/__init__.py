"""
Memory Log Storage Utilities

Collection of reusable utilities for memory log file storage operations.

Modules:
- path_builder: Pure path generation functions
- directory_manager: Directory creation and management
- file_finder: File listing and existence checks
- id_parser: ID extraction from filenames
"""

# Path Builder Utilities
from .path_builder import (
    build_user_directory,
    build_user_memory_logs_dir,
    build_memory_log_filename,
    build_memory_log_file_path,
    get_glob_pattern,
    MEMORY_LOG_PREFIX,
    MEMORY_LOG_SUFFIX,
    MEMORY_LOGS_FOLDER,
    USER_PREFIX,
)

# Directory Manager Utilities
from .directory_manager import (
    ensure_directory_exists,
    directory_exists,
    create_directory_structure,
)

# File Finder Utilities
from .file_finder import (
    list_files_by_pattern,
    file_exists,
    count_files_by_pattern,
    get_file_size,
    find_latest_file,
)

# ID Parser Utilities
from .id_parser import (
    extract_id_from_filename,
    extract_memory_log_id,
    validate_id_format,
    parse_id_list,
)

__all__ = [
    # Path Builder
    "build_user_directory",
    "build_user_memory_logs_dir",
    "build_memory_log_filename",
    "build_memory_log_file_path",
    "get_glob_pattern",
    "MEMORY_LOG_PREFIX",
    "MEMORY_LOG_SUFFIX",
    "MEMORY_LOGS_FOLDER",
    "USER_PREFIX",
    # Directory Manager
    "ensure_directory_exists",
    "directory_exists",
    "create_directory_structure",
    # File Finder
    "list_files_by_pattern",
    "file_exists",
    "count_files_by_pattern",
    "get_file_size",
    "find_latest_file",
    # ID Parser
    "extract_id_from_filename",
    "extract_memory_log_id",
    "validate_id_format",
    "parse_id_list",
]
