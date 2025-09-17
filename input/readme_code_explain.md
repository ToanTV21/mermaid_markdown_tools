# Input Module - Code Explanation

## 📁 Module Overview

The `input` folder contains the **InputModule** which implements **UC-01.1: Read Log File**. This module is responsible for reading and validating log files from various sources with comprehensive error handling and large file support.

## 📂 Files in this Folder

- `input_module.py` - Main module implementation
- `sample_logcat.txt` - Sample automotive log data for testing
- `readme_code_explain.md` - This documentation file

---

## 🔧 `input_module.py` - Core Implementation

### Class: `InputModule`

**Purpose**: Handles file reading, validation, and large file support according to use case specifications.

#### Key Attributes:
```python
def __init__(self, config: Optional[Dict[str, Any]] = None):
    super().__init__(config)
    self.max_file_size = self.config.get('max_file_size', 2 * 1024 * 1024 * 1024)  # 2GB
    self.chunk_size = self.config.get('chunk_size', 1024 * 1024)  # 1MB chunks
    self.supported_encodings = ['utf-8', 'ascii', 'latin-1']
    self.supported_extensions = ['.txt', '.log', '.logcat']
```

### Main Method: `read_log_file()`

**Purpose**: Main flow for UC-01.1 - Read Log File

```python
def read_log_file(self, file_path: str) -> List[str]:
    """
    Main flow for UC-01.1: Read Log File
    
    Steps:
    1. Validate file path exists
    2. Check file permissions
    3. Validate file format
    4. Open file in read mode
    5. Read all lines into memory
    6. Return line array for processing
    7. Log successful file reading
    """
```

#### Step-by-Step Process:

##### Step 1: File Path Validation
```python
def _validate_file_path(self, file_path: str) -> bool:
    """Validate that file path exists"""
    try:
        path = Path(file_path)
        if not path.exists():
            self.log_error(f"File does not exist: {file_path}")
            return False
        
        if not path.is_file():
            self.log_error(f"Path is not a file: {file_path}")
            return False
            
        return True
    except Exception as e:
        self.log_error(f"Error validating file path {file_path}: {str(e)}")
        return False
```

##### Step 2: Permission Checking
```python
def _check_file_permissions(self, file_path: str) -> bool:
    """Check if user has read permissions"""
    try:
        path = Path(file_path)
        if not path.is_file():
            return False
            
        # Check if file is readable
        with open(file_path, 'r') as f:
            pass  # Just test if we can open for reading
        return True
    except PermissionError:
        self.log_error(f"Permission denied for file: {file_path}")
        return False
```

##### Step 3: File Format Validation
```python
def _validate_file_format(self, file_path: str) -> bool:
    """Validate file format is supported"""
    path = Path(file_path)
    extension = path.suffix.lower()
    
    if extension not in self.supported_extensions:
        self.log_error(f"Unsupported file extension: {extension}")
        return False
        
    return True
```

### Large File Handling (AF3: Large File Handling)

The module implements sophisticated large file handling:

```python
def _read_file_lines(self, file_path: str) -> List[str]:
    """
    Read file lines with support for large files
    Implements AF3: Large File Handling
    """
    file_size = os.path.getsize(file_path)
    self.log_debug(f"File size: {file_size} bytes")
    
    # Check if file exceeds memory threshold
    if file_size > self.chunk_size:
        self.log_info(f"Large file detected ({file_size} bytes), using chunked reading")
        return self._read_file_chunked(file_path)
    else:
        return self._read_file_normal(file_path)
```

#### Normal File Reading:
```python
def _read_file_normal(self, file_path: str) -> List[str]:
    """Read file normally for smaller files"""
    lines = []
    
    # Try different encodings
    for encoding in self.supported_encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                lines = file.readlines()
            self.log_debug(f"Successfully read file with encoding: {encoding}")
            break
        except UnicodeDecodeError:
            self.log_debug(f"Failed to read with encoding: {encoding}")
            continue
```

