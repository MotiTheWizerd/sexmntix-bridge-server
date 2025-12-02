# ICMS Pipeline (Identity Conversation Memory System)

The ICMS Pipeline is the core mechanism for processing user requests and retrieving relevant context and memory. It orchestrates several "ICM" (Internal Context Memory) components to understand the user's intent, temporal context, identity, and world view before fetching specific memories.

## Overview

The pipeline is implemented in `src/services/conversation_memory_pipeline/pipeline.py`. It takes a user query and context (user_id, project_id, etc.) and returns a comprehensive context object containing intent, time resolution, session state, identity, world view, and retrieved memories.

## Components

The pipeline consists of the following key components:

1.  **Intent ICM (`ICMBrain`)**:
    *   **Purpose**: Classifies the intent of the user's query.
    *   **Input**: User query.
    *   **Output**: Intent classification (e.g., "factual", "personal", "action") and confidence score.

2.  **Time ICM (`TimeICMBrain`)**:
    *   **Purpose**: Resolves time references in the query to absolute time windows.
    *   **Input**: User query, current time, timezone offset.
    *   **Output**: Start time, end time, and resolution confidence.

3.  **Session State**:
    *   **Purpose**: Computes the current session state.
    *   **Input**: Session ID, User ID, Project ID.
    *   **Output**: Session details (e.g., active session, last interaction).

4.  **Identity ICM (`IdentityICMService`)**:
    *   **Purpose**: Retrieves and computes identity-related information for the user and project.
    *   **Input**: User ID, Project ID.
    *   **Output**: Identity profile (e.g., user name, preferences, project details).

5.  **World View ICM (`WorldViewService`)**:
    *   **Purpose**: Computes or retrieves a cached "world view" summary. This represents a high-level understanding of the user's context and recent history.
    *   **Input**: User ID, Project ID, Session ID.
    *   **Output**: World view summary (textual description).

6.  **Retrieval Strategy**:
    *   **Purpose**: Determines *how* and *what* to retrieve based on the intent and query.
    *   **Logic**:
        *   Analyzes the intent and query to decide if memory retrieval is necessary.
        *   Selects a strategy (e.g., "pgvector" for semantic search, "none" to skip).
        *   Identifies "required memory" (specific topics or entities to look for).

7.  **Memory Retrieval (`ConversationMemoryRetrievalService`)**:
    *   **Purpose**: Fetches specific conversation memories from the vector database.
    *   **Input**: Query, time window, required memory, retrieval strategy.
    *   **Output**: List of relevant memory chunks.

## Pipeline Flow

The `run` method in `ConversationMemoryPipeline` executes the following steps:

1.  **Initialization**: Sets up the execution context (current time, request ID).
2.  **Parallel ICM Execution**:
    *   **Intent Classification**: `intent_icm.classify(query)`
    *   **Time Resolution**: `time_icm.resolve(query, ...)`
    *   **Session State**: `compute_session_state(...)`
3.  **Strategy Resolution**:
    *   Determines `retrieval_strategy` and `required_memory` based on the intent and query.
4.  **Context Enrichment**:
    *   **Identity**: `compute_identity(...)`
    *   **World View**: `compute_world_view(...)` (may use LLM or cache).
5.  **Logging**:
    *   Logs the results of each ICM component (Intent, Time, Session, Identity, World View) for debugging and analysis.
6.  **Short Circuit Check**:
    *   Checks if retrieval should be skipped (e.g., strategy is "none" or a sentinel indicates no retrieval needed).
    *   If skipped, returns the computed context without memory results.
7.  **Memory Retrieval**:
    *   If not skipped, calls `retrieval_service.fetch_required_memory(...)` to get relevant memories.
8.  **Final Result**:
    *   Combines all computed data (Intent, Time, Session, Identity, World View, Memories) into a dictionary and returns it.

## Output Structure

The pipeline returns a dictionary with the following keys:

*   `intent`: Result from Intent ICM.
*   `time`: Result from Time ICM.
*   `session`: Session state information.
*   `identity`: Identity profile.
*   `world_view`: World view summary.
*   `inject_world_view`: Boolean indicating if the world view should be injected into the LLM context (true if newly computed).
*   `results`: List of retrieved memory items (empty if retrieval was skipped).

## Key Files

*   `src/services/conversation_memory_pipeline/pipeline.py`: Main pipeline logic.
*   `src/services/conversation_memory_pipeline/identity.py`: Identity ICM logic.
*   `src/services/conversation_memory_pipeline/world_view.py`: World View ICM logic.
*   `src/services/conversation_memory_pipeline/strategies.py`: Retrieval strategy logic.
*   `src/modules/SXPrefrontal/brains/`: Implementation of ICM brains (Intent, Time).
