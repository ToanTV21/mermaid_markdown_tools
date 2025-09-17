"""
Main LogAnalyzer - Orchestrates all analysis modules
Implements the complete log analysis workflow according to use case specifications
"""

import sys
import argparse
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add development folder to path for imports
sys.path.append(str(Path(__file__).parent / "development_folder" / "dev_and_test"))

# Import all modules
from data_models import BaseModule, AnalysisResult, LogEntry, SequenceEvent, Template
from input.input_module import InputModule
from template_sequence.template_sequence_module import TemplateSequenceModule
from read_log.read_log_module import ReadLogModule
from quick_compare.quick_compare_module import QuickCompareModule
from export_sequence.export_sequence_module import ExportSequenceModule
from export_test_evidence.export_test_evidence_module import ExportTestEvidenceModule


class LogAnalyzer(BaseModule):
    """
    Main LogAnalyzer class that orchestrates all analysis modules
    Implements the complete workflow from log reading to evidence generation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Initialize all modules
        self.input_module = InputModule(config)
        self.template_module = TemplateSequenceModule(config)
        self.read_log_module = ReadLogModule(config)
        self.quick_compare_module = QuickCompareModule(config)
        self.export_sequence_module = ExportSequenceModule(config)
        self.export_evidence_module = ExportTestEvidenceModule(config)
        
        # Analysis state
        self.current_analysis: Optional[AnalysisResult] = None
        self.log_entries: List[LogEntry] = []
        self.sequence_events: List[SequenceEvent] = []
        self.templates: List[Template] = []
    
    def analyze(self, log_file_path: str, 
                keyword: Optional[str] = None,
                tag: Optional[str] = None,
                level: Optional[str] = None,
                template_file: Optional[str] = None,
                test_id: Optional[str] = None) -> AnalysisResult:
        """
        Main analysis workflow that orchestrates all modules
        
        Args:
            log_file_path: Path to log file to analyze
            keyword: Optional keyword to search for
            tag: Optional tag to filter by
            level: Optional log level to filter by
            template_file: Optional custom template file
            test_id: Optional test ID for evidence generation
            
        Returns:
            Complete analysis result
        """
        self.log_info(f"Starting log analysis for file: {log_file_path}")
        
        try:
            # Step 1: Load templates (UC-02.1)
            self.log_info("Loading template configuration...")
            self.templates = self.template_module.load_template_configuration(template_file)
            
            # Step 2: Read log file (UC-01.1)
            self.log_info("Reading log file...")
            log_lines = self.input_module.read_log_file(log_file_path)
            
            # Step 3: Parse log entries (UC-03.1)
            self.log_info("Parsing log entries...")
            self.log_entries = self.read_log_module.parse_log_entries(log_lines)
            
            # Step 4: Search and filter logs (UC-03.2) - if criteria provided
            if keyword or tag or level:
                self.log_info("Applying search filters...")
                from data_models import LogLevel
                filter_level = LogLevel(level) if level else None
                self.log_entries = self.read_log_module.search_and_filter_logs(
                    self.log_entries, keyword, tag, filter_level
                )
            
            # Step 5: Generate sequence events (UC-04.1)
            self.log_info("Generating sequence events...")
            self.sequence_events = self.quick_compare_module.generate_sequence_events(
                self.log_entries, self.templates
            )
            
            # Step 6: Export sequence diagrams (UC-04.2)
            self.log_info("Exporting sequence diagrams...")
            diagram_paths = self.quick_compare_module.export_sequence_diagrams(self.sequence_events)
            
            # Step 7: Export to JSON (UC-05.1)
            self.log_info("Exporting to JSON format...")
            json_path = self.export_sequence_module.export_to_json_format(
                self.sequence_events, self.log_entries, self.templates
            )
            
            # Step 8: Generate test evidence (UC-06.1) - if test_id provided
            evidence_path = ""
            if test_id:
                self.log_info("Generating test evidence report...")
                evidence_path = self.export_evidence_module.generate_test_evidence_report(
                    test_id, log_file_path, self.sequence_events, self.log_entries
                )
            
            # Step 9: Export template diagram (UC-02.2)
            self.log_info("Exporting template diagram...")
            template_diagram_path = self.template_module.export_template_diagram()
            
            # Create analysis result
            self.current_analysis = self._create_analysis_result(
                log_file_path, diagram_paths, json_path, evidence_path, template_diagram_path
            )
            
            self.log_info("Analysis completed successfully")
            return self.current_analysis
            
        except Exception as e:
            self.log_error(f"Analysis failed: {str(e)}")
            raise
    
    def _create_analysis_result(self, log_file_path: str, diagram_paths: Dict[str, str], 
                              json_path: str, evidence_path: str, template_diagram_path: str) -> AnalysisResult:
        """Create complete analysis result"""
        # Calculate statistics
        statistics = {
            'log_entries_count': len(self.log_entries),
            'sequence_events_count': len(self.sequence_events),
            'templates_used_count': len(self.templates),
            'output_files': {
                'overview_diagram': diagram_paths.get('overview', ''),
                'detailed_diagram': diagram_paths.get('detailed', ''),
                'json_export': json_path,
                'evidence_report': evidence_path,
                'template_diagram': template_diagram_path
            }
        }
        
        # Add module-specific statistics
        statistics.update({
            'input_module_stats': self.input_module.get_file_info(log_file_path),
            'read_log_stats': self.read_log_module.get_parsing_statistics(),
            'quick_compare_stats': self.quick_compare_module.get_sequence_statistics(self.sequence_events),
            'export_sequence_stats': self.export_sequence_module.get_export_statistics(),
            'export_evidence_stats': self.export_evidence_module.get_evidence_statistics()
        })
        
        # Create metadata
        metadata = {
            'analysis_timestamp': self._get_current_timestamp(),
            'log_file_path': log_file_path,
            'config_used': self.config,
            'modules_used': [
                'InputModule', 'TemplateSequenceModule', 'ReadLogModule',
                'QuickCompareModule', 'ExportSequenceModule', 'ExportTestEvidenceModule'
            ]
        }
        
        return AnalysisResult(
            log_entries=self.log_entries,
            sequence_events=self.sequence_events,
            templates_used=self.templates,
            statistics=statistics,
            metadata=metadata
        )
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of current analysis"""
        if not self.current_analysis:
            return {"error": "No analysis performed yet"}
        
        return {
            'log_entries': len(self.current_analysis.log_entries),
            'sequence_events': len(self.current_analysis.sequence_events),
            'templates_used': len(self.current_analysis.templates_used),
            'output_files': self.current_analysis.statistics.get('output_files', {}),
            'analysis_timestamp': self.current_analysis.metadata.get('analysis_timestamp', '')
        }
    
    def validate_all_modules(self) -> Dict[str, Any]:
        """Validate all modules according to business rules"""
        validation_results = {
            'input_module': self.input_module.validate_business_rules("dummy_path"),
            'template_module': self.template_module.validate_business_rules(),
            'read_log_module': self.read_log_module.validate_business_rules(),
            'quick_compare_module': self.quick_compare_module.validate_business_rules(self.sequence_events),
            'export_sequence_module': self.export_sequence_module.validate_business_rules(),
            'export_evidence_module': self.export_evidence_module.validate_business_rules()
        }
        
        # Overall validation result
        all_valid = all(result.get('valid', False) for result in validation_results.values())
        
        return {
            'overall_valid': all_valid,
            'module_results': validation_results
        }
    
    def update_log_pattern(self, new_pattern: str) -> bool:
        """Update log pattern in ReadLogModule"""
        return self.read_log_module.update_log_pattern(new_pattern)
    
    def export_template_diagram(self) -> bool:
        """Export template diagram"""
        return self.template_module.export_template_diagram()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all modules"""
        return {
            'input_module': {
                'max_file_size': self.input_module.max_file_size,
                'chunk_size': self.input_module.chunk_size,
                'supported_encodings': self.input_module.supported_encodings
            },
            'template_module': {
                'templates_loaded': len(self.templates),
                'template_file': self.template_module.template_file_path
            },
            'read_log_module': {
                'current_pattern': self.read_log_module.log_pattern,
                'max_results': self.read_log_module.max_results
            },
            'quick_compare_module': {
                'max_events_per_diagram': self.quick_compare_module.max_events_per_diagram,
                'overview_event_limit': self.quick_compare_module.overview_event_limit
            },
            'export_sequence_module': {
                'max_file_size': self.export_sequence_module.max_file_size,
                'pretty_print': self.export_sequence_module.pretty_print
            },
            'export_evidence_module': {
                'compliance_mode': self.export_evidence_module.compliance_mode,
                'retention_period': self.export_evidence_module.retention_period
            }
        }


def main():
    """Main entry point for command-line usage"""
    parser = argparse.ArgumentParser(description='Log Analysis Automation Tool')
    parser.add_argument('log_file', help='Path to log file to analyze')
    parser.add_argument('--keyword', help='Search keyword in log messages')
    parser.add_argument('--tag', help='Filter by log tag')
    parser.add_argument('--level', help='Filter by log level (V/D/I/W/E)')
    parser.add_argument('--template-file', help='Custom template file (JSON)')
    parser.add_argument('--test-id', help='Test ID for evidence generation')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--config', help='Configuration file path')
    
    args = parser.parse_args()
    
    # Create configuration
    config = {
        'debug': args.debug,
        'template_file': args.template_file
    }
    
    # Load additional config if provided
    if args.config:
        try:
            import json
            with open(args.config, 'r') as f:
                additional_config = json.load(f)
                config.update(additional_config)
        except Exception as e:
            print(f"Error loading config file: {e}")
            return 1
    
    # Initialize analyzer
    analyzer = LogAnalyzer(config)
    
    try:
        # Run analysis
        result = analyzer.analyze(
            log_file_path=args.log_file,
            keyword=args.keyword,
            tag=args.tag,
            level=args.level,
            template_file=args.template_file,
            test_id=args.test_id
        )
        
        # Print summary
        summary = analyzer.get_analysis_summary()
        print("\n" + "="*50)
        print("ANALYSIS COMPLETED SUCCESSFULLY")
        print("="*50)
        print(f"Log Entries Processed: {summary['log_entries']}")
        print(f"Sequence Events Generated: {summary['sequence_events']}")
        print(f"Templates Used: {summary['templates_used']}")
        print(f"Analysis Timestamp: {summary['analysis_timestamp']}")
        print("\nOutput Files:")
        for file_type, file_path in summary['output_files'].items():
            if file_path:
                print(f"  {file_type}: {file_path}")
        print("="*50)
        
        return 0
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
