# Log Analysis Automation Tool

A comprehensive Python tool for analyzing log files (especially Android logcat) and generating sequence diagrams automatically. This tool is specifically designed for automotive systems and follows the use case specifications for log analysis automation.

## 🏗 Architecture Overview

```
┌─────────────────┐
│   Input Module  │ → Reads log files
└────────┬────────┘
         ↓
┌─────────────────┐
│ ReadLog Module  │ → Parses & searches logs
└────────┬────────┘
         ↓
┌─────────────────┐     ┌────────────────────┐
│ QuickCompare    │←────│ TemplateSequence   │
│    Module       │     │     Module         │
└────────┬────────┘     └────────────────────┘
         ↓
    ┌────┴────┐
    ↓         ↓
┌────────┐ ┌──────────┐
│Export  │ │Export    │
│Sequence│ │Evidence  │
└────────┘ └──────────┘
```

## 📦 Module Description

### Core Modules

1. **InputModule** (UC-01.1)
   - Reads input log files with validation
   - Handles large files with chunked reading
   - Supports multiple encodings (UTF-8, ASCII, Latin-1)
   - Implements business rules for file size limits

2. **TemplateSequenceModule** (UC-02.1, UC-02.2)
   - Manages log pattern templates
   - Exports template diagrams to Mermaid
   - Supports custom template loading from JSON
   - Validates template structure and regex patterns

3. **ReadLogModule** (UC-03.1, UC-03.2, UC-03.3)
   - Parses log entries using configurable patterns
   - Searches/filters logs by keyword, tag, or level
   - Saves searched results to temporary files
   - Updates log patterns dynamically

4. **QuickCompareModule** (UC-04.1, UC-04.2)
   - Compares logs against templates
   - Generates sequence events
   - Creates overview and detailed Mermaid diagrams
   - Handles pagination for large event sets

5. **ExportSequenceModule** (UC-05.1)
   - Exports sequences to JSON format
   - Preserves all sequence metadata
   - Supports compression for large files
   - Validates JSON output

6. **ExportTestEvidenceModule** (UC-06.1)
   - Generates test evidence reports
   - Creates markdown documentation
   - Includes sequence diagrams and log samples
   - Supports compliance mode for regulatory requirements

## 🚀 Quick Start

### Installation

```bash
# No external dependencies required - uses Python 3 standard library
python3 --version  # Ensure Python 3.6+
```

### Basic Usage

```bash
# 1. Run the main analyzer
python3 log_analyzer.py input/sample_logcat.txt

# 2. With filters
python3 log_analyzer.py input/sample_logcat.txt --keyword "Camera" --level I

# 3. With test evidence generation
python3 log_analyzer.py input/sample_logcat.txt --test-id "TEST_001"

# 4. With custom templates
python3 log_analyzer.py input/sample_logcat.txt --template-file template_sequence/templates.json
```

### Command-Line Options

```bash
python3 log_analyzer.py <input_file> [options]

Options:
  --keyword KEYWORD     Search keyword in log messages
  --tag TAG            Filter by log tag
  --level LEVEL        Filter by log level (V/D/I/W/E)
  --template-file FILE Custom template file (JSON)
  --test-id ID         Test ID for evidence generation
  --debug              Enable debug logging
  --config FILE        Configuration file path
```

## 📊 Output Files

The tool generates the following output files:

| File | Description |
|------|-------------|
| `template_seq_diagram.md` | Template visualization in Mermaid format |
| `searched_temp.txt` | Filtered log entries (when search is used) |
| `overview_seq.md` | Simplified sequence diagram |
| `detail_seq.md` | Detailed sequence diagram with timestamps |
| `output_seq.json` | Structured sequence data |
| `test_evidence_*.md` | Test evidence report |

## 🛠 Programmatic Usage

### Basic Analysis

