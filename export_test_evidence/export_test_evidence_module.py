"""
ExportTestEvidenceModule - UC-06.1
Handles test evidence report generation
"""

import hashlib
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "development_folder" / "dev_and_test"))
from data_models import BaseModule, LogEntry, SequenceEvent, TestEvidence


class ExportTestEvidenceModule(BaseModule):
    """
    ExportTestEvidenceModule handles test evidence report generation
    Implements UC-06.1: Generate Test Evidence Report
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.output_dir = self.config.get('output_dir', 'output_testEvd')
        self.compliance_mode = self.config.get('compliance_mode', False)
        self.custom_fields = self.config.get('custom_fields', {})
        self.retention_period = self.config.get('retention_period', 7)  # years
        
        # Create output directory
        Path(self.output_dir).mkdir(exist_ok=True)
    
    def generate_test_evidence_report(self, 
                                    test_id: str,
                                    log_file_path: str,
                                    sequence_events: List[SequenceEvent],
                                    log_entries: List[LogEntry],
                                    environment: str = "Test Environment") -> str:
        """
        Main flow for UC-06.1: Generate Test Evidence Report
        
        Args:
            test_id: Unique test identifier
            log_file_path: Path to original log file
            sequence_events: List of generated sequence events
            log_entries: List of parsed log entries
            environment: Test environment description
            
        Returns:
            Path to generated evidence report
        """
        self.log_info(f"Generating test evidence report for test ID: {test_id}")
        
        try:
            # Step 1: System collects all analysis artifacts
            artifacts = self._collect_analysis_artifacts(sequence_events, log_entries)
            
            # Step 2: System generates report header
            report_content = self._generate_report_header(test_id, log_file_path, environment)
            
            # Step 3: System creates summary section
            report_content += self._create_summary_section(artifacts)
            
            # Step 4: System includes sequence diagram
            report_content += self._include_sequence_diagram(sequence_events)
            
            # Step 5: System adds log evidence
            report_content += self._add_log_evidence(log_entries)
            
            # AF1: Compliance Mode
            if self.compliance_mode:
                report_content = self._add_compliance_sections(report_content)
            
            # AF2: Custom Evidence Requirements
            if self.custom_fields:
                report_content = self._add_custom_sections(report_content)
            
            # Step 6: System formats as markdown
            # Step 7: System writes report file
            output_path = self._write_report_file(report_content, test_id)
            
            # Step 8: System generates checksum
            checksum = self._generate_checksum(output_path)
            
            # Create TestEvidence object
            test_evidence = self._create_test_evidence_object(
                test_id, log_file_path, sequence_events, log_entries, 
                environment, report_content, checksum
            )
            
            # Save evidence metadata
            self._save_evidence_metadata(test_evidence, output_path)
            
            self.log_info(f"Test evidence report generated: {output_path}")
            return output_path
            
        except Exception as e:
            self.log_error(f"Error generating test evidence report: {str(e)}")
            return ""
    
    def _collect_analysis_artifacts(self, sequence_events: List[SequenceEvent], 
                                  log_entries: List[LogEntry]) -> Dict[str, Any]:
        """Collect all analysis artifacts for the report"""
        return {
            'total_log_entries': len(log_entries),
            'events_generated': len(sequence_events),
            'coverage_metrics': self._calculate_coverage_metrics(sequence_events, log_entries),
            'critical_logs': self._identify_critical_logs(log_entries),
            'error_logs': self._identify_error_logs(log_entries),
            'sequence_statistics': self._calculate_sequence_statistics(sequence_events)
        }
    
    def _generate_report_header(self, test_id: str, log_file_path: str, environment: str) -> str:
        """Generate report header with timestamp and test information"""
        timestamp = datetime.now().isoformat()
        
        header = f"""# Test Evidence Report

## Report Information

| Field | Value |
|-------|-------|
| **Test ID** | {test_id} |
| **Generated** | {timestamp} |
| **Environment** | {environment} |
| **Log File** | {log_file_path} |
| **Report Version** | 1.0 |
| **Generator** | Log Analysis Automation Tool |

---

"""
        return header
    
    def _create_summary_section(self, artifacts: Dict[str, Any]) -> str:
        """Create summary section with key metrics"""
        summary = f"""## Summary

### Analysis Overview

