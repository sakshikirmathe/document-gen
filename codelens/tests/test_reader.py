"""
Unit tests for the Codebase Reader module.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from codelens.app.core.reader import CodebaseReader


@pytest.fixture
def temp_vbnet_project():
    """Create a temporary VB.net project structure for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create some VB.net files
        (temp_path / "Module1.vb").write_text("""
Namespace MyApp
    Module Module1
        Sub Main()
            Console.WriteLine("Hello, World!")
        End Sub
    End Module
End Namespace
""")

        (temp_path / "Form1.vb").write_text("""
Namespace MyApp.UI
    Public Class Form1
        Inherits System.Windows.Forms.Form

        Private Sub Form1_Load(sender As Object, e As EventArgs) Handles MyBase.Load
            Text = "Hello World Form"
        End Sub
    End Class
End Namespace
""")

        # Create a .vbproj file
        (temp_path / "TestProject.vbproj").write_text("""<?xml version="1.0" encoding="utf-8"?>
<Project ToolsVersion="15.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <PropertyGroup>
    <Configuration Condition=" '$(Configuration)' == '' ">Debug</Configuration>
    <Platform Condition=" '$(Platform)' == '' ">AnyCPU</Platform>
    <ProjectGuid>{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}</ProjectGuid>
    <OutputType>WinExe</OutputType>
    <RootNamespace>MyApp</RootNamespace>
    <AssemblyName>TestProject</AssemblyName>
    <TargetFrameworkVersion>v4.8</TargetFrameworkVersion>
    <FileAlignment>512</FileAlignment>
    <MyType>WindowsForms</MyType>
  </PropertyGroup>
  <ItemGroup>
    <Reference Include="System" />
    <Reference Include="System.Drawing" />
    <Reference Include="System.Windows.Forms" />
    <Reference Include="System.Data" />
    <Reference Include="System.Xml" />
  </ItemGroup>
  <ItemGroup>
    <Compile Include="Module1.vb" />
    <Compile Include="Form1.vb" />
    <Compile Include="My Project\AssemblyInfo.vb" />
    <Compile Include="My Project\Application.Designer.vb" />
    <Compile Include="My Project\Resources.resx" />
    <Compile Include="My Project\Settings.Designer.vb" />
  </ItemGroup>
  <ItemGroup>
    <EmbeddedResource Include="My Project\Resources.resx" />
  </ItemGroup>
  <ItemGroup>
    <None Include="My Project\Settings.settings" />
  </ItemGroup>
  <Import Project="$(MSBuildToolsPath)\Microsoft.VisualBasic.targets" />
</Project>
""")

        # Create excluded files to test exclusion logic
        (temp_path / "bin").mkdir()
        (temp_path / "bin" / "Debug").mkdir()
        (temp_path / "bin" / "Debug" / "TestProject.exe").write_text("fake binary")

        (temp_path / "obj").mkdir()
        (temp_path / "obj" / "Debug").mkdir()
        (temp_path / "obj" / "Debug" / "TestProject.exe").write_text("fake binary")

        (temp_path / ".vs").mkdir()
        (temp_path / ".vs" / "TestProject").mkdir()
        (temp_path / ".vs" / "TestProject" / "v15").mkdir()
        (temp_path / ".vs" / "TestProject" / "v15" / ".suo").write_text("fake suo")

        yield temp_path


@pytest.mark.asyncio
async def test_reader_initialization(temp_vbnet_project):
    """Test that the CodebaseReader initializes correctly."""
    reader = CodebaseReader(str(temp_vbnet_project))
    assert reader.source_path == temp_vbnet_project.resolve()
    assert len(reader.exclusions) > 0


@pytest.mark.asyncio
async def test_reader_walk_files(temp_vbnet_project):
    """Test that the reader walks files correctly and excludes appropriate files."""
    reader = CodebaseReader(str(temp_vbnet_project))

    files = []
    async for file_path in reader.walk_files():
        files.append(file_path.relative_to(temp_vbnet_project))

    # Convert to strings for easier comparison
    file_strs = [str(f) for f in files]

    # Should include VB.net files
    assert "Module1.vb" in file_strs
    assert "Form1.vb" in file_strs
    assert "TestProject.vbproj" in file_strs

    # Should exclude bin/obj/.vs directories
    assert not any("bin" in f for f in file_strs)
    assert not any("obj" in f for f in file_strs)
    assert not any(".vs" in f for f in file_strs)

    # Should include My Project files (not excluded by default in our implementation)
    # Actually, My Project/ is excluded by default, so let's check that
    # Looking at the exclusions, My Project/ IS in the exclusion list
    # So these should be excluded:
    assert not any("My Project" in f for f in file_strs)


@pytest.mark.asyncio
async def test_reader_read_file(temp_vbnet_project):
    """Test that the reader can read file contents correctly."""
    reader = CodebaseReader(str(temp_vbnet_project))

    # Read a VB.net file
    vb_file = temp_vbnet_project / "Module1.vb"
    content = await reader.read_file(vb_file)

    assert content is not None
    assert "Namespace MyApp" in content
    assert "Module Module1" in content
    assert "Sub Main()" in content
    assert 'Console.WriteLine("Hello, World!")' in content


@pytest.mark.asyncio
async def test_reader_read_codebase(temp_vbnet_project):
    """Test reading the entire codebase."""
    reader = CodebaseReader(str(temp_vbnet_project))

    file_contents = await reader.read_codebase()

    # Should have read our VB.net and project files
    assert "Module1.vb" in file_contents
    assert "Form1.vb" in file_contents
    assert "TestProject.vbproj" in file_contents

    # Should not have read excluded files
    assert not any("bin" in k for k in file_contents.keys())
    assert not any("obj" in k for k in file_contents.keys())
    assert not any(".vs" in k for k in file_contents.keys())

    # Check content of one file
    assert "Namespace MyApp" in file_contents["Module1.vb"]
    assert "Public Class Form1" in file_contents["Form1.vb"]


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])