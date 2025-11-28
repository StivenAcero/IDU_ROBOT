import pytest
from unittest.mock import Mock
from datetime import datetime
from googleapiclient.errors import HttpError

from src.email_drive import EmailDrive
from test.mocks.gmail_mock import GmailServiceMock


# -------------------------------------------------------------------
# FIXTURE PRINCIPAL
# -------------------------------------------------------------------
@pytest.fixture
def email_drive(mocker):
    """EmailDrive con Gmail API totalmente mockeado."""
    mock_config = Mock()
    mock_config.scopes = ["gmail"]
    mock_config.label_email = "IDU"
    mock_config.mailer_idu = "IDU"
    mock_config.email_subject = "Informe"
    mock_config.max_results_email = 20

    mocker.patch("src.email_drive.IduConfig.load_config", return_value=mock_config)
    mocker.patch("src.email_drive.GoogleCredentials.get_credentials", return_value=Mock())
    mocker.patch("src.email_drive.logging.getLogger", return_value=Mock())

    service = GmailServiceMock()
    mocker.patch("src.email_drive.build", return_value=service)

    ed = EmailDrive()
    ed._service = service
    ed._config = mock_config
    return ed


# -------------------------------------------------------------------
# TEST get_or_create_label
# -------------------------------------------------------------------
def test_get_or_create_label_exists(email_drive):
    email_drive._service.labels_mock.set_list_response(
        [{"id": "L1", "name": "IDU"}]
    )
    assert email_drive.get_or_create_label() == "L1"


def test_get_or_create_label_creates(email_drive):
    email_drive._service.labels_mock.set_list_response([])
    email_drive._service.labels_mock.set_create_response({"id": "NEWL"})
    assert email_drive.get_or_create_label() == "NEWL"


def test_get_or_create_label_error(email_drive):
    email_drive._service.labels_mock.set_list_error(
        HttpError(Mock(status=500), b"ERR")
    )
    assert email_drive.get_or_create_label() == ""


# -------------------------------------------------------------------
# TEST _search_by_subject
# -------------------------------------------------------------------
def test_search_by_subject_found(email_drive):
    email_drive._service.messages_mock.set_list_response(
        [{"id": "M1"}, {"id": "M2"}]
    )
    result = email_drive._search_by_subject("IDU", "2025/02/05")
    assert result == ["M1", "M2"]


def test_search_by_subject_empty(email_drive):
    email_drive._service.messages_mock.set_list_response([])
    assert email_drive._search_by_subject("IDU", "2025/02/05") == []


def test_search_by_subject_error(email_drive):
    email_drive._service.messages_mock.set_list_error(
        HttpError(Mock(status=500), b"ERR")
    )
    assert email_drive._search_by_subject("IDU", "2025/02/05") == []


# -------------------------------------------------------------------
# TEST search_emails_today
# -------------------------------------------------------------------
def test_search_emails_today(email_drive, mocker):
    # Mock del date.today() dentro del módulo src.email_drive
    fake_date = Mock()
    fake_date.today.return_value = datetime(2025, 2, 10).date()

    mocker.patch("src.email_drive.date", fake_date)

    # Gmail devuelve mensajes duplicados → deben quedar únicos
    email_drive._service.messages_mock.set_list_response(
        [{"id": "X1"}, {"id": "X1"}]
    )

    result = email_drive.search_emails_today()
    assert result == ["X1"]


# -------------------------------------------------------------------
# TEST _filter_emails_to_tag
# -------------------------------------------------------------------
def test_filter_emails_to_tag(email_drive):
    # message has only label A → need label B
    email_drive._service.messages_mock.set_get_response(
        {"labelIds": ["A"]}
    )
    result = email_drive._filter_emails_to_tag(["M1"], ["B"])
    assert result == ["M1"]


def test_filter_emails_to_tag_skip(email_drive):
    # already has label
    email_drive._service.messages_mock.set_get_response(
        {"labelIds": ["A", "B"]}
    )
    result = email_drive._filter_emails_to_tag(["M1"], ["A"])
    assert result == []


def test_filter_emails_to_tag_error(email_drive):
    email_drive._service.messages_mock.set_get_error(
        HttpError(Mock(status=500), b"ERR")
    )
    assert email_drive._filter_emails_to_tag(["M1"], ["A"]) == []


# -------------------------------------------------------------------
# TEST add_label_to_emails
# -------------------------------------------------------------------
def test_add_label_to_emails_empty(email_drive):
    assert email_drive.add_label_to_emails([], ["L1"]) == {'labeled': 0, 'failed': 0}


def test_add_label_to_emails_no_verify(email_drive, mocker):
    mocker.patch.object(email_drive, "_batch_modify_labels", return_value={'labeled': 1, 'failed': 0})
    assert email_drive.add_label_to_emails(["A"], ["L1"], verificar=False) == {'labeled': 1, 'failed': 0}


