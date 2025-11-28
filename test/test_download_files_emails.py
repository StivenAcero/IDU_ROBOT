import pytest
from unittest.mock import Mock, patch, mock_open
from src.download_files_emails import FileDrive


# -------------------------------------------------------------------
# FIXTURE PRINCIPAL SIN pytest-mock
# -------------------------------------------------------------------
@pytest.fixture
def file_drive():
    """Crea una instancia de FileDrive con TODOS los servicios externos mockeados."""

    # Mock de config
    mock_config = Mock()
    mock_config.scopes = ["email.read"]
    mock_config.label_email = "TEST_LABEL"
    mock_config.download_path = "/tmp"

    with patch("src.download_files_emails.IduConfig.load_config", return_value=mock_config), \
         patch("src.download_files_emails.GoogleCredentials.get_credentials", return_value=Mock()), \
         patch("src.download_files_emails.build") as mock_build, \
         patch("src.download_files_emails.logging.getLogger", return_value=Mock()):

        mock_gmail = Mock()
        mock_build.return_value = mock_gmail

        fd = FileDrive()
        fd._gmail_service = mock_gmail
        return fd


# -------------------------------------------------------------------
# TESTS get_or_create_label
# -------------------------------------------------------------------

def test_get_or_create_label_exists(file_drive):
    mock_labels = {"labels": [{"name": "DESCARGADO", "id": "123"}]}
    file_drive._gmail_service.users().labels().list().execute.return_value = mock_labels

    result = file_drive.get_or_create_label("DESCARGADO")
    assert result == "123"


def test_get_or_create_label_creates(file_drive):
    file_drive._gmail_service.users().labels().list().execute.return_value = {"labels": []}
    file_drive._gmail_service.users().labels().create().execute.return_value = {"id": "XYZ"}

    result = file_drive.get_or_create_label("DESCARGADO")
    assert result == "XYZ"


def test_get_or_create_label_error(file_drive):
    file_drive._gmail_service.users().labels().list.side_effect = Exception("ERROR")

    result = file_drive.get_or_create_label("DESCARGADO")
    assert result == ""


# -------------------------------------------------------------------
# TESTS search_emails_today_by_label
# -------------------------------------------------------------------

def test_search_emails_found(file_drive):
    file_drive._gmail_service.users().messages().list().execute.return_value = {
        "messages": [{"id": "1"}, {"id": "2"}]
    }

    result = file_drive.search_emails_today_by_label()
    assert result == ["1", "2"]


def test_search_emails_empty(file_drive):
    file_drive._gmail_service.users().messages().list().execute.return_value = {
        "messages": []
    }

    result = file_drive.search_emails_today_by_label()
    assert result == []


def test_search_emails_error(file_drive):
    file_drive._gmail_service.users().messages().list.side_effect = Exception("ERR")

    result = file_drive.search_emails_today_by_label()
    assert result == []


# -------------------------------------------------------------------
# TESTS get_attachments_from_email
# -------------------------------------------------------------------

def test_get_attachments_with_files(file_drive):
    file_drive._gmail_service.users().messages().get().execute.return_value = {
        "payload": {
            "parts": [
                {
                    "filename": "test.pdf",
                    "mimeType": "application/pdf",
                    "body": {"attachmentId": "A1", "size": 123}
                }
            ]
        }
    }

    result = file_drive.get_attachments_from_email("MSG1")
    assert len(result) == 1
    assert result[0]["filename"] == "test.pdf"
    assert result[0]["attachmentId"] == "A1"


def test_get_attachments_empty(file_drive):
    file_drive._gmail_service.users().messages().get().execute.return_value = {"payload": {}}

    result = file_drive.get_attachments_from_email("MSG1")
    assert result == []


def test_get_attachments_error(file_drive):
    file_drive._gmail_service.users().messages().get.side_effect = Exception("ERR")

    result = file_drive.get_attachments_from_email("MSG1")
    assert result == []


# -------------------------------------------------------------------
# TESTS download_attachment
# -------------------------------------------------------------------

def test_download_attachment_ok(file_drive):
    mock_attachment = {"data": b"SGVsbG8=".decode()}  # base64("Hola")
    file_drive._gmail_service.users().messages().attachments().get().execute.return_value = mock_attachment

    with patch("builtins.open", mock_open()):
        result = file_drive.download_attachment("MSG1", "A1", "test.txt")

    assert result is True


def test_download_attachment_error(file_drive):
    file_drive._gmail_service.users().messages().attachments().get.side_effect = Exception("ERR")

    result = file_drive.download_attachment("MSG1", "A1", "test.txt")
    assert result is False


# -------------------------------------------------------------------
# TEST add_downloaded_label
# -------------------------------------------------------------------

def test_add_downloaded_label_ok(file_drive):
    result = file_drive.add_downloaded_label("MSG1", "LBL")
    assert result is True


def test_add_downloaded_label_error(file_drive):
    file_drive._gmail_service.users().messages().modify.side_effect = Exception("ERR")

    result = file_drive.add_downloaded_label("MSG1", "LBL")
    assert result is False


# -------------------------------------------------------------------
# TESTS download_files
# -------------------------------------------------------------------

def test_download_files_no_label(file_drive):
    with patch.object(file_drive, "get_or_create_label", return_value=""):
        result = file_drive.download_files()

    assert result["total_correos"] == 0
    assert result["descargados"] == 0


def test_download_files_no_emails(file_drive):
    with patch.object(file_drive, "get_or_create_label", return_value="LBL"), \
         patch.object(file_drive, "search_emails_today_by_label", return_value=[]):

        result = file_drive.download_files()

    assert result["total_correos"] == 0
    assert result["total_adjuntos"] == 0


def test_download_files_success_flow(file_drive):
    with patch.object(file_drive, "get_or_create_label", return_value="LBL"), \
         patch.object(file_drive, "search_emails_today_by_label", return_value=["MSG1"]), \
         patch.object(file_drive, "get_attachments_from_email", return_value=[
             {"filename": "a.txt", "attachmentId": "A1", "size": 11}
         ]), \
         patch.object(file_drive, "download_attachment", return_value=True), \
         patch.object(file_drive, "add_downloaded_label", return_value=True):

        result = file_drive.download_files()

    assert result["total_correos"] == 1
    assert result["descargados"] == 1
    assert result["etiquetados"] == 1
    assert result["fallidos"] == 0


def test_download_files_attachment_fail(file_drive):
    with patch.object(file_drive, "get_or_create_label", return_value="LBL"), \
         patch.object(file_drive, "search_emails_today_by_label", return_value=["MSG1"]), \
         patch.object(file_drive, "get_attachments_from_email", return_value=[
             {"filename": "a.txt", "attachmentId": "A1", "size": 11}
         ]), \
         patch.object(file_drive, "download_attachment", return_value=False), \
         patch.object(file_drive, "add_downloaded_label", return_value=True):

        result = file_drive.download_files()

    assert result["fallidos"] == 1
    assert result["etiquetados"] == 0
