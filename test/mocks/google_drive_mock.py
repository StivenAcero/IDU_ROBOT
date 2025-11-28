from unittest.mock import Mock
from googleapiclient.errors import HttpError


class GoogleDriveFilesMock:
    """
    Mock realista que simula:
        service.files().list().execute()
        service.files().create().execute()
        service.files().update().execute()
    """

    def __init__(self):
        # Respuestas por defecto
        self._list_response = {"files": []}
        self._create_response = {"id": None}
        self._update_response = {}

        # Side effects (HttpError)
        self._list_error = None
        self._create_error = None
        self._update_error = None

        # Crear mocks de métodos
        self.list = Mock()
        self.create = Mock()
        self.update = Mock()

        # Conectar mock.execute() para cada método
        self.list.return_value.execute = self._exec_list
        self.create.return_value.execute = self._exec_create
        self.update.return_value.execute = self._exec_update

    # ------------------------------------------
    # LIST
    # ------------------------------------------
    def set_list_response(self, files):
        self._list_response = {"files": files}

    def set_list_error(self, err: HttpError):
        self._list_error = err

    def _exec_list(self):
        if self._list_error:
            raise self._list_error
        return self._list_response

    # ------------------------------------------
    # CREATE
    # ------------------------------------------
    def set_create_response(self, obj):
        self._create_response = obj

    def set_create_error(self, err: HttpError):
        self._create_error = err

    def _exec_create(self):
        if self._create_error:
            raise self._create_error
        return self._create_response

    # ------------------------------------------
    # UPDATE
    # ------------------------------------------
    def set_update_response(self, obj):
        self._update_response = obj

    def set_update_error(self, err: HttpError):
        self._update_error = err

    def _exec_update(self):
        if self._update_error:
            raise self._update_error
        return self._update_response


class GoogleDriveServiceMock:
    """
    Mock principal equivalente a build('drive', 'v3', credentials).
    Garantiza que service.files() SIEMPRE retorne el mismo objeto.
    """

    def __init__(self):
        self.files_mock = GoogleDriveFilesMock()
        self.files = Mock(return_value=self.files_mock)
