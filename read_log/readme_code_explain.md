# Read Log Module - Code Explanation

## 📁 Module Overview

The `read_log` folder contains the **ReadLogModule** which implements **UC-03.1: Parse Log Entries**, **UC-03.2: Search and Filter Logs**, and **UC-03.3: Update Log Pattern**. This module handles log parsing, searching, filtering, and pattern management with comprehensive error handling.

## 📂 Files in this Folder

- `read_log_module.py` - Main module implementation
- `log_patterns.txt` - Configuration file with multiple log format patterns
- `logcat_analyzer.py` - Legacy analyzer (if present)
- `readme_code_explain.md` - This documentation file

---

## 🔧 `read_log_module.py` - Core Implementation

### Class: `ReadLogModule`

**Purpose**: Handles log parsing, searching, filtering, and pattern updates according to use case specifications.

#### Key Attributes:
```python
def __init__(self, config: Optional[Dict[str, Any]] = None):
    super().__init__(config)
    self.log_pattern = self.config.get('log_pattern', self._get_default_android_pattern())
    self.compiled_pattern = re.compile(self.log_pattern)
    self.temp_results_dir = self.config.get('temp_results_dir', 'temp_results')
    self.max_results = self.config.get('max_results', 10000)
    
    # Create temp results directory
    Path(self.temp_results_dir).mkdir(exist_ok=True)
```

### Main Method 1: `parse_log_entries()`

**Purpose**: Main flow for UC-03.1 - Parse Log Entries

```python
def parse_log_entries(self, log_lines: List[str]) -> List[LogEntry]:
    """
    Main flow for UC-03.1: Parse Log Entries
    
    Steps:
    1. System receives array of log lines
    2. System compiles regex pattern (pre-stored regex txt file for using to compile)
    3. FOR each log line:
       - System applies regex pattern
       - System extracts timestamp, level, tag, message
       - System creates LogEntry object
       - System handles multi-line messages
    4. System stores parsed entries
    5. System reports parsing statistics
    6. Save results into temp_results files according to pre-stored regex file at step 2
    """
```

#### Step-by-Step Process:

##### Step 1: Pattern Compilation
```python
def _get_default_android_pattern(self) -> str:
    """Get default Android logcat pattern"""
    return r'^(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(\w+)\s+(\w+):\s*(.*)$'

# Pattern is pre-compiled in __init__
self.compiled_pattern = re.compile(self.log_pattern)
```

##### Step 2: Log Line Processing
```python
for line in log_lines:
    line_number += 1
    line = line.strip()
    
    if not line:  # Skip empty lines
        continue
    
    # Apply regex pattern
    match = self.compiled_pattern.match(line)
    
    if match:
        # Step 3a: System applies regex pattern
        # Step 3b: System extracts timestamp, level, tag, message
        try:
            log_entry = self._create_log_entry_from_match(match, line, line_number)
            parsed_entries.append(log_entry)
            
            # Clear multi-line buffer on successful parse
            multi_line_buffer = ""
            
        except Exception as e:
            self.log_warning(f"Error creating log entry from line {line_number}: {str(e)}")
            unparsed_lines.append(line)
```

##### Step 3: Log Entry Creation
```python
def _create_log_entry_from_match(self, match: re.Match, original_line: str, line_number: int) -> LogEntry:
    """Create LogEntry from regex match"""
    groups = match.groups()
    
    # Extract components
    timestamp = groups[0] if len(groups) > 0 else ""
    level_str = groups[1] if len(groups) > 1 else "I"
    tag = groups[2] if len(groups) > 2 else ""
    message = groups[3] if len(groups) > 3 else ""
    
    # Convert level string to LogLevel enum
    try:
        level = LogLevel(level_str)
    except ValueError:
        self.log_warning(f"Unknown log level: {level_str}, defaulting to INFO")
        level = LogLevel.INFO
    
    return LogEntry(
        timestamp=timestamp,
        level=level,
        tag=tag,
        message=message,
        original_line=original_line,
        line_number=line_number
    )
```

##### Step 4: Multi-line Handling
```python
def _is_continuation_line(self, line: str, parsed_entries: List[LogEntry]) -> bool:
    """Check if line is continuation of previous entry"""
    if not parsed_entries:
        return False
    
    # Simple heuristic: if line doesn't start with timestamp pattern, it's likely a continuation
    timestamp_pattern = r'^\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}'
    return not re.match(timestamp_pattern, line)

# In main processing loop:
else:
    # AF1: Non-Matching Line Format
    if self._is_continuation_line(line, parsed_entries):
        # Append to previous message
        if parsed_entries:
            parsed_entries[-1].message += " " + line
            parsed_entries[-1].original_line += "\n" + line
    else:
        # Store as unparsed entry
        unparsed_lines.append(line)
```

