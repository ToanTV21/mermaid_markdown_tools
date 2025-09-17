"""
Test Runner for Log Analysis Automation Tool
Comprehensive testing suite for all modules
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from data_models import LogEntry, LogLevel, SequenceEvent, Template
from input.input_module import InputModule
from template_sequence.template_sequence_module import TemplateSequenceModule
from read_log.read_log_module import ReadLogModule
from quick_compare.quick_compare_module import QuickCompareModule
from export_sequence.export_sequence_module import ExportSequenceModule
from export_test_evidence.export_test_evidence_module import ExportTestEvidenceModule


class TestRunner:
    """Comprehensive test runner for all modules"""
    
    def __init__(self):
        self.test_results = {}
        self.temp_dir = None
        self.sample_log_file = None
    
    def setup_test_environment(self):
        """Setup test environment with temporary files"""
        self.temp_dir = tempfile.mkdtemp(prefix="log_analyzer_test_")
        print(f"Test environment created: {self.temp_dir}")
        
        # Create sample log file
        self.sample_log_file = Path(self.temp_dir) / "sample_log.txt"
        with open(self.sample_log_file, 'w') as f:
            f.write("09-17 10:30:15.123 I ActivityManager: Starting activity\n")
            f.write("09-17 10:30:15.456 D CameraService: Camera initialized\n")
            f.write("09-17 10:30:15.789 E SystemService: Error occurred\n")
            f.write("09-17 10:30:16.012 W NetworkService: Connection timeout\n")
    
    def cleanup_test_environment(self):
        """Cleanup test environment"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"Test environment cleaned up: {self.temp_dir}")
    
    def test_input_module(self) -> Dict[str, Any]:
        """Test InputModule functionality"""
        print("\n=== Testing InputModule ===")
        test_results = {"passed": 0, "failed": 0, "errors": []}
        
        try:
            config = {'debug': True}
            input_module = InputModule(config)
            
            # Test 1: Read valid file
            try:
                lines = input_module.read_log_file(str(self.sample_log_file))
                assert len(lines) == 4, f"Expected 4 lines, got {len(lines)}"
                test_results["passed"] += 1
                print("✓ Read valid file test passed")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Read valid file: {str(e)}")
                print(f"✗ Read valid file test failed: {e}")
            
            # Test 2: File not found
            try:
                input_module.read_log_file("nonexistent_file.txt")
                test_results["failed"] += 1
                test_results["errors"].append("File not found should raise exception")
                print("✗ File not found test failed: should raise exception")
            except FileNotFoundError:
                test_results["passed"] += 1
                print("✓ File not found test passed")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"File not found: {str(e)}")
                print(f"✗ File not found test failed: {e}")
            
            # Test 3: Get file info
            try:
                file_info = input_module.get_file_info(str(self.sample_log_file))
                assert 'file_size' in file_info, "File info missing file_size"
                test_results["passed"] += 1
                print("✓ Get file info test passed")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Get file info: {str(e)}")
                print(f"✗ Get file info test failed: {e}")
            
            # Test 4: Validate business rules
            try:
                validation = input_module.validate_business_rules(str(self.sample_log_file))
                assert 'valid' in validation, "Validation result missing valid field"
                test_results["passed"] += 1
                print("✓ Validate business rules test passed")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Validate business rules: {str(e)}")
                print(f"✗ Validate business rules test failed: {e}")
            
        except Exception as e:
            test_results["failed"] += 1
            test_results["errors"].append(f"InputModule setup: {str(e)}")
            print(f"✗ InputModule setup failed: {e}")
        
        return test_results
    
    def test_template_sequence_module(self) -> Dict[str, Any]:
        """Test TemplateSequenceModule functionality"""
        print("\n=== Testing TemplateSequenceModule ===")
        test_results = {"passed": 0, "failed": 0, "errors": []}
        
        try:
            config = {'debug': True}
            template_module = TemplateSequenceModule(config)
            
            # Test 1: Load default templates
            try:
                templates = template_module.load_template_configuration()
                assert len(templates) > 0, "No templates loaded"
                test_results["passed"] += 1
                print("✓ Load default templates test passed")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Load default templates: {str(e)}")
                print(f"✗ Load default templates test failed: {e}")
            
            # Test 2: Export template diagram
            try:
                output_path = Path(self.temp_dir) / "test_template_diagram.md"
                success = template_module.export_template_diagram(str(output_path))
                assert success, "Template diagram export failed"
                assert output_path.exists(), "Template diagram file not created"
                test_results["passed"] += 1
                print("✓ Export template diagram test passed")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Export template diagram: {str(e)}")
                print(f"✗ Export template diagram test failed: {e}")
            
            # Test 3: Get template by name
            try:
                template = template_module.get_template_by_name("Camera Service Start")
                assert template is not None, "Template not found by name"
                test_results["passed"] += 1
                print("✓ Get template by name test passed")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Get template by name: {str(e)}")
                print(f"✗ Get template by name test failed: {e}")
            
            # Test 4: Validate business rules
            try:
                validation = template_module.validate_business_rules()
                assert 'valid' in validation, "Validation result missing valid field"
                test_results["passed"] += 1
                print("✓ Validate business rules test passed")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Validate business rules: {str(e)}")
                print(f"✗ Validate business rules test failed: {e}")
            
        except Exception as e:
            test_results["failed"] += 1
            test_results["errors"].append(f"TemplateSequenceModule setup: {str(e)}")
            print(f"✗ TemplateSequenceModule setup failed: {e}")
        
        return test_results
    
    def test_read_log_module(self) -> Dict[str, Any]:
        """Test ReadLogModule functionality"""
        print("\n=== Testing ReadLogModule ===")
        test_results = {"passed": 0, "failed": 0, "errors": []}
        
        try:
            config = {'debug': True, 'temp_results_dir': str(Path(self.temp_dir) / "temp_results")}
            read_log_module = ReadLogModule(config)
            
            # Test 1: Parse log entries
            try:
                sample_logs = [
                    "09-17 10:30:15.123 I ActivityManager: Starting activity",
                    "09-17 10:30:15.456 D CameraService: Camera initialized",
                    "09-17 10:30:15.789 E SystemService: Error occurred"
                ]
                parsed_entries = read_log_module.parse_log_entries(sample_logs)
                assert len(parsed_entries) == 3, f"Expected 3 parsed entries, got {len(parsed_entries)}"
                test_results["passed"] += 1
                print("✓ Parse log entries test passed")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Parse log entries: {str(e)}")
                print(f"✗ Parse log entries test failed: {e}")
            
            # Test 2: Search and filter logs
            try:
                filtered_entries = read_log_module.search_and_filter_logs(
                    parsed_entries, keyword="Camera"
                )
                assert len(filtered_entries) == 1, f"Expected 1 filtered entry, got {len(filtered_entries)}"
                test_results["passed"] += 1
                print("✓ Search and filter logs test passed")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Search and filter logs: {str(e)}")
                print(f"✗ Search and filter logs test failed: {e}")
            
            # Test 3: Update log pattern
            try:
                new_pattern = r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+\[(\w+)\]\s+(\w+):\s*(.*)$'
                success = read_log_module.update_log_pattern(new_pattern)
                assert success, "Log pattern update failed"
                test_results["passed"] += 1
                print("✓ Update log pattern test passed")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Update log pattern: {str(e)}")
                print(f"✗ Update log pattern test failed: {e}")
            
            # Test 4: Get parsing statistics
            try:
                stats = read_log_module.get_parsing_statistics()
                assert 'current_pattern' in stats, "Statistics missing current_pattern"
                test_results["passed"] += 1
                print("✓ Get parsing statistics test passed")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Get parsing statistics: {str(e)}")
                print(f"✗ Get parsing statistics test failed: {e}")
            
        except Exception as e:
            test_results["failed"] += 1
            test_results["errors"].append(f"ReadLogModule setup: {str(e)}")
            print(f"✗ ReadLogModule setup failed: {e}")
        
        return test_results
    
    def test_quick_compare_module(self) -> Dict[str, Any]:
        """Test QuickCompareModule functionality"""
        print("\n=== Testing QuickCompareModule ===")
        test_results = {"passed": 0, "failed": 0, "errors": []}
        
        try:
            config = {'debug': True, 'output_dir': str(Path(self.temp_dir) / "output_seq")}
            quick_compare_module = QuickCompareModule(config)
            
            # Create sample data
            sample_logs = [
                LogEntry("09-17 10:30:15.123", LogLevel.INFO, "ActivityManager", "Starting CameraActivity", "original", 1),
                LogEntry("09-17 10:30:15.456", LogLevel.DEBUG, "CameraService", "Camera initialized", "original", 2),
                LogEntry("09-17 10:30:15.789", LogLevel.ERROR, "CameraHAL", "Hardware error", "original", 3)
            ]
            
            sample_templates = [
                Template("Camera Start", r".*Camera.*", {"from": "System", "to": "Camera", "message": "Start"}, 1),
                Template("Camera Error", r".*error.*", {"from": "Camera", "to": "System", "message": "Error"}, 2)
            ]
            
            # Test 1: Generate sequence events
            try:
                events = quick_compare_module.generate_sequence_events(sample_logs, sample_templates)
                assert len(events) > 0, "No sequence events generated"
                test_results["passed"] += 1
                print("✓ Generate sequence events test passed")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Generate sequence events: {str(e)}")
                print(f"✗ Generate sequence events test failed: {e}")
            
            # Test 2: Export sequence diagrams
            try:
                diagram_paths = quick_compare_module.export_sequence_diagrams(events)
                assert 'overview' in diagram_paths, "Overview diagram not created"
                assert 'detailed' in diagram_paths, "Detailed diagram not created"
                test_results["passed"] += 1
                print("✓ Export sequence diagrams test passed")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Export sequence diagrams: {str(e)}")
                print(f"✗ Export sequence diagrams test failed: {e}")
            
            # Test 3: Get sequence statistics
            try:
                stats = quick_compare_module.get_sequence_statistics(events)
                assert 'total_events' in stats, "Statistics missing total_events"
                test_results["passed"] += 1
                print("✓ Get sequence statistics test passed")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Get sequence statistics: {str(e)}")
                print(f"✗ Get sequence statistics test failed: {e}")
            
            # Test 4: Validate business rules
            try:
                validation = quick_compare_module.validate_business_rules(events)
                assert 'valid' in validation, "Validation result missing valid field"
                test_results["passed"] += 1
                print("✓ Validate business rules test passed")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Validate business rules: {str(e)}")
                print(f"✗ Validate business rules test failed: {e}")
            
        except Exception as e:
            test_results["failed"] += 1
            test_results["errors"].append(f"QuickCompareModule setup: {str(e)}")
            print(f"✗ QuickCompareModule setup failed: {e}")
        
        return test_results
    
    def test_export_sequence_module(self) -> Dict[str, Any]:
        """Test ExportSequenceModule functionality"""
        print("\n=== Testing ExportSequenceModule ===")
        test_results = {"passed": 0, "failed": 0, "errors": []}
        
        try:
            config = {'debug': True, 'output_dir': str(Path(self.temp_dir) / "output_seq")}
            export_sequence_module = ExportSequenceModule(config)
            
            # Create sample data
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
            
            # Test 1: Export to JSON format
            try:
                output_path = export_sequence_module.export_to_json_format(
                    sample_events, sample_logs, sample_templates, "test_output.json"
                )
                assert output_path != "", "JSON export failed"
                assert Path(output_path).exists(), "JSON file not created"
                test_results["passed"] += 1
                print("✓ Export to JSON format test passed")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Export to JSON format: {str(e)}")
                print(f"✗ Export to JSON format test failed: {e}")
            
            # Test 2: Validate business rules
            try:
                validation = export_sequence_module.validate_business_rules()
                assert 'valid' in validation, "Validation result missing valid field"
                test_results["passed"] += 1
                print("✓ Validate business rules test passed")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Validate business rules: {str(e)}")
                print(f"✗ Validate business rules test failed: {e}")
            
            # Test 3: Get export statistics
            try:
                stats = export_sequence_module.get_export_statistics()
                assert 'output_directory' in stats, "Statistics missing output_directory"
                test_results["passed"] += 1
                print("✓ Get export statistics test passed")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Get export statistics: {str(e)}")
                print(f"✗ Get export statistics test failed: {e}")
            
        except Exception as e:
            test_results["failed"] += 1
            test_results["errors"].append(f"ExportSequenceModule setup: {str(e)}")
            print(f"✗ ExportSequenceModule setup failed: {e}")
        
        return test_results
    
    def test_export_test_evidence_module(self) -> Dict[str, Any]:
        """Test ExportTestEvidenceModule functionality"""
        print("\n=== Testing ExportTestEvidenceModule ===")
        test_results = {"passed": 0, "failed": 0, "errors": []}
        
        try:
            config = {
                'debug': True,
                'output_dir': str(Path(self.temp_dir) / "output_testEvd"),
                'compliance_mode': True
            }
            export_evidence_module = ExportTestEvidenceModule(config)
            
            # Create sample data
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
            
            # Test 1: Generate test evidence report
            try:
                report_path = export_evidence_module.generate_test_evidence_report(
                    test_id="TEST_001",
                    log_file_path=str(self.sample_log_file),
                    sequence_events=sample_events,
                    log_entries=sample_logs,
                    environment="Automotive Test Environment"
                )
                assert report_path != "", "Evidence report generation failed"
                assert Path(report_path).exists(), "Evidence report file not created"
                test_results["passed"] += 1
                print("✓ Generate test evidence report test passed")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Generate test evidence report: {str(e)}")
                print(f"✗ Generate test evidence report test failed: {e}")
            
            # Test 2: Validate business rules
            try:
                validation = export_evidence_module.validate_business_rules()
                assert 'valid' in validation, "Validation result missing valid field"
                test_results["passed"] += 1
                print("✓ Validate business rules test passed")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Validate business rules: {str(e)}")
                print(f"✗ Validate business rules test failed: {e}")
            
            # Test 3: Get evidence statistics
            try:
                stats = export_evidence_module.get_evidence_statistics()
                assert 'output_directory' in stats, "Statistics missing output_directory"
                test_results["passed"] += 1
                print("✓ Get evidence statistics test passed")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Get evidence statistics: {str(e)}")
                print(f"✗ Get evidence statistics test failed: {e}")
            
        except Exception as e:
            test_results["failed"] += 1
            test_results["errors"].append(f"ExportTestEvidenceModule setup: {str(e)}")
            print(f"✗ ExportTestEvidenceModule setup failed: {e}")
        
        return test_results
    
    def run_all_tests(self):
        """Run all tests and generate summary"""
        print("="*60)
        print("LOG ANALYSIS AUTOMATION TOOL - COMPREHENSIVE TEST SUITE")
        print("="*60)
        
        self.setup_test_environment()
        
        try:
            # Run all module tests
            self.test_results['input_module'] = self.test_input_module()
            self.test_results['template_sequence_module'] = self.test_template_sequence_module()
            self.test_results['read_log_module'] = self.test_read_log_module()
            self.test_results['quick_compare_module'] = self.test_quick_compare_module()
            self.test_results['export_sequence_module'] = self.test_export_sequence_module()
            self.test_results['export_test_evidence_module'] = self.test_export_test_evidence_module()
            
            # Generate summary
            self.generate_test_summary()
            
        finally:
            self.cleanup_test_environment()
    
    def generate_test_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        total_passed = 0
        total_failed = 0
        total_errors = []
        
        for module_name, results in self.test_results.items():
            passed = results['passed']
            failed = results['failed']
            errors = results['errors']
            
            total_passed += passed
            total_failed += failed
            total_errors.extend(errors)
            
            status = "PASS" if failed == 0 else "FAIL"
            print(f"{module_name:25} | {passed:3} passed | {failed:3} failed | {status}")
        
        print("-" * 60)
        print(f"{'TOTAL':25} | {total_passed:3} passed | {total_failed:3} failed | {'PASS' if total_failed == 0 else 'FAIL'}")
        
        if total_errors:
            print("\nERRORS:")
            for i, error in enumerate(total_errors, 1):
                print(f"{i:3}. {error}")
        
        print("\n" + "="*60)
        if total_failed == 0:
            print("🎉 ALL TESTS PASSED! 🎉")
        else:
            print(f"❌ {total_failed} TESTS FAILED")
        print("="*60)


if __name__ == "__main__":
    test_runner = TestRunner()
    test_runner.run_all_tests()