#### Chunked Reading for Large Files:
```python
def _read_file_chunked(self, file_path: str) -> List[str]:
    """
    Read large file in chunks to manage memory
    Implements AF3: Large File Handling
    """
    lines = []
    current_line = ""
    
    for encoding in self.supported_encodings:
        try:
            with open(file_path, 'r', encoding=encoding, buffering=self.chunk_size) as file:
                while True:
                    chunk = file.read(self.chunk_size)
                    if not chunk:
                        break
                    
                    # Process chunk and maintain line continuity
                    chunk_lines = chunk.split('\n')
                    
                    # First chunk line might be continuation of previous line
                    if current_line:
                        chunk_lines[0] = current_line + chunk_lines[0]
                    
                    # Last chunk line might be incomplete
                    current_line = chunk_lines[-1]
                    chunk_lines = chunk_lines[:-1]
                    
                    # Add complete lines
                    lines.extend([line.strip() for line in chunk_lines if line.strip()])
```

### Alternative Flows (Error Handling)

#### AF1: File Not Found
```python
# Step 3a. File does not exist at specified path
# - System throws FileNotFoundError
# - System logs error with file path
# - System suggests checking file location
# - Use case ends with error state
```

#### AF2: Permission Denied
```python
# Step 3b. User lacks read permissions
# - System catches permission exception
# - System logs permission error
# - System suggests checking file permissions
# - Use case ends with error state
```

#### AF3: Large File Handling
```python
# Step 5a. File size exceeds memory threshold (>1GB)
# - System switches to chunked reading mode
# - System processes file in batches
# - System maintains line continuity
# - Continue with step 6
```

### Business Rules Implementation

#### BR1: Maximum file size limit is 2GB
```python
self.max_file_size = self.config.get('max_file_size', 2 * 1024 * 1024 * 1024)  # 2GB

def validate_business_rules(self, file_path: str) -> Dict[str, Any]:
    # BR1: Check file size
    file_size = os.path.getsize(file_path)
    if file_size > self.max_file_size:
        validation_result['errors'].append(f"File size {file_size} exceeds limit {self.max_file_size}")
        validation_result['valid'] = False
```

#### BR2: Supported encodings: UTF-8, ASCII, Latin-1
```python
self.supported_encodings = ['utf-8', 'ascii', 'latin-1']

# Try different encodings in order of preference
for encoding in self.supported_encodings:
    try:
        with open(file_path, 'r', encoding=encoding) as file:
            lines = file.readlines()
        break
    except UnicodeDecodeError:
        continue
```

#### BR3: Empty files should generate warning but not error
```python
# BR3: Check for empty file
if file_size == 0:
    validation_result['warnings'].append("File is empty")
```

#### BR4: File paths must be absolute or relative to working directory
```python
# BR4: Validate path format
path = Path(file_path)
if not path.is_absolute() and not path.exists():
    # Check if relative path exists
    if not Path.cwd().joinpath(file_path).exists():
        validation_result['errors'].append("File path does not exist")
        validation_result['valid'] = False
```

### Utility Methods

#### File Information Retrieval:
```python
def get_file_info(self, file_path: str) -> Dict[str, Any]:
    """Get file information for analysis"""
    try:
        path = Path(file_path)
        stat = path.stat()
        
        return {
            'file_path': str(path.absolute()),
            'file_name': path.name,
            'file_size': stat.st_size,
            'file_extension': path.suffix,
            'created_time': stat.st_ctime,
            'modified_time': stat.st_mtime,
            'is_readable': os.access(file_path, os.R_OK),
            'encoding_detected': self._detect_encoding(file_path)
        }
```

#### Encoding Detection:
```python
def _detect_encoding(self, file_path: str) -> Optional[str]:
    """Detect file encoding"""
    try:
        import chardet
        with open(file_path, 'rb') as file:
            raw_data = file.read(10000)  # Read first 10KB
            result = chardet.detect(raw_data)
            return result.get('encoding', 'utf-8')
    except ImportError:
        self.log_debug("chardet not available, using default encoding detection")
        return 'utf-8'
```

