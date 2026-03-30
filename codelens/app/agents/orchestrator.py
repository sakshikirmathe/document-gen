"""
Orchestrator Agent for CodeLens.
Responsible for identifying modules in the codebase and creating execution plans.
"""

import structlog
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime  # Fix: was missing

from codelens.app.agents.base import BaseAgent
from codelens.app.models.agent import AgentInput, AgentOutput, ModuleMap, ModuleDefinition

logger = structlog.get_logger(__name__)


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent that analyzes the codebase structure and identifies modules.
    Uses VB.net-specific signals including namespace clusters, project boundaries,
    and architectural pattern detection.
    """

    def __init__(self, agent_id: str = "orchestrator"):
        super().__init__(agent_id, "orchestrator")

    async def _execute(self, input_data: AgentInput) -> AgentOutput:
        """Execute the orchestrator agent to identify modules in the codebase."""
        try:
            self.logger.info("Orchestrator agent starting analysis")

            file_tree = input_data.input_data.get("file_tree", {})
            ast_summaries = input_data.input_data.get("ast_summaries", {})
            namespace_graph = input_data.input_data.get("namespace_graph", {})
            vbnet_project_info = input_data.input_data.get("vbnet_project_info", {})

            modules = await self._identify_modules(
                file_tree, ast_summaries, namespace_graph, vbnet_project_info
            )

            module_map = ModuleMap(
                modules=modules,
                orchestrator_notes=f"Identified {len(modules)} modules using VB.net-specific analysis"
            )

            self.logger.info("Orchestrator agent completed analysis", modules_identified=len(modules))

            return AgentOutput(
                status="completed",
                output_data=module_map.dict(),
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                completed_at=datetime.utcnow()
            )

        except Exception as e:
            self.logger.error("Orchestrator agent failed", error=str(e))
            return AgentOutput(
                status="failed",
                error=str(e),
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                completed_at=datetime.utcnow()
            )

    async def _identify_modules(
        self,
        file_tree: Dict[str, Any],
        ast_summaries: Dict[str, Any],
        namespace_graph: Dict[str, Any],
        vbnet_project_info: Dict[str, Any]
    ) -> List[ModuleDefinition]:
        """Identify modules using VB.net-specific signals."""
        modules = []

        project_modules = self._identify_project_boundaries(vbnet_project_info)
        modules.extend(project_modules)

        namespace_modules = self._identify_namespace_clusters(file_tree, ast_summaries, namespace_graph)
        modules.extend(namespace_modules)

        pattern_modules = self._identify_architectural_patterns(file_tree, ast_summaries)
        modules.extend(pattern_modules)

        merged_modules = self._merge_and_deduplicate_modules(modules)
        prioritized_modules = self._assign_priorities(merged_modules)

        return prioritized_modules

    def _identify_project_boundaries(self, vbnet_project_info: Dict[str, Any]) -> List[ModuleDefinition]:
        """Identify modules based on .sln/.vbproj project boundaries."""
        modules = []
        projects = vbnet_project_info.get("projects", [])
        for i, project in enumerate(projects):
            module_def = ModuleDefinition(
                module_id=f"project_{project.get('name', f'project_{i}')}",
                module_name=project.get("name", f"Project {i}"),
                description=f"Module derived from {project.get('name', 'VB.net project')}",
                files=project.get("files", []),
                dependencies=[],
                priority=i,
                agent_prompt_hints=f"Analyze this VB.net project: {project.get('name', '')}"
            )
            modules.append(module_def)
        return modules

    def _identify_namespace_clusters(
        self,
        file_tree: Dict[str, Any],
        ast_summaries: Dict[str, Any],
        namespace_graph: Dict[str, Any]
    ) -> List[ModuleDefinition]:
        """Identify modules based on namespace clusters."""
        modules = []
        namespace_to_files: Dict[str, List[str]] = {}

        for file_path, file_info in ast_summaries.items():
            namespaces = file_info.get("namespaces", [])
            for ns in namespaces:
                if ns not in namespace_to_files:
                    namespace_to_files[ns] = []
                namespace_to_files[ns].append(file_path)

        for i, (namespace, files) in enumerate(namespace_to_files.items()):
            if len(files) >= 2:
                module_def = ModuleDefinition(
                    module_id=f"namespace_{namespace.replace('.', '_')}",
                    module_name=f"{namespace} Module",
                    description=f"Module containing files in the {namespace} namespace",
                    files=files,
                    dependencies=[],
                    priority=i + 100,
                    agent_prompt_hints=f"Analyze the {namespace} namespace and its related components"
                )
                modules.append(module_def)
        return modules

    def _identify_architectural_patterns(
        self,
        file_tree: Dict[str, Any],
        ast_summaries: Dict[str, Any]
    ) -> List[ModuleDefinition]:
        """Identify modules based on VB.net architectural patterns."""
        modules = []
        patterns = {
            "DAL": {
                "keywords": ["dal", "dataaccess", "repository", "repositories"],
                "indicators": ["SqlConnection", "DataAdapter", "DataSet", "EntityFramework"],
                "description": "Data Access Layer - handles database operations"
            },
            "BLL": {
                "keywords": ["bll", "businesslogic", "service", "services", "manager"],
                "indicators": ["business rule", "service class", "manager"],
                "description": "Business Logic Layer - contains business rules and workflows"
            },
            "UI": {
                "keywords": ["ui", "forms", "views", "pages", "controls"],
                "indicators": ["Form", "UserControl", "Page", "System.Windows.Forms"],
                "description": "User Interface Layer - handles user interaction"
            },
            "Models": {
                "keywords": ["models", "entities", "dto", "viewmodels"],
                "indicators": ["class", "properties", "data model"],
                "description": "Data Models - represents business entities and data structures"
            },
            "Utilities": {
                "keywords": ["utils", "utility", "helpers", "common"],
                "indicators": ["helper", "utility", "extension"],
                "description": "Utilities - helper functions and common utilities"
            }
        }

        for pattern_name, pattern_info in patterns.items():
            pattern_files = []
            for file_path, file_info in ast_summaries.items():
                path_lower = file_path.lower()
                if any(keyword in path_lower for keyword in pattern_info["keywords"]):
                    pattern_files.append(file_path)
                elif any(indicator in str(file_info) for indicator in pattern_info["indicators"]):
                    pattern_files.append(file_path)

            if len(pattern_files) >= 2:
                module_def = ModuleDefinition(
                    module_id=f"pattern_{pattern_name.lower()}",
                    module_name=f"{pattern_info['description']}",
                    description=f"Module identified by {pattern_name} architectural pattern",
                    files=pattern_files,
                    dependencies=[],
                    priority=200 + list(patterns.keys()).index(pattern_name),
                    agent_prompt_hints=f"Focus on {pattern_name.lower()} concerns: {pattern_info['description']}"
                )
                modules.append(module_def)
        return modules

    def _merge_and_deduplicate_modules(self, modules: List[ModuleDefinition]) -> List[ModuleDefinition]:
        """Merge overlapping modules and remove duplicates."""
        if not modules:
            return modules
        seen_ids = set()
        unique_modules = []
        for module in modules:
            if module.module_id not in seen_ids:
                seen_ids.add(module.module_id)
                unique_modules.append(module)
        return unique_modules

    def _assign_priorities(self, modules: List[ModuleDefinition]) -> List[ModuleDefinition]:
        """Assign priorities to modules based on dependencies."""
        for i, module in enumerate(modules):
            if module.priority == 0:
                module.priority = i
        return sorted(modules, key=lambda m: m.priority)