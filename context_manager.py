"""
Context Manager - Intelligent context window management for LLM

This module manages the context window for LLM interactions, handling:
    - Conversation history
    - Sensor data aggregation
    - Priority-based context pruning
    - Temporal context decay
    - Context compression

The context manager ensures the most relevant information is always
available to the LLM within token limits.

Features:
    - Sliding window with priority queue
    - Automatic compression of old context
    - Emergency context injection
    - Context relevance scoring
    - Multi-modal context support

Example:
    >>> manager = ContextManager(max_tokens=2048)
    >>> manager.add_sensor_data({'gps': (50.1, 24.5), 'battery': 75})
    >>> manager.add_event('obstacle_detected', priority='high')
    >>> context = manager.get_context()
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
import json


class ContextPriority(Enum):
    """Priority levels for context entries"""
    CRITICAL = 4  # Emergency, safety-critical
    HIGH = 3      # Important mission data
    MEDIUM = 2    # Regular updates
    LOW = 1       # Background info


class ContextType(Enum):
    """Types of context entries"""
    SENSOR_DATA = "sensor"
    EVENT = "event"
    MISSION_UPDATE = "mission"
    CONVERSATION = "conversation"
    SYSTEM_STATE = "system"
    ENVIRONMENTAL = "environmental"


@dataclass
class ContextEntry:
    """Single context entry with metadata"""
    content: Any
    context_type: ContextType
    priority: ContextPriority
    timestamp: datetime
    tokens: int = 0  # Estimated token count
    ttl: Optional[int] = None  # Time to live in seconds
    sticky: bool = False  # Never auto-remove
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if entry has expired based on TTL"""
        if self.ttl is None or self.sticky:
            return False
        
        age = (datetime.now() - self.timestamp).total_seconds()
        return age > self.ttl
    
    def get_age_seconds(self) -> float:
        """Get age of entry in seconds"""
        return (datetime.now() - self.timestamp).total_seconds()
    
    def get_relevance_score(self) -> float:
        """
        Calculate relevance score based on priority, age, and stickiness
        Higher score = more relevant
        """
        # Base score from priority
        score = self.priority.value * 100
        
        # Sticky items get bonus
        if self.sticky:
            score += 200
        
        # Decay score with age (half-life of 5 minutes)
        age_minutes = self.get_age_seconds() / 60
        decay_factor = 0.5 ** (age_minutes / 5)
        score *= decay_factor
        
        # Critical items decay slower
        if self.priority == ContextPriority.CRITICAL:
            score *= 2
        
        return score


