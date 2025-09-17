# Template Sequence Module - Code Explanation

## 📁 Module Overview

The `template_sequence` folder contains the **TemplateSequenceModule** which implements **UC-02.1: Load Template Configuration** and **UC-02.2: Export Template Diagram**. This module manages log pattern templates and generates visual representations of template configurations.

## 📂 Files in this Folder

- `template_sequence_module.py` - Main module implementation
- `templates.json` - Template configuration file with 15 automotive templates
- `input_pdf_template/` - Input template files
  - `template_detail.md` - Detailed template documentation
  - `template_overview.md` - Overview template documentation
- `ouput_markdown_template_seq/` - Output directory for generated diagrams
- `readme_code_explain.md` - This documentation file

---

## 🔧 `template_sequence_module.py` - Core Implementation

### Class: `TemplateSequenceModule`

**Purpose**: Handles template configuration loading and diagram export according to use case specifications.

#### Key Attributes:
```python
def __init__(self, config: Optional[Dict[str, Any]] = None):
    super().__init__(config)
    self.templates: List[Template] = []
    self.template_file_path = self.config.get('template_file', 'templates.json')
    self.default_templates = self._get_default_templates()
```

### Main Method 1: `load_template_configuration()`

**Purpose**: Main flow for UC-02.1 - Load Template Configuration

```python
def load_template_configuration(self, template_file: Optional[str] = None) -> List[Template]:
    """
    Main flow for UC-02.1: Load Template Configuration
    
    Steps:
    1. Attempt to load template configuration file
    2. Validate JSON structure
    3. Parse template definitions
    4. Validate each template's required fields
    5. Sort templates by priority
    6. Store templates in memory
    7. Report number of loaded templates
    """
```

#### Step-by-Step Process:

##### Step 1: Template File Loading
```python
def _template_file_exists(self, template_path: str) -> bool:
    """Check if template file exists"""
    return Path(template_path).exists()
```

##### Step 2: JSON Structure Validation
```python
def _validate_json_structure(self, template_path: str) -> bool:
    """Validate JSON structure of template file"""
    try:
        with open(template_path, 'r', encoding='utf-8') as file:
            json.load(file)
        return True
    except json.JSONDecodeError as e:
        self.log_error(f"JSON parsing failed: {str(e)}")
        return False
```

##### Step 3: Template Definition Parsing
```python
def _parse_template_definitions(self, template_path: str) -> List[Dict[str, Any]]:
    """Parse template definitions from JSON file"""
    with open(template_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    if 'templates' not in data:
        raise ValueError("Template file must contain 'templates' array")
    
    return data['templates']
```

##### Step 4: Template Field Validation
```python
def _validate_template_fields(self, templates_data: List[Dict[str, Any]]) -> List[Template]:
    """Validate each template's required fields"""
    valid_templates = []
    
    for template_data in templates_data:
        try:
            # Validate required fields
            if not self._has_required_fields(template_data):
                self.log_warning(f"Skipping template with missing required fields: {template_data.get('name', 'unknown')}")
                continue
            
            # Validate regex pattern
            if not self._validate_regex_pattern(template_data['pattern']):
                self.log_warning(f"Skipping template with invalid regex: {template_data['name']}")
                continue
            
            # Create Template object
            template = Template.from_dict(template_data)
            valid_templates.append(template)
            
        except Exception as e:
            self.log_warning(f"Error validating template {template_data.get('name', 'unknown')}: {str(e)}")
            continue
    
    return valid_templates
```

##### Step 5: Priority-Based Sorting
```python
def _sort_templates_by_priority(self, templates: List[Template]) -> List[Template]:
    """Sort templates by priority (1 = highest, 999 = lowest)"""
    return sorted(templates, key=lambda t: t.priority)
```

### Alternative Flows (Error Handling)

#### AF1: Template File Missing
```python
def _handle_missing_template_file(self) -> List[Template]:
    """AF1: Template File Missing"""
    self.log_info("Template file not found, loading default templates")
    self.templates = self.default_templates.copy()
    return self.templates
```

#### AF2: Invalid JSON Format
```python
def _handle_invalid_json(self, template_path: str) -> List[Template]:
    """AF2: Invalid JSON Format"""
    self.log_error(f"Invalid JSON format in {template_path}, falling back to defaults")
    self.templates = self.default_templates.copy()
    return self.templates
```

#### AF3: Invalid Template Structure
```python
# Step 4a. Required field missing in template
# - System skips invalid template
# - System logs validation error
# - System continues with valid templates
# - Continue with remaining templates
```

### Main Method 2: `export_template_diagram()`

**Purpose**: Main flow for UC-02.2 - Export Template Diagram

```python
def export_template_diagram(self, output_path: str = "template_seq_diagram.md") -> bool:
    """
    Main flow for UC-02.2: Export Template Diagram
    
    Steps:
    1. User initiates template export
    2. Generate Mermaid graph structure
    3. Iterate through loaded templates
    4. Create nodes for each template
    5. Add pattern information
    6. Write diagram to markdown file
    7. Confirm successful export
    """
```

