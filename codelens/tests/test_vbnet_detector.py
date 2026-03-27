"""
Unit tests for the VB.net Detector module.
"""

import pytest
from pathlib import Path
from codelens.app.core.vbnet_detector import VBNetDetector


@pytest.fixture
def vbnet_detector():
    """Create a VBNetDetector instance for testing."""
    return VBNetDetector()


def test_vbnet_detector_initialization(vbnet_detector):
    """Test that the VBNetDetector initializes correctly."""
    assert vbnet_detector is not None
    assert len(vbnet_detector.vbnet_keywords) > 0
    assert len(vbnet_detector.vbnet_attributes) > 0
    assert len(vbnet_detector.framework_patterns) > 0
    assert len(vbnet_detector.data_access_patterns) > 0


def test_detect_vbnet_file(vbnet_detector):
    """Test detection of a VB.net file."""
    vbnet_content = '''
Namespace MyApp
    Module Module1
        Sub Main()
            Console.WriteLine("Hello, World!")
        End Sub
    End Module
End Namespace
'''

    file_path = Path("Module1.vb")
    is_vbnet = vbnet_detector.detect_language(file_path, vbnet_content)
    assert is_vbnet is True


def test_detect_non_vbnet_file(vbnet_detector):
    """Test that non-VB.net files are not detected as VB.net."""
    python_content = '''
def main():
    print("Hello, World!")
    return 0

if __name__ == "__main__":
    main()
'''

    file_path = Path("main.py")
    is_vbnet = vbnet_detector.detect_language(file_path, python_content)
    assert is_vbnet is False


def test_detect_vbnet_by_extension(vbnet_detector):
    """Test that .vb files are detected by extension even with minimal content."""
    minimal_vb = '''
' Just a comment
'''

    file_path = Path("Test.vb")
    is_vbnet = vbnet_detector.detect_language(file_path, minimal_vb)
    assert is_vbnet is True


def test_detect_frameworks(vbnet_detector):
    """Test framework detection."""
    winforms_content = '''
Imports System.Windows.Forms

Public Class MainForm
    Inherits Form

    Private Sub Button1_Click(sender As Object, e As EventArgs) Handles Button1.Click
        MessageBox.Show("Hello")
    End Sub
End Class
'''

    frameworks = vbnet_detector.detect_frameworks(winforms_content)
    assert 'WinForms' in frameworks


def test_detect_data_access(vbnet_detector):
    """Test data access technology detection."""
    ado_content = '''
Imports System.Data.SqlClient

Public Class DataAccess
    Public Function GetData() As DataTable
        Using conn As New SqlConnection("connection string")
            Using cmd As New SqlCommand("SELECT * FROM Table", conn)
                Dim adapter As New SqlDataAdapter(cmd)
                Dim dt As New DataTable
                adapter.Fill(dt)
                Return dt
            End Using
        End Using
    End Function
End Class
'''

    data_access = vbnet_detector.detect_data_access(ado_content)
    assert 'ADO.NET' in data_access


def test_comprehensive_vbnet_analysis(vbnet_detector):
    """Test comprehensive analysis of a VB.net file."""
    vbnet_content = '''
Namespace MyApp.DataAccess
    ''' <summary>
    ''' Handles database operations
    ''' </summary>
    Public Class CustomerRepository
        Inherits BaseRepository

        Public Function GetCustomerById(id As Integer) As Customer
            Using conn As New SqlConnection(_connectionString)
                Using cmd As New SqlCommand("SELECT * FROM Customers WHERE Id = @Id", conn)
                    cmd.Parameters.AddWithValue("@Id", id)
                    Using reader As SqlDataReader = cmd.ExecuteReader()
                        If reader.Read()
                            Return New Customer With {
                                .Id = reader.GetInt32(0),
                                .Name = reader.GetString(1),
                                .Email = reader.GetString(2)
                            }
                        End If
                    End Using
                End Using
            End Using

            Return Nothing
        End Function
    End Class
End Namespace
'''

    file_path = Path("CustomerRepository.vb")
    analysis = vbnet_detector.analyze_vbnet_file(file_path, vbnet_content)

    # Basic properties
    assert analysis['is_vbnet'] is True
    assert analysis['has_namespace'] is True
    assert analysis['has_class'] is True
    assert analysis['line_count'] > 0
    assert analysis['code_lines'] > 0

    # Keywords found
    assert 'Namespace' in analysis['keywords_found']
    assert 'Class' in analysis['keywords_found']
    assert 'Function' in analysis['keywords_found']
    assert 'End Function' in analysis['keywords_found']
    assert 'End Class' in analysis['keywords_found']
    assert 'End Namespace' in analysis['keywords_found']
    assert 'Using' in analysis['keywords_found']
    assert 'New' in analysis['keywords_found']

    # Attributes found
    assert 'summary' in analysis['attributes_found']

    # Framework detection (should be none in this pure data access example)
    # Actually, SqlClient suggests ADO.NET which is data access, not a UI framework

    # Data access detection
    assert 'ADO.NET' in analysis['data_access']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])