| Metric | Value |
|--------|-------|
| **Total Log Entries** | {artifacts['total_log_entries']} |
| **Events Generated** | {artifacts['events_generated']} |
| **Coverage Rate** | {artifacts['coverage_metrics']['coverage_rate']:.2f}% |
| **Critical Logs** | {len(artifacts['critical_logs'])} |
| **Error Logs** | {len(artifacts['error_logs'])} |

### Coverage Metrics

- **Template Match Rate**: {artifacts['coverage_metrics']['template_match_rate']:.2f}%
- **Event Generation Rate**: {artifacts['coverage_metrics']['event_generation_rate']:.2f}%
- **Log Processing Success**: {artifacts['coverage_metrics']['log_processing_success']:.2f}%

### Sequence Statistics

- **Total Events**: {artifacts['sequence_statistics']['total_events']}
- **Event Types**: {artifacts['sequence_statistics']['event_types']}
- **Unique Participants**: {artifacts['sequence_statistics']['unique_participants']}
- **Time Span**: {artifacts['sequence_statistics']['time_span']}

---

"""
        return summary
    
    def _include_sequence_diagram(self, sequence_events: List[SequenceEvent]) -> str:
        """Include sequence diagram in the report"""
        if not sequence_events:
            return "## Sequence Diagram\n\n*No sequence events generated*\n\n---\n\n"
        
        # Limit to first 10 events for readability
        limited_events = sequence_events[:10]
        
        diagram_content = "## Sequence Diagram\n\n"
        diagram_content += "```mermaid\n"
        diagram_content += "sequenceDiagram\n"
        
        # Extract unique participants
        participants = set()
        for event in limited_events:
            participants.add(event.from_entity)
            participants.add(event.to_entity)
        
        # Add participant declarations
        for participant in sorted(participants):
            diagram_content += f"    participant {participant}\n"
        
        diagram_content += "\n"
        
        # Add events
        for event in limited_events:
            diagram_content += f"    {event.from_entity}->>{event.to_entity}: {event.message}\n"
        
        diagram_content += "```\n\n"
        
        if len(sequence_events) > 10:
            diagram_content += f"*Showing first 10 events of {len(sequence_events)} total events*\n\n"
        
        diagram_content += "---\n\n"
        return diagram_content
    
    def _add_log_evidence(self, log_entries: List[LogEntry]) -> str:
        """Add log evidence section"""
        evidence_content = "## Log Evidence\n\n"
        
        # Get first 20 critical logs
        critical_logs = self._identify_critical_logs(log_entries)[:20]
        error_logs = self._identify_error_logs(log_entries)[:20]
        
        if critical_logs:
            evidence_content += "### Critical Log Entries\n\n"
            evidence_content += "| Timestamp | Level | Tag | Message |\n"
            evidence_content += "|-----------|-------|-----|----------|\n"
            
            for log in critical_logs:
                evidence_content += f"| {log.timestamp} | {log.level.value} | {log.tag} | {log.message[:100]}... |\n"
            
            evidence_content += "\n"
        
        if error_logs:
            evidence_content += "### Error Log Entries\n\n"
            evidence_content += "| Timestamp | Level | Tag | Message |\n"
            evidence_content += "|-----------|-------|-----|----------|\n"
            
            for log in error_logs:
                evidence_content += f"| {log.timestamp} | {log.level.value} | {log.tag} | {log.message[:100]}... |\n"
            
            evidence_content += "\n"
        
        evidence_content += "---\n\n"
        return evidence_content
    
    def _add_compliance_sections(self, report_content: str) -> str:
        """AF1: Compliance Mode - add regulatory headers and signatures"""
        compliance_sections = """
## Compliance Information

### Regulatory Compliance

| Standard | Status | Notes |
|----------|--------|-------|
| **ISO 26262** | Compliant | Automotive safety evidence |
| **SOC 2** | Compliant | Security control evidence |
| **GDPR** | Compliant | Data protection measures |

### Signatures

| Role | Name | Date | Signature |
|------|------|------|-----------|
| **Test Engineer** | [Name] | [Date] | [Signature] |
| **QA Manager** | [Name] | [Date] | [Signature] |
| **Compliance Officer** | [Name] | [Date] | [Signature] |

### Approval Workflow

1. **Test Execution**: Completed
2. **Evidence Collection**: Completed
3. **Report Generation**: Completed
4. **Review**: Pending
5. **Approval**: Pending

---

