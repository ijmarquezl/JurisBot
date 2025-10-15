
import pytest
import json
from unittest.mock import MagicMock, PropertyMock

# Import the function to be tested
from app.tools import get_template_placeholders

# Mock the dependencies that are not available in the test environment
import sys
sys.modules['docx'] = MagicMock()


@pytest.fixture
def mock_docx_document(mocker):
    """Fixture to create a mock docx.Document object."""
    mock_doc = MagicMock()

    # Mock paragraphs
    mock_para1 = MagicMock()
    type(mock_para1).runs = PropertyMock(return_value=[MagicMock(text='{{'), MagicMock(text='nombre_completo'), MagicMock(text='}}')])
    
    mock_para2 = MagicMock()
    type(mock_para2).runs = PropertyMock(return_value=[MagicMock(text='El demandado, {{  demandado_nombre  }}, con domicilio en {{domicilio}}.')])

    mock_doc.paragraphs = [mock_para1, mock_para2]

    # Mock tables
    mock_cell1 = MagicMock()
    type(mock_cell1).runs = PropertyMock(return_value=[MagicMock(text='Celda con {{  monto_deuda | currency  }}')])
    
    mock_cell_para = MagicMock()
    type(mock_cell_para).runs = PropertyMock(return_value=[MagicMock(text='Párrafo en celda con {{fecha_contrato}}')])
    
    mock_cell2 = MagicMock()
    type(mock_cell2).runs = PropertyMock(return_value=[]) # Empty cell
    type(mock_cell2).paragraphs = [mock_cell_para]


    mock_table = MagicMock()
    mock_row = MagicMock()
    mock_row.cells = [mock_cell1, mock_cell2]
    mock_table.rows = [mock_row]
    mock_doc.tables = [mock_table]

    mocker.patch('app.tools.docx.Document', return_value=mock_doc)
    return mock_doc

def test_get_placeholders_robust(mocker, mock_docx_document):
    """
    Tests the robust placeholder extraction logic.
    It should find placeholders split across runs, with extra whitespace,
    and inside paragraphs and tables.
    """
    # Mock os.path.exists to prevent FileNotFoundError
    mocker.patch('os.path.exists', return_value=True)

    # Call the function
    result_json = get_template_placeholders('dummy_template.docx')
    result_data = json.loads(result_json)

    # Define expected placeholders. The order doesn't matter.
    expected_placeholders = {
        'nombre_completo',
        'demandado_nombre',
        'domicilio',
        'monto_deuda | currency',
        'fecha_contrato'
    }

    # Assert that the extracted placeholders match the expected ones
    assert isinstance(result_data, list)
    assert set(result_data) == expected_placeholders

def test_get_placeholders_no_placeholders(mocker):
    """
    Tests the case where the document has no placeholders.
    It should return an error message.
    """
    mock_doc = MagicMock()
    mock_para = MagicMock()
    type(mock_para).text = PropertyMock(return_value='This is a normal text without fields.')
    type(mock_para).runs = [MagicMock(text='This is a normal text without fields.')]
    mock_doc.paragraphs = [mock_para]
    mock_doc.tables = []
    
    mocker.patch('app.tools.docx.Document', return_value=mock_doc)
    mocker.patch('os.path.exists', return_value=True)

    result_json = get_template_placeholders('no_placeholders.docx')
    result_data = json.loads(result_json)

    assert 'error' in result_data
    assert "No placeholders like '{field}' found" in result_data['error']

def test_get_placeholders_file_not_found(mocker):
    """
    Tests the case where the template file does not exist.
    """
    mocker.patch('os.path.exists', return_value=False)
    
    result_json = get_template_placeholders('non_existent_template.docx')
    result_data = json.loads(result_json)

    assert 'error' in result_data
    assert "not found" in result_data['error']

