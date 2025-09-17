"""
TemplateSequenceModule - UC-02.1 & UC-02.2
Handles template configuration loading and diagram export
"""

import json
import re
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "development_folder" / "dev_and_test"))
from data_models import BaseModule, Template


class TemplateSequenceModule(BaseModule):
    """
    TemplateSequenceModule handles template configuration and visualization
    Implements UC-02.1: Load Template Configuration
    Implements UC-02.2: Export Template Diagram
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.templates: List[Template] = []
        self.template_file_path = self.config.get('template_file', 'templates.json')
        self.default_templates = self._get_default_templates()
    
    def load_template_configuration(self, template_file: Optional[str] = None) -> List[Template]:
        """
        Main flow for UC-02.1: Load Template Configuration
        
        Args:
            template_file: Optional path to template file
            
        Returns:
            List of loaded templates
        """
        template_path = template_file or self.template_file_path
        self.log_info(f"Loading template configuration from: {template_path}")
        
        try:
            # Step 1: Attempt to load template configuration file
            if self._template_file_exists(template_path):
                # Step 2: Validate JSON structure
                if self._validate_json_structure(template_path):
                    # Step 3: Parse template definitions
                    templates_data = self._parse_template_definitions(template_path)
                    
                    # Step 4: Validate each template's required fields
                    valid_templates = self._validate_template_fields(templates_data)
                    
                    # Step 5: Sort templates by priority
                    self.templates = self._sort_templates_by_priority(valid_templates)
                    
                    # Step 6: Store templates in memory
                    self.log_info(f"Loaded {len(self.templates)} templates successfully")
                    
                    # Step 7: Report number of loaded templates
                    return self.templates
                else:
                    # AF2: Invalid JSON Format
                    return self._handle_invalid_json(template_path)
            else:
                # AF1: Template File Missing
                return self._handle_missing_template_file()
                
        except Exception as e:
            self.log_error(f"Error loading template configuration: {str(e)}")
            return self._handle_missing_template_file()
    
    def _template_file_exists(self, template_path: str) -> bool:
        """Check if template file exists"""
        return Path(template_path).exists()
    
    def _validate_json_structure(self, template_path: str) -> bool:
        """Validate JSON structure of template file"""
        try:
            with open(template_path, 'r', encoding='utf-8') as file:
                json.load(file)
            return True
        except json.JSONDecodeError as e:
            self.log_error(f"JSON parsing failed: {str(e)}")
            return False
        except Exception as e:
            self.log_error(f"Error reading template file: {str(e)}")
            return False
    
    def _parse_template_definitions(self, template_path: str) -> List[Dict[str, Any]]:
        """Parse template definitions from JSON file"""
        with open(template_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        if 'templates' not in data:
            raise ValueError("Template file must contain 'templates' array")
        
        return data['templates']
    
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
    
    def _has_required_fields(self, template_data: Dict[str, Any]) -> bool:
        """Check if template has all required fields"""
        required_fields = ['name', 'pattern', 'sequence_mapping']
        return all(field in template_data for field in required_fields)
    
    def _validate_regex_pattern(self, pattern: str) -> bool:
        """Validate that regex pattern is compilable"""
        try:
            re.compile(pattern)
            return True
        except re.error:
            return False
    
    def _sort_templates_by_priority(self, templates: List[Template]) -> List[Template]:
        """Sort templates by priority (1 = highest, 999 = lowest)"""
        return sorted(templates, key=lambda t: t.priority)
    
    def _handle_missing_template_file(self) -> List[Template]:
        """AF1: Template File Missing"""
        self.log_info("Template file not found, loading default templates")
        self.templates = self.default_templates.copy()
        return self.templates
    
    def _handle_invalid_json(self, template_path: str) -> List[Template]:
        """AF2: Invalid JSON Format"""
        self.log_error(f"Invalid JSON format in {template_path}, falling back to defaults")
        self.templates = self.default_templates.copy()
        return self.templates
    
    def export_template_diagram(self, output_path: str = "template_seq_diagram.md") -> bool:
        """
        Main flow for UC-02.2: Export Template Diagram
        
        Args:
            output_path: Path for output diagram file
            
        Returns:
            True if successful, False otherwise
        """
        self.log_info(f"Exporting template diagram to: {output_path}")
        
        try:
            # Step 1: User initiates template export
            if not self.templates:
                self.log_warning("No templates loaded, loading defaults first")
                self.load_template_configuration()
            
            # Step 2: Generate Mermaid graph structure
            mermaid_content = self._generate_mermaid_structure()
            
            # Step 3: Iterate through loaded templates
            # Step 4: Create nodes for each template
            # Step 5: Add pattern information
            mermaid_content += self._create_template_nodes()
            
            # Step 6: Write diagram to markdown file
            success = self._write_diagram_to_file(output_path, mermaid_content)
            
            if success:
                # Step 7: Confirm successful export
                self.log_info(f"Template diagram exported successfully to {output_path}")
                return True
            else:
                return False
                
        except Exception as e:
            self.log_error(f"Error exporting template diagram: {str(e)}")
            return False
    
    def _generate_mermaid_structure(self) -> str:
        """Generate Mermaid graph structure header"""
        return """# Template Configuration Diagram

