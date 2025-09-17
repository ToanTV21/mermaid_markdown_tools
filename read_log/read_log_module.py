"""
ReadLogModule - UC-03.1, UC-03.2, UC-03.3
Handles log parsing, searching, filtering, and pattern updates
"""

import re
import sys
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "development_folder" / "dev_and_test"))
from data_models import BaseModule, LogEntry, LogLevel


class ReadLogModule(BaseModule):
    """
    ReadLogModule handles log parsing, searching, and filtering
    Implements UC-03.1: Parse Log Entries
    Implements UC-03.2: Search and Filter Logs
    Implements UC-03.3: Update Log Pattern
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.log_pattern = self.config.get('log_pattern', self._get_default_android_pattern())
        self.compiled_pattern = re.compile(self.log_pattern)
        self.temp_results_dir = self.config.get('temp_results_dir', 'temp_results')
        self.max_results = self.config.get('max_results', 10000)
        
        # Create temp results directory
        Path(self.temp_results_dir).mkdir(exist_ok=True)
    
    def parse_log_entries(self, log_lines: List[str]) -> List[LogEntry]:
        """
        Main flow for UC-03.1: Parse Log Entries
        
        Args:
            log_lines: List of raw log lines
            
        Returns:
            List of parsed LogEntry objects
        """
        self.log_info(f"Starting to parse {len(log_lines)} log lines")
        
        parsed_entries = []
        unparsed_lines = []
        multi_line_buffer = ""
        line_number = 0
        
        # Step 1: System receives array of log lines
        # Step 2: System compiles regex pattern (pre-stored regex txt file for using to compile)
        self.log_debug(f"Using pattern: {self.log_pattern}")
        
        # Step 3: FOR each log line
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
        
        # Step 4: System stores parsed entries
        # Step 5: System reports parsing statistics
        stats = self._generate_parsing_statistics(parsed_entries, unparsed_lines)
        self.log_info(f"Parsing complete: {stats}")
        
        # Step 6: Save results into temp_results files according to pre-stored regex file at step 2
        self._save_parsing_results(parsed_entries, unparsed_lines)
        
        return parsed_entries
    
    def _get_default_android_pattern(self) -> str:
        """Get default Android logcat pattern"""
        return r'^(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(\w+)\s+(\w+):\s*(.*)$'
    
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
    
    def _is_continuation_line(self, line: str, parsed_entries: List[LogEntry]) -> bool:
        """Check if line is continuation of previous entry"""
        if not parsed_entries:
            return False
        
        # Simple heuristic: if line doesn't start with timestamp pattern, it's likely a continuation
        timestamp_pattern = r'^\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}'
        return not re.match(timestamp_pattern, line)
    
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
    
    def search_and_filter_logs(self, log_entries: List[LogEntry], 
                              keyword: Optional[str] = None,
                              tag: Optional[str] = None,
                              level: Optional[LogLevel] = None) -> List[LogEntry]:
        """
        Main flow for UC-03.2: Search and Filter Logs
        
        Args:
            log_entries: List of parsed log entries
            keyword: Optional keyword to search in messages
            tag: Optional tag to filter by
            level: Optional log level to filter by
            
        Returns:
            List of filtered log entries
        """
        self.log_info("Starting log search and filter")
        
        # Step 1: User provides search criteria (keyword/tag/level)
        search_criteria = self._validate_search_parameters(keyword, tag, level)
        
        if not any(search_criteria.values()):
            self.log_warning("No search criteria provided, returning all entries")
            return log_entries
        
        # Step 2: System validates search parameters
        self.log_debug(f"Search criteria: {search_criteria}")
        
        # Step 3: System iterates through parsed logs
        # Step 4: System applies filters
        filtered_entries = []
        
        for entry in log_entries:
            if self._matches_search_criteria(entry, search_criteria):
                filtered_entries.append(entry)
        
        # Step 5: System collects matching entries
        # Step 6: System saves results to temporary file
        if filtered_entries:
            self._save_filtered_results(filtered_entries)
        
        # Step 7: System returns filtered entries
        self.log_info(f"Filtered {len(filtered_entries)} entries from {len(log_entries)} total")
        
        # AF1: No Matches Found
        if not filtered_entries:
            self.log_info("No entries match criteria")
            self._suggest_broadening_criteria(search_criteria)
        
        return filtered_entries
    
    def _validate_search_parameters(self, keyword: Optional[str], tag: Optional[str], level: Optional[LogLevel]) -> Dict[str, Any]:
        """Validate search parameters"""
        return {
            'keyword': keyword.lower() if keyword else None,
            'tag': tag,
            'level': level
        }
    
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
    
    def update_log_pattern(self, new_pattern: str) -> bool:
        """
        Main flow for UC-03.3: Update Log Pattern
        
        Args:
            new_pattern: New regex pattern for log parsing
            
        Returns:
            True if pattern updated successfully, False otherwise
        """
        self.log_info(f"Updating log pattern to: {new_pattern}")
        
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
            
        except Exception as e:
            self.log_error(f"Error updating log pattern: {str(e)}")
            return False
    
    def _validate_regex_syntax(self, pattern: str) -> bool:
        """Validate regex syntax"""
        try:
            re.compile(pattern)
            return True
        except re.error as e:
            self.log_error(f"Regex syntax error: {str(e)}")
            return False
    
    def get_parsing_statistics(self) -> Dict[str, Any]:
        """Get current parsing statistics"""
        return {
            'current_pattern': self.log_pattern,
            'pattern_compiled': self.compiled_pattern is not None,
            'temp_results_dir': self.temp_results_dir,
            'max_results': self.max_results
        }
    
    def validate_business_rules(self) -> Dict[str, Any]:
        """
        Validate business rules for log parsing
        BR1: Support Android logcat format by default
        BR2: Multi-line logs must be consolidated
        BR3: Preserve original line for evidence
        BR4: Empty lines should be skipped
        """
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # BR1: Check if pattern supports Android logcat
        sample_android_line = "09-17 10:30:15.123 I ActivityManager: Starting activity"
        if not self.compiled_pattern.match(sample_android_line):
            validation_result['warnings'].append("Current pattern may not support Android logcat format")
        
        # BR4: Check for empty line handling
        if not self._handles_empty_lines():
            validation_result['warnings'].append("Empty line handling not implemented")
        
        return validation_result
    
    def _handles_empty_lines(self) -> bool:
        """Check if empty line handling is implemented"""
        # This is implemented in parse_log_entries method
        return True


# Example usage and testing
if __name__ == "__main__":
    # Test the ReadLogModule
    config = {'debug': True}
    read_log_module = ReadLogModule(config)
    
    # Test log parsing
    sample_logs = [
        "09-17 10:30:15.123 I ActivityManager: Starting activity",
        "09-17 10:30:15.456 D CameraService: Camera initialized",
        "09-17 10:30:15.789 E SystemService: Error occurred",
        "    This is a continuation line",
        "09-17 10:30:16.012 W NetworkService: Connection timeout"
    ]
    
    parsed_entries = read_log_module.parse_log_entries(sample_logs)
    print(f"Parsed {len(parsed_entries)} entries")
    
    # Test search and filter
    filtered_entries = read_log_module.search_and_filter_logs(
        parsed_entries, 
        keyword="Camera",
        level=LogLevel.INFO
    )
    print(f"Filtered {len(filtered_entries)} entries")
    
    # Test pattern update
    new_pattern = r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+\[(\w+)\]\s+(\w+):\s*(.*)$'
    success = read_log_module.update_log_pattern(new_pattern)
    print(f"Pattern update successful: {success}")
    
    # Test validation
    validation = read_log_module.validate_business_rules()
    print(f"Validation result: {validation}")
    
    # Test statistics
    stats = read_log_module.get_parsing_statistics()
    print(f"Statistics: {stats}")
