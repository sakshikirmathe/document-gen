"""
VB.net-specific language and framework detection module.
Analyzes file contents and project structure to detect VB.net characteristics.
"""

import re
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)


class VBNetDetector:
    """
    Detects VB.net-specific patterns in files and projects.
    Handles language detection, framework identification, and architectural patterns.
    """

    def __init__(self):
        self.logger = logger.bind(component="VBNetDetector")

        # VB.net-specific keywords and patterns
        self.vbnet_keywords = {
            'Namespace', 'End Namespace', 'Class', 'End Class',
            'Module', 'End Module', 'Interface', 'End Interface',
            'Structure', 'End Structure', 'Enum', 'End Enum',
            'Function', 'End Function', 'Sub', 'End Sub',
            'Property', 'End Property', 'Get', 'Set',
            'Imports', 'Inherits', 'Implements', 'Overrides',
            'Overloads', 'Overridable', 'MustOverride', 'NotOverridable',
            'Public', 'Private', 'Protected', 'Friend', 'Protected Friend',
            'Shared', 'Static', 'ReadOnly', 'WriteOnly', 'Dim',
            'As', 'Of', 'New', 'Nothing', 'IsNot', 'Is',
            'Try', 'Catch', 'Finally', 'End Try',
            'Throw', 'Using', 'End Using',
            'If', 'Then', 'Else', 'ElseIf', 'End If',
            'Select Case', 'Case', 'Case Else', 'End Select',
            'For', 'To', 'Step', 'Next', 'Each', 'In',
            'Do', 'Loop', 'While', 'Until', 'Exit',
            'Continue', 'GoTo', 'On Error', 'Resume',
            'With', 'End With', 'SyncLock', 'End SyncLock',
            'Event', 'RaiseEvent', 'AddHandler', 'RemoveHandler',
            'Handles', 'WithEvents', 'AddressOf', 'Alias',
            'Declare', 'Lib', 'Ansi', 'Unicode', 'Auto',
            'MarshalAs', 'DllImport', 'Preserve',
            'Overloads', 'Overrides', 'Overridable', 'MustOverride',
            'MustInherit', 'NotInheritable', 'Partial',
            'Custom', 'Narrowing', 'Widening', 'Operator',
            'Converter', 'Widening', 'Narrowing', 'DirectCast',
            'TryCast', 'CType', 'DirectCast', 'TryCast'
        }

        # VB.net-specific attributes
        self.vbnet_attributes = {
            'Obsolete', 'Conditional', 'DebuggerHidden',
            'DebuggerStepThrough', 'CallerMemberName',
            'CallerFilePath', 'CallerLineNumber',
            'Description', 'Category', 'DisplayName',
            'Browsable', 'EditorBrowsable', 'DesignerSerializationVisibility',
            'DefaultProperty', 'DefaultEvent', 'ToolboxItem',
            'ToolboxBitmap', 'Serializable', 'NonSerialized',
            'FieldOffset', 'MarshalAs', 'DllImport', 'StructLayout'
        }

        # Framework detection patterns
        self.framework_patterns = {
            'WinForms': [
                r'System\.Windows\.Forms',
                r'System\.Drawing',
                r'Inherits\s+Form',
                r'Class\s+\w+\s*:\s*Form'
            ],
            'WPF': [
                r'System\.Windows',
                r'System\.Windows\.Controls',
                r'Inherits\s+Window|UserControl|Page'
            ],
            'ASP.NET WebForms': [
                r'System\.Web\.UI',
                r'Page\s*:\s*System\.Web\.UI\.Page',
                r'<\%@\s*Page',
                r'CodeBehind\s*=',
                r'Inherits\s+\w+\s*:\s*System\.Web\.UI\.Page'
            ],
            'ASP.NET MVC': [
                r'System\.Web\.Mvc',
                r'Controller\s*:\s*System\.Web\.Mvc\.Controller',
                r'ActionResult',
                r'HttpGet|HttpPost|HttpPut|HttpDelete'
            ],
            'WCF': [
                r'System\.ServiceModel',
                r'ServiceContract|OperationContract|DataContract',
                r'ServiceBehavior|OperationBehavior'
            ],
            'Console': [
                r'System\.Console',
                r'Module\s+\w+.*Sub\s+Main',
                r'Sub\s+Main\s*\('
            ],
            'Service': [
                r'System\.ServiceProcess',
                r'Inherits\s+ServiceBase'
            ]
        }

        # Data access patterns
        self.data_access_patterns = {
            'ADO.NET': [
                r'System\.Data',
                r'SqlConnection|OleDbConnection|OdbcConnection',
                r'SqlCommand|OleDbCommand|OdbcCommand',
                r'SqlDataAdapter|OleDbDataAdapter|OdbcDataAdapter',
                r'DataSet|DataTable|DataView',
                r'ExecuteReader|ExecuteNonQuery|ExecuteScalar'
            ],
            'Entity Framework': [
                r'System\.Data\.Entity',
                r'DbContext|ObjectContext',
                r'DbSet|ObjectSet',
                r'OnModelCreating',
                r'DbMigration'
            ],
            'LINQ': [
                r'System\.Linq',
                r'From\s+\w+\s+In\s+',
                r'Select\s+|Where\s+|OrderBy\s+|Group\s+By\s+',
                r'Aggregate\s+|Join\s+|Group\s+Join\s+'
            ]
        }

    def detect_language(self, file_path: Path, content: str) -> bool:
        """
        Detect if a file is VB.net based on content analysis.
        Returns True if VB.net is detected.
        """
        # Check file extension first
        if file_path.suffix.lower() in ['.vb', '.vbproj', '.sln']:
            return True

        # For .vb files, check content
        if file_path.suffix.lower() == '.vb':
            # Count VB.net keywords
            keyword_matches = 0
            for keyword in self.vbnet_keywords:
                # Use word boundaries to avoid partial matches
                pattern = rf'\b{re.escape(keyword)}\b'
                matches = len(re.findall(pattern, content, re.IGNORECASE))
                keyword_matches += matches

            # If we find multiple VB.net keywords, it's likely VB.net
            if keyword_matches >= 3:
                return True

            # Check for VB.net-specific patterns
            vbnet_patterns = [
                r'^\s*Namespace\s+\w+',
                r'^\s*End\s+Namespace',
                r'^\s*Class\s+\w+',
                r'^\s*End\s+Class',
                r'^\s*Module\s+\w+',
                r'^\s*End\s+Module',
                r'^\s*Interface\s+\w+',
                r'^\s*End\s+Interface',
                r'^\s*Structure\s+\w+',
                r'^\s*End\s+Structure',
                r'^\s*Enum\s+\w+',
                r'^\s*End\s+Enum',
                r'^\s*Imports\s+[\w\.]+',
                r'^\s*Public\s+',
                r'^\s*Private\s+',
                r'^\s*Friend\s+',
                r'^\s*Protected\s+'
            ]

            pattern_matches = 0
            for pattern in vbnet_patterns:
                if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                    pattern_matches += 1

            if pattern_matches >= 2:
                return True

        return False

    def detect_frameworks(self, content: str, file_paths: List[str] = None) -> Set[str]:
        """
        Detect VB.net frameworks used in the codebase.
        Returns a set of detected framework names.
        """
        detected = set()

        # Check content for framework patterns
        for framework, patterns in self.framework_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    detected.add(framework)
                    break  # Found this framework, no need to check other patterns

        # If we have file paths, check for project files
        if file_paths:
            for file_path in file_paths:
                path_obj = Path(file_path)
                if path_obj.suffix.lower() == '.vbproj':
                    # Read .vbproj file to detect frameworks
                    try:
                        # This would be implemented to read the actual file
                        # For now, we'll rely on content scanning above
                        pass
                    except Exception:
                        pass

        return detected

    def detect_data_access(self, content: str) -> Set[str]:
        """
        Detect data access technologies used in the codebase.
        Returns a set of detected data access technologies.
        """
        detected = set()

        for tech, patterns in self.data_access_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    detected.add(tech)
                    break

        return detected

    def detect_architectural_patterns(self, file_structure: Dict[str, List[str]]) -> Set[str]:
        """
        Detect architectural patterns based on folder/file structure.
        file_structure: dict mapping folder names to lists of files in those folders
        Returns a set of detected architectural patterns.
        """
        detected = set()

        # Common VB.net architectural patterns
        patterns = {
            'DAL': ['dal', 'dataaccess', 'data access', 'repository', 'repositories'],
            'BLL': ['bll', 'businesslogic', 'business logic', 'service', 'services', 'manager', 'managers'],
            'UI': ['ui', 'forms', 'views', 'pages', 'controls'],
            'Models': ['models', 'entities', 'dto', 'viewmodels', 'view models'],
            'Utilities': ['utils', 'utility', 'helpers', 'helper', 'common', 'extension', 'extensions'],
            'Controllers': ['controllers', 'api', 'webapi'],
            'Providers': ['providers', 'provider']
        }

        # Normalize folder names for comparison
        normalized_structure = {}
        for folder, files in file_structure.items():
            normalized_folder = folder.lower().replace(' ', '').replace('-', '').replace('_', '')
            normalized_structure[normalized_folder] = [f.lower() for f in files]

        # Check for pattern matches
        for pattern_name, keywords in patterns.items():
            for keyword in keywords:
                if keyword in normalized_structure:
                    detected.add(pattern_name)
                    break

        return detected

    def analyze_vbnet_file(self, file_path: Path, content: str) -> Dict[str, any]:
        """
        Perform comprehensive analysis of a VB.net file.
        Returns a dictionary with analysis results.
        """
        analysis = {
            'is_vbnet': self.detect_language(file_path, content),
            'frameworks': set(),
            'data_access': set(),
            'keywords_found': [],
            'attributes_found': [],
            'has_namespace': False,
            'has_class': False,
            'has_module': False,
            'has_interface': False,
            'line_count': 0,
            'code_lines': 0,
            'comment_lines': 0
        }

        if not analysis['is_vbnet']:
            return analysis

        lines = content.split('\n')
        analysis['line_count'] = len(lines)

        # Count different types of lines
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            elif stripped.startswith("'"):
                analysis['comment_lines'] += 1
            else:
                analysis['code_lines'] += 1

        # Find VB.net keywords
        for keyword in self.vbnet_keywords:
            pattern = rf'\b{re.escape(keyword)}\b'
            if re.search(pattern, content, re.IGNORECASE):
                analysis['keywords_found'].append(keyword)

        # Find VB.net attributes
        for attribute in self.vbnet_attributes:
            pattern = rf'<{re.escapeAttribute)}(?:\([^>]*\))?>'
            if re.search(pattern, content, re.IGNORECASE):
                analysis['attributes_found'].append(attribute)

        # Check for structural elements
        analysis['has_namespace'] = bool(re.search(r'\bNamespace\s+\w+', content))
        analysis['has_class'] = bool(re.search(r'\bClass\s+\w+', content))
        analysis['has_module'] = bool(re.search(r'\bModule\s+\w+', content))
        analysis['has_interface'] = bool(re.search(r'\bInterface\s+\w+', content))

        # Detect frameworks and data access
        analysis['frameworks'] = self.detect_frameworks(content)
        analysis['data_access'] = self.detect_data_access(content)

        return analysis