# -------------------------------------------------------------------
# TEST _batch_modify_labels
# -------------------------------------------------------------------
def test_batch_modify_labels_ok(email_drive):
    email_drive._service.messages_mock.set_batch_response({})
    assert email_drive._batch_modify_labels(["M1", "M2"], ["L1"]) == {
        'labeled': 2, 'failed': 0
    }


def test_batch_modify_labels_error(email_drive):
    email_drive._service.messages_mock.set_batch_error(
        HttpError(Mock(status=500), b"ERR")
    )
    assert email_drive._batch_modify_labels(["M1"], ["L1"]) == {
        'labeled': 0, 'failed': 1
    }


# -------------------------------------------------------------------
# TEST get_email_date
# -------------------------------------------------------------------
def test_get_email_date_ok(email_drive):
    email_drive._service.messages_mock.set_get_response({
        "payload": {
            "headers": [
                {"name": "Date", "value": "Fri, 14 Feb 2025 10:00:00 -0500"}
            ]
        }
    })

    assert email_drive.get_email_date("M1") == (2025, 2)


def test_get_email_date_error(email_drive):
    email_drive._service.messages_mock.set_get_error(
        HttpError(Mock(status=500), b"ERR")
    )
    assert email_drive.get_email_date("M1") == (None, None)


# -------------------------------------------------------------------
# TEST _group_emails_by_month
# -------------------------------------------------------------------
def test_group_emails_by_month(email_drive):
    # FIRST EMAIL: valid
    email_drive._service.messages_mock.set_get_response({
        "payload": {"headers": [{"name": "Date", "value": "Fri, 14 Feb 2025 10:00:00 -0500"}]}
    })

    # SECOND EMAIL: invalid date
    email_drive.get_email_date = Mock(side_effect=[(2025, 2), (None, None)])

    grouped, dateless = email_drive._group_emails_by_month(["A", "B"])

    assert grouped == {(2025, 2): ["A"]}
    assert dateless == ["B"]


# -------------------------------------------------------------------
# TEST _process_monthly_emails
# -------------------------------------------------------------------
def test_process_monthly_emails(email_drive, mocker):
    correos = {(2025, 2): ["A", "B"]}

    mocker.patch.object(email_drive, "get_or_create_label", return_value="L2")
    mocker.patch.object(email_drive, "add_label_to_emails", return_value={'labeled': 2})

    stats, total = email_drive._process_monthly_emails(correos, "L1")

    assert total == 2
    assert stats == {
        "Febrero 2025": {'total': 2, 'nuevos': 2}
    }


# -------------------------------------------------------------------
# TEST _process_dateless_emails
# -------------------------------------------------------------------
def test_process_dateless_emails(email_drive, mocker):
    mocker.patch.object(email_drive, "add_label_to_emails", return_value={'labeled': 1})

    stats, total = email_drive._process_dateless_emails(["X"], "L1")

    assert total == 1
    assert stats == {
        "Sin fecha": {'total': 1, 'nuevos': 1}
    }


def test_process_dateless_emails_empty(email_drive):
    stats, total = email_drive._process_dateless_emails([], "L1")
    assert stats == {}
    assert total == 0


# -------------------------------------------------------------------
# TEST final: label_idu_emails_per_month
# -------------------------------------------------------------------
def test_label_idu_emails_per_month_no_label(email_drive, mocker):
    mocker.patch.object(email_drive, "get_or_create_label", return_value="")
    assert email_drive.label_idu_emails_per_month() == {
        'exitoso': False,
        'error': 'No se pudo crear etiqueta padre'
    }


def test_label_idu_emails_per_month_no_emails(email_drive, mocker):
    mocker.patch.object(email_drive, "get_or_create_label", return_value="L1")
    mocker.patch.object(email_drive, "search_emails_today", return_value=[])

    result = email_drive.label_idu_emails_per_month()
    assert result["total_encontrados"] == 0
    assert result["procesados"] == 0


def test_label_idu_emails_per_month_full(email_drive, mocker):
    mocker.patch.object(email_drive, "get_or_create_label", return_value="L1")
    mocker.patch.object(email_drive, "search_emails_today", return_value=["A"])

    mocker.patch.object(email_drive, "_group_emails_by_month", return_value=(
        {(2025, 2): ["A"]},
        []
    ))

    mocker.patch.object(email_drive, "_process_monthly_emails", return_value=(
        {"Febrero 2025": {'total': 1, 'nuevos': 1}}, 1
    ))

    mocker.patch.object(email_drive, "_process_dateless_emails", return_value=({}, 0))

    result = email_drive.label_idu_emails_per_month()

    assert result["exitoso"] is True
    assert result["procesados"] == 1
