import pytest
from unittest.mock import Mock, patch
import pandas as pd

from src.sheet_service import SheetService


# ----------------------------------------------------------
# FIXTURE PRINCIPAL – crea SheetService con todo mockeado
# ----------------------------------------------------------
@pytest.fixture
def sheet_service(request):
    """
    Devuelve una instancia real de SheetService pero con
    IduConfig.load_config, GoogleCredentials.get_credentials y build parcheados.
    Parches se detienen automáticamente al finalizar el test.
    """
    # --- preparar mocks y patchers ---
    mock_config = Mock()
    mock_config.scopes = ["scope1"]
    mock_config.spreadsheet_id = "TEST_ID"
    mock_config.range_name = "Hoja1!A1:D100"

    # Mock del servicio build(...) y su .spreadsheets()
    mock_service = Mock()
    mock_spreadsheets = Mock()
    mock_service.spreadsheets.return_value = mock_spreadsheets

    p_load = patch("src.sheet_service.IduConfig.load_config", return_value=mock_config)
    p_creds = patch("src.sheet_service.GoogleCredentials.get_credentials", return_value=Mock())
    p_build = patch("src.sheet_service.build", return_value=mock_service)

    # Start patches
    started_load = p_load.start()
    started_creds = p_creds.start()
    started_build = p_build.start()

    # Asegurar que se detengan al terminar el test
    def fin():
        p_load.stop()
        p_creds.stop()
        p_build.stop()

    request.addfinalizer(fin)

    # Crear la instancia (constructor usará los parches ya iniciados)
    service = SheetService()

    # Reemplazar _spreadsheets por nuestro mock (asegura control total)
    service._spreadsheets = mock_spreadsheets

    # Preconfigurar comportamiento por defecto para values().get().execute() y batchUpdate().execute()
    mv = mock_spreadsheets.values.return_value
    mv.get.return_value.execute.return_value = {"values": []}
    mv.batchUpdate.return_value.execute.return_value = {}

    return service


# ----------------------------------------------------------
# read_sheet
# ----------------------------------------------------------
def test_read_sheet_ok(sheet_service):
    sheet_service._spreadsheets.values().get().execute.return_value = {
        "values": [["A", "B"], ["1", "2"]]
    }
    result = sheet_service.read_sheet()
    assert result == [["A", "B"], ["1", "2"]]


def test_read_sheet_error(sheet_service):
    sheet_service._spreadsheets.values().get().execute.side_effect = Exception("Boom")
    result = sheet_service.read_sheet()
    assert result == []


# ----------------------------------------------------------
# validate_missing_files
# ----------------------------------------------------------
def test_validate_missing_files_ok(sheet_service):
    data = [
        ["CHIPS", "ESTADO"],
        ["123", ""],
        ["456", "OK"],
        ["789", ""]
    ]
    count, registros, total = sheet_service.validate_missing_files(data)
    assert count == 2
    assert total == 3
    assert registros[0]["CHIPS"] == "123"
    assert registros[1]["CHIPS"] == "789"


def test_validate_missing_files_missing_columns(sheet_service):
    data = [
        ["A", "B"],
        ["x", "y"]
    ]
    count, regs, total = sheet_service.validate_missing_files(data)
    assert (count, regs, total) == (0, [], 0)


# ----------------------------------------------------------
# _estado_vacio
# ----------------------------------------------------------
def test_estado_vacio_fuera_de_rango(sheet_service):
    fila = ["solo una columna"]
    assert sheet_service._estado_vacio(fila, 3) is True


# ----------------------------------------------------------
# agrupar_chips_sin_estado
# ----------------------------------------------------------
def test_agrupar_chips(sheet_service):
    registros = [{"CHIPS": str(i)} for i in range(1, 11)]
    df = sheet_service.agrupar_chips_sin_estado(registros, max_por_grupo=5)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert df.iloc[0]["chips"] == ["1", "2", "3", "4", "5"]
    assert df.iloc[1]["chips"] == ["6", "7", "8", "9", "10"]


def test_agrupar_chips_sin_estado_lista_vacia(sheet_service):
    df = sheet_service.agrupar_chips_sin_estado([])
    assert df.empty
    assert list(df.columns) == ["solicitud", "chips"]


# ----------------------------------------------------------
# obtener_letra_columna
# ----------------------------------------------------------
def test_obtener_letra_columna_ok(sheet_service):
    encabezado = ["A", "B", "CHIPS"]
    assert sheet_service.obtener_letra_columna(encabezado, "CHIPS") == "C"


def test_obtener_letra_columna_error(sheet_service):
    with pytest.raises(ValueError):
        sheet_service.obtener_letra_columna(["X", "Y"], "CHIPS")


# ----------------------------------------------------------
# actualizar_estado_chips
# ----------------------------------------------------------
def test_actualizar_estado_ok(sheet_service):
    # Use encabezado donde CHIPS esté en idx 1 (como espera el test)
    encabezado = ["ESTADO", "CHIPS"]

    sheet_service.read_sheet = Mock(return_value=[
        encabezado,
        ["", "111"],
        ["", "222"],
    ])

    # batchUpdate -> execute retorna exitoso
    sheet_service._spreadsheets.values().batchUpdate().execute.return_value = {}

    updated = sheet_service.actualizar_estado_chips(
        spreadsheet_id="TEST",
        encabezado=encabezado,
        chips_list=["222"]
    )

    assert updated == 1


def test_actualizar_estado_no_estado_column(sheet_service):
    # Si encabezado no contiene 'ESTADO', obtener_letra_columna lanzará ValueError
    with pytest.raises(ValueError):
        sheet_service.actualizar_estado_chips(
            spreadsheet_id="ID",
            encabezado=["CHIPS", "OTRA"],
            chips_list=["123"]
        )


def test_actualizar_estado_no_chips_column(sheet_service):
    encabezado = ["ESTADO"]  # no CHIPS
    sheet_service.read_sheet = Mock(return_value=[encabezado])

    updated = sheet_service.actualizar_estado_chips(
        spreadsheet_id="ID",
        encabezado=encabezado,
        chips_list=["111"]
    )

    assert updated == 0


def test_actualizar_estado_sin_coincidencias(sheet_service):
    encabezado = ["ESTADO", "CHIPS"]
    sheet_service.read_sheet = Mock(return_value=[
        encabezado,
        ["", "111"]
    ])

    updated = sheet_service.actualizar_estado_chips(
        spreadsheet_id="ID",
        encabezado=encabezado,
        chips_list=["999"]
    )

    assert updated == 0


def test_actualizar_estado_batch_error(sheet_service):
    encabezado = ["ESTADO", "CHIPS"]
    sheet_service.read_sheet = Mock(return_value=[
        encabezado,
        ["", "111"]
    ])

    # Forzar que execute() lance
    sheet_service._spreadsheets.values().batchUpdate().execute.side_effect = Exception("boom")

    updated = sheet_service.actualizar_estado_chips(
        spreadsheet_id="ID",
        encabezado=encabezado,
        chips_list=["111"]
    )

    assert updated == 0


