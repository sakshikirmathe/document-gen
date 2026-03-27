"""
File tree data models for CodeLens.
Defines the data structures for representing the codebase structure.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from pathlib import Path


class FileNode(BaseModel):
    """
    Represents a single file in the codebase.
    """
    path: str = Field(..., description="Relative path from project root")
    name: str = Field(..., description="File name")
    size: int = Field(..., description="File size in bytes")
    content: Optional[str] = Field(
        default=None,
        description="File content (loaded on demand)"
    )
    is_binary: bool = Field(
        default=False,
        description="Whether the file is binary"
    )
    language: Optional[str] = Field(
        default=None,
        description="Detected programming language (e.g., 'vbnet')"
    )

    class Config:
        json_encoders = {
            # Don't include content in JSON output by default to avoid large responses
            str: lambda v: v[:100] + "..." if len(v) > 100 else v
        }


class FileTree(BaseModel):
    """
    Represents the entire codebase as a tree structure.
    """
    root_path: str = Field(..., description="Absolute path to project root")
    files: List[FileNode] = Field(
        default_factory=list,
        description="List of all files in the codebase"
    )
    total_files: int = Field(
        default=0,
        description="Total number of files"
    )
    total_size: int = Field(
        default=0,
        description="Total size of all files in bytes"
    )
    language_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of files by language"
    )

    def add_file(self, file_node: FileNode) -> None:
        """Add a file to the tree."""
        self.files.append(file_node)
        self.total_files += 1
        self.total_size += file_node.size

        if file_node.language:
            self.language_breakdown[file_node.language] = \
                self.language_breakdown.get(file_node.language, 0) + 1

    def get_file_by_path(self, path: str) -> Optional[FileNode]:
        """Get a file by its relative path."""
        for file in self.files:
            if file.path == path:
                return file
        return None

    def get_files_by_language(self, language: str) -> List[FileNode]:
        """Get all files of a specific language."""
        return [f for f in self.files if f.language == language]

    def get_vbnet_files(self) -> List[FileNode]:
        """Get all VB.net files."""
        return self.get_files_by_language("vbnet")

    class Config:
        json_encoders = {
            # Don't include content in JSON output by default
            FileNode: lambda node: node.dict(exclude={"content"})
        }