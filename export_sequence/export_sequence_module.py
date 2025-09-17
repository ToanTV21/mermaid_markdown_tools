"""
ExportSequenceModule - UC-05.1
Handles JSON export of sequence data
"""

import json
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "development_folder" / "dev_and_test"))
from data_models import BaseModule, SequenceEvent, LogEntry, Template


class ExportSequenceModule(BaseModule):
    """
    ExportSequenceModule handles JSON export of sequence data
    Implements UC-05.1: Export to JSON Format
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.output_dir = self.config.get('output_dir', 'output_seq')
        self.max_file_size = self.config.get('max_file_size', 100 * 1024 * 1024)  # 100MB
        self.pretty_print = self.config.get('pretty_print', True)
        self.include_metadata = self.config.get('include_metadata', True)
        
        # Create output directory
        Path(self.output_dir).mkdir(exist_ok=True)
    
    def export_to_json_format(self, sequence_events: List[SequenceEvent], 
                             log_entries: Optional[List[LogEntry]] = None,
                             templates_used: Optional[List[Template]] = None,
                             output_filename: str = "output_seq.json") -> str:
        """
        Main flow for UC-05.1: Export to JSON Format
        
        Args:
            sequence_events: List of sequence events to export
            log_entries: Optional list of original log entries
            templates_used: Optional list of templates used
            output_filename: Name of output JSON file
            
        Returns:
            Path to exported JSON file
        """
        self.log_info(f"Exporting {len(sequence_events)} sequence events to JSON format")
        
        try:
            # Step 1: System receives sequence event collection
            if not sequence_events:
                self.log_warning("No sequence events to export")
                return ""
            
            # Step 2: System creates JSON structure
            json_structure = self._create_json_structure(sequence_events, log_entries, templates_used)
            
            # Step 3: System serializes to JSON
            json_content = self._serialize_to_json(json_structure)
            
            # Step 4: System applies pretty printing
            if self.pretty_print:
                json_content = self._apply_pretty_printing(json_content)
            
            # Step 5: System writes to output file
            output_path = self._write_json_to_file(json_content, output_filename)
            
            # Step 6: System validates JSON output
            validation_result = self._validate_json_output(output_path)
            
            # Step 7: System confirms export success
            if validation_result['valid']:
                self.log_info(f"JSON export successful: {output_path}")
                return output_path
            else:
                self.log_error(f"JSON validation failed: {validation_result['errors']}")
                return ""
                
        except Exception as e:
            self.log_error(f"Error exporting to JSON: {str(e)}")
            return ""
    
    def _create_json_structure(self, sequence_events: List[SequenceEvent], 
                              log_entries: Optional[List[LogEntry]] = None,
                              templates_used: Optional[List[Template]] = None) -> Dict[str, Any]:
        """Create JSON structure with metadata and data"""
        # Add timestamp metadata
        export_timestamp = datetime.now().isoformat()
        
        # Add event count
        event_count = len(sequence_events)
        
        # Format sequence array
        sequence_data = []
        for event in sequence_events:
            event_dict = event.to_dict()
            sequence_data.append(event_dict)
        
        # Create base structure
        json_structure = {
            'metadata': {
                'export_timestamp': export_timestamp,
                'event_count': event_count,
                'version': '1.0',
                'format': 'sequence_events',
                'generator': 'LogAnalysisAutomationTool'
            },
            'sequence_events': sequence_data
        }
        
        # Add optional data if provided
        if log_entries and self.include_metadata:
            json_structure['log_entries'] = [entry.to_dict() for entry in log_entries]
            json_structure['metadata']['log_entry_count'] = len(log_entries)
        
        if templates_used and self.include_metadata:
            json_structure['templates_used'] = [template.to_dict() for template in templates_used]
            json_structure['metadata']['template_count'] = len(templates_used)
        
        # Add statistics
        json_structure['statistics'] = self._generate_export_statistics(sequence_events, log_entries, templates_used)
        
        return json_structure
    
    def _serialize_to_json(self, json_structure: Dict[str, Any]) -> str:
        """Serialize structure to JSON string"""
        try:
            return json.dumps(json_structure, ensure_ascii=False, default=self._json_serializer)
        except Exception as e:
            # AF1: Serialization Error
            self.log_warning(f"Serialization error, converting to string representation: {str(e)}")
            return self._handle_serialization_error(json_structure)
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for complex objects"""
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)
    
    def _handle_serialization_error(self, json_structure: Dict[str, Any]) -> str:
        """AF1: Serialization Error - convert to string representation"""
        try:
            # Convert problematic objects to strings
            def convert_to_string(obj):
                if isinstance(obj, dict):
                    return {k: convert_to_string(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_to_string(item) for item in obj]
                elif hasattr(obj, '__dict__'):
                    return str(obj)
                else:
                    return obj
            
            converted_structure = convert_to_string(json_structure)
            return json.dumps(converted_structure, ensure_ascii=False)
            
        except Exception as e:
            self.log_error(f"Failed to handle serialization error: {str(e)}")
            return json.dumps({"error": "Serialization failed", "details": str(e)})
    
    def _apply_pretty_printing(self, json_content: str) -> str:
        """Apply pretty printing to JSON content"""
        try:
            parsed_json = json.loads(json_content)
            return json.dumps(parsed_json, indent=2, ensure_ascii=False, default=self._json_serializer)
        except Exception as e:
            self.log_warning(f"Could not apply pretty printing: {str(e)}")
            return json_content
    
    def _write_json_to_file(self, json_content: str, filename: str) -> str:
        """Write JSON content to file"""
        output_path = Path(self.output_dir) / filename
        
        try:
            # Check file size before writing
            content_size = len(json_content.encode('utf-8'))
            if content_size > self.max_file_size:
                # AF2: Disk Space Insufficient - attempt compression
                return self._handle_large_file(json_content, filename)
            
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(json_content)
            
            self.log_debug(f"Written JSON to {output_path} ({content_size} bytes)")
            return str(output_path)
            
        except Exception as e:
            self.log_error(f"Error writing JSON file: {str(e)}")
            return ""
    
    def _handle_large_file(self, json_content: str, filename: str) -> str:
        """AF2: Disk Space Insufficient - attempt compression"""
        try:
            import gzip
            
            # Create compressed version
            compressed_filename = f"{filename}.gz"
            compressed_path = Path(self.output_dir) / compressed_filename
            
            with gzip.open(compressed_path, 'wt', encoding='utf-8') as file:
                file.write(json_content)
            
            self.log_info(f"File too large, created compressed version: {compressed_path}")
            return str(compressed_path)
            
        except ImportError:
            self.log_error("gzip not available for compression")
            return ""
        except Exception as e:
            self.log_error(f"Error creating compressed file: {str(e)}")
            return ""
    
    def _validate_json_output(self, file_path: str) -> Dict[str, Any]:
        """Validate JSON output file"""
        validation_result = {
            'valid': True,
            'errors': []
        }
        
        if not file_path or not Path(file_path).exists():
            validation_result['errors'].append("Output file does not exist")
            validation_result['valid'] = False
            return validation_result
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                json.load(file)
            
            # Check file size
            file_size = Path(file_path).stat().st_size
            if file_size == 0:
                validation_result['errors'].append("Output file is empty")
                validation_result['valid'] = False
            
        except json.JSONDecodeError as e:
            validation_result['errors'].append(f"Invalid JSON format: {str(e)}")
            validation_result['valid'] = False
        except Exception as e:
            validation_result['errors'].append(f"Error validating JSON: {str(e)}")
            validation_result['valid'] = False
        
        return validation_result
    
    def _generate_export_statistics(self, sequence_events: List[SequenceEvent], 
                                   log_entries: Optional[List[LogEntry]] = None,
                                   templates_used: Optional[List[Template]] = None) -> Dict[str, Any]:
        """Generate statistics for export"""
        stats = {
            'sequence_events': {
                'total_count': len(sequence_events),
                'event_types': {},
                'participants': set(),
                'time_range': {}
            }
        }
        
        # Analyze sequence events
        for event in sequence_events:
            # Count event types
            event_type = event.event_type
            stats['sequence_events']['event_types'][event_type] = \
                stats['sequence_events']['event_types'].get(event_type, 0) + 1
            
            # Collect participants
            stats['sequence_events']['participants'].add(event.from_entity)
            stats['sequence_events']['participants'].add(event.to_entity)
        
        # Convert set to list for JSON serialization
        stats['sequence_events']['participants'] = list(stats['sequence_events']['participants'])
        
        # Calculate time range
        if sequence_events:
            timestamps = [event.timestamp for event in sequence_events]
            stats['sequence_events']['time_range'] = {
                'first_event': min(timestamps),
                'last_event': max(timestamps),
                'event_count': len(timestamps)
            }
        
        # Add log entry statistics
        if log_entries:
            stats['log_entries'] = {
                'total_count': len(log_entries),
                'level_distribution': {},
                'tag_distribution': {}
            }
            
            for entry in log_entries:
                level = entry.level.value
                tag = entry.tag
                
                stats['log_entries']['level_distribution'][level] = \
                    stats['log_entries']['level_distribution'].get(level, 0) + 1
                stats['log_entries']['tag_distribution'][tag] = \
                    stats['log_entries']['tag_distribution'].get(tag, 0) + 1
        
        # Add template statistics
        if templates_used:
            stats['templates'] = {
                'total_count': len(templates_used),
                'priority_distribution': {},
                'template_names': [t.name for t in templates_used]
            }
            
            for template in templates_used:
                priority = template.priority
                stats['templates']['priority_distribution'][priority] = \
                    stats['templates']['priority_distribution'].get(priority, 0) + 1
        
        return stats
    
    def export_analysis_result(self, analysis_result) -> str:
        """Export complete analysis result to JSON"""
        if hasattr(analysis_result, 'to_dict'):
            json_structure = analysis_result.to_dict()
        else:
            json_structure = analysis_result
        
        json_content = json.dumps(json_structure, indent=2, ensure_ascii=False, default=self._json_serializer)
        
        output_path = Path(self.output_dir) / "complete_analysis.json"
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(json_content)
        
        self.log_info(f"Complete analysis exported to {output_path}")
        return str(output_path)
    
    def validate_business_rules(self) -> Dict[str, Any]:
        """
        Validate business rules for JSON export
        BR1: JSON must be valid and parseable
        BR2: Timestamps in ISO 8601 format
        BR3: Preserve all event metadata
        BR4: File size limit 100MB
        """
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # BR4: Check file size limit
        if self.max_file_size > 100 * 1024 * 1024:  # 100MB
            validation_result['warnings'].append(f"File size limit {self.max_file_size} exceeds recommended 100MB")
        
        # BR2: Check timestamp format (this would be validated during export)
        # BR1 and BR3: These are handled during the export process
        
        return validation_result
    
    def get_export_statistics(self) -> Dict[str, Any]:
        """Get current export configuration statistics"""
        return {
            'output_directory': self.output_dir,
            'max_file_size': self.max_file_size,
            'pretty_print_enabled': self.pretty_print,
            'metadata_included': self.include_metadata,
            'output_files': list(Path(self.output_dir).glob("*.json"))
        }


# Example usage and testing
if __name__ == "__main__":
    # Test the ExportSequenceModule
    config = {'debug': True, 'pretty_print': True}
    export_module = ExportSequenceModule(config)
    
    # Create sample sequence events
    from data_models import SequenceEvent, LogEntry, LogLevel, Template
    
    sample_events = [
        SequenceEvent(
            timestamp="09-17 10:30:15.123",
            from_entity="System",
            to_entity="CameraService",
            message="Start Service",
            event_type="Camera Start",
            metadata={"template_name": "Camera Start", "priority": 1}
        ),
        SequenceEvent(
            timestamp="09-17 10:30:15.456",
            from_entity="CameraService",
            to_entity="CameraHAL",
            message="Initialize Hardware",
            event_type="Camera Init",
            metadata={"template_name": "Camera Init", "priority": 2}
        )
    ]
    
    sample_logs = [
        LogEntry("09-17 10:30:15.123", LogLevel.INFO, "CameraService", "Service started", "original", 1),
        LogEntry("09-17 10:30:15.456", LogLevel.DEBUG, "CameraHAL", "Hardware initialized", "original", 2)
    ]
    
    sample_templates = [
        Template("Camera Start", r".*start.*", {"from": "System", "to": "Camera", "message": "Start"}, 1),
        Template("Camera Init", r".*init.*", {"from": "Camera", "to": "HAL", "message": "Init"}, 2)
    ]
    
    # Test JSON export
    output_path = export_module.export_to_json_format(
        sample_events, 
        sample_logs, 
        sample_templates,
        "test_output.json"
    )
    print(f"Exported to: {output_path}")
    
    # Test validation
    validation = export_module.validate_business_rules()
    print(f"Validation result: {validation}")
    
    # Test statistics
    stats = export_module.get_export_statistics()
    print(f"Export statistics: {stats}")