---

## 📊 Sample Data: `sample_logcat.txt`

### Purpose:
Contains realistic automotive log data for testing and demonstration.

### Content Structure:
```
09-17 10:30:15.123 I ActivityManager: Starting activity com.android.camera/.CameraActivity
09-17 10:30:15.124 D CameraService: Camera service starting
09-17 10:30:15.125 I CameraService: Binding to camera service
...
```

### Log Format:
- **Timestamp**: MM-DD HH:MM:SS.mmm
- **Level**: I (Info), D (Debug), E (Error), W (Warning)
- **Tag**: Component name (ActivityManager, CameraService, etc.)
- **Message**: Detailed log message

### Automotive-Specific Events:
- Camera service lifecycle
- Vehicle HAL integration
- Gear change events
- Hardware initialization
- Error handling scenarios

---

## 🧪 Testing and Usage

### Basic Usage:
```python
from input.input_module import InputModule

# Initialize module
config = {'debug': True}
input_module = InputModule(config)

# Read log file
lines = input_module.read_log_file("sample_logcat.txt")
print(f"Read {len(lines)} lines")
```

### Error Handling:
```python
try:
    lines = input_module.read_log_file("nonexistent_file.txt")
except FileNotFoundError:
    print("File not found")
except PermissionError:
    print("Permission denied")
```

### File Information:
```python
file_info = input_module.get_file_info("sample_logcat.txt")
print(f"File size: {file_info['file_size']} bytes")
print(f"Encoding: {file_info['encoding_detected']}")
```

### Validation:
```python
validation = input_module.validate_business_rules("sample_logcat.txt")
if validation['valid']:
    print("File validation passed")
else:
    print(f"Validation errors: {validation['errors']}")
```

---

## 🔧 Configuration Options

### Default Configuration:
```python
config = {
    'max_file_size': 2 * 1024 * 1024 * 1024,  # 2GB
    'chunk_size': 1024 * 1024,  # 1MB
    'supported_encodings': ['utf-8', 'ascii', 'latin-1'],
    'supported_extensions': ['.txt', '.log', '.logcat']
}
```

### Custom Configuration:
```python
config = {
    'max_file_size': 1024 * 1024 * 1024,  # 1GB limit
    'chunk_size': 512 * 1024,  # 512KB chunks
    'debug': True
}
input_module = InputModule(config)
```

---

## 📈 Performance Characteristics

### Memory Usage:
- **Small Files**: Loads entire file into memory
- **Large Files**: Processes in chunks to manage memory
- **Memory Limit**: 2x file size maximum

### Speed:
- **Small Files**: Direct memory loading
- **Large Files**: Chunked processing with buffering
- **Encoding Detection**: Automatic fallback through supported encodings

### Error Recovery:
- **File Not Found**: Immediate failure with clear error message
- **Permission Denied**: Clear error with suggestion
- **Encoding Issues**: Automatic fallback to different encodings
- **Large Files**: Automatic switch to chunked processing

---

## 🛡️ Security Considerations

### File Access:
- **Permission Checking**: Validates read permissions before access
- **Path Validation**: Ensures file exists and is accessible
- **Extension Validation**: Only allows supported file types

### Data Protection:
- **No Writing**: Module only reads files, never modifies
- **Temporary Processing**: Data processed in memory only
- **Cleanup**: No persistent data storage

---

## 🔄 Integration with Other Modules

### Input to ReadLogModule:
```python
# InputModule reads raw lines
lines = input_module.read_log_file("logfile.txt")

# ReadLogModule parses the lines
parsed_entries = read_log_module.parse_log_entries(lines)
```

### Error Propagation:
```python
try:
    lines = input_module.read_log_file(file_path)
    # Continue with processing
except Exception as e:
    # Handle error and propagate to calling module
    raise
```

---

This InputModule provides a robust foundation for file reading with comprehensive error handling, large file support, and automotive-grade reliability. It serves as the entry point for all log analysis operations in the system.