class ContextManager:
    """
    Manages LLM context window with intelligent pruning
    
    The context manager maintains a sliding window of relevant information,
    automatically pruning old or low-priority data to stay within token limits.
    
    Attributes:
        max_tokens (int): Maximum context window size in tokens
        entries (deque): Queue of context entries
        current_tokens (int): Current token count
        pruning_enabled (bool): Whether automatic pruning is active
    """
    
    def __init__(self,
                 max_tokens: int = 2048,
                 pruning_threshold: float = 0.8,
                 compression_enabled: bool = True):
        """
        Initialize Context Manager
        
        Args:
            max_tokens: Maximum tokens in context window
            pruning_threshold: Start pruning at this % of max_tokens
            compression_enabled: Enable context compression
        """
        self.max_tokens = max_tokens
        self.pruning_threshold = pruning_threshold
        self.compression_enabled = compression_enabled
        
        self.entries: List[ContextEntry] = []
        self.current_tokens = 0
        self.pruning_enabled = True
        
        # Statistics
        self.total_entries_added = 0
        self.total_entries_pruned = 0
        self.total_compressions = 0
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(
            f"ContextManager initialized "
            f"(max_tokens={max_tokens}, threshold={pruning_threshold})"
        )
    
    def add_sensor_data(self,
                       sensor_data: Dict[str, Any],
                       priority: ContextPriority = ContextPriority.MEDIUM,
                       ttl: int = 300) -> None:
        """
        Add sensor data to context
        
        Args:
            sensor_data: Dictionary of sensor readings
            priority: Priority level
            ttl: Time to live in seconds (default: 5 minutes)
        
        Example:
            >>> manager.add_sensor_data({
            ...     'gps': {'lat': 50.123, 'lon': 24.456},
            ...     'battery': 75,
            ...     'altitude': 100
            ... })
        """
        # Compress sensor data for efficiency
        compressed = self._compress_sensor_data(sensor_data)
        
        entry = ContextEntry(
            content=compressed,
            context_type=ContextType.SENSOR_DATA,
            priority=priority,
            timestamp=datetime.now(),
            tokens=self._estimate_tokens(compressed),
            ttl=ttl,
            metadata={'raw_keys': list(sensor_data.keys())}
        )
        
        self._add_entry(entry)
    
    def add_event(self,
                  event_name: str,
                  event_data: Optional[Dict[str, Any]] = None,
                  priority: ContextPriority = ContextPriority.HIGH,
                  sticky: bool = False) -> None:
        """
        Add event to context
        
        Args:
            event_name: Name/type of event
            event_data: Optional event details
            priority: Priority level
            sticky: Whether event should persist (never auto-pruned)
        
        Example:
            >>> manager.add_event('obstacle_detected', {
            ...     'type': 'power_line',
            ...     'distance': 100,
            ...     'bearing': 45
            ... }, priority=ContextPriority.CRITICAL)
        """
        content = {
            'event': event_name,
            'data': event_data or {},
            'time': datetime.now().isoformat()
        }
        
        entry = ContextEntry(
            content=content,
            context_type=ContextType.EVENT,
            priority=priority,
            timestamp=datetime.now(),
            tokens=self._estimate_tokens(content),
            sticky=sticky
        )
        
        self._add_entry(entry)
        
        self.logger.info(f"Event added: {event_name} (priority={priority.name})")
    
    def add_mission_update(self,
                          update: Dict[str, Any],
                          priority: ContextPriority = ContextPriority.HIGH) -> None:
        """
        Add mission status update
        
        Args:
            update: Mission update data
            priority: Priority level
        """
        entry = ContextEntry(
            content=update,
            context_type=ContextType.MISSION_UPDATE,
            priority=priority,
            timestamp=datetime.now(),
            tokens=self._estimate_tokens(update),
            sticky=True  # Mission updates are important
        )
        
        self._add_entry(entry)
    
    def add_conversation(self,
                        role: str,
                        message: str,
                        priority: ContextPriority = ContextPriority.MEDIUM) -> None:
        """
        Add conversation turn (user/assistant)
        
        Args:
            role: 'user' or 'assistant'
            message: Conversation message
            priority: Priority level
        """
        content = {
            'role': role,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        entry = ContextEntry(
            content=content,
            context_type=ContextType.CONVERSATION,
            priority=priority,
            timestamp=datetime.now(),
            tokens=self._estimate_tokens(message),
            ttl=600  # 10 minutes
        )
        
        self._add_entry(entry)
    
    def add_system_state(self,
                        state: Dict[str, Any],
                        sticky: bool = True) -> None:
        """
        Add system state snapshot
        
        Args:
            state: System state dictionary
            sticky: Keep in context (default: True)
        """
        entry = ContextEntry(
            content=state,
            context_type=ContextType.SYSTEM_STATE,
            priority=ContextPriority.HIGH,
            timestamp=datetime.now(),
            tokens=self._estimate_tokens(state),
            sticky=sticky
        )
        
        self._add_entry(entry)
    
    def add_environmental_data(self,
                               env_data: Dict[str, Any],
                               ttl: int = 600) -> None:
        """
        Add environmental data (weather, terrain, etc.)
        
        Args:
            env_data: Environmental data dictionary
            ttl: Time to live in seconds (default: 10 minutes)
        """
        entry = ContextEntry(
            content=env_data,
            context_type=ContextType.ENVIRONMENTAL,
            priority=ContextPriority.MEDIUM,
            timestamp=datetime.now(),
            tokens=self._estimate_tokens(env_data),
            ttl=ttl
        )
        
        self._add_entry(entry)
    
    def _add_entry(self, entry: ContextEntry) -> None:
        """
        Internal method to add entry and trigger pruning if needed
        
        Args:
            entry: ContextEntry to add
        """
        self.entries.append(entry)
        self.current_tokens += entry.tokens
        self.total_entries_added += 1
        
        # Auto-prune if we're over threshold
        if self.pruning_enabled:
            threshold_tokens = int(self.max_tokens * self.pruning_threshold)
            if self.current_tokens > threshold_tokens:
                self._prune_context()
    
    def get_context(self,
                   context_type: Optional[ContextType] = None,
                   min_priority: Optional[ContextPriority] = None,
                   max_age_seconds: Optional[int] = None) -> str:
        """
        Get formatted context string for LLM
        
        Args:
            context_type: Filter by context type (optional)
            min_priority: Minimum priority level (optional)
            max_age_seconds: Maximum age in seconds (optional)
        
        Returns:
            Formatted context string
        
        Example:
            >>> context = manager.get_context(
            ...     context_type=ContextType.SENSOR_DATA,
            ...     min_priority=ContextPriority.MEDIUM
            ... )
        """
        # Remove expired entries
        self._remove_expired()
        
        # Filter entries
        filtered = self.entries
        
        if context_type:
            filtered = [e for e in filtered if e.context_type == context_type]
        
        if min_priority:
            filtered = [e for e in filtered if e.priority.value >= min_priority.value]
        
        if max_age_seconds:
            now = datetime.now()
            filtered = [
                e for e in filtered 
                if (now - e.timestamp).total_seconds() <= max_age_seconds
            ]
        
        # Sort by relevance
        filtered.sort(key=lambda e: e.get_relevance_score(), reverse=True)
        
        # Format context
        context_parts = []
        
        # Group by type
        by_type: Dict[ContextType, List[ContextEntry]] = {}
        for entry in filtered:
            if entry.context_type not in by_type:
                by_type[entry.context_type] = []
            by_type[entry.context_type].append(entry)
        
        # Format each type
        for ctx_type, entries in by_type.items():
            context_parts.append(f"\n=== {ctx_type.value.upper()} ===")
            for entry in entries:
                context_parts.append(self._format_entry(entry))
        
        return '\n'.join(context_parts)
    
    def get_context_dict(self) -> Dict[str, Any]:
        """
        Get context as structured dictionary
        
        Returns:
            Dictionary with context organized by type
        """
        self._remove_expired()
        
        result = {}
        for entry in self.entries:
            type_key = entry.context_type.value
            if type_key not in result:
                result[type_key] = []
            
            result[type_key].append({
                'content': entry.content,
                'priority': entry.priority.name,
                'age_seconds': entry.get_age_seconds(),
                'timestamp': entry.timestamp.isoformat()
            })
        
        return result
    
    def _prune_context(self) -> None:
        """
        Prune context to fit within max_tokens
        
        Removes lowest relevance entries first, respecting sticky flag.
        """
        if not self.entries:
            return
        
        # Don't prune if we're under max
        if self.current_tokens <= self.max_tokens:
            return
        
        self.logger.debug(
            f"Pruning context: {self.current_tokens}/{self.max_tokens} tokens"
        )
        
        # Sort by relevance (lowest first)
        sortable = [e for e in self.entries if not e.sticky]
        sortable.sort(key=lambda e: e.get_relevance_score())
        
        # Remove entries until we're under limit
        tokens_to_remove = self.current_tokens - self.max_tokens
        removed_count = 0
        
        for entry in sortable:
            if tokens_to_remove <= 0:
                break
            
            self.entries.remove(entry)
            tokens_to_remove -= entry.tokens
            self.current_tokens -= entry.tokens
            removed_count += 1
            self.total_entries_pruned += 1
        
        self.logger.info(
            f"Pruned {removed_count} entries, "
            f"now {self.current_tokens}/{self.max_tokens} tokens"
        )
    
    def _remove_expired(self) -> None:
        """Remove expired entries"""
        expired = [e for e in self.entries if e.is_expired()]
        
        for entry in expired:
            self.entries.remove(entry)
            self.current_tokens -= entry.tokens
            self.total_entries_pruned += 1
        
        if expired:
            self.logger.debug(f"Removed {len(expired)} expired entries")
    
    def _compress_sensor_data(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compress sensor data for efficient storage
        
        Args:
            sensor_data: Raw sensor data
        
        Returns:
            Compressed sensor data
        """
        if not self.compression_enabled:
            return sensor_data
        
        compressed = {}
        
        for key, value in sensor_data.items():
            # Round floats to reduce tokens
            if isinstance(value, float):
                compressed[key] = round(value, 2)
            # Simplify nested dicts
            elif isinstance(value, dict):
                # Keep only essential fields
                if 'lat' in value and 'lon' in value:
                    compressed[key] = f"{value['lat']:.4f},{value['lon']:.4f}"
                else:
                    compressed[key] = str(value)[:50]  # Truncate
            else:
                compressed[key] = value
        
        self.total_compressions += 1
        return compressed
    
    def _estimate_tokens(self, content: Any) -> int:
        """
        Estimate token count for content
        
        Args:
            content: Content to estimate
        
        Returns:
            Estimated token count
        """
        # Simple estimation: ~4 chars per token
        if isinstance(content, str):
            return len(content) // 4
        elif isinstance(content, dict):
            json_str = json.dumps(content)
            return len(json_str) // 4
        else:
            return len(str(content)) // 4
    
    def _format_entry(self, entry: ContextEntry) -> str:
        """Format entry for context string"""
        age = int(entry.get_age_seconds())
        
        content_str = ""
        if isinstance(entry.content, dict):
            content_str = json.dumps(entry.content, indent=2)
        else:
            content_str = str(entry.content)
        
        return (
            f"[{entry.priority.name}] "
            f"({age}s ago) "
            f"{content_str}"
        )
    
    def clear(self) -> None:
        """Clear all context"""
        self.entries.clear()
        self.current_tokens = 0
        self.logger.info("Context cleared")
    
    def clear_type(self, context_type: ContextType) -> None:
        """
        Clear all entries of specific type
        
        Args:
            context_type: Type to clear
        """
        to_remove = [e for e in self.entries if e.context_type == context_type]
        
        for entry in to_remove:
            self.entries.remove(entry)
            self.current_tokens -= entry.tokens
        
        self.logger.info(f"Cleared {len(to_remove)} entries of type {context_type.name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get context manager statistics
        
        Returns:
            Dictionary with statistics
        """
        return {
            'total_entries': len(self.entries),
            'current_tokens': self.current_tokens,
            'max_tokens': self.max_tokens,
            'utilization': self.current_tokens / self.max_tokens,
            'entries_by_type': {
                ctx_type.name: len([e for e in self.entries if e.context_type == ctx_type])
                for ctx_type in ContextType
            },
            'entries_by_priority': {
                priority.name: len([e for e in self.entries if e.priority == priority])
                for priority in ContextPriority
            },
            'total_added': self.total_entries_added,
            'total_pruned': self.total_entries_pruned,
            'total_compressions': self.total_compressions,
            'sticky_count': len([e for e in self.entries if e.sticky])
        }
    
    def __repr__(self):
        return (f"ContextManager(entries={len(self.entries)}, "
                f"tokens={self.current_tokens}/{self.max_tokens})")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    manager = ContextManager(max_tokens=2048)
    
    # Add various types of context
    manager.add_sensor_data({
        'gps': {'lat': 50.123, 'lon': 24.456},
        'battery': 75,
        'altitude': 100,
        'heading': 45
    })
    
    manager.add_event('obstacle_detected', {
        'type': 'power_line',
        'distance': 150,
        'confidence': 0.95
    }, priority=ContextPriority.CRITICAL)
    
    manager.add_mission_update({
        'status': 'en_route',
        'progress': 0.45,
        'waypoint': 3
    })
    
    # Get formatted context
    context = manager.get_context()
    print("FORMATTED CONTEXT:")
    print(context)
    print("\n" + "="*80 + "\n")
    
    # Get stats
    stats = manager.get_stats()
    print("STATISTICS:")
    print(json.dumps(stats, indent=2))
