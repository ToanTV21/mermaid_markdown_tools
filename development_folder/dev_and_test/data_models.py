"""
Data Models for Log Analysis Automation Tool
Based on use case documentation specifications
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class LogLevel(Enum):
    """Log severity levels"""
    VERBOSE = "V"
    DEBUG = "D"
    INFO = "I"
    WARNING = "W"
    ERROR = "E"
    FATAL = "F"


class CameraMode(Enum):
    """Camera operation modes"""
    CAM_NORMAL = "CamNormal"
    CAM_DIAG = "CamDiag"
    CAM_PKS = "CamPKS"


class CameraState(Enum):
    """Camera states"""
    CAM_ON = "CamON"
    CAM_OFF = "CamOFF"


class ErrorCode(Enum):
    """Error codes for camera operations"""
    NO_ERROR = "NoError"
    HARDWARE_ERROR = "HardwareError"
    TIMEOUT_ERROR = "TimeoutError"
    PERMISSION_ERROR = "PermissionError"


@dataclass
class LogEntry:
    """Structured log entry representation"""
    timestamp: str
    level: LogLevel
    tag: str
    message: str
    original_line: str
    line_number: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'timestamp': self.timestamp,
            'level': self.level.value,
            'tag': self.tag,
            'message': self.message,
            'original_line': self.original_line,
            'line_number': self.line_number
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """Create LogEntry from dictionary"""
        return cls(
            timestamp=data['timestamp'],
            level=LogLevel(data['level']),
            tag=data['tag'],
            message=data['message'],
            original_line=data['original_line'],
            line_number=data['line_number']
        )


@dataclass
class CameraInfo:
    """Camera information structure for AIDL communication"""
    mode: CameraMode
    state: CameraState
    error: ErrorCode
    sequence_id: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'mode': self.mode.value,
            'state': self.state.value,
            'error': self.error.value,
            'sequence_id': self.sequence_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CameraInfo':
        """Create CameraInfo from dictionary"""
        return cls(
            mode=CameraMode(data['mode']),
            state=CameraState(data['state']),
            error=ErrorCode(data['error']),
            sequence_id=data['sequence_id']
        )


@dataclass
class SequenceEvent:
    """Sequence event for diagram generation"""
    timestamp: str
    from_entity: str
    to_entity: str
    message: str
    event_type: str
    metadata: Dict[str, Any]
    log_entry: Optional[LogEntry] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'timestamp': self.timestamp,
            'from_entity': self.from_entity,
            'to_entity': self.to_entity,
            'message': self.message,
            'event_type': self.event_type,
            'metadata': self.metadata,
            'log_entry': self.log_entry.to_dict() if self.log_entry else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SequenceEvent':
        """Create SequenceEvent from dictionary"""
        return cls(
            timestamp=data['timestamp'],
            from_entity=data['from_entity'],
            to_entity=data['to_entity'],
            message=data['message'],
            event_type=data['event_type'],
            metadata=data['metadata'],
            log_entry=LogEntry.from_dict(data['log_entry']) if data['log_entry'] else None
        )


@dataclass
class Template:
    """Log pattern template for sequence generation"""
    name: str
    pattern: str
    sequence_mapping: Dict[str, str]
    priority: int
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'pattern': self.pattern,
            'sequence_mapping': self.sequence_mapping,
            'priority': self.priority,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Template':
        """Create Template from dictionary"""
        return cls(
            name=data['name'],
            pattern=data['pattern'],
            sequence_mapping=data['sequence_mapping'],
            priority=data['priority'],
            description=data.get('description', '')
        )


@dataclass
class AnalysisResult:
    """Complete analysis result container"""
    log_entries: List[LogEntry]
    sequence_events: List[SequenceEvent]
    templates_used: List[Template]
    statistics: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'log_entries': [entry.to_dict() for entry in self.log_entries],
            'sequence_events': [event.to_dict() for event in self.sequence_events],
            'templates_used': [template.to_dict() for template in self.templates_used],
            'statistics': self.statistics,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        """Create AnalysisResult from dictionary"""
        return cls(
            log_entries=[LogEntry.from_dict(entry) for entry in data['log_entries']],
            sequence_events=[SequenceEvent.from_dict(event) for event in data['sequence_events']],
            templates_used=[Template.from_dict(template) for template in data['templates_used']],
            statistics=data['statistics'],
            metadata=data['metadata']
        )


@dataclass
class TestEvidence:
    """Test evidence report data"""
    test_id: str
    timestamp: str
    environment: str
    log_file_path: str
    total_log_entries: int
    events_generated: int
    coverage_metrics: Dict[str, Any]
    sequence_diagram: str
    critical_logs: List[LogEntry]
    checksum: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'test_id': self.test_id,
            'timestamp': self.timestamp,
            'environment': self.environment,
            'log_file_path': self.log_file_path,
            'total_log_entries': self.total_log_entries,
            'events_generated': self.events_generated,
            'coverage_metrics': self.coverage_metrics,
            'sequence_diagram': self.sequence_diagram,
            'critical_logs': [log.to_dict() for log in self.critical_logs],
            'checksum': self.checksum
        }


class BaseModule:
    """Base class for all analysis modules"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.debug = self.config.get('debug', False)
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """Setup logging for the module"""
        import logging
        logger = logging.getLogger(self.__class__.__name__)
        if self.debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
        return logger
    
    def log_debug(self, message: str):
        """Log debug message"""
        if self.debug:
            self.logger.debug(message)
    
    def log_info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def log_error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def log_warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
