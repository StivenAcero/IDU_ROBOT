import pytest
from unittest.mock import Mock
from googleapiclient.errors import HttpError
from datetime import datetime
from src.upload_drive import UploadDrive
from test.mocks.google_drive_mock import GoogleDriveServiceMock


# ------------------------------------------------------------------------------
# FIXTURE PRINCIPAL — Driver Mockeado correctamente
# ------------------------------------------------------------------------------
@pytest.fixture
def upload_drive(mocker):
    """UploadDrive inicializado con servicio Google Drive simulado."""

    # Mock configuración
    mock_config = Mock()
    mock_config.scopes = ["drive"]
    mock_config.drive_folder_id = "ROOT"
    mock_config.download_path = "/local"

    # Parcheos obligatorios
    mocker.patch("src.upload_drive.IduConfig.load_config", return_value=mock_config)
    mocker.patch("src.upload_drive.GoogleCredentials.get_credentials", return_value=Mock())
    mocker.patch("src.upload_drive.logging.getLogger", return_value=Mock())
    mocker.patch("src.upload_drive.MediaFileUpload", return_value=Mock())

    # Servicio de Drive totalmente simulado
    service = GoogleDriveServiceMock()
    mocker.patch("src.upload_drive.build", return_value=service)

    ud = UploadDrive()
    ud._service = service
    ud._config = mock_config
    return ud


# ------------------------------------------------------------------------------
# TEST create_year_folder
# ------------------------------------------------------------------------------
def test_create_year_folder(upload_drive):
    upload_drive._service.files_mock.set_create_response({"id": "Y1"})
    assert upload_drive.create_year_folder() == "Y1"


def test_create_year_folder_error(upload_drive):
    upload_drive._service.files_mock.set_create_error(
        HttpError(Mock(status=500), b"ERR")
    )
    assert upload_drive.create_year_folder() is None


# ------------------------------------------------------------------------------
# TEST get_current_year_folder
# ------------------------------------------------------------------------------
def test_get_current_year_folder_found(upload_drive):
    upload_drive._service.files_mock.set_list_response(
        [{"id": "Y9", "name": "2025"}]
    )
    assert upload_drive.get_current_year_folder() == "Y9"


def test_get_current_year_folder_not_found(upload_drive, mocker):
    upload_drive._service.files_mock.set_list_response([])
    mocker.patch.object(upload_drive, "create_year_folder", return_value="NEWY")
    assert upload_drive.get_current_year_folder() == "NEWY"


def test_get_current_year_folder_error(upload_drive):
    upload_drive._service.files_mock.set_list_error(
        HttpError(Mock(status=500), b"ERR")
    )
    assert upload_drive.get_current_year_folder() is None


# ------------------------------------------------------------------------------
# TEST create_month_folder
# ------------------------------------------------------------------------------
def test_create_month_folder(upload_drive):
    upload_drive._service.files_mock.set_create_response({"id": "M55"})
    assert upload_drive.create_month_folder("Y") == "M55"


def test_create_month_folder_error(upload_drive):
    upload_drive._service.files_mock.set_create_error(
        HttpError(Mock(status=500), b"ERR")
    )
    assert upload_drive.create_month_folder("Y") is None


# ------------------------------------------------------------------------------
# TEST get_current_month_folder
# ------------------------------------------------------------------------------
def test_get_current_month_folder_found(upload_drive, mocker):

    # 🔥 Mockear el mes actual como “02”
    mocker.patch(
        "src.upload_drive.datetime",
        Mock(now=lambda: datetime(2025, 2, 10), strftime=datetime.strftime)
    )

    # Simular carpetas encontradas
    upload_drive._service.files_mock.set_list_response(
        [{"id": "M123", "name": "02 Febrero"}]
    )

    result = upload_drive.get_current_month_folder("YEAR1")
    assert result == "M123"


def test_get_current_month_folder_not_found(upload_drive, mocker):
    upload_drive._service.files_mock.set_list_response([])
    mocker.patch.object(upload_drive, "create_month_folder", return_value="NEW_M")
    assert upload_drive.get_current_month_folder("Y") == "NEW_M"