#### Diagram Generation Process:

##### Step 1: Mermaid Structure Generation
```python
def _generate_mermaid_structure(self) -> str:
    """Generate Mermaid graph structure header"""
    return """# Template Configuration Diagram

```mermaid
graph TD
    A[Template System] --> B[Loaded Templates]
    
"""
```

##### Step 2: Template Node Creation
```python
def _create_template_nodes(self) -> str:
    """Create nodes for each template with pattern information"""
    content = ""
    
    for i, template in enumerate(self.templates):
        node_id = f"T{i+1}"
        content += f"    B --> {node_id}[{template.name}]
    {node_id} --> |Priority: {template.priority}| P{i+1}[Pattern: {template.pattern[:50]}...]
    {node_id} --> |Mapping| M{i+1}[{', '.join(template.sequence_mapping.keys())}]
    
"
    
    content += "```\n\n## Template Details\n\n"
    
    for template in self.templates:
        content += f"### {template.name}\n"
        content += f"- **Priority**: {template.priority}\n"
        content += f"- **Pattern**: `{template.pattern}`\n"
        content += f"- **Sequence Mapping**: {json.dumps(template.sequence_mapping, indent=2)}\n"
        if template.description:
            content += f"- **Description**: {template.description}\n"
        content += "\n"
    
    return content
```

##### Step 3: File Writing with Error Handling
```python
def _write_diagram_to_file(self, output_path: str, content: str) -> bool:
    """Write diagram content to file"""
    try:
        # Check write permissions
        output_dir = Path(output_path).parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        return True
        
    except PermissionError:
        # AF1: Write Permission Denied
        self.log_warning(f"Cannot write to {output_path}, attempting alternate location")
        return self._handle_write_permission_denied(content)
```

#### AF1: Write Permission Denied
```python
def _handle_write_permission_denied(self, content: str) -> bool:
    """AF1: Write Permission Denied - provide diagram to stdout"""
    self.log_info("Providing diagram to stdout due to permission issues")
    print("\n" + "="*50)
    print("TEMPLATE DIAGRAM")
    print("="*50)
    print(content)
    print("="*50)
    return True
```

### Default Templates: `_get_default_templates()`

**Purpose**: Provides default automotive camera system templates

```python
def _get_default_templates(self) -> List[Template]:
    """Get default templates for automotive camera system"""
    return [
        Template(
            name="Camera Service Start",
            pattern=r"(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(\w+)\s+(\w+):\s*(.*CameraService.*start.*)",
            sequence_mapping={
                "from": "System",
                "to": "CameraService",
                "message": "Service Start"
            },
            priority=1,
            description="Camera service initialization"
        ),
        # ... 14 more templates
    ]
```

### Business Rules Implementation

#### BR1: Templates must contain: name, pattern, sequence_mapping
```python
def _has_required_fields(self, template_data: Dict[str, Any]) -> bool:
    """Check if template has all required fields"""
    required_fields = ['name', 'pattern', 'sequence_mapping']
    return all(field in template_data for field in required_fields)
```

#### BR2: Priority values range from 1 (highest) to 999 (lowest)
```python
def validate_business_rules(self) -> Dict[str, Any]:
    # BR2: Check priority ranges
    for template in self.templates:
        if not (1 <= template.priority <= 999):
            validation_result['errors'].append(f"Template {template.name} has invalid priority: {template.priority}")
            validation_result['valid'] = False
```

#### BR3: Duplicate template names are not allowed
```python
# BR3: Check for duplicate names
names = [t.name for t in self.templates]
if len(names) != len(set(names)):
    validation_result['errors'].append("Duplicate template names found")
    validation_result['valid'] = False
```

#### BR4: Regex patterns must be valid and compilable
```python
def _validate_regex_pattern(self, pattern: str) -> bool:
    """Validate that regex pattern is compilable"""
    try:
        re.compile(pattern)
        return True
    except re.error:
        return False
```

### Utility Methods

#### Template Retrieval:
```python
def get_template_by_name(self, name: str) -> Optional[Template]:
    """Get template by name"""
    for template in self.templates:
        if template.name == name:
            return template
    return None

def get_templates_by_priority(self, min_priority: int = 1, max_priority: int = 999) -> List[Template]:
    """Get templates within priority range"""
    return [t for t in self.templates if min_priority <= t.priority <= max_priority]
```

---

## 📊 Template Configuration: `templates.json`

### Purpose:
Contains 15 pre-configured templates for automotive camera systems.

### Template Structure:
```json
{
  "templates": [
    {
      "name": "Camera Service Start",
      "pattern": "(\\d{2}-\\d{2}\\s+\\d{2}:\\d{2}:\\d{2}\\.\\d{3})\\s+(\\w+)\\s+(\\w+):\\s*(.*CameraService.*start.*)",
      "sequence_mapping": {
        "from": "System",
        "to": "CameraService",
        "message": "Service Start"
      },
      "priority": 1,
      "description": "Camera service initialization"
    }
  ]
}
```

### Template Categories:

#### 1. **Service Lifecycle Templates** (Priority 1-3)
- Camera Service Start
- Camera Activity Launch
- Camera HAL Connection

#### 2. **Vehicle Integration Templates** (Priority 4)
- Vehicle Gear Change

#### 3. **Error Handling Templates** (Priority 5)
- Camera Error

#### 4. **Stream Management Templates** (Priority 6-7)
- Camera Stream Start
- Camera Stream Stop

#### 5. **Display Integration Templates** (Priority 8)
- Display Service Update

#### 6. **Capture Operations Templates** (Priority 9-10)
- Camera Capture Request
- Camera Capture Complete

#### 7. **Service Binding Templates** (Priority 11-12)
- Service Binding
- Service Unbinding

#### 8. **Activity Lifecycle Templates** (Priority 13)
- Activity Lifecycle

#### 9. **Permission Management Templates** (Priority 14)
- Permission Request

#### 10. **Hardware Integration Templates** (Priority 15)
- Hardware Initialization

### Pattern Explanation:

#### Regex Pattern Components:
```regex
(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(\w+)\s+(\w+):\s*(.*CameraService.*start.*)
│                    │    │    │    │
│                    │    │    │    └─ Message content
│                    │    │    └─ Tag
│                    │    └─ Log Level
│                    └─ Timestamp
└─ Group 1: Timestamp
```

#### Sequence Mapping:
```json
{
  "from": "System",           // Source entity
  "to": "CameraService",      // Target entity
  "message": "Service Start"  // Event message
}
```

---

## 🧪 Testing and Usage

### Basic Usage:
```python
from template_sequence.template_sequence_module import TemplateSequenceModule

# Initialize module
config = {'debug': True}
template_module = TemplateSequenceModule(config)

# Load templates
templates = template_module.load_template_configuration()
print(f"Loaded {len(templates)} templates")

# Export diagram
success = template_module.export_template_diagram("template_diagram.md")
print(f"Export successful: {success}")
```

### Custom Template File:
```python
# Load custom templates
templates = template_module.load_template_configuration("custom_templates.json")
```

### Template Retrieval:
```python
# Get specific template
camera_template = template_module.get_template_by_name("Camera Service Start")

# Get high priority templates
high_priority = template_module.get_templates_by_priority(1, 5)
```

### Validation:
```python
validation = template_module.validate_business_rules()
if validation['valid']:
    print("All templates valid")
else:
    print(f"Validation errors: {validation['errors']}")
```

---

## 🔧 Configuration Options

### Default Configuration:
```python
config = {
    'template_file': 'templates.json',
    'debug': False
}
```

### Custom Configuration:
```python
config = {
    'template_file': 'custom_templates.json',
    'debug': True
}
template_module = TemplateSequenceModule(config)
```

---

## 📈 Performance Characteristics

### Template Loading:
- **Small Files**: Direct JSON parsing
- **Large Files**: Memory-efficient processing
- **Validation**: Fast regex compilation checking

### Diagram Generation:
- **Small Template Sets**: Direct generation
- **Large Template Sets**: Efficient node creation
- **Output**: Markdown with embedded Mermaid

### Memory Usage:
- **Templates**: Stored in memory for fast access
- **Diagrams**: Generated on-demand
- **Cleanup**: No persistent storage

---

## 🛡️ Error Handling

### Template Loading Errors:
- **File Not Found**: Fallback to default templates
- **Invalid JSON**: Clear error messages with fallback
- **Invalid Templates**: Skip invalid, continue with valid

### Diagram Export Errors:
- **Permission Denied**: Output to stdout
- **Invalid Path**: Create directory structure
- **Write Failure**: Graceful error handling

---

## 🔄 Integration with Other Modules

### Input to QuickCompareModule:
```python
# TemplateSequenceModule provides templates
templates = template_module.load_template_configuration()

# QuickCompareModule uses templates for matching
events = quick_compare_module.generate_sequence_events(log_entries, templates)
```

### Template Validation:
```python
# Validate templates before use
validation = template_module.validate_business_rules()
if validation['valid']:
    # Use templates safely
    templates = template_module.templates
```

---

## 📊 Generated Diagram Output

### Mermaid Graph Structure:
```mermaid
graph TD
    A[Template System] --> B[Loaded Templates]
    B --> T1[Camera Service Start]
    T1 --> |Priority: 1| P1[Pattern: (\d{2}-\d{2}\s+\d{2}:...]
    T1 --> |Mapping| M1[from, to, message]
```

### Markdown Documentation:
```markdown
## Template Details

### Camera Service Start
- **Priority**: 1
- **Pattern**: `(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(\w+)\s+(\w+):\s*(.*CameraService.*start.*)`
- **Sequence Mapping**: {
  "from": "System",
  "to": "CameraService",
  "message": "Service Start"
}
- **Description**: Camera service initialization
```

---

This TemplateSequenceModule provides a robust foundation for template management with comprehensive validation, error handling, and visual documentation generation. It serves as the configuration backbone for the entire log analysis system.
