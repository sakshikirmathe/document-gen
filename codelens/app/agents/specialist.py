"""
Specialist Agent for CodeLens.
Responsible for deep analysis of individual modules in the codebase.
"""

import structlog
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime  # Fix: was missing

from codelens.app.agents.base import BaseAgent
from codelens.app.models.agent import AgentInput, AgentOutput, AgentReport

logger = structlog.get_logger(__name__)


class SpecialistAgent(BaseAgent):
    """
    Specialist Agent that performs deep analysis of a single module.
    Analyzes module overview, file breakdown, key classes/functions, data models,
    API endpoints, configuration, dependencies, error handling, testing, and tech debt.
    """

    def __init__(self, module_definition: Dict[str, Any], file_contents: Dict[str, str], config: Dict[str, Any]):
        agent_id = f"specialist_{module_definition.get('module_id', 'unknown')}"
        super().__init__(agent_id, "specialist")
        self.module_definition = module_definition
        self.file_contents = file_contents
        self.config = config

    async def _execute(self, input_data: AgentInput) -> AgentOutput:
        """Execute the specialist agent to analyze a module."""
        try:
            self.logger.info("Specialist agent starting analysis", module_id=self.module_definition.get("module_id"))

            module_id = self.module_definition.get("module_id", "")
            module_name = self.module_definition.get("module_name", "")
            description = self.module_definition.get("description", "")
            files = self.module_definition.get("files", [])
            dependencies = self.module_definition.get("dependencies", [])
            prompt_hints = self.module_definition.get("agent_prompt_hints", "")

            report = await self._analyze_module(
                module_id, module_name, description, files, dependencies, prompt_hints
            )

            self.logger.info(
                "Specialist agent completed analysis",
                module_id=module_id,
                report_sections=len(report.dict())
            )

            return AgentOutput(
                status="completed",
                output_data=report.dict(),
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                completed_at=datetime.utcnow()
            )

        except Exception as e:
            self.logger.error("Specialist agent failed", module_id=self.module_definition.get("module_id"), error=str(e))
            return AgentOutput(
                status="failed",
                error=str(e),
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                completed_at=datetime.utcnow()
            )

    async def _analyze_module(
        self,
        module_id: str,
        module_name: str,
        description: str,
        files: List[str],
        dependencies: List[str],
        prompt_hints: str
    ) -> AgentReport:
        """Perform comprehensive analysis of a module."""
        file_breakdown = {}
        key_classes_functions = []
        data_models_schemas = []
        api_endpoints = []
        configuration_env_vars = []
        external_dependencies = []
        error_handling_patterns = []
        testing_info = {}
        known_issues_tech_debt = []

        for file_path in files:
            if file_path in self.file_contents:
                content = self.file_contents[file_path]
                file_analysis = self._analyze_file(file_path, content)

                file_breakdown[file_path] = file_analysis.get("purpose", "File analysis pending")
                key_classes_functions.extend(file_analysis.get("classes_functions", []))
                data_models_schemas.extend(file_analysis.get("data_models", []))
                api_endpoints.extend(file_analysis.get("api_endpoints", []))
                configuration_env_vars.extend(file_analysis.get("config_vars", []))
                error_handling_patterns.extend(file_analysis.get("error_handling", []))
                known_issues_tech_debt.extend(file_analysis.get("tech_debt", []))

                if file_analysis.get("testing"):
                    testing_info[file_path] = file_analysis["testing"]

        internal_dependencies = dependencies

        overview = self._generate_module_overview(
            module_name, description, files, file_breakdown, key_classes_functions
        )

        return AgentReport(
            module_id=module_id,
            module_name=module_name,
            overview=overview,
            file_breakdown=file_breakdown,
            key_classes_functions=key_classes_functions,
            data_models_schemas=data_models_schemas,
            api_endpoints=api_endpoints,
            configuration_env_vars=configuration_env_vars,
            internal_dependencies=internal_dependencies,
            external_dependencies=external_dependencies,
            error_handling_patterns=error_handling_patterns,
            testing_info=testing_info,
            known_issues_tech_debt=known_issues_tech_debt
        )

    def _analyze_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze a single file to extract relevant information."""
        analysis = {
            "purpose": "",
            "classes_functions": [],
            "data_models": [],
            "api_endpoints": [],
            "config_vars": [],
            "error_handling": [],
            "testing": None,
            "tech_debt": []
        }

        lines = content.split('\n')

        if "controller" in file_path.lower() or "api" in file_path.lower():
            analysis["purpose"] = "Handles HTTP requests and API endpoints"
        elif "model" in file_path.lower() or "entity" in file_path.lower():
            analysis["purpose"] = "Defines data models and entities"
        elif "service" in file_path.lower():
            analysis["purpose"] = "Contains business logic and service implementations"
        elif "repository" in file_path.lower() or "dal" in file_path.lower():
            analysis["purpose"] = "Handles data access and database operations"
        elif "util" in file_path.lower() or "helper" in file_path.lower():
            analysis["purpose"] = "Provides utility functions and common helpers"
        else:
            analysis["purpose"] = "Module component file"

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if line_stripped.startswith('Class ') or line_stripped.startswith('Module '):
                parts = line_stripped.split()
                if len(parts) >= 2:
                    class_name = parts[1]
                    analysis["classes_functions"].append({
                        "name": class_name,
                        "type": "class" if line_stripped.startswith('Class ') else "module",
                        "line": i + 1,
                        "description": f"{class_name} class/module"
                    })
            elif line_stripped.startswith('Function ') or line_stripped.startswith('Sub '):
                parts = line_stripped.split()
                if len(parts) >= 2:
                    func_name = parts[1].split('(')[0] if '(' in parts[1] else parts[1]
                    analysis["classes_functions"].append({
                        "name": func_name,
                        "type": "function" if line_stripped.startswith('Function ') else "sub",
                        "line": i + 1,
                        "description": f"{func_name} function/subroutine"
                    })

        in_class = False
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if line_stripped.startswith('Class ') or line_stripped.startswith('Structure '):
                in_class = True
            elif line_stripped.startswith('End Class') or line_stripped.startswith('End Structure'):
                in_class = False
            elif in_class and (' As ' in line_stripped or 'Property ' in line_stripped):
                if ' As ' in line_stripped:
                    parts = line_stripped.split(' As ')
                    if len(parts) >= 2:
                        analysis["data_models"].append({
                            "name": parts[0].strip(),
                            "type": parts[1].strip(),
                            "line": i + 1
                        })

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if any(attr in line_stripped for attr in ['<HttpGet>', '<HttpPost>', '<HttpPut>', '<HttpDelete>', 'ActionResult']):
                analysis["api_endpoints"].append({
                    "line": i + 1,
                    "content": line_stripped[:100] + "..." if len(line_stripped) > 100 else line_stripped
                })

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if any(config in line_stripped for config in ['ConfigurationManager', 'AppSettings', 'ConnectionStrings']):
                analysis["config_vars"].append({
                    "line": i + 1,
                    "content": line_stripped[:100] + "..." if len(line_stripped) > 100 else line_stripped
                })

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if any(err in line_stripped for err in ['Try ', 'Catch ', 'Finally ', 'On Error GoTo', 'Throw ', 'Exception']):
                analysis["error_handling"].append({
                    "line": i + 1,
                    "pattern": line_stripped[:100] + "..." if len(line_stripped) > 100 else line_stripped
                })

        if any(test in content.lower() for test in ['test ', 'unittest ', 'xunit ', 'nunit ', 'mstest']):
            analysis["testing"] = {
                "framework": "Detected testing framework",
                "indicators": ["Test methods or test classes found"]
            }

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if any(debt in line_stripped.upper() for debt in ['TODO', 'FIXME', 'HACK', 'DEPRECATED', 'OBSOLETE']):
                analysis["tech_debt"].append({
                    "line": i + 1,
                    "content": line_stripped[:100] + "..." if len(line_stripped) > 100 else line_stripped
                })

        return analysis

    def _generate_module_overview(
        self,
        module_name: str,
        description: str,
        files: List[str],
        file_breakdown: Dict[str, str],
        key_classes_functions: List[Dict[str, Any]]
    ) -> str:
        """Generate a 2-3 paragraph executive summary of the module."""
        paragraph1 = (
            f"The {module_name} module is responsible for {description.lower()}. "
            f"It contains {len(files)} files that work together to provide "
            f"{module_name.lower()} functionality within the application."
        )
        paragraph2 = (
            f"The module includes {len(key_classes_functions)} key classes and functions "
            f"that implement its core functionality. These components are organized "
            f"to maintain separation of concerns and follow VB.net best practices."
        )
        paragraph3 = (
            f"Key responsibilities of this module include handling {module_name.lower()} "
            f"operations, managing related data, and providing interfaces for "
            f"other modules to interact with its functionality."
        )

        overview = f"{paragraph1}\n\n{paragraph2}"
        if len(files) > 5 or len(key_classes_functions) > 10:
            overview += f"\n\n{paragraph3}"
        return overview