def test_get_current_month_folder_error(upload_drive):
    upload_drive._service.files_mock.set_list_error(
        HttpError(Mock(status=500), b"ERR")
    )
    assert upload_drive.get_current_month_folder("Y") is None


# ------------------------------------------------------------------------------
# TEST _validate_folders
# ------------------------------------------------------------------------------
def test_validate_folders_ok(upload_drive, mocker):
    mocker.patch.object(upload_drive, "get_current_year_folder", return_value="Y")
    mocker.patch.object(upload_drive, "get_current_month_folder", return_value="M")
    mocker.patch("os.path.exists", return_value=True)

    assert upload_drive._validate_folders() == ("Y", "M", "/local")


def test_validate_folders_fail_year(upload_drive, mocker):
    mocker.patch.object(upload_drive, "get_current_year_folder", return_value=None)
    assert upload_drive._validate_folders() is None


def test_validate_folders_fail_month(upload_drive, mocker):
    mocker.patch.object(upload_drive, "get_current_year_folder", return_value="Y")
    mocker.patch.object(upload_drive, "get_current_month_folder", return_value=None)
    assert upload_drive._validate_folders() is None


def test_validate_folders_fail_local(upload_drive, mocker):
    mocker.patch.object(upload_drive, "get_current_year_folder", return_value="Y")
    mocker.patch.object(upload_drive, "get_current_month_folder", return_value="M")
    mocker.patch("os.path.exists", return_value=False)
    assert upload_drive._validate_folders() is None


# ------------------------------------------------------------------------------
# TEST _upload_single_file
# ------------------------------------------------------------------------------
def test_upload_single_file_ok(upload_drive):
    upload_drive._service.files_mock.set_create_response({"id": "F1"})
    assert upload_drive._upload_single_file("/local/a.txt", "a.txt", "MID") == {
        "filename": "a.txt",
        "id": "F1",
    }


def test_upload_single_file_retry_success(upload_drive):
    err = HttpError(Mock(status=500), b"ERR")

    upload_drive._service.files_mock.set_create_error(err)

    # Luego de 2 errores, éxito
    upload_drive._service.files_mock._create_error = None
    upload_drive._service.files_mock.set_create_response({"id": "F77"})

    result = upload_drive._upload_single_file("/local/a.txt", "a.txt", "MID")
    assert result["id"] is not None


def test_upload_single_file_fail_final(upload_drive):
    upload_drive._service.files_mock.set_create_error(
        HttpError(Mock(status=500), b"ERR")
    )
    upload_drive._max_retries = 1  # Evita loops largos
    assert upload_drive._upload_single_file("/local/a.txt", "a.txt", "MID") is None


# ------------------------------------------------------------------------------
# TEST upload_files
# ------------------------------------------------------------------------------
def test_upload_files_success(upload_drive, mocker):
    mocker.patch.object(upload_drive, "_validate_folders", return_value=("Y", "M", "/local"))
    mocker.patch("os.listdir", return_value=["a.txt"])
    mocker.patch("os.path.isfile", return_value=True)

    mocker.patch.object(upload_drive, "_upload_single_file", return_value={"filename": "a.txt", "id": 1})

    res = upload_drive.upload_files()

    assert len(res["success"]) == 1
    assert res["failed"] == []


def test_upload_files_some_fail(upload_drive, mocker):
    mocker.patch.object(upload_drive, "_validate_folders", return_value=("Y", "M", "/local"))

    mocker.patch("os.listdir", return_value=["a.txt", "b.txt"])
    mocker.patch("os.path.isfile", return_value=True)

    upload_drive._upload_single_file = Mock(side_effect=[{"filename": "a.txt", "id": 1}, None])

    res = upload_drive.upload_files()

    assert len(res["success"]) == 1
    assert res["failed"] == ["b.txt"]


def test_upload_files_invalid(upload_drive, mocker):
    mocker.patch.object(upload_drive, "_validate_folders", return_value=None)

    res = upload_drive.upload_files()
    assert res["error"] == "Validación de carpetas falló"
