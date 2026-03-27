"""
Codebase Reader module for CodeLens.
Handles async file walking, reading file contents, and applying exclusions.
"""

import os
import asyncio
from pathlib import Path
from typing import AsyncIterator, Dict, Set, List, Optional
import aiofiles
import structlog

logger = structlog.get_logger(__name__)


class CodebaseReader:
    """
    Asynchronously walks through a codebase directory, reads file contents,
    and applies exclusion patterns.
    """

    def __init__(self, source_path: str, exclusions: Optional[Set[str]] = None):
        self.source_path = Path(source_path).resolve()
        self.exclusions = exclusions or self._get_default_vbnet_exclusions()
        self.logger = logger.bind(component="CodebaseReader")

        if not self.source_path.exists():
            raise ValueError(f"Source path does not exist: {self.source_path}")
        if not self.source_path.is_dir():
            raise ValueError(f"Source path is not a directory: {self.source_path}")

    def _get_default_vbnet_exclusions(self) -> Set[str]:
        """
        Get default exclusion patterns for VB.net projects.
        Based on the implementation plan section 5.2.
        """
        return {
            # Compiled output
            "bin/",
            "obj/",
            # Visual Studio settings
            ".vs/",
            "*.user",
            "*.suo",
            # NuGet packages
            "packages/",
            # Designer and resource files (excluded by default)
            "*.Designer.vb",
            "*.resx",
            # VB.net project metadata
            "My Project/",
            # MSBuild cache
            "*.cache",
            # Standard exclusions
            ".git/",
            ".svn/",
            ".hg/",
            "__pycache__/",
            "*.pyc",
            ".pytest_cache/",
            ".coverage",
            "htmlcov/",
            ".tox/",
            ".venv/",
            "env/",
            "node_modules/",
            "bower_components/",
        }

    def _should_exclude(self, file_path: Path) -> bool:
        """
        Check if a file should be excluded based on exclusion patterns.
        """
        # Convert to relative path for pattern matching
        try:
            rel_path = file_path.relative_to(self.source_path)
        except ValueError:
            # File is outside source path
            return True

        # Check against exclusion patterns
        str_path = str(rel_path)
        for pattern in self.exclusions:
            if pattern.endswith("/"):
                # Directory pattern
                if any(part == pattern.rstrip("/") for part in rel_path.parts):
                    return True
                # Also check if path starts with the pattern
                if str_path.startswith(pattern):
                    return True
            elif "*" in pattern:
                # Wildcard pattern (simple implementation)
                import fnmatch
                if fnmatch.fnmatch(str_path, pattern) or fnmatch.fnmatch(file_path.name, pattern):
                    return True
            else:
                # Exact match
                if str_path == pattern or file_path.name == pattern:
                    return True

        return False

    async def walk_files(self) -> AsyncIterator[Path]:
        """
        Asynchronously walk through the source directory and yield file paths
        that are not excluded.
        """
        self.logger.info("Starting file walk", source_path=str(self.source_path))

        for root, dirs, files in os.walk(self.source_path):
            # Modify dirs in-place to skip excluded directories
            rel_root = Path(root).relative_to(self.source_path)
            dirs[:] = [
                d for d in dirs
                if not self._should_exclude(rel_root / d)
            ]

            for file in files:
                file_path = Path(root) / file
                if not self._should_exclude(file_path):
                    yield file_path

        self.logger.info("File walk completed")

    async def read_file(self, file_path: Path) -> Optional[str]:
        """
        Asynchronously read a file's contents.
        Returns None if the file cannot be read.
        """
        try:
            # Try UTF-8 first
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return content
        except UnicodeDecodeError:
            # Fallback to latin-1 for legacy VB.net files
            try:
                async with aiofiles.open(file_path, 'r', encoding='latin-1') as f:
                    content = await f.read()
                    self.logger.warning(
                        "File read with latin-1 encoding",
                        file=str(file_path.relative_to(self.source_path))
                    )
                    return content
            except Exception as e:
                self.logger.error(
                    "Failed to read file with fallback encoding",
                    file=str(file_path.relative_to(self.source_path)),
                    error=str(e)
                )
                return None
        except Exception as e:
            self.logger.error(
                "Failed to read file",
                file=str(file_path.relative_to(self.source_path)),
                error=str(e)
            )
            return None

    async def read_codebase(self) -> Dict[str, str]:
        """
        Read all non-excluded files in the codebase.
        Returns a dictionary mapping relative file paths to their contents.
        """
        self.logger.info("Starting codebase read")
        file_contents = {}

        async for file_path in self.walk_files():
            content = await self.read_file(file_path)
            if content is not None:
                # Store with relative path as key
                rel_path = file_path.relative_to(self.source_path)
                file_contents[str(rel_path)] = content
                self.logger.debug(
                    "File read successfully",
                    file=str(rel_path),
                    size=len(content)
                )

        self.logger.info(
            "Codebase read completed",
            total_files=len(file_contents)
        )
        return file_contents