```python
from log_analyzer import LogAnalyzer

# Initialize analyzer
config = {'debug': True}
analyzer = LogAnalyzer(config)

# Run analysis
result = analyzer.analyze("input/sample_logcat.txt")

# Get summary
summary = analyzer.get_analysis_summary()
print(f"Processed {summary['log_entries']} log entries")
print(f"Generated {summary['sequence_events']} sequence events")
```

### Filtered Analysis

```python
# Run analysis with filters
result = analyzer.analyze(
    log_file_path="input/sample_logcat.txt",
    keyword="Camera",
    tag="CameraService",
    level="I"
)
```

### Test Evidence Generation

```python
# Run analysis with test evidence
result = analyzer.analyze(
    log_file_path="input/sample_logcat.txt",
    test_id="AUTOMOTIVE_TEST_001"
)
```

### Custom Configuration

```python
# Custom configuration
config = {
    'debug': True,
    'compliance_mode': True,
    'custom_fields': {
        'Test Environment': 'Automotive IVI System',
        'Test Duration': '2 hours'
    }
}
analyzer = LogAnalyzer(config)
```

## 🔧 Customization

### Custom Log Patterns

The tool supports various log formats through configurable regex patterns:

```python
from read_log.read_log_module import ReadLogModule

reader = ReadLogModule()
# Update pattern for different log format
custom_pattern = r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+\[(\w+)\]\s+(\w+):\s*(.+)$'
reader.update_log_pattern(custom_pattern)
```

### Custom Templates

Create a `templates.json` file:

```json
{
  "templates": [
    {
      "name": "Your Pattern Name",
      "pattern": "regex_pattern_here",
      "sequence_mapping": {
        "from": "Source",
        "to": "{group1}",
        "message": "{group2}"
      },
      "priority": 1,
      "description": "Pattern description"
    }
  ]
}
```

## 🎯 Use Cases

### 1. Android Development
- Activity lifecycle analysis
- Service interaction tracking
- IPC communication visualization

### 2. Automotive (Android Automotive OS)
- Car service state tracking
- Vehicle HAL integration analysis
- System service communication
- Reverse camera activation analysis

### 3. Testing & QA
- Generate test evidence
- Create sequence documentation
- Analyze application flow
- Compliance reporting

### 4. Debugging
- Visualize component interactions
- Track error propagation
- Identify timing issues
- Performance analysis

## 🔍 Log Pattern Support

### Default Android Logcat Format
```
MM-DD HH:MM:SS.mmm LEVEL TAG: Message
09-17 10:30:15.123 I ActivityManager: Starting activity
```

### Supported Formats
- Standard Android logcat
- Syslog format
- Custom application logs
- JSON logs
- CSV logs
- Automotive ECU logs
- ISO 8601 timestamps

## 📈 Performance Requirements

### Efficiency Metrics
- **Log Processing Speed**: >10,000 lines/second
- **Pattern Matching Rate**: >5,000 comparisons/second
- **Memory Efficiency**: <2x input file size
- **Export Time**: <2 seconds for 1000 events

### Quality Metrics
- **Parse Success Rate**: >95% of log lines
- **Template Match Rate**: >80% of relevant logs
- **Sequence Accuracy**: >99% correct ordering
- **Evidence Completeness**: 100% required fields

### Reliability Metrics
- **Error Recovery Rate**: >99% graceful handling
- **Data Integrity**: 100% checksum validation
- **Availability**: 99.9% uptime for service mode
- **Concurrent Users**: Support 10 simultaneous analyses

## 🔒 Security Considerations

### Access Control
- File access based on OS permissions
- Template modification restricted to admins
- Pattern updates require elevated privileges
- Evidence reports may contain sensitive data

### Data Protection
- Log sanitization before export
- Support for encrypted log files
- Audit trail for all operations
- Automatic cleanup after retention period

### Compliance
- **GDPR**: Personal data handling in logs
- **ISO 26262**: Automotive safety evidence
- **SOC 2**: Security control evidence
- **HIPAA**: Healthcare data in logs (if applicable)

## 🚗 Automotive-Specific Features

