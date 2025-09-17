# Log Analysis Automation Tool

A modular Python tool for analyzing log files (especially Android logcat) and generating sequence diagrams automatically.

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

1. **InputModule**
   - Reads input log files
   - Validates file existence

2. **TemplateSequenceModule**
   - Manages log pattern templates
   - Exports template diagrams to Mermaid
   - Supports custom template loading

3. **ReadLogModule**
   - Parses log entries using configurable patterns
   - Searches/filters logs by keyword, tag, or level
   - Saves searched results to temporary file

4. **QuickCompareModule**
   - Compares logs against templates
   - Generates sequence events
   - Creates overview and detailed Mermaid diagrams

5. **ExportSequenceModule**
   - Exports sequences to JSON format
   - Preserves all sequence metadata

6. **ExportTestEvidenceModule**
   - Generates test evidence reports
   - Creates markdown documentation
   - Includes sequence diagrams and log samples

## 🚀 Quick Start

### Installation

```bash
# No external dependencies required - uses Python 3 standard library
python3 --version  # Ensure Python 3.6+
```

### Basic Usage

```bash
# 1. Save the main script as log_analyzer.py
# 2. Create or use your logcat file
# 3. Run the analyzer
python3 log_analyzer.py logcat_main.txt
```

### Command-Line Options

```bash
# Full command syntax
python3 log_analyzer.py <input_file> [options]

# Options:
  --keyword KEYWORD     Search keyword in log messages
  --tag TAG            Filter by log tag
  --level LEVEL        Filter by log level (V/D/I/W/E)
  --template-file FILE Custom template file (JSON)
  --debug              Enable debug logging
```

### Examples

```bash
# Basic analysis
python3 log_analyzer.py logcat_main.txt

# Search for specific keyword
python3 log_analyzer.py logcat_main.txt --keyword "MainActivity"

# Filter by error level
python3 log_analyzer.py logcat_main.txt --level E

# Use custom templates
python3 log_analyzer.py logcat_main.txt --template-file my_templates.json

# Combined filters with debug
python3 log_analyzer.py logcat_main.txt --keyword "onCreate" --tag "ActivityManager" --debug
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
| `output_evd.md` | Test evidence report |

## 🛠 Customization

### Custom Log Patterns

The default pattern supports Android logcat format. To use custom patterns:

```python
from log_analyzer import ReadLogModule

reader = ReadLogModule()
# Custom pattern for different log format
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
      "priority": 1
    }
  ]
}
```

### Programmatic Usage

```python
from log_analyzer import LogAnalyzer

# Initialize with configuration
config = {
    'debug': True,
    'template_file': 'custom_templates.json'
}

analyzer = LogAnalyzer(config)

# Run analysis
analyzer.analyze(
    "logcat_main.txt",
    keyword="search_term",
    tag="MyTag",
    level="I"
)
```

## 🔍 Log Pattern Support

### Default Android Logcat Format
```
MM-DD HH:MM:SS.mmm LEVEL TAG: Message
09-17 10:30:15.123 I ActivityManager: Starting activity
```

### Custom Formats Supported
- Standard syslog
- Custom application logs
- Any format with configurable regex patterns

## 🎯 Use Cases

1. **Android Development**
   - Activity lifecycle analysis
   - Service interaction tracking
   - IPC communication visualization

2. **Automotive (Android Automotive OS)**
   - Car service state tracking
   - Vehicle HAL integration analysis
   - System service communication

3. **Testing & QA**
   - Generate test evidence
   - Create sequence documentation
   - Analyze application flow

4. **Debugging**
   - Visualize component interactions
   - Track error propagation
   - Identify timing issues

## 🔧 Best Practices

1. **Template Design**
   - Create specific patterns for your use case
   - Use priority to handle overlapping patterns
   - Test patterns with sample logs

2. **Performance**
   - Use filters to reduce data processing
   - Limit sequence diagram size for readability
   - Process large files in chunks if needed

3. **Maintenance**
   - Keep templates in version control
   - Document custom patterns
   - Regular expression optimization

## 📈 Next Steps

1. **Extend Templates**: Add more patterns for your specific logs
2. **Customize Output**: Modify export formats as needed
3. **Integrate CI/CD**: Add to automated testing pipelines
4. **Add Visualizations**: Extend with additional diagram types

## 🤝 Contributing

To extend the tool:

1. Inherit from `BaseModule` for new modules
2. Follow the existing pattern for module integration
3. Add new export formats as needed
4. Update templates for new log patterns

## 📝 License

This tool is provided as-is for development and testing purposes.
