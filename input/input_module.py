"""
InputModule - UC-01.1: Read Log File
Handles file reading, validation, and large file support
"""

import os
import sys
from typing import List, Optional, Dict, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "development_folder" / "dev_and_test"))
from data_models import BaseModule


class InputModule(BaseModule):
    """
    InputModule handles reading and validating log files
    Implements UC-01.1: Read Log File
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.max_file_size = self.config.get('max_file_size', 2 * 1024 * 1024 * 1024)  # 2GB
        self.chunk_size = self.config.get('chunk_size', 1024 * 1024)  # 1MB chunks
        self.supported_encodings = ['utf-8', 'ascii', 'latin-1']
        self.supported_extensions = ['.txt', '.log', '.logcat']
    
    def read_log_file(self, file_path: str) -> List[str]:
        """
        Main flow for UC-01.1: Read Log File
        
        Args:
            file_path: Path to the log file
            
        Returns:
            List of log lines
            
        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If no read permissions
            ValueError: If file format not supported
        """
        self.log_info(f"Starting to read log file: {file_path}")
        
        # Step 1: Validate file path exists
        if not self._validate_file_path(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Step 2: Check file permissions
        if not self._check_file_permissions(file_path):
            raise PermissionError(f"No read permissions for file: {file_path}")
        
        # Step 3: Validate file format
        if not self._validate_file_format(file_path):
            raise ValueError(f"Unsupported file format: {file_path}")
        
        # Step 4: Open file in read mode
        try:
            # Step 5: Read all lines into memory
            lines = self._read_file_lines(file_path)
            
            # Step 6: Return line array for processing
            self.log_info(f"Successfully read {len(lines)} lines from {file_path}")
            return lines
            
        except Exception as e:
            self.log_error(f"Error reading file {file_path}: {str(e)}")
            raise
    
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
        except Exception as e:
            self.log_error(f"Error checking permissions for {file_path}: {str(e)}")
            return False
    
    def _validate_file_format(self, file_path: str) -> bool:
        """Validate file format is supported"""
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension not in self.supported_extensions:
            self.log_error(f"Unsupported file extension: {extension}")
            return False
            
        return True
    
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
            except Exception as e:
                self.log_error(f"Error reading file with encoding {encoding}: {str(e)}")
                continue
        
        if not lines:
            raise ValueError(f"Could not read file with any supported encoding: {file_path}")
        
        # Remove empty lines and strip whitespace
        lines = [line.strip() for line in lines if line.strip()]
        return lines
    
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
                
                # Add the last line if it's complete
                if current_line.strip():
                    lines.append(current_line.strip())
                
                self.log_debug(f"Successfully read large file with encoding: {encoding}")
                break
                
            except UnicodeDecodeError:
                self.log_debug(f"Failed to read large file with encoding: {encoding}")
                continue
            except Exception as e:
                self.log_error(f"Error reading large file with encoding {encoding}: {str(e)}")
                continue
        
        if not lines:
            raise ValueError(f"Could not read large file with any supported encoding: {file_path}")
        
        self.log_info(f"Read {len(lines)} lines from large file using chunked reading")
        return lines
    
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
        except Exception as e:
            self.log_error(f"Error getting file info for {file_path}: {str(e)}")
            return {}
    
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
        except Exception as e:
            self.log_debug(f"Error detecting encoding: {str(e)}")
            return 'utf-8'
    
    def validate_business_rules(self, file_path: str) -> Dict[str, Any]:
        """
        Validate business rules for file reading
        BR1: Maximum file size limit is 2GB
        BR2: Supported encodings: UTF-8, ASCII, Latin-1
        BR3: Empty files should generate warning but not error
        BR4: File paths must be absolute or relative to working directory
        """
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        try:
            # BR1: Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                validation_result['errors'].append(f"File size {file_size} exceeds limit {self.max_file_size}")
                validation_result['valid'] = False
            
            # BR3: Check for empty file
            if file_size == 0:
                validation_result['warnings'].append("File is empty")
            
            # BR4: Validate path format
            path = Path(file_path)
            if not path.is_absolute() and not path.exists():
                # Check if relative path exists
                if not Path.cwd().joinpath(file_path).exists():
                    validation_result['errors'].append("File path does not exist")
                    validation_result['valid'] = False
            
        except Exception as e:
            validation_result['errors'].append(f"Error validating file: {str(e)}")
            validation_result['valid'] = False
        
        return validation_result


# Example usage and testing
if __name__ == "__main__":
    # Test the InputModule
    config = {'debug': True}
    input_module = InputModule(config)
    
    # Test with a sample file
    test_file = "sample_log.txt"
    
    try:
        # Create a sample log file for testing
        with open(test_file, 'w') as f:
            f.write("09-17 10:30:15.123 I ActivityManager: Starting activity\n")
            f.write("09-17 10:30:15.456 D CameraService: Camera initialized\n")
            f.write("09-17 10:30:15.789 E SystemService: Error occurred\n")
        
        # Test file reading
        lines = input_module.read_log_file(test_file)
        print(f"Read {len(lines)} lines successfully")
        
        # Test file info
        file_info = input_module.get_file_info(test_file)
        print(f"File info: {file_info}")
        
        # Test validation
        validation = input_module.validate_business_rules(test_file)
        print(f"Validation result: {validation}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)