### Safety & Performance
- **Boot-time optimization**: Camera ready within 2-3 seconds
- **Memory constraints**: Embedded systems buffer management
- **Real-time requirements**: Frame processing at 30fps minimum

### Vehicle Integration
- **Gear-dependent logic**: Reverse camera activation on gear change
- **Power management**: Handle suspend/resume cycles gracefully
- **Multi-display support**: Different cameras for different screen zones

### HIDL/AIDL Integration
```java
// Example HIDL camera service binding
ICameraProvider cameraProvider = ICameraProvider.getService();
// AIDL vehicle service connection
IVehicle vehicleService = IVehicle.Stub.asInterface(
    ServiceManager.getService("vehicle"));
```

### Testing Checkpoints
- [ ] Camera enumeration under 500ms
- [ ] Stream configuration under 1000ms
- [ ] First frame delivery under 2000ms
- [ ] Gear change response under 200ms
- [ ] Clean shutdown under 1000ms

## 🧪 Testing

### Run Test Suite

```bash
# Run comprehensive test suite
python3 run_tests.py

# Run example usage
python3 example_usage.py
```

### Test Coverage
- Unit tests for all modules
- Integration tests for complete workflow
- Performance benchmarking
- Error handling validation
- Automotive-specific scenarios

## 📁 Project Structure

```
mermaid_markdown_tools/
├── development_folder/
│   └── dev_and_test/
│       ├── data_models.py          # Data model classes
│       └── test_runner.py          # Comprehensive test suite
├── input/
│   ├── input_module.py             # UC-01.1: Read Log File
│   └── sample_logcat.txt           # Sample log data
├── template_sequence/
│   ├── template_sequence_module.py # UC-02.1, UC-02.2: Template management
│   └── templates.json              # Template configurations
├── read_log/
│   ├── read_log_module.py          # UC-03.1, UC-03.2, UC-03.3: Log parsing
│   └── log_patterns.txt            # Log pattern definitions
├── quick_compare/
│   └── quick_compare_module.py     # UC-04.1, UC-04.2: Sequence generation
├── export_sequence/
│   └── export_sequence_module.py   # UC-05.1: JSON export
├── export_test_evidence/
│   └── export_test_evidence_module.py # UC-06.1: Evidence generation
├── output_seq/                     # Sequence diagram outputs
├── output_testEvd/                 # Test evidence outputs
├── temp_results/                   # Temporary processing files
├── log_analyzer.py                 # Main orchestrator
├── config.json                     # Configuration file
├── run_tests.py                    # Test runner script
├── example_usage.py                # Usage examples
└── README.md                       # This file
```

## 🤝 Contributing

To extend the tool:

1. **Inherit from BaseModule** for new modules
2. **Follow existing patterns** for module integration
3. **Add new export formats** as needed
4. **Update templates** for new log patterns
5. **Add tests** for new functionality

### Module Development Guidelines

1. **Implement required use cases** from documentation
2. **Follow business rules** and validation requirements
3. **Add comprehensive error handling**
4. **Include performance metrics**
5. **Write unit tests** for all functionality

## 📝 License

This tool is provided as-is for development and testing purposes.

## 🆘 Support

For issues or questions:
1. Check the test suite for examples
2. Review the use case documentation
3. Examine the configuration options
4. Run the example usage script

## 🔮 Future Enhancements

### Planned Features
1. **Real-time Log Streaming**: Monitor logs in real-time
2. **Machine Learning Integration**: Auto-generate templates from logs
3. **Distributed Log Analysis**: Process logs from multiple sources
4. **Interactive Visualization**: Web-based diagram viewer
5. **Advanced Analytics**: Anomaly detection and pattern prediction

### Roadmap
- **Q1 2024**: Real-time streaming support
- **Q2 2024**: ML-based template generation
- **Q3 2024**: Distributed analysis capabilities
- **Q4 2024**: Interactive web interface

---

**Built for Automotive Excellence** 🚗📸✨