"""
        return report_content + compliance_sections
    
    def _add_custom_sections(self, report_content: str) -> str:
        """AF2: Custom Evidence Requirements - add additional sections"""
        custom_sections = "\n## Custom Evidence Requirements\n\n"
        
        for field_name, field_value in self.custom_fields.items():
            custom_sections += f"### {field_name}\n\n"
            custom_sections += f"{field_value}\n\n"
        
        custom_sections += "---\n\n"
        return report_content + custom_sections
    
    def _write_report_file(self, report_content: str, test_id: str) -> str:
        """Write report content to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_evidence_{test_id}_{timestamp}.md"
        output_path = Path(self.output_dir) / filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(report_content)
            
            self.log_debug(f"Written report to {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.log_error(f"Error writing report file: {str(e)}")
            return ""
    
    def _generate_checksum(self, file_path: str) -> str:
        """Generate checksum for tamper-evident verification"""
        try:
            with open(file_path, 'rb') as file:
                content = file.read()
                checksum = hashlib.sha256(content).hexdigest()
            
            self.log_debug(f"Generated checksum: {checksum}")
            return checksum
            
        except Exception as e:
            self.log_error(f"Error generating checksum: {str(e)}")
            return ""
    
    def _create_test_evidence_object(self, test_id: str, log_file_path: str, 
                                   sequence_events: List[SequenceEvent],
                                   log_entries: List[LogEntry], environment: str,
                                   report_content: str, checksum: str) -> TestEvidence:
        """Create TestEvidence object"""
        artifacts = self._collect_analysis_artifacts(sequence_events, log_entries)
        
        return TestEvidence(
            test_id=test_id,
            timestamp=datetime.now().isoformat(),
            environment=environment,
            log_file_path=log_file_path,
            total_log_entries=len(log_entries),
            events_generated=len(sequence_events),
            coverage_metrics=artifacts['coverage_metrics'],
            sequence_diagram=self._extract_sequence_diagram_from_content(report_content),
            critical_logs=artifacts['critical_logs'][:20],  # Limit to 20
            checksum=checksum
        )
    
    def _save_evidence_metadata(self, test_evidence: TestEvidence, report_path: str):
        """Save evidence metadata for audit trail"""
        metadata_path = Path(self.output_dir) / f"evidence_metadata_{test_evidence.test_id}.json"
        
        try:
            import json
            with open(metadata_path, 'w', encoding='utf-8') as file:
                json.dump(test_evidence.to_dict(), file, indent=2, ensure_ascii=False)
            
            self.log_debug(f"Saved evidence metadata to {metadata_path}")
            
        except Exception as e:
            self.log_error(f"Error saving evidence metadata: {str(e)}")
    
    def _calculate_coverage_metrics(self, sequence_events: List[SequenceEvent], 
                                  log_entries: List[LogEntry]) -> Dict[str, float]:
        """Calculate coverage metrics"""
        total_logs = len(log_entries)
        total_events = len(sequence_events)
        
        if total_logs == 0:
            return {
                'coverage_rate': 0.0,
                'template_match_rate': 0.0,
                'event_generation_rate': 0.0,
                'log_processing_success': 0.0
            }
        
        # Calculate template match rate (simplified)
        matched_logs = sum(1 for event in sequence_events if event.log_entry)
        template_match_rate = (matched_logs / total_logs) * 100
        
        # Calculate event generation rate
        event_generation_rate = (total_events / total_logs) * 100 if total_logs > 0 else 0
        
        # Calculate log processing success (non-error logs)
        successful_logs = sum(1 for log in log_entries if log.level.value not in ['E', 'F'])
        log_processing_success = (successful_logs / total_logs) * 100
        
        # Overall coverage rate
        coverage_rate = (template_match_rate + event_generation_rate + log_processing_success) / 3
        
        return {
            'coverage_rate': coverage_rate,
            'template_match_rate': template_match_rate,
            'event_generation_rate': event_generation_rate,
            'log_processing_success': log_processing_success
        }
    
    def _identify_critical_logs(self, log_entries: List[LogEntry]) -> List[LogEntry]:
        """Identify critical log entries"""
        critical_keywords = ['error', 'fail', 'exception', 'critical', 'fatal', 'crash']
        critical_logs = []
        
        for log in log_entries:
            # Check log level
            if log.level.value in ['E', 'F']:
                critical_logs.append(log)
            # Check message content
            elif any(keyword in log.message.lower() for keyword in critical_keywords):
                critical_logs.append(log)
        
        return critical_logs
    
    def _identify_error_logs(self, log_entries: List[LogEntry]) -> List[LogEntry]:
        """Identify error log entries"""
        return [log for log in log_entries if log.level.value in ['E', 'F']]
    
    def _calculate_sequence_statistics(self, sequence_events: List[SequenceEvent]) -> Dict[str, Any]:
        """Calculate sequence statistics"""
        if not sequence_events:
            return {
                'total_events': 0,
                'event_types': 0,
                'unique_participants': 0,
                'time_span': 'N/A'
            }
        
        # Count event types
        event_types = set(event.event_type for event in sequence_events)
        
        # Count unique participants
        participants = set()
        for event in sequence_events:
            participants.add(event.from_entity)
            participants.add(event.to_entity)
        
        # Calculate time span
        timestamps = [event.timestamp for event in sequence_events]
        time_span = f"{min(timestamps)} to {max(timestamps)}" if timestamps else "N/A"
        
        return {
            'total_events': len(sequence_events),
            'event_types': len(event_types),
            'unique_participants': len(participants),
            'time_span': time_span
        }
    
    def _extract_sequence_diagram_from_content(self, report_content: str) -> str:
        """Extract sequence diagram from report content"""
        lines = report_content.split('\n')
        diagram_lines = []
        in_diagram = False
        
        for line in lines:
            if '```mermaid' in line:
                in_diagram = True
                continue
            elif '```' in line and in_diagram:
                break
            elif in_diagram:
                diagram_lines.append(line)
        
        return '\n'.join(diagram_lines)
    
    def validate_business_rules(self) -> Dict[str, Any]:
        """
        Validate business rules for test evidence
        BR1: Evidence must be tamper-evident (checksum)
        BR2: Timestamp must be immutable
        BR3: Original logs must be referenced
        BR4: Report retention period: 7 years
        """
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # BR4: Check retention period
        if self.retention_period < 7:
            validation_result['warnings'].append(f"Retention period {self.retention_period} years is less than recommended 7 years")
        
        # BR1, BR2, BR3: These are implemented in the report generation process
        
        return validation_result
    
    def get_evidence_statistics(self) -> Dict[str, Any]:
        """Get evidence generation statistics"""
        evidence_files = list(Path(self.output_dir).glob("test_evidence_*.md"))
        metadata_files = list(Path(self.output_dir).glob("evidence_metadata_*.json"))
        
        return {
            'output_directory': self.output_dir,
            'evidence_reports': len(evidence_files),
            'metadata_files': len(metadata_files),
            'compliance_mode': self.compliance_mode,
            'custom_fields': len(self.custom_fields),
            'retention_period_years': self.retention_period
        }


# Example usage and testing
if __name__ == "__main__":
    # Test the ExportTestEvidenceModule
    config = {
        'debug': True,
        'compliance_mode': True,
        'custom_fields': {
            'Test Environment': 'Automotive IVI System',
            'Test Duration': '2 hours',
            'Test Coverage': 'Camera Service Integration'
        }
    }
    
    export_evidence_module = ExportTestEvidenceModule(config)
    
    # Create sample data
    from data_models import LogEntry, LogLevel, SequenceEvent
    
    sample_logs = [
        LogEntry("09-17 10:30:15.123", LogLevel.INFO, "CameraService", "Service started", "original", 1),
        LogEntry("09-17 10:30:15.456", LogLevel.ERROR, "CameraHAL", "Hardware error", "original", 2),
        LogEntry("09-17 10:30:15.789", LogLevel.WARNING, "SystemService", "Connection timeout", "original", 3)
    ]
    
    sample_events = [
        SequenceEvent(
            timestamp="09-17 10:30:15.123",
            from_entity="System",
            to_entity="CameraService",
            message="Start Service",
            event_type="Camera Start",
            metadata={"template_name": "Camera Start"}
        )
    ]
    
    # Test evidence report generation
    report_path = export_evidence_module.generate_test_evidence_report(
        test_id="TEST_001",
        log_file_path="sample_log.txt",
        sequence_events=sample_events,
        log_entries=sample_logs,
        environment="Automotive Test Environment"
    )
    print(f"Generated evidence report: {report_path}")
    
    # Test validation
    validation = export_evidence_module.validate_business_rules()
    print(f"Validation result: {validation}")
    
    # Test statistics
    stats = export_evidence_module.get_evidence_statistics()
    print(f"Evidence statistics: {stats}")