##### Step 5: Statistics Generation
```python
def _generate_parsing_statistics(self, parsed_entries: List[LogEntry], unparsed_lines: List[str]) -> Dict[str, Any]:
    """Generate parsing statistics"""
    total_lines = len(parsed_entries) + len(unparsed_lines)
    success_rate = (len(parsed_entries) / total_lines * 100) if total_lines > 0 else 0
    
    # Count by level
    level_counts = {}
    for entry in parsed_entries:
        level = entry.level.value
        level_counts[level] = level_counts.get(level, 0) + 1
    
    return {
        'total_lines': total_lines,
        'parsed_entries': len(parsed_entries),
        'unparsed_lines': len(unparsed_lines),
        'success_rate': round(success_rate, 2),
        'level_distribution': level_counts
    }
```

##### Step 6: Results Storage
```python
def _save_parsing_results(self, parsed_entries: List[LogEntry], unparsed_lines: List[str]):
    """Save parsing results to temp files"""
    try:
        # Save parsed entries
        parsed_file = Path(self.temp_results_dir) / "parsed_entries.txt"
        with open(parsed_file, 'w', encoding='utf-8') as f:
            for entry in parsed_entries:
                f.write(f"{entry.timestamp} {entry.level.value} {entry.tag}: {entry.message}\n")
        
        # Save unparsed lines
        if unparsed_lines:
            unparsed_file = Path(self.temp_results_dir) / "unparsed_lines.txt"
            with open(unparsed_file, 'w', encoding='utf-8') as f:
                for line in unparsed_lines:
                    f.write(f"{line}\n")
        
        self.log_debug(f"Saved parsing results to {self.temp_results_dir}")
        
    except Exception as e:
        self.log_error(f"Error saving parsing results: {str(e)}")
```

### Main Method 2: `search_and_filter_logs()`

**Purpose**: Main flow for UC-03.2 - Search and Filter Logs

```python
def search_and_filter_logs(self, log_entries: List[LogEntry], 
                          keyword: Optional[str] = None,
                          tag: Optional[str] = None,
                          level: Optional[LogLevel] = None) -> List[LogEntry]:
    """
    Main flow for UC-03.2: Search and Filter Logs
    
    Steps:
    1. User provides search criteria (keyword/tag/level)
    2. System validates search parameters
    3. System iterates through parsed logs
    4. System applies filters:
       - Check keyword in message
       - Match tag exactly
       - Match severity level
    5. System collects matching entries
    6. System saves results to temporary file
    7. System returns filtered entries
    """
```

#### Search Criteria Processing:
```python
def _validate_search_parameters(self, keyword: Optional[str], tag: Optional[str], level: Optional[LogLevel]) -> Dict[str, Any]:
    """Validate search parameters"""
    return {
        'keyword': keyword.lower() if keyword else None,
        'tag': tag,
        'level': level
    }
```

#### Filter Application:
```python
def _matches_search_criteria(self, entry: LogEntry, criteria: Dict[str, Any]) -> bool:
    """Check if entry matches search criteria"""
    # AF2: Multiple Criteria - apply AND logic
    
    # Keyword search (case-insensitive)
    if criteria['keyword']:
        if criteria['keyword'] not in entry.message.lower():
            return False
    
    # Tag matching (case-sensitive)
    if criteria['tag']:
        if entry.tag != criteria['tag']:
            return False
    
    # Level filter (includes specified level and higher)
    if criteria['level']:
        if not self._level_matches(entry.level, criteria['level']):
            return False
    
    return True
```

#### Level Matching Logic:
```python
def _level_matches(self, entry_level: LogLevel, filter_level: LogLevel) -> bool:
    """Check if entry level matches filter (includes higher levels)"""
    level_hierarchy = {
        LogLevel.VERBOSE: 0,
        LogLevel.DEBUG: 1,
        LogLevel.INFO: 2,
        LogLevel.WARNING: 3,
        LogLevel.ERROR: 4,
        LogLevel.FATAL: 5
    }
    
    return level_hierarchy[entry_level] >= level_hierarchy[filter_level]
```

