#!/usr/bin/env python3
"""
Example Usage Script for Log Analysis Automation Tool
Demonstrates how to use the tool programmatically
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from log_analyzer import LogAnalyzer


def example_basic_analysis():
    """Example: Basic log analysis"""
    print("=== Example 1: Basic Log Analysis ===")
    
    # Initialize analyzer with default configuration
    config = {'debug': True}
    analyzer = LogAnalyzer(config)
    
    # Run analysis on sample log file
    try:
        result = analyzer.analyze("input/sample_logcat.txt")
        
        # Print summary
        summary = analyzer.get_analysis_summary()
        print(f"Analysis completed successfully!")
        print(f"Log entries processed: {summary['log_entries']}")
        print(f"Sequence events generated: {summary['sequence_events']}")
        print(f"Templates used: {summary['templates_used']}")
        
        return True
    except Exception as e:
        print(f"Analysis failed: {e}")
        return False


def example_filtered_analysis():
    """Example: Analysis with filters"""
    print("\n=== Example 2: Filtered Analysis ===")
    
    # Initialize analyzer
    config = {'debug': True}
    analyzer = LogAnalyzer(config)
    
    # Run analysis with filters
    try:
        result = analyzer.analyze(
            log_file_path="input/sample_logcat.txt",
            keyword="Camera",  # Only logs containing "Camera"
            level="I"  # Only INFO level logs
        )
        
        summary = analyzer.get_analysis_summary()
        print(f"Filtered analysis completed!")
        print(f"Filtered log entries: {summary['log_entries']}")
        print(f"Sequence events: {summary['sequence_events']}")
        
        return True
    except Exception as e:
        print(f"Filtered analysis failed: {e}")
        return False


def example_test_evidence_generation():
    """Example: Test evidence generation"""
    print("\n=== Example 3: Test Evidence Generation ===")
    
    # Initialize analyzer with compliance mode
    config = {
        'debug': True,
        'compliance_mode': True,
        'custom_fields': {
            'Test Environment': 'Automotive IVI System',
            'Test Duration': '2 hours',
            'Test Coverage': 'Camera Service Integration'
        }
    }
    analyzer = LogAnalyzer(config)
    
    # Run analysis with test evidence
    try:
        result = analyzer.analyze(
            log_file_path="input/sample_logcat.txt",
            test_id="AUTOMOTIVE_CAMERA_TEST_001"
        )
        
        summary = analyzer.get_analysis_summary()
        print(f"Test evidence generation completed!")
        print(f"Evidence report: {summary['output_files'].get('evidence_report', 'Not generated')}")
        
        return True
    except Exception as e:
        print(f"Test evidence generation failed: {e}")
        return False


def example_custom_templates():
    """Example: Using custom templates"""
    print("\n=== Example 4: Custom Templates ===")
    
    # Initialize analyzer with custom template file
    config = {
        'debug': True,
        'template_file': 'template_sequence/templates.json'
    }
    analyzer = LogAnalyzer(config)
    
    # Run analysis with custom templates
    try:
        result = analyzer.analyze(
            log_file_path="input/sample_logcat.txt",
            template_file="template_sequence/templates.json"
        )
        
        summary = analyzer.get_analysis_summary()
        print(f"Custom template analysis completed!")
        print(f"Templates used: {summary['templates_used']}")
        print(f"Template diagram: {summary['output_files'].get('template_diagram', 'Not generated')}")
        
        return True
    except Exception as e:
        print(f"Custom template analysis failed: {e}")
        return False


def example_performance_analysis():
    """Example: Performance analysis and validation"""
    print("\n=== Example 5: Performance Analysis ===")
    
    # Initialize analyzer
    config = {'debug': True}
    analyzer = LogAnalyzer(config)
    
    try:
        # Run analysis
        result = analyzer.analyze("input/sample_logcat.txt")
        
        # Get performance metrics
        performance_metrics = analyzer.get_performance_metrics()
        print("Performance Metrics:")
        for module, metrics in performance_metrics.items():
            print(f"  {module}:")
            for key, value in metrics.items():
                print(f"    {key}: {value}")
        
        # Validate all modules
        validation_results = analyzer.validate_all_modules()
        print(f"\nValidation Results:")
        print(f"  Overall Valid: {validation_results['overall_valid']}")
        for module, result in validation_results['module_results'].items():
            status = "PASS" if result.get('valid', False) else "FAIL"
            print(f"  {module}: {status}")
        
        return True
    except Exception as e:
        print(f"Performance analysis failed: {e}")
        return False


def example_automotive_specific():
    """Example: Automotive-specific analysis"""
    print("\n=== Example 6: Automotive-Specific Analysis ===")
    
    # Initialize analyzer with automotive configuration
    config = {
        'debug': True,
        'compliance_mode': True,
        'custom_fields': {
            'Vehicle Model': '2024 Automotive IVI',
            'ECU Version': 'v2.1.0',
            'Test Scenario': 'Reverse Camera Activation',
            'Safety Level': 'ASIL-B'
        }
    }
    analyzer = LogAnalyzer(config)
    
    try:
        # Run automotive analysis
        result = analyzer.analyze(
            log_file_path="input/sample_logcat.txt",
            test_id="AUTOMOTIVE_REVERSE_CAMERA_001",
            keyword="gear"
        )
        
        summary = analyzer.get_analysis_summary()
        print(f"Automotive analysis completed!")
        print(f"Gear-related events: {summary['sequence_events']}")
        print(f"Evidence report: {summary['output_files'].get('evidence_report', 'Not generated')}")
        
        return True
    except Exception as e:
        print(f"Automotive analysis failed: {e}")
        return False


def main():
    """Run all examples"""
    print("Log Analysis Automation Tool - Example Usage")
    print("=" * 50)
    
    examples = [
        example_basic_analysis,
        example_filtered_analysis,
        example_test_evidence_generation,
        example_custom_templates,
        example_performance_analysis,
        example_automotive_specific
    ]
    
    results = []
    for example in examples:
        try:
            success = example()
            results.append(success)
        except Exception as e:
            print(f"Example failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("EXAMPLE EXECUTION SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    for i, (example, success) in enumerate(zip(examples, results), 1):
        status = "PASS" if success else "FAIL"
        print(f"Example {i}: {example.__name__:30} | {status}")
    
    print("-" * 50)
    print(f"Total: {passed}/{total} examples passed")
    
    if passed == total:
        print("🎉 All examples executed successfully!")
    else:
        print(f"❌ {total - passed} examples failed")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit(main())