```mermaid
graph TD
    A[Template System] --> B[Loaded Templates]
    
"""
    
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
        except Exception as e:
            self.log_error(f"Error writing diagram file: {str(e)}")
            return False
    
    def _handle_write_permission_denied(self, content: str) -> bool:
        """AF1: Write Permission Denied - provide diagram to stdout"""
        self.log_info("Providing diagram to stdout due to permission issues")
        print("\n" + "="*50)
        print("TEMPLATE DIAGRAM")
        print("="*50)
        print(content)
        print("="*50)
        return True
    
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
            Template(
                name="Camera Activity Launch",
                pattern=r"(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(\w+)\s+(\w+):\s*(.*ActivityManager.*Starting.*Camera.*)",
                sequence_mapping={
                    "from": "ActivityManager",
                    "to": "CameraActivity",
                    "message": "Start Activity"
                },
                priority=2,
                description="Camera activity launch"
            ),
            Template(
                name="Camera HAL Connection",
                pattern=r"(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(\w+)\s+(\w+):\s*(.*CameraHAL.*connect.*)",
                sequence_mapping={
                    "from": "CameraService",
                    "to": "CameraHAL",
                    "message": "HAL Connection"
                },
                priority=3,
                description="Camera HAL connection"
            ),
            Template(
                name="Vehicle Gear Change",
                pattern=r"(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(\w+)\s+(\w+):\s*(.*VehicleHAL.*gear.*change.*)",
                sequence_mapping={
                    "from": "VehicleHAL",
                    "to": "CameraApp",
                    "message": "Gear Change Event"
                },
                priority=4,
                description="Vehicle gear change event"
            ),
            Template(
                name="Camera Error",
                pattern=r"(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(\w+)\s+(\w+):\s*(.*Camera.*error.*)",
                sequence_mapping={
                    "from": "CameraHAL",
                    "to": "CameraService",
                    "message": "Error Notification"
                },
                priority=5,
                description="Camera error handling"
            )
        ]
    
    def get_template_by_name(self, name: str) -> Optional[Template]:
        """Get template by name"""
        for template in self.templates:
            if template.name == name:
                return template
        return None
    
    def get_templates_by_priority(self, min_priority: int = 1, max_priority: int = 999) -> List[Template]:
        """Get templates within priority range"""
        return [t for t in self.templates if min_priority <= t.priority <= max_priority]
    
    def validate_business_rules(self) -> Dict[str, Any]:
        """
        Validate business rules for templates
        BR1: Templates must contain: name, pattern, sequence_mapping
        BR2: Priority values range from 1 (highest) to 999 (lowest)
        BR3: Duplicate template names are not allowed
        BR4: Regex patterns must be valid and compilable
        """
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # BR3: Check for duplicate names
        names = [t.name for t in self.templates]
        if len(names) != len(set(names)):
            validation_result['errors'].append("Duplicate template names found")
            validation_result['valid'] = False
        
        # BR2: Check priority ranges
        for template in self.templates:
            if not (1 <= template.priority <= 999):
                validation_result['errors'].append(f"Template {template.name} has invalid priority: {template.priority}")
                validation_result['valid'] = False
        
        # BR4: Validate regex patterns
        for template in self.templates:
            if not self._validate_regex_pattern(template.pattern):
                validation_result['errors'].append(f"Template {template.name} has invalid regex pattern")
                validation_result['valid'] = False
        
        return validation_result


# Example usage and testing
if __name__ == "__main__":
    # Test the TemplateSequenceModule
    config = {'debug': True}
    template_module = TemplateSequenceModule(config)
    
    # Test template loading
    templates = template_module.load_template_configuration()
    print(f"Loaded {len(templates)} templates")
    
    # Test template export
    success = template_module.export_template_diagram("test_template_diagram.md")
    print(f"Template export successful: {success}")
    
    # Test validation
    validation = template_module.validate_business_rules()
    print(f"Validation result: {validation}")
    
    # Test template retrieval
    camera_template = template_module.get_template_by_name("Camera Service Start")
    if camera_template:
        print(f"Found template: {camera_template.name}")
    
    high_priority_templates = template_module.get_templates_by_priority(1, 2)
    print(f"High priority templates: {len(high_priority_templates)}")