#### Results Storage:
```python
def _save_filtered_results(self, filtered_entries: List[LogEntry]):
    """Save filtered results to temporary file"""
    try:
        # Limit results to max_results
        limited_entries = filtered_entries[:self.max_results]
        
        filtered_file = Path(self.temp_results_dir) / "searched_temp.txt"
        with open(filtered_file, 'w', encoding='utf-8') as f:
            for entry in limited_entries:
                f.write(f"{entry.timestamp} {entry.level.value} {entry.tag}: {entry.message}\n")
        
        self.log_debug(f"Saved {len(limited_entries)} filtered entries to {filtered_file}")
        
    except Exception as e:
        self.log_error(f"Error saving filtered results: {str(e)}")
```

### Main Method 3: `update_log_pattern()`

**Purpose**: Main flow for UC-03.3 - Update Log Pattern

```python
def update_log_pattern(self, new_pattern: str) -> bool:
    """
    Main flow for UC-03.3: Update Log Pattern
    
    Steps:
    1. Admin provides new regex pattern
    2. System validates regex syntax
    3. System compiles test pattern
    4. System tests pattern on sample line
    5. System updates active pattern
    6. System logs pattern change
    7. System confirms update success
    """
```

#### Pattern Validation:
```python
def _validate_regex_syntax(self, pattern: str) -> bool:
    """Validate regex syntax"""
    try:
        re.compile(pattern)
        return True
    except re.error as e:
        self.log_error(f"Regex syntax error: {str(e)}")
        return False
```

#### Pattern Update:
```python
try:
    # Step 1: Admin provides new regex pattern
    # Step 2: System validates regex syntax
    if not self._validate_regex_syntax(new_pattern):
        # AF1: Invalid Regex
        self.log_error("Invalid regex syntax")
        return False
    
    # Step 3: System compiles test pattern
    test_pattern = re.compile(new_pattern)
    
    # Step 4: System tests pattern on sample line
    sample_line = "09-17 10:30:15.123 I ActivityManager: Starting activity"
    if not test_pattern.match(sample_line):
        self.log_warning("Pattern doesn't match sample Android logcat line")
    
    # Step 5: System updates active pattern
    old_pattern = self.log_pattern
    self.log_pattern = new_pattern
    self.compiled_pattern = test_pattern
    
    # Step 6: System logs pattern change
    self.log_info(f"Pattern updated from '{old_pattern}' to '{new_pattern}'")
    
    # Step 7: System confirms update success
    return True
```

### Alternative Flows (Error Handling)

#### AF1: Non-Matching Line Format
```python
# Step 3a. Line doesn't match pattern
# - System checks if continuation of previous entry
# - If yes: append to previous message
# - If no: store as unparsed entry
# - Continue with next line
```

#### AF2: Malformed Timestamp
```python
# Step 3b. Timestamp parsing fails
# - System uses placeholder timestamp
# - System logs warning
# - Continue processing with degraded timestamp
```

#### AF1: No Matches Found (Search)
```python
# AF1: No Matches Found
if not filtered_entries:
    self.log_info("No entries match criteria")
    self._suggest_broadening_criteria(search_criteria)
```

#### AF2: Multiple Criteria (Search)
```python
# AF2: Multiple Criteria - apply AND logic
# - System applies all criteria
# - System processes all criteria
# - Continue with matching entries
```

#### AF1: Invalid Regex (Pattern Update)
```python
# AF1: Invalid Regex
# - System reports syntax error
# - System maintains current pattern
# - System provides error details
# - Use case ends with error
```

### Business Rules Implementation

#### BR1: Support Android logcat format by default
```python
def _get_default_android_pattern(self) -> str:
    """Get default Android logcat pattern"""
    return r'^(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(\w+)\s+(\w+):\s*(.*)$'
```

#### BR2: Multi-line logs must be consolidated
```python
def _is_continuation_line(self, line: str, parsed_entries: List[LogEntry]) -> bool:
    """Check if line is continuation of previous entry"""
    if not parsed_entries:
        return False
    
    # Simple heuristic: if line doesn't start with timestamp pattern, it's likely a continuation
    timestamp_pattern = r'^\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}'
    return not re.match(timestamp_pattern, line)
```

#### BR3: Preserve original line for evidence
```python
return LogEntry(
    timestamp=timestamp,
    level=level,
    tag=tag,
    message=message,
    original_line=original_line,  # Preserved for evidence
    line_number=line_number
)
```

