"""
Query Builder

Abstract ChromaDB filter syntax for building type-safe queries.
"""

from typing import Dict, Any, List, Optional, Union


class QueryBuilder:
    """
    Build ChromaDB where filter queries in a type-safe manner.

    Provides methods to construct filters without directly using
    ChromaDB's where syntax, making code more maintainable and less error-prone.

    ChromaDB Filter Operators:
    - $eq: Equal
    - $ne: Not equal
    - $gt: Greater than
    - $gte: Greater than or equal
    - $lt: Less than
    - $lte: Less than or equal
    - $in: In list
    - $nin: Not in list

    Logical Operators:
    - $and: All conditions must be true
    - $or: Any condition must be true
    """

    @staticmethod
    def equal(field: str, value: Any) -> Dict[str, Any]:
        """
        Create an equality filter: field == value

        Args:
            field: Metadata field name
            value: Value to match

        Returns:
            ChromaDB where filter dict
        """
        return {field: {"$eq": value}}

    @staticmethod
    def not_equal(field: str, value: Any) -> Dict[str, Any]:
        """
        Create a not-equal filter: field != value

        Args:
            field: Metadata field name
            value: Value to not match

        Returns:
            ChromaDB where filter dict
        """
        return {field: {"$ne": value}}

    @staticmethod
    def greater_than(field: str, value: Union[int, float]) -> Dict[str, Any]:
        """
        Create a greater-than filter: field > value

        Args:
            field: Metadata field name
            value: Value to compare against

        Returns:
            ChromaDB where filter dict
        """
        return {field: {"$gt": value}}

    @staticmethod
    def greater_than_equal(field: str, value: Union[int, float]) -> Dict[str, Any]:
        """
        Create a greater-than-or-equal filter: field >= value

        Args:
            field: Metadata field name
            value: Value to compare against

        Returns:
            ChromaDB where filter dict
        """
        return {field: {"$gte": value}}

    @staticmethod
    def less_than(field: str, value: Union[int, float]) -> Dict[str, Any]:
        """
        Create a less-than filter: field < value

        Args:
            field: Metadata field name
            value: Value to compare against

        Returns:
            ChromaDB where filter dict
        """
        return {field: {"$lt": value}}

    @staticmethod
    def less_than_equal(field: str, value: Union[int, float]) -> Dict[str, Any]:
        """
        Create a less-than-or-equal filter: field <= value

        Args:
            field: Metadata field name
            value: Value to compare against

        Returns:
            ChromaDB where filter dict
        """
        return {field: {"$lte": value}}

    @staticmethod
    def in_list(field: str, values: List[Any]) -> Dict[str, Any]:
        """
        Create an in-list filter: field in values

        Args:
            field: Metadata field name
            values: List of values to match

        Returns:
            ChromaDB where filter dict
        """
        return {field: {"$in": values}}

    @staticmethod
    def not_in_list(field: str, values: List[Any]) -> Dict[str, Any]:
        """
        Create a not-in-list filter: field not in values

        Args:
            field: Metadata field name
            values: List of values to not match

        Returns:
            ChromaDB where filter dict
        """
        return {field: {"$nin": values}}

    @staticmethod
    def and_filters(*filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine multiple filters with AND logic.

        All filters must be true.

        Args:
            *filters: Variable number of filter dicts

        Returns:
            Combined ChromaDB where filter dict
        """
        if not filters:
            return {}

        if len(filters) == 1:
            return filters[0]

        return {"$and": list(filters)}

    @staticmethod
    def or_filters(*filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine multiple filters with OR logic.

        Any filter can be true.

        Args:
            *filters: Variable number of filter dicts

        Returns:
            Combined ChromaDB where filter dict
        """
        if not filters:
            return {}

        if len(filters) == 1:
            return filters[0]

        return {"$or": list(filters)}

    @staticmethod
    def by_user_and_project(
        user_id: str, project_id: str
    ) -> Dict[str, Any]:
        """
        Create a filter for user and project isolation.

        Args:
            user_id: User identifier
            project_id: Project identifier

        Returns:
            ChromaDB where filter dict
        """
        return QueryBuilder.and_filters(
            QueryBuilder.equal("user_id", user_id),
            QueryBuilder.equal("project_id", project_id),
        )

    @staticmethod
    def by_component(component: str) -> Dict[str, Any]:
        """
        Create a filter for specific component.

        Args:
            component: Component name

        Returns:
            ChromaDB where filter dict
        """
        return QueryBuilder.equal("component", component)

    @staticmethod
    def by_components(components: List[str]) -> Dict[str, Any]:
        """
        Create a filter for multiple components.

        Args:
            components: List of component names

        Returns:
            ChromaDB where filter dict
        """
        return QueryBuilder.in_list("component", components)

    @staticmethod
    def by_tags(tags: List[str]) -> Dict[str, Any]:
        """
        Create a filter for specific tags.

        Args:
            tags: List of tag values

        Returns:
            ChromaDB where filter dict
        """
        return QueryBuilder.in_list("tags", tags)

    @staticmethod
    def by_agent(agent: str) -> Dict[str, Any]:
        """
        Create a filter for specific agent.

        Args:
            agent: Agent name

        Returns:
            ChromaDB where filter dict
        """
        return QueryBuilder.equal("agent", agent)

    @staticmethod
    def is_valid_filter(where_filter: Optional[Dict[str, Any]]) -> bool:
        """
        Check if a filter dict is valid.

        Args:
            where_filter: Filter dict to validate

        Returns:
            True if filter is valid or None
        """
        return where_filter is None or isinstance(where_filter, dict)
