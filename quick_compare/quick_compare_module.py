"""
QuickCompareModule - UC-04.1 & UC-04.2
Handles sequence event generation and diagram export
"""

import re
import sys
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "development_folder" / "dev_and_test"))
from data_models import BaseModule, LogEntry, SequenceEvent, Template


class QuickCompareModule(BaseModule):
    """
    QuickCompareModule handles sequence event generation and diagram export
    Implements UC-04.1: Generate Sequence Events
    Implements UC-04.2: Export Sequence Diagrams
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.max_events_per_diagram = self.config.get('max_events_per_diagram', 1000)
        self.overview_event_limit = self.config.get('overview_event_limit', 20)
        self.output_dir = self.config.get('output_dir', 'output_seq')
        
        # Create output directory
        Path(self.output_dir).mkdir(exist_ok=True)
    
    def generate_sequence_events(self, log_entries: List[LogEntry], templates: List[Template]) -> List[SequenceEvent]:
        """
        Main flow for UC-04.1: Generate Sequence Events
        
        Args:
            log_entries: List of parsed log entries
            templates: List of configured templates
            
        Returns:
            List of generated sequence events
        """
        self.log_info(f"Generating sequence events from {len(log_entries)} log entries using {len(templates)} templates")
        
        sequence_events = []
        unmatched_entries = []
        
        # Step 1: System receives parsed logs and templates
        # Step 2: FOR each log entry
        for log_entry in log_entries:
            event_created = False
            
            # FOR each template (by priority)
            for template in sorted(templates, key=lambda t: t.priority):
                # Apply regex pattern to message
                match = re.search(template.pattern, log_entry.message)
                
                if match:
                    # If match found:
                    # Extract groups from pattern
                    groups = match.groups()
                    
                    # Map to sequence entities
                    sequence_event = self._create_sequence_event(log_entry, template, groups)
                    
                    if sequence_event:
                        # Create SequenceEvent
                        sequence_events.append(sequence_event)
                        event_created = True
                        
                        # Break template loop (first match wins by priority)
                        break
            
            # AF1: No Template Matches
            if not event_created:
                unmatched_entries.append(log_entry)
                self.log_debug(f"No template match for log entry: {log_entry.message[:50]}...")
        
        # Step 3: System collects all sequence events
        # Step 4: System preserves chronological order
        sequence_events.sort(key=lambda e: e.timestamp)
        
        # Step 5: System enriches with metadata
        sequence_events = self._enrich_events_with_metadata(sequence_events)
        
        # Step 6: System returns event collection
        self.log_info(f"Generated {len(sequence_events)} sequence events, {len(unmatched_entries)} unmatched")
        
        return sequence_events
    
    def _create_sequence_event(self, log_entry: LogEntry, template: Template, groups: List[str]) -> Optional[SequenceEvent]:
        """Create sequence event from log entry and template match"""
        try:
            # Map groups to sequence entities
            from_entity = self._map_entity(template.sequence_mapping.get('from', 'Unknown'), groups)
            to_entity = self._map_entity(template.sequence_mapping.get('to', 'Unknown'), groups)
            message = self._map_entity(template.sequence_mapping.get('message', 'Event'), groups)
            
            # Create metadata
            metadata = {
                'template_name': template.name,
                'template_priority': template.priority,
                'log_level': log_entry.level.value,
                'log_tag': log_entry.tag,
                'groups': groups
            }
            
            return SequenceEvent(
                timestamp=log_entry.timestamp,
                from_entity=from_entity,
                to_entity=to_entity,
                message=message,
                event_type=template.name,
                metadata=metadata,
                log_entry=log_entry
            )
            
        except Exception as e:
            self.log_error(f"Error creating sequence event: {str(e)}")
            return None
    
    def _map_entity(self, mapping: str, groups: List[str]) -> str:
        """Map template mapping to actual values using regex groups"""
        if not mapping:
            return "Unknown"
        
        # Replace {groupN} with actual group values
        result = mapping
        for i, group in enumerate(groups):
            placeholder = f"{{group{i+1}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(group))
        
        # Replace common placeholders
        result = result.replace("{timestamp}", groups[0] if groups else "")
        result = result.replace("{level}", groups[1] if len(groups) > 1 else "")
        result = result.replace("{tag}", groups[2] if len(groups) > 2 else "")
        result = result.replace("{message}", groups[3] if len(groups) > 3 else "")
        
        # Sanitize for Mermaid (remove special characters)
        result = re.sub(r'[^\w\s-]', '', result)
        result = re.sub(r'\s+', '_', result.strip())
        
        return result or "Unknown"
    
    def _enrich_events_with_metadata(self, events: List[SequenceEvent]) -> List[SequenceEvent]:
        """Enrich events with additional metadata"""
        # Add sequence numbers
        for i, event in enumerate(events):
            event.metadata['sequence_number'] = i + 1
        
        # Add timing information
        if len(events) > 1:
            for i in range(1, len(events)):
                prev_time = self._parse_timestamp(events[i-1].timestamp)
                curr_time = self._parse_timestamp(events[i].timestamp)
                if prev_time and curr_time:
                    duration = (curr_time - prev_time).total_seconds()
                    events[i].metadata['time_since_previous'] = duration
        
        return events
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime object"""
        try:
            # Handle Android logcat format: MM-DD HH:MM:SS.mmm
            if re.match(r'\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}', timestamp_str):
                # Use current year for parsing
                current_year = datetime.now().year
                full_timestamp = f"{current_year}-{timestamp_str}"
                return datetime.strptime(full_timestamp, "%Y-%m-%d %H:%M:%S.%f")
        except Exception:
            pass
        return None
    
    def export_sequence_diagrams(self, sequence_events: List[SequenceEvent]) -> Dict[str, str]:
        """
        Main flow for UC-04.2: Export Sequence Diagrams
        
        Args:
            sequence_events: List of sequence events
            
        Returns:
            Dictionary with overview and detailed diagram paths
        """
        self.log_info(f"Exporting sequence diagrams for {len(sequence_events)} events")
        
        try:
            # Step 1: System prepares sequence events
            if not sequence_events:
                self.log_warning("No sequence events to export")
                return {}
            
            # Step 2: System generates overview diagram
            overview_content = self._generate_overview_diagram(sequence_events)
            overview_path = self._write_diagram_file("overview_seq.md", overview_content)
            
            # Step 3: System generates detailed diagram
            detailed_content = self._generate_detailed_diagram(sequence_events)
            detailed_path = self._write_diagram_file("detail_seq.md", detailed_content)
            
            # Step 4: System writes both diagrams to files
            # Step 5: System validates Mermaid syntax
            validation_result = self._validate_mermaid_syntax(overview_content, detailed_content)
            
            # Step 6: System reports export success
            if validation_result['valid']:
                self.log_info("Sequence diagrams exported successfully")
                return {
                    'overview': overview_path,
                    'detailed': detailed_path
                }
            else:
                self.log_error(f"Mermaid syntax validation failed: {validation_result['errors']}")
                return {}
                
        except Exception as e:
            self.log_error(f"Error exporting sequence diagrams: {str(e)}")
            return {}
    
    def _generate_overview_diagram(self, events: List[SequenceEvent]) -> str:
        """Generate overview diagram with limited events"""
        # AF1: Too Many Events - limit to overview_event_limit
        limited_events = events[:self.overview_event_limit]
        
        # Extract unique participants
        participants = self._extract_participants(limited_events)
        
        content = "# Sequence Overview\n\n"
        content += "```mermaid\n"
        content += "sequenceDiagram\n"
        
        # Add participant declarations
        for participant in participants:
            content += f"    participant {participant}\n"
        
        content += "\n"
        
        # Add events (simplified flow)
        for event in limited_events:
            content += f"    {event.from_entity}->>{event.to_entity}: {event.message}\n"
        
        content += "```\n\n"
        content += f"*Overview showing first {len(limited_events)} events of {len(events)} total*\n"
        
        return content
    
    def _generate_detailed_diagram(self, events: List[SequenceEvent]) -> str:
        """Generate detailed diagram with all events and metadata"""
        # AF1: Too Many Events - paginate if necessary
        if len(events) > self.max_events_per_diagram:
            return self._generate_paginated_diagrams(events)
        
        # Extract unique participants
        participants = self._extract_participants(events)
        
        content = "# Detailed Sequence Diagram\n\n"
        content += "```mermaid\n"
        content += "sequenceDiagram\n"
        
        # Add participant declarations
        for participant in participants:
            content += f"    participant {participant}\n"
        
        content += "\n"
        
        # Add events with timestamps and metadata
        for i, event in enumerate(events):
            # Add timestamp note for every 10th event
            if i % 10 == 0:
                content += f"    Note over {participants[0]},{participants[-1]}: {event.timestamp}\n"
            
            # Add event
            content += f"    {event.from_entity}->>{event.to_entity}: {event.message}\n"
            
            # Add metadata note for important events
            if event.metadata.get('log_level') in ['E', 'F']:
                content += f"    Note over {event.to_entity}: Error Event\n"
        
        content += "```\n\n"
        content += f"*Detailed view showing all {len(events)} events with timestamps*\n"
        
        return content
    
    def _generate_paginated_diagrams(self, events: List[SequenceEvent]) -> str:
        """Generate paginated diagrams for large event sets"""
        content = "# Detailed Sequence Diagram (Paginated)\n\n"
        
        total_pages = (len(events) + self.max_events_per_diagram - 1) // self.max_events_per_diagram
        
        for page in range(total_pages):
            start_idx = page * self.max_events_per_diagram
            end_idx = min(start_idx + self.max_events_per_diagram, len(events))
            page_events = events[start_idx:end_idx]
            
            content += f"## Page {page + 1} of {total_pages}\n\n"
            content += self._generate_detailed_diagram(page_events)
            content += "\n"
        
        return content
    
    def _extract_participants(self, events: List[SequenceEvent]) -> List[str]:
        """Extract unique participants from events"""
        participants = set()
        for event in events:
            participants.add(event.from_entity)
            participants.add(event.to_entity)
        
        # AF2: Invalid Characters - sanitize participant names
        sanitized_participants = []
        for participant in sorted(participants):
            sanitized = self._sanitize_participant_name(participant)
            sanitized_participants.append(sanitized)
        
        return sanitized_participants
    
    def _sanitize_participant_name(self, name: str) -> str:
        """Sanitize participant name for Mermaid"""
        # Remove special characters and replace with underscores
        sanitized = re.sub(r'[^\w\s-]', '', name)
        sanitized = re.sub(r'\s+', '_', sanitized.strip())
        
        # Ensure it starts with a letter
        if sanitized and not sanitized[0].isalpha():
            sanitized = f"P_{sanitized}"
        
        return sanitized or "Unknown"
    
    def _write_diagram_file(self, filename: str, content: str) -> str:
        """Write diagram content to file"""
        output_path = Path(self.output_dir) / filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(content)
            
            self.log_debug(f"Written diagram to {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.log_error(f"Error writing diagram file {filename}: {str(e)}")
            return ""
    
    def _validate_mermaid_syntax(self, overview_content: str, detailed_content: str) -> Dict[str, Any]:
        """Validate Mermaid syntax in diagrams"""
        validation_result = {
            'valid': True,
            'errors': []
        }
        
        # Basic validation - check for required Mermaid elements
        required_elements = ['sequenceDiagram', 'participant', '->>']
        
        for content_name, content in [('overview', overview_content), ('detailed', detailed_content)]:
            for element in required_elements:
                if element not in content:
                    validation_result['errors'].append(f"Missing {element} in {content_name} diagram")
                    validation_result['valid'] = False
        
        return validation_result
    
    def get_sequence_statistics(self, events: List[SequenceEvent]) -> Dict[str, Any]:
        """Get statistics about sequence events"""
        if not events:
            return {}
        
        # Count events by type
        event_types = {}
        for event in events:
            event_type = event.event_type
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        # Count events by participant
        participant_counts = {}
        for event in events:
            participant_counts[event.from_entity] = participant_counts.get(event.from_entity, 0) + 1
            participant_counts[event.to_entity] = participant_counts.get(event.to_entity, 0) + 1
        
        # Calculate timing statistics
        timestamps = [self._parse_timestamp(event.timestamp) for event in events]
        timestamps = [t for t in timestamps if t is not None]
        
        timing_stats = {}
        if len(timestamps) > 1:
            durations = [(timestamps[i] - timestamps[i-1]).total_seconds() 
                        for i in range(1, len(timestamps))]
            timing_stats = {
                'total_duration': (timestamps[-1] - timestamps[0]).total_seconds(),
                'average_interval': sum(durations) / len(durations),
                'min_interval': min(durations),
                'max_interval': max(durations)
            }
        
        return {
            'total_events': len(events),
            'event_types': event_types,
            'participant_counts': participant_counts,
            'timing_stats': timing_stats,
            'first_event': events[0].timestamp if events else None,
            'last_event': events[-1].timestamp if events else None
        }
    
    def validate_business_rules(self, events: List[SequenceEvent]) -> Dict[str, Any]:
        """
        Validate business rules for sequence generation
        BR1: First matching template wins (by priority)
        BR2: Preserve timestamp accuracy to milliseconds
        BR3: Entity names must be valid Mermaid identifiers
        BR4: Maximum 1000 events per diagram by default
        """
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # BR2: Check timestamp accuracy
        for event in events:
            if not re.match(r'\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}', event.timestamp):
                validation_result['warnings'].append(f"Event {event.event_type} has non-millisecond timestamp")
        
        # BR3: Check entity names
        for event in events:
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', event.from_entity):
                validation_result['warnings'].append(f"Invalid entity name: {event.from_entity}")
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', event.to_entity):
                validation_result['warnings'].append(f"Invalid entity name: {event.to_entity}")
        
        # BR4: Check event count
        if len(events) > self.max_events_per_diagram:
            validation_result['warnings'].append(f"Event count {len(events)} exceeds diagram limit {self.max_events_per_diagram}")
        
        return validation_result


# Example usage and testing
if __name__ == "__main__":
    # Test the QuickCompareModule
    config = {'debug': True}
    quick_compare_module = QuickCompareModule(config)
    
    # Create sample log entries and templates
    from data_models import LogEntry, LogLevel, Template
    
    sample_logs = [
        LogEntry("09-17 10:30:15.123", LogLevel.INFO, "ActivityManager", "Starting CameraActivity", "original", 1),
        LogEntry("09-17 10:30:15.456", LogLevel.DEBUG, "CameraService", "Camera initialized", "original", 2),
        LogEntry("09-17 10:30:15.789", LogLevel.ERROR, "CameraHAL", "Hardware error", "original", 3)
    ]
    
    sample_templates = [
        Template("Camera Start", r".*Camera.*", {"from": "System", "to": "Camera", "message": "Start"}, 1),
        Template("Camera Error", r".*error.*", {"from": "Camera", "to": "System", "message": "Error"}, 2)
    ]
    
    # Test sequence event generation
    events = quick_compare_module.generate_sequence_events(sample_logs, sample_templates)
    print(f"Generated {len(events)} sequence events")
    
    # Test diagram export
    diagram_paths = quick_compare_module.export_sequence_diagrams(events)
    print(f"Exported diagrams: {diagram_paths}")
    
    # Test statistics
    stats = quick_compare_module.get_sequence_statistics(events)
    print(f"Statistics: {stats}")
    
    # Test validation
    validation = quick_compare_module.validate_business_rules(events)
    print(f"Validation result: {validation}")