#### BR4: Empty lines should be skipped
```python
if not line:  # Skip empty lines
    continue
```

### Additional Business Rules (Search)

#### BR1: Keyword search is case-insensitive
```python
if criteria['keyword']:
    if criteria['keyword'] not in entry.message.lower():  # Case-insensitive
        return False
```

#### BR2: Tag matching is case-sensitive
```python
if criteria['tag']:
    if entry.tag != criteria['tag']:  # Case-sensitive
        return False
```

#### BR3: Level filter includes specified level and higher
```python
def _level_matches(self, entry_level: LogLevel, filter_level: LogLevel) -> bool:
    """Check if entry level matches filter (includes higher levels)"""
    level_hierarchy = {
        LogLevel.VERBOSE: 0,
        LogLevel.DEBUG: 1,
        LogLevel.INFO: 2,
        LogLevel.WARNING: 3,
        LogLevel.ERROR: 4,
        LogLevel.FATAL: 5
    }
    
    return level_hierarchy[entry_level] >= level_hierarchy[filter_level]
```

#### BR4: Results limited to 10,000 entries by default
```python
self.max_results = self.config.get('max_results', 10000)

# Limit results to max_results
limited_entries = filtered_entries[:self.max_results]
```

### Utility Methods

#### Statistics Retrieval:
```python
def get_parsing_statistics(self) -> Dict[str, Any]:
    """Get current parsing statistics"""
    return {
        'current_pattern': self.log_pattern,
        'pattern_compiled': self.compiled_pattern is not None,
        'temp_results_dir': self.temp_results_dir,
        'max_results': self.max_results
    }
```

#### Suggestion System:
```python
def _suggest_broadening_criteria(self, criteria: Dict[str, Any]):
    """Suggest broadening search criteria when no matches found"""
    suggestions = []
    
    if criteria['keyword']:
        suggestions.append("Try a shorter or more general keyword")
    
    if criteria['tag']:
        suggestions.append("Check tag spelling or try partial tag match")
    
    if criteria['level']:
        suggestions.append("Try a lower severity level (e.g., INFO instead of ERROR)")
    
    if suggestions:
        self.log_info("Suggestions to broaden search: " + "; ".join(suggestions))
```

---

## 📊 Log Patterns Configuration: `log_patterns.txt`

### Purpose:
Contains multiple regex patterns for different log formats.

### Pattern Categories:

#### 1. **Android Logcat Patterns**
```regex
# Default Android Logcat Pattern
DEFAULT_ANDROID_LOGCAT=^(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(\w+)\s+(\w+):\s*(.*)$

# Alternative with year
ANDROID_LOGCAT_WITH_YEAR=^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(\w+)\s+(\w+):\s*(.*)$
```

#### 2. **System Log Patterns**
```regex
# Standard Syslog Pattern
SYSLOG=^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\w+)\s+(\w+):\s*(.*)$

# Custom Application Log Pattern
CUSTOM_APP_LOG=^\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s+(\w+)\s+(\w+):\s*(.*)$
```

#### 3. **ISO Standards**
```regex
# ISO 8601 Timestamp Pattern
ISO_8601=^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z)\s+(\w+)\s+(\w+):\s*(.*)$
```

#### 4. **Automotive-Specific Patterns**
```regex
# Automotive ECU Pattern
AUTOMOTIVE_ECU=^\[(\w+)\]\s+(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(\w+)\s+(\w+):\s*(.*)$

# Automotive Camera System Pattern
AUTOMOTIVE_CAMERA=^\[(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\]\s+\[(\w+)\]\s+\[(\w+)\]\s+\[(\w+)\]\s+(.*)$
```

#### 5. **Structured Data Patterns**
```regex
# JSON Log Pattern
JSON_LOG=^\{"timestamp":\s*"([^"]+)",\s*"level":\s*"([^"]+)",\s*"tag":\s*"([^"]+)",\s*"message":\s*"([^"]+)"\}$

# CSV Log Pattern
CSV_LOG=^([^,]+),([^,]+),([^,]+),(.*)$

# Tab-separated Log Pattern
TAB_SEPARATED=^([^\t]+)\t([^\t]+)\t([^\t]+)\t(.*)$
```

#### 6. **Thread and Process Information**
```regex
# Pattern for logs with thread information
THREAD_INFO=^(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(\w+)\s+(\w+)\s+\((\d+)\):\s*(.*)$

# Pattern for logs with process information
PROCESS_INFO=^(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(\w+)\s+(\w+)\s+\((\d+)\):\s*(.*)$
```

