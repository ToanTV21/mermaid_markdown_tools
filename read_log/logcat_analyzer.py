#!/usr/bin/env python3
"""
Configurable Android Automotive CameraApp Log Analyzer
Supports custom patterns and template comparison for break point detection
"""

import re
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum

class LogLevel(Enum):
    VERBOSE = "V"
    DEBUG = "D"
    INFO = "I"
    WARN = "W"
    ERROR = "E"
    FATAL = "F"

@dataclass
class LogEntry:
    timestamp: str
    level: LogLevel
    tag: str
    pid: str
    message: str
    raw_line: str

@dataclass
class MethodCall:
    timestamp: str
    class_name: str
    method_name: str
    level: LogLevel
    message: str
    thread_info: str = ""
    pattern_type: str = ""

@dataclass
class FlowStep:
    step_id: str
    participants: List[str]
    description: str
    expected_pattern: str
    critical: bool = True
    found: bool = False

class ConfigurableLogAnalyzer:
    def __init__(self, config_file: str = "camera_patterns.yaml"):
        self.config_file = config_file
        self.config = self._load_config()
        self.flow_graph = {}  # Flow prediction graph from template
        self.detected_calls = []  # Track detected method calls
        self.missing_predictions = []  # Track predicted but missing calls
        
        # Compile patterns from config
        self.method_patterns = {}
        self.tag_filters = set()
        self.compile_patterns()
        
    def _load_config(self) -> dict:
        """Load configuration from YAML file"""
        config_path = Path(self.config_file)
        if not config_path.exists():
            self._create_default_config()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _create_default_config(self):
        """Create default configuration file"""
        default_config = {
            'log_parsing': {
                'log_pattern': r'(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(\d+)\s+(\d+)\s+([VDIWEF])\s+([^:]+):\s*(.*)',
                'tag_filters': [
                    'CameraApp', 'CameraService', 'CameraHAL', 
                    'CameraProvider', 'AutoCamera', 'IVICamera'
                ]
            },
            'method_patterns': {
                'camera_init': {
                    'pattern': r'(CameraManager|CameraService)\.?(init|initialize|create).*',
                    'participants': ['CameraApp', 'CameraService'],
                    'critical': True
                },
                'camera_open': {
                    'pattern': r'(Camera|CameraDevice)\.?(open|connect).*',
                    'participants': ['CameraApp', 'CameraHAL'],
                    'critical': True
                },
                'camera_configure': {
                    'pattern': r'(Camera|CameraDevice)\.?(configure|setup|createSession).*',
                    'participants': ['CameraApp', 'CameraHAL'],
                    'critical': True
                },
                'preview_start': {
                    'pattern': r'(Preview|Stream)\.?(start|begin|create).*',
                    'participants': ['CameraApp', 'CameraService'],
                    'critical': True
                },
                'preview_stop': {
                    'pattern': r'(Preview|Stream)\.?(stop|end|destroy).*',
                    'participants': ['CameraApp', 'CameraService'],
                    'critical': False
                },
                'camera_close': {
                    'pattern': r'(Camera|CameraDevice)\.?(close|disconnect|release).*',
                    'participants': ['CameraApp', 'CameraHAL'],
                    'critical': True
                },
                'error_pattern': {
                    'pattern': r'.*(error|exception|failed|timeout|crash).*',
                    'participants': ['System'],
                    'critical': True
                },
                'hal_callback': {
                    'pattern': r'(HAL|Provider).*callback.*',
                    'participants': ['CameraHAL', 'CameraApp'],
                    'critical': False
                }
            },
            'automotive_specific': {
                'gear_change': {
                    'pattern': r'.*(gear|drive|park|reverse).*',
                    'participants': ['VehicleHAL', 'CameraApp'],
                    'critical': False
                },
                'display_change': {
                    'pattern': r'.*(display|screen|surface).*change.*',
                    'participants': ['DisplayService', 'CameraApp'],
                    'critical': False
                },
                'power_management': {
                    'pattern': r'.*(power|sleep|wake|suspend).*',
                    'participants': ['PowerManager', 'CameraApp'],
                    'critical': True
                }
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
        
        return default_config
    
    def compile_patterns(self):
        """Compile regex patterns from config"""
        # Combine method patterns and automotive patterns
        all_patterns = {}
        all_patterns.update(self.config.get('method_patterns', {}))
        all_patterns.update(self.config.get('automotive_specific', {}))
        
        for pattern_name, pattern_config in all_patterns.items():
            self.method_patterns[pattern_name] = {
                'regex': re.compile(pattern_config['pattern'], re.IGNORECASE),
                'participants': pattern_config.get('participants', []),
                'critical': pattern_config.get('critical', True)
            }
        
        # Load tag filters
        self.tag_filters = set(self.config['log_parsing']['tag_filters'])
    
    def parse_logcat(self, log_file: str) -> List[LogEntry]:
        """Parse logcat file using configured patterns"""
        entries = []
        log_pattern = re.compile(self.config['log_parsing']['log_pattern'])
        
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                match = log_pattern.match(line)
                if match:
                    timestamp, pid, tid, level_str, tag, message = match.groups()
                    
                    # Filter by configured tags or message content
                    if (any(filter_tag.lower() in tag.lower() for filter_tag in self.tag_filters) or
                        any(filter_tag.lower() in message.lower() for filter_tag in self.tag_filters)):
                        
                        entry = LogEntry(
                            timestamp=timestamp,
                            level=LogLevel(level_str),
                            tag=tag.strip(),
                            pid=f"{pid}:{tid}",
                            message=message.strip(),
                            raw_line=line
                        )
                        entries.append(entry)
        
        return entries
    
    def extract_method_calls(self, entries: List[LogEntry]) -> List[MethodCall]:
        """Extract method calls using configured patterns"""
        method_calls = []
        
        for entry in entries:
            for pattern_name, pattern_info in self.method_patterns.items():
                match = pattern_info['regex'].search(entry.message)
                if match:
                    # Extract class and method if available
                    parts = entry.message.split('.')
                    class_name = parts[0] if len(parts) > 1 else entry.tag
                    method_name = pattern_name
                    
                    method_call = MethodCall(
                        timestamp=entry.timestamp,
                        class_name=class_name,
                        method_name=method_name,
                        level=entry.level,
                        message=entry.message,
                        thread_info=entry.pid,
                        pattern_type=pattern_name
                    )
                    method_calls.append(method_call)
                    break
        
    def predict_next_calls(self, current_call: MethodCall) -> List[dict]:
        """Predict next expected calls based on template flow graph"""
        predictions = []
        current_class = current_call.class_name
        
        if current_class in self.flow_graph:
            for next_step in self.flow_graph[current_class]:
                predictions.append({
                    'expected_class': next_step['next_class'],
                    'expected_method': next_step['expected_method'],
                    'description': next_step['description'],
                    'step_id': next_step['step_id'],
                    'current_call': current_call
                })
        
        return predictions
    
    def analyze_flow_gaps(self, method_calls: List[MethodCall]) -> List[dict]:
        """Analyze gaps in flow based on template predictions"""
        flow_gaps = []
        
        for i, call in enumerate(method_calls):
            predictions = self.predict_next_calls(call)
            
            if predictions:
                # Look for expected next calls in subsequent logs
                next_calls = method_calls[i+1:i+10]  # Check next 10 calls
                
                for prediction in predictions:
                    found = False
                    for next_call in next_calls:
                        # Match by class name or method pattern
                        if (prediction['expected_class'].lower() in next_call.class_name.lower() or
                            prediction['expected_method'].lower() in next_call.method_name.lower() or
                            prediction['expected_method'].lower() in next_call.message.lower()):
                            found = True
                            break
                    
                    if not found:
                        flow_gaps.append({
                            'after_call': call,
                            'missing_class': prediction['expected_class'],
                            'missing_method': prediction['expected_method'],
                            'expected_description': prediction['description'],
                            'step_id': prediction['step_id'],
                            'timestamp': call.timestamp
                        })
        
        return flow_gaps
    
    def load_template(self, template_file: str) -> List[FlowStep]:
        """Load expected flow template and build flow graph"""
        if not Path(template_file).exists():
            return []
        
        flow_steps = []
        self.flow_graph = {}  # Build flow prediction graph
        
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Parse mermaid sequence diagram
            sequence_pattern = re.compile(r'(\w+)->>(\w+):\s*(.+)')
            note_pattern = re.compile(r'Note over.*?:\s*(.+)')
            
            step_id = 1
            previous_step = None
            
            for line in content.split('\n'):
                line = line.strip()
                
                seq_match = sequence_pattern.search(line)
                if seq_match:
                    from_part, to_part, description = seq_match.groups()
                    
                    # Extract method/function name from description
                    method_pattern = r'(\w+)\(\)|(\w+)\s*\(|(\w+)
    
    def compare_with_template(self, method_calls: List[MethodCall], 
                             template_steps: List[FlowStep]) -> List[FlowStep]:
        """Compare actual calls with template and mark found/missing steps"""
        
        for step in template_steps:
            # Check if this step was found in actual logs
            for call in method_calls:
                if (any(keyword in call.method_name.lower() 
                       for keyword in step.expected_pattern.split()) or
                    any(keyword in call.message.lower() 
                       for keyword in step.expected_pattern.split())):
                    step.found = True
                    break
        
        return template_steps
    
    def generate_comparison_markdown(self, entries: List[LogEntry], 
                                   method_calls: List[MethodCall],
                                   template_comparison: List[FlowStep],
                                   output_file: str, template_type: str = "overview"):
        """Generate markdown with template comparison and flow predictions"""
        
        # Analyze flow gaps if template is loaded
        flow_gaps = []
        if hasattr(self, 'flow_graph') and self.flow_graph:
            flow_gaps = self.analyze_flow_gaps(method_calls)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# CameraApp Flow Analysis - {template_type.title()}\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Template**: {template_type}\n")
            f.write(f"**Total Steps Expected**: {len(template_comparison)}\n")
            
            found_steps = sum(1 for step in template_comparison if step.found)
            f.write(f"**Steps Found**: {found_steps}/{len(template_comparison)}\n")
            f.write(f"**Success Rate**: {found_steps/len(template_comparison)*100:.1f}%\n")
            f.write(f"**Flow Gaps Detected**: {len(flow_gaps)}\n\n")
            
            # Flow gaps analysis - NEW SECTION
            if flow_gaps:
                f.write("## 🔍 Flow Gap Analysis (Template-Based Predictions)\n\n")
                f.write("| After Call | Missing Class | Expected Method | Timestamp |\n")
                f.write("|------------|---------------|-----------------|------------|\n")
                
                for gap in flow_gaps[:15]:  # Show first 15 gaps
                    f.write(f"| {gap['after_call'].class_name}:{gap['after_call'].method_name} | "
                           f"❌ **{gap['missing_class']}** | {gap['missing_method']} | {gap['timestamp']} |\n")
                f.write("\n")
                
                f.write("### 🎯 Predicted Next Calls\n\n")
                for gap in flow_gaps[:10]:
                    f.write(f"- After `{gap['after_call'].class_name}:{gap['after_call'].method_name}` "
                           f"→ Expected: `{gap['missing_class']}:{gap['missing_method']}`\n")
                f.write("\n")
            
            # Flow status
            f.write("## 📊 Flow Execution Status\n\n")
            f.write("| Step | Status | Description | Critical |\n")
            f.write("|------|--------|-------------|----------|\n")
            
            for step in template_comparison:
                status_icon = "✅" if step.found else "❌"
                critical_icon = "🔴" if step.critical else "🟡"
                f.write(f"| {step.step_id} | {status_icon} | {step.description} | {critical_icon} |\n")
            
            # Generate sequence diagram with X marks and predictions
            f.write("\n## 🔄 Actual vs Expected Flow\n\n")
            f.write("```mermaid\n")
            f.write("sequenceDiagram\n")
            
            # Extract participants
            all_participants = set()
            for step in template_comparison:
                all_participants.update(step.participants)
            
            for participant in sorted(all_participants):
                f.write(f"    participant {participant}\n")
            f.write("\n")
            
            # Generate sequence with X marks for missing steps
            for step in template_comparison:
                if len(step.participants) >= 2:
                    from_part, to_part = step.participants[0], step.participants[1]
                    if step.found:
                        f.write(f"    {from_part}->>{to_part}: {step.description}\n")
                    else:
                        f.write(f"    {from_part}-x{to_part}: ❌ {step.description}\n")
                        f.write(f"    Note over {from_part},{to_part}: MISSING - Check logs\n")
            
            f.write("```\n\n")
            
            # Missing critical steps analysis
            missing_critical = [s for s in template_comparison if not s.found and s.critical]
            if missing_critical:
                f.write("## 🚨 Critical Missing Steps\n\n")
                for step in missing_critical:
                    f.write(f"- **{step.step_id}**: {step.description}\n")
                f.write("\n")
            
            # Debug recommendations with template-based suggestions
            f.write("## 🔧 Debug Recommendations\n\n")
            if flow_gaps:
                f.write("### Template-Based Predictions:\n")
                unique_missing_classes = set(gap['missing_class'] for gap in flow_gaps)
                for missing_class in list(unique_missing_classes)[:5]:
                    f.write(f"1. **Add logging to `{missing_class}`** - Not detected in logs\n")
                f.write("\n")
            
            if missing_critical:
                f.write("### Priority Issues:\n")
                for step in missing_critical:
                    f.write(f"1. Check logs for patterns related to: `{step.expected_pattern}`\n")
                f.write("\n")
            
            f.write("### Next Actions:\n")
            f.write("1. Focus on first missing critical step\n")
            f.write("2. Add more detailed logging around missing steps\n")
            f.write("3. Check template predictions for expected call flow\n")
            f.write("4. Verify service binding and AIDL communications\n")

def create_template_files():
    """Create template files for automotive camera flows"""
    
    # Overview template
    overview_template = '''# Camera Flow Overview Template

```mermaid
sequenceDiagram
    participant User
    participant CameraApp
    participant CameraService
    participant CameraHAL
    participant Hardware
    
    User->>CameraApp: Launch App
    CameraApp->>CameraService: Initialize Camera Manager
    CameraService->>CameraHAL: Connect to HAL
    CameraHAL->>Hardware: Initialize Hardware
    Hardware-->>CameraHAL: Hardware Ready
    CameraHAL-->>CameraService: HAL Ready
    CameraService-->>CameraApp: Camera Available
    
    User->>CameraApp: Open Camera
    CameraApp->>CameraService: Open Camera Device
    CameraService->>CameraHAL: Camera Open
    CameraHAL->>Hardware: Power On Camera
    Hardware-->>CameraHAL: Camera Ready
    CameraHAL-->>CameraService: Device Opened
    CameraService-->>CameraApp: Camera Opened
    
    CameraApp->>CameraService: Configure Session
    CameraService->>CameraHAL: Create Capture Session
    CameraApp->>CameraService: Start Preview
    CameraService->>CameraHAL: Start Preview Stream
    CameraHAL->>Hardware: Start Streaming
    
    Note over CameraApp,Hardware: Preview Running
    
    User->>CameraApp: Close Camera
    CameraApp->>CameraService: Close Camera
    CameraService->>CameraHAL: Release Resources
    CameraHAL->>Hardware: Power Down
```
'''
    
    # Detail template
    detail_template = '''# Camera Flow Detail Template

```mermaid
sequenceDiagram
    participant User
    participant CameraApp
    participant CameraManager
    participant CameraService
    participant CameraProvider
    participant CameraHAL
    participant VehicleHAL
    participant Hardware
    
    Note over User,Hardware: App Launch Phase
    User->>CameraApp: Launch CameraApp
    CameraApp->>CameraManager: getCameraManager()
    CameraManager->>CameraService: bindService()
    CameraService->>CameraProvider: connectToProvider()
    CameraProvider->>CameraHAL: HIDL Connect
    CameraHAL->>Hardware: HAL Initialize
    
    Note over User,Hardware: Vehicle State Check
    CameraApp->>VehicleHAL: Check Gear Position
    VehicleHAL-->>CameraApp: Gear Status
    CameraApp->>VehicleHAL: Register Gear Listener
    
    Note over User,Hardware: Camera Discovery
    CameraApp->>CameraManager: getCameraIdList()
    CameraManager->>CameraService: getCameraList()
    CameraService->>CameraProvider: getCameraDeviceInterface()
    CameraProvider-->>CameraService: Camera List
    CameraService-->>CameraManager: Available Cameras
    CameraManager-->>CameraApp: Camera IDs
    
    Note over User,Hardware: Camera Open Sequence
    User->>CameraApp: Select Camera
    CameraApp->>CameraManager: openCamera()
    CameraManager->>CameraService: connectDevice()
    CameraService->>CameraProvider: openCameraDevice()
    CameraProvider->>CameraHAL: camera_device_open()
    CameraHAL->>Hardware: Power On & Initialize
    Hardware-->>CameraHAL: Init Complete
    CameraHAL-->>CameraProvider: Device Ready
    CameraProvider-->>CameraService: Camera Opened
    CameraService-->>CameraManager: Device Available
    CameraManager-->>CameraApp: onOpened() Callback
    
    Note over User,Hardware: Session Configuration
    CameraApp->>CameraManager: createCaptureSession()
    CameraManager->>CameraService: configureStreams()
    CameraService->>CameraProvider: configureStreams()
    CameraProvider->>CameraHAL: configure_streams()
    CameraHAL->>Hardware: Configure Pipeline
    Hardware-->>CameraHAL: Config Complete
    CameraHAL-->>CameraProvider: Streams Configured
    CameraProvider-->>CameraService: Configuration Done
    CameraService-->>CameraManager: Session Ready
    CameraManager-->>CameraApp: onConfigured() Callback
    
    Note over User,Hardware: Preview Start
    CameraApp->>CameraManager: setRepeatingRequest()
    CameraManager->>CameraService: capture()
    CameraService->>CameraProvider: processCaptureRequest()
    CameraProvider->>CameraHAL: process_capture_request()
    CameraHAL->>Hardware: Start Streaming
    Hardware-->>CameraHAL: Frame Data
    CameraHAL-->>CameraProvider: Frame Ready
    CameraProvider-->>CameraService: Frame Available
    CameraService-->>CameraManager: Frame Callback
    CameraManager-->>CameraApp: onImageAvailable()
    
    Note over User,Hardware: Running State
    loop Frame Processing
        Hardware-->>CameraApp: Continuous Frames
    end
    
    Note over User,Hardware: Cleanup Sequence  
    User->>CameraApp: Exit App
    CameraApp->>CameraManager: close()
    CameraManager->>CameraService: disconnect()
    CameraService->>CameraProvider: close()
    CameraProvider->>CameraHAL: camera_device_close()
    CameraHAL->>Hardware: Power Down
    Hardware-->>CameraHAL: Shutdown Complete
```
'''
    
    # Write template files
    with open('cameraFlow_overview.md', 'w', encoding='utf-8') as f:
        f.write(overview_template)
    
    with open('cameraFlow_detail.md', 'w', encoding='utf-8') as f:
        f.write(detail_template)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Configurable Android Automotive CameraApp Log Analyzer')
    parser.add_argument('input_log', help='Input logcat file (txt format)')
    parser.add_argument('-c', '--config', default='camera_patterns.yaml', 
                       help='Configuration file (default: camera_patterns.yaml)')
    parser.add_argument('-t', '--template', help='Template file to compare against')
    parser.add_argument('-o', '--output', default='camera_analysis.md', 
                       help='Output markdown file')
    parser.add_argument('--create-templates', action='store_true', 
                       help='Create template files')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    args = parser.parse_args()
    
    if args.create_templates:
        create_template_files()
        print("✅ Created template files:")
        print("   - cameraFlow_overview.md")
        print("   - cameraFlow_detail.md")
        print("   - camera_patterns.yaml (if not exists)")
        return 0
    
    if not Path(args.input_log).exists():
        print(f"❌ Input file '{args.input_log}' not found")
        return 1
    
    analyzer = ConfigurableLogAnalyzer(args.config)
    
    print(f"📄 Parsing logcat: {args.input_log}")
    entries = analyzer.parse_logcat(args.input_log)
    print(f"📊 Found {len(entries)} relevant log entries")
    
    print("🔍 Extracting method calls...")
    method_calls = analyzer.extract_method_calls(entries)
    print(f"📋 Extracted {len(method_calls)} method calls")
    
    # Load and compare with template if provided
    template_comparison = []
    if args.template and Path(args.template).exists():
        print(f"📋 Loading template: {args.template}")
        template_steps = analyzer.load_template(args.template)
        template_comparison = analyzer.compare_with_template(method_calls, template_steps)
        template_type = "detail" if "detail" in args.template.lower() else "overview"
        
        print(f"🔍 Analyzing flow gaps using template predictions...")
        flow_gaps = analyzer.analyze_flow_gaps(method_calls)
        print(f"📊 Found {len(flow_gaps)} potential flow gaps")
        
        analyzer.generate_comparison_markdown(entries, method_calls, template_comparison, 
                                            args.output, template_type)
        print(f"✅ Generated comparison analysis: {args.output}")
        
        found_steps = sum(1 for step in template_comparison if step.found)
        success_rate = found_steps/len(template_comparison)*100 if template_comparison else 0
        print(f"📈 Flow completion: {found_steps}/{len(template_comparison)} ({success_rate:.1f}%)")
        
        if flow_gaps:
            print(f"⚠️  Flow gaps detected - Check 'Flow Gap Analysis' section")
            print(f"🎯 Template suggests missing calls from: {', '.join(set(gap['missing_class'] for gap in flow_gaps[:5]))}")
        
    else:
        # Generate basic analysis without template
        analyzer.generate_comparison_markdown(entries, method_calls, [], args.output)
        print(f"✅ Generated basic analysis: {args.output}")
        print("💡 Use --template to enable flow prediction analysis")
    
    return 0

if __name__ == '__main__':
    exit(main())

                    method_match = re.search(method_pattern, description)
                    expected_method = method_match.group(1) or method_match.group(2) or method_match.group(3) if method_match else description
                    
                    flow_step = FlowStep(
                        step_id=f"step_{step_id}",
                        participants=[from_part, to_part],
                        description=description.strip(),
                        expected_pattern=expected_method.lower(),
                        critical=True
                    )
                    flow_steps.append(flow_step)
                    
                    # Build flow prediction graph
                    if from_part not in self.flow_graph:
                        self.flow_graph[from_part] = []
                    self.flow_graph[from_part].append({
                        'next_class': to_part,
                        'expected_method': expected_method,
                        'description': description,
                        'step_id': step_id
                    })
                    
                    # Link sequential steps
                    if previous_step:
                        previous_step['next_step'] = flow_step
                    previous_step = flow_step
                    
                    step_id += 1
        
        return flow_steps
    
    def compare_with_template(self, method_calls: List[MethodCall], 
                             template_steps: List[FlowStep]) -> List[FlowStep]:
        """Compare actual calls with template and mark found/missing steps"""
        
        for step in template_steps:
            # Check if this step was found in actual logs
            for call in method_calls:
                if (any(keyword in call.method_name.lower() 
                       for keyword in step.expected_pattern.split()) or
                    any(keyword in call.message.lower() 
                       for keyword in step.expected_pattern.split())):
                    step.found = True
                    break
        
        return template_steps
    
    def generate_comparison_markdown(self, entries: List[LogEntry], 
                                   method_calls: List[MethodCall],
                                   template_comparison: List[FlowStep],
                                   output_file: str, template_type: str = "overview"):
        """Generate markdown with template comparison"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# CameraApp Flow Analysis - {template_type.title()}\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Template**: {template_type}\n")
            f.write(f"**Total Steps Expected**: {len(template_comparison)}\n")
            
            found_steps = sum(1 for step in template_comparison if step.found)
            f.write(f"**Steps Found**: {found_steps}/{len(template_comparison)}\n")
            f.write(f"**Success Rate**: {found_steps/len(template_comparison)*100:.1f}%\n\n")
            
            # Flow status
            f.write("## 📊 Flow Execution Status\n\n")
            f.write("| Step | Status | Description | Critical |\n")
            f.write("|------|--------|-------------|----------|\n")
            
            for step in template_comparison:
                status_icon = "✅" if step.found else "❌"
                critical_icon = "🔴" if step.critical else "🟡"
                f.write(f"| {step.step_id} | {status_icon} | {step.description} | {critical_icon} |\n")
            
            # Generate sequence diagram with X marks
            f.write("\n## 🔄 Actual vs Expected Flow\n\n")
            f.write("```mermaid\n")
            f.write("sequenceDiagram\n")
            
            # Extract participants
            all_participants = set()
            for step in template_comparison:
                all_participants.update(step.participants)
            
            for participant in sorted(all_participants):
                f.write(f"    participant {participant}\n")
            f.write("\n")
            
            # Generate sequence with X marks for missing steps
            for step in template_comparison:
                if len(step.participants) >= 2:
                    from_part, to_part = step.participants[0], step.participants[1]
                    if step.found:
                        f.write(f"    {from_part}->>{to_part}: {step.description}\n")
                    else:
                        f.write(f"    {from_part}-x{to_part}: ❌ {step.description}\n")
                        f.write(f"    Note over {from_part},{to_part}: MISSING STEP\n")
            
            f.write("```\n\n")
            
            # Missing critical steps analysis
            missing_critical = [s for s in template_comparison if not s.found and s.critical]
            if missing_critical:
                f.write("## 🚨 Critical Missing Steps\n\n")
                for step in missing_critical:
                    f.write(f"- **{step.step_id}**: {step.description}\n")
                f.write("\n")
            
            # Debug recommendations
            f.write("## 🔧 Debug Recommendations\n\n")
            if missing_critical:
                f.write("### Priority Issues:\n")
                for step in missing_critical:
                    f.write(f"1. Check logs for patterns related to: `{step.expected_pattern}`\n")
                f.write("\n")
            
            f.write("### Next Actions:\n")
            f.write("1. Focus on first missing critical step\n")
            f.write("2. Add more detailed logging around missing steps\n")
            f.write("3. Check exception handlers in missing flow areas\n")
            f.write("4. Verify hardware/service dependencies\n")

def create_template_files():
    """Create template files for automotive camera flows"""
    
    # Overview template
    overview_template = '''# Camera Flow Overview Template

```mermaid
sequenceDiagram
    participant User
    participant CameraApp
    participant CameraService
    participant CameraHAL
    participant Hardware
    
    User->>CameraApp: Launch App
    CameraApp->>CameraService: Initialize Camera Manager
    CameraService->>CameraHAL: Connect to HAL
    CameraHAL->>Hardware: Initialize Hardware
    Hardware-->>CameraHAL: Hardware Ready
    CameraHAL-->>CameraService: HAL Ready
    CameraService-->>CameraApp: Camera Available
    
    User->>CameraApp: Open Camera
    CameraApp->>CameraService: Open Camera Device
    CameraService->>CameraHAL: Camera Open
    CameraHAL->>Hardware: Power On Camera
    Hardware-->>CameraHAL: Camera Ready
    CameraHAL-->>CameraService: Device Opened
    CameraService-->>CameraApp: Camera Opened
    
    CameraApp->>CameraService: Configure Session
    CameraService->>CameraHAL: Create Capture Session
    CameraApp->>CameraService: Start Preview
    CameraService->>CameraHAL: Start Preview Stream
    CameraHAL->>Hardware: Start Streaming
    
    Note over CameraApp,Hardware: Preview Running
    
    User->>CameraApp: Close Camera
    CameraApp->>CameraService: Close Camera
    CameraService->>CameraHAL: Release Resources
    CameraHAL->>Hardware: Power Down
```
'''
    
    # Detail template
    detail_template = '''# Camera Flow Detail Template

```mermaid
sequenceDiagram
    participant User
    participant CameraApp
    participant CameraManager
    participant CameraService
    participant CameraProvider
    participant CameraHAL
    participant VehicleHAL
    participant Hardware
    
    Note over User,Hardware: App Launch Phase
    User->>CameraApp: Launch CameraApp
    CameraApp->>CameraManager: getCameraManager()
    CameraManager->>CameraService: bindService()
    CameraService->>CameraProvider: connectToProvider()
    CameraProvider->>CameraHAL: HIDL Connect
    CameraHAL->>Hardware: HAL Initialize
    
    Note over User,Hardware: Vehicle State Check
    CameraApp->>VehicleHAL: Check Gear Position
    VehicleHAL-->>CameraApp: Gear Status
    CameraApp->>VehicleHAL: Register Gear Listener
    
    Note over User,Hardware: Camera Discovery
    CameraApp->>CameraManager: getCameraIdList()
    CameraManager->>CameraService: getCameraList()
    CameraService->>CameraProvider: getCameraDeviceInterface()
    CameraProvider-->>CameraService: Camera List
    CameraService-->>CameraManager: Available Cameras
    CameraManager-->>CameraApp: Camera IDs
    
    Note over User,Hardware: Camera Open Sequence
    User->>CameraApp: Select Camera
    CameraApp->>CameraManager: openCamera()
    CameraManager->>CameraService: connectDevice()
    CameraService->>CameraProvider: openCameraDevice()
    CameraProvider->>CameraHAL: camera_device_open()
    CameraHAL->>Hardware: Power On & Initialize
    Hardware-->>CameraHAL: Init Complete
    CameraHAL-->>CameraProvider: Device Ready
    CameraProvider-->>CameraService: Camera Opened
    CameraService-->>CameraManager: Device Available
    CameraManager-->>CameraApp: onOpened() Callback
    
    Note over User,Hardware: Session Configuration
    CameraApp->>CameraManager: createCaptureSession()
    CameraManager->>CameraService: configureStreams()
    CameraService->>CameraProvider: configureStreams()
    CameraProvider->>CameraHAL: configure_streams()
    CameraHAL->>Hardware: Configure Pipeline
    Hardware-->>CameraHAL: Config Complete
    CameraHAL-->>CameraProvider: Streams Configured
    CameraProvider-->>CameraService: Configuration Done
    CameraService-->>CameraManager: Session Ready
    CameraManager-->>CameraApp: onConfigured() Callback
    
    Note over User,Hardware: Preview Start
    CameraApp->>CameraManager: setRepeatingRequest()
    CameraManager->>CameraService: capture()
    CameraService->>CameraProvider: processCaptureRequest()
    CameraProvider->>CameraHAL: process_capture_request()
    CameraHAL->>Hardware: Start Streaming
    Hardware-->>CameraHAL: Frame Data
    CameraHAL-->>CameraProvider: Frame Ready
    CameraProvider-->>CameraService: Frame Available
    CameraService-->>CameraManager: Frame Callback
    CameraManager-->>CameraApp: onImageAvailable()
    
    Note over User,Hardware: Running State
    loop Frame Processing
        Hardware-->>CameraApp: Continuous Frames
    end
    
    Note over User,Hardware: Cleanup Sequence  
    User->>CameraApp: Exit App
    CameraApp->>CameraManager: close()
    CameraManager->>CameraService: disconnect()
    CameraService->>CameraProvider: close()
    CameraProvider->>CameraHAL: camera_device_close()
    CameraHAL->>Hardware: Power Down
    Hardware-->>CameraHAL: Shutdown Complete
```
'''
    
    # Write template files
    with open('cameraFlow_overview.md', 'w', encoding='utf-8') as f:
        f.write(overview_template)
    
    with open('cameraFlow_detail.md', 'w', encoding='utf-8') as f:
        f.write(detail_template)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Configurable Android Automotive CameraApp Log Analyzer')
    parser.add_argument('input_log', help='Input logcat file (txt format)')
    parser.add_argument('-c', '--config', default='camera_patterns.yaml', 
                       help='Configuration file (default: camera_patterns.yaml)')
    parser.add_argument('-t', '--template', help='Template file to compare against')
    parser.add_argument('-o', '--output', default='camera_analysis.md', 
                       help='Output markdown file')
    parser.add_argument('--create-templates', action='store_true', 
                       help='Create template files')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    args = parser.parse_args()
    
    if args.create_templates:
        create_template_files()
        print("✅ Created template files:")
        print("   - cameraFlow_overview.md")
        print("   - cameraFlow_detail.md")
        print("   - camera_patterns.yaml (if not exists)")
        return 0
    
    if not Path(args.input_log).exists():
        print(f"❌ Input file '{args.input_log}' not found")
        return 1
    
    analyzer = ConfigurableLogAnalyzer(args.config)
    
    print(f"📄 Parsing logcat: {args.input_log}")
    entries = analyzer.parse_logcat(args.input_log)
    print(f"📊 Found {len(entries)} relevant log entries")
    
    print("🔍 Extracting method calls...")
    method_calls = analyzer.extract_method_calls(entries)
    print(f"📋 Extracted {len(method_calls)} method calls")
    
    # Load and compare with template if provided
    template_comparison = []
    if args.template and Path(args.template).exists():
        print(f"📋 Loading template: {args.template}")
        template_steps = analyzer.load_template(args.template)
        template_comparison = analyzer.compare_with_template(method_calls, template_steps)
        template_type = "detail" if "detail" in args.template.lower() else "overview"
        
        analyzer.generate_comparison_markdown(entries, method_calls, template_comparison, 
                                            args.output, template_type)
        print(f"✅ Generated comparison analysis: {args.output}")
        
        found_steps = sum(1 for step in template_comparison if step.found)
        success_rate = found_steps/len(template_comparison)*100 if template_comparison else 0
        print(f"📈 Flow completion: {found_steps}/{len(template_comparison)} ({success_rate:.1f}%)")
    else:
        # Generate basic analysis without template
        analyzer.generate_comparison_markdown(entries, method_calls, [], args.output)
        print(f"✅ Generated basic analysis: {args.output}")
    
    return 0

if __name__ == '__main__':
    exit(main())
