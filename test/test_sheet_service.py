import pytest
from unittest.mock import Mock

from src.sheet_service import SheetService


# -------------------------------------------------------------------
# FIXTURE PRINCIPAL
# -------------------------------------------------------------------
@pytest.fixture
def sheet_service(mocker):
    """Fixture que crea una instancia mockeada de SheetService."""
    service = SheetService()

    # Mock de servicio interno de Google para no llamar a la API real
    mock_spreadsheets = mocker.Mock()
    mock_values = mocker.Mock()
    mock_values.batchUpdate.return_value.execute.return_value = {}

    mock_spreadsheets.values.return_value = mock_values
    service._spreadsheets = mock_spreadsheets

    return service


# -------------------------------------------------------------------
# TESTS EXISTENTES (NO MODIFICADOS)
# -------------------------------------------------------------------

def test_read_sheet_ok(sheet_service, mocker):
    mock_result = {"values": [["A", "B"], ["1", "2"]]}
    mocker.patch.object(sheet_service._spreadsheets.values(), "get", return_value=Mock(execute=lambda: mock_result))

    result = sheet_service.read_sheet()
    assert result == [["A", "B"], ["1", "2"]]


def test_read_sheet_error(sheet_service, mocker):
    mocker.patch.object(sheet_service._spreadsheets.values(), "get", side_effect=Exception("Error"))

    result = sheet_service.read_sheet()
    assert result == []


def test_validate_missing_files_ok(sheet_service):
    data = [
        ["CHIPS", "ESTADO"],
        ["A1", ""],
        ["A2", " "],
        ["A3", "OK"],
    ]
    total, registros, filas_total = sheet_service.validate_missing_files(data)

    assert total == 2
    assert filas_total == 3
    assert registros[0]["CHIPS"] == "A1"
    assert registros[1]["CHIPS"] == "A2"


def test_validate_missing_files_missing_columns(sheet_service):
    data = [
        ["X", "Y"],
        ["data1", "data2"],
    ]

    total, registros, filas = sheet_service.validate_missing_files(data)
    assert total == 0
    assert registros == []
    assert filas == 0


def test_agrupar_chips_empty(sheet_service):
    df = sheet_service.agrupar_chips_sin_estado([])
    assert df.empty
    assert list(df.columns) == ["solicitud", "chips"]


def test_agrupar_chips(sheet_service):
    registros = [
        {"CHIPS": "A1"},
        {"CHIPS": "A2"},
        {"CHIPS": "A3"},
        {"CHIPS": "A4"},
        {"CHIPS": "A5"},
        {"CHIPS": "A6"},
    ]

    df = sheet_service.agrupar_chips_sin_estado(registros, max_por_grupo=5)

    assert len(df) == 2
    assert df.iloc[0]["chips"] == ["A1", "A2", "A3", "A4", "A5"]
    assert df.iloc[1]["chips"] == ["A6"]


def test_obtener_letra_columna_ok(sheet_service):
    encabezado = ["CHIPS", "ESTADO"]
    letra = sheet_service.obtener_letra_columna(encabezado, "ESTADO")
    assert letra == "B"


def test_obtener_letra_columna_error(sheet_service):
    encabezado = ["A", "B", "C"]
    with pytest.raises(ValueError):
        sheet_service.obtener_letra_columna(encabezado, "ESTADO")


def test_actualizar_estado_ok(sheet_service, mocker):
    encabezado = ["ESTADO", "CHIPS"]
    sheet_service.read_sheet = Mock(return_value=[
        encabezado,
        ["", "111"],
        ["", "222"],
    ])

    mock_batch = mocker.Mock()
    sheet_service._spreadsheets.values.return_value = mock_batch
    mock_batch.batchUpdate.return_value.execute.return_value = {}

    updated = sheet_service.actualizar_estado_chips(
        spreadsheet_id="ID",
        encabezado=encabezado,
        chips_list=["111"]
    )

    assert updated == 1


def test_actualizar_estado_no_estado_column(sheet_service):
    with pytest.raises(ValueError):
        sheet_service.actualizar_estado_chips(
            spreadsheet_id="ID",
            encabezado=["CHIPS"],
            chips_list=["111"]
        )


def test_actualizar_estado_no_chips_column(sheet_service, mocker):
    """Debe retornar 0 cuando falta la columna CHIPS."""
    mocker.patch.object(
        sheet_service, 
        "obtener_letra_columna", 
        side_effect=[None, None]  # Retorna None para ambas columnas
    )
    
    updated = sheet_service.actualizar_estado_chips(
        spreadsheet_id="ID",
        encabezado=["ESTADO"],
        chips_list=["111"]
    )
    
    assert updated == 0


def test_actualizar_estado_sin_coincidencias(sheet_service, mocker):
    encabezado = ["ESTADO", "CHIPS"]
    sheet_service.read_sheet = Mock(return_value=[
        encabezado,
        ["", "111"],
        ["", "222"],
    ])

    mocker.patch.object(sheet_service._spreadsheets, "values", return_value=mocker.Mock())

    updated = sheet_service.actualizar_estado_chips(
        spreadsheet_id="ID",
        encabezado=encabezado,
        chips_list=["999"]
    )

    assert updated == 0


def test_actualizar_estado_batch_error(sheet_service, mocker):
    encabezado = ["ESTADO", "CHIPS"]
    sheet_service.read_sheet = Mock(return_value=[
        encabezado,
        ["", "111"]
    ])

    mock_values = mocker.Mock()
    mock_values.batchUpdate.side_effect = Exception("ERROR")
    sheet_service._spreadsheets.values.return_value = mock_values

    updated = sheet_service.actualizar_estado_chips(
        spreadsheet_id="ID",
        encabezado=encabezado,
        chips_list=["111"]
    )

    assert updated == 0


# -------------------------------------------------------------------
# NUEVOS TESTS PARA 100% COVERAGE
# -------------------------------------------------------------------

def test_agrupar_chips_empty_direct():
    """Cubre la línea 43 del archivo."""
    service = SheetService()
    df = service.agrupar_chips_sin_estado([])

    assert df.empty
    assert list(df.columns) == ["solicitud", "chips"]


def test_actualizar_estado_columna_estado_none(sheet_service, mocker):
    """Cubre líneas 111–112: if not columna_estado → return 0."""
    mocker.patch.object(sheet_service, "obtener_letra_columna", return_value=None)

    updated = sheet_service.actualizar_estado_chips(
        spreadsheet_id="ID",
        encabezado=["CHIPS"],
        chips_list=["111"]
    )

    assert updated == 0