---

## 🧪 Testing and Usage

### Basic Usage:
```python
from read_log.read_log_module import ReadLogModule

# Initialize module
config = {'debug': True}
read_log_module = ReadLogModule(config)

# Parse log entries
sample_logs = [
    "09-17 10:30:15.123 I ActivityManager: Starting activity",
    "09-17 10:30:15.456 D CameraService: Camera initialized",
    "09-17 10:30:15.789 E SystemService: Error occurred"
]
parsed_entries = read_log_module.parse_log_entries(sample_logs)
print(f"Parsed {len(parsed_entries)} entries")
```

### Search and Filter:
```python
# Search with keyword
filtered_entries = read_log_module.search_and_filter_logs(
    parsed_entries, 
    keyword="Camera"
)

# Filter by level
from data_models import LogLevel
filtered_entries = read_log_module.search_and_filter_logs(
    parsed_entries, 
    level=LogLevel.INFO
)

# Multiple criteria
filtered_entries = read_log_module.search_and_filter_logs(
    parsed_entries, 
    keyword="Camera",
    tag="CameraService",
    level=LogLevel.INFO
)
```

### Pattern Update:
```python
# Update to custom pattern
new_pattern = r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+\[(\w+)\]\s+(\w+):\s*(.*)$'
success = read_log_module.update_log_pattern(new_pattern)
print(f"Pattern update successful: {success}")
```

### Statistics:
```python
stats = read_log_module.get_parsing_statistics()
print(f"Current pattern: {stats['current_pattern']}")
print(f"Max results: {stats['max_results']}")
```

---

## 🔧 Configuration Options

### Default Configuration:
```python
config = {
    'log_pattern': '^\\d{2}-\\d{2}\\s+\\d{2}:\\d{2}:\\d{2}\\.\\d{3}\\s+(\\w+)\\s+(\\w+):\\s*(.*)$',
    'temp_results_dir': 'temp_results',
    'max_results': 10000
}
```

### Custom Configuration:
```python
config = {
    'log_pattern': r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+\[(\w+)\]\s+(\w+):\s*(.*)$',
    'temp_results_dir': 'custom_temp',
    'max_results': 50000,
    'debug': True
}
read_log_module = ReadLogModule(config)
```

---

## 📈 Performance Characteristics

### Parsing Speed:
- **Compiled Regex**: Pre-compiled patterns for fast matching
- **Streaming Processing**: Processes lines as they're read
- **Memory Efficient**: Minimal memory overhead per entry

### Search Performance:
- **Indexed Search**: Fast keyword and tag matching
- **Level Hierarchy**: Efficient level filtering
- **Result Limiting**: Prevents memory overflow

### Storage:
- **Temporary Files**: Results saved for later processing
- **Cleanup**: Automatic cleanup of temporary files
- **Compression**: Optional compression for large result sets

---

## 🛡️ Error Handling

### Parsing Errors:
- **Malformed Lines**: Graceful handling with warnings
- **Invalid Timestamps**: Fallback to placeholder values
- **Encoding Issues**: Automatic encoding detection

### Search Errors:
- **No Matches**: Clear feedback with suggestions
- **Invalid Criteria**: Validation with helpful messages
- **Memory Limits**: Automatic result limiting

### Pattern Errors:
- **Invalid Regex**: Clear syntax error messages
- **Compilation Failure**: Fallback to previous pattern
- **Test Failure**: Warning with sample line testing

---

## 🔄 Integration with Other Modules

### Input from InputModule:
```python
# InputModule provides raw lines
lines = input_module.read_log_file("logfile.txt")

# ReadLogModule parses the lines
parsed_entries = read_log_module.parse_log_entries(lines)
```

### Output to QuickCompareModule:
```python
# ReadLogModule provides parsed entries
parsed_entries = read_log_module.parse_log_entries(lines)

# QuickCompareModule uses entries for sequence generation
events = quick_compare_module.generate_sequence_events(parsed_entries, templates)
```

### Template Integration:
```python
# Templates can be updated based on parsing results
if parsing_stats['success_rate'] < 80:
    # Suggest pattern update
    read_log_module.update_log_pattern(new_pattern)
```

---

This ReadLogModule provides comprehensive log processing capabilities with robust error handling, flexible pattern management, and efficient search functionality. It serves as the core processing engine for converting raw log data into structured, searchable entries.
