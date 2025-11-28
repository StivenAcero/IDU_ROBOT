from unittest.mock import Mock


class GmailMessagesMock:
    """Simula users().messages() en Gmail API."""

    def __init__(self):
        self._list_response = {"messages": []}
        self._list_error = None

        self._get_response = {}
        self._get_error = None

        self._batch_response = {}
        self._batch_error = None

        # Métodos mockeados
        self.list = Mock()
        self.list.return_value.execute = self._exec_list

        self.get = Mock()
        self.get.return_value.execute = self._exec_get

        self.batchModify = Mock()
        self.batchModify.return_value.execute = self._exec_batch

    def set_list_response(self, messages):
        self._list_response = {"messages": messages}

    def set_list_error(self, err):
        self._list_error = err

    def _exec_list(self):
        if self._list_error:
            raise self._list_error
        return self._list_response

    def set_get_response(self, resp):
        self._get_response = resp

    def set_get_error(self, err):
        self._get_error = err

    def _exec_get(self):
        if self._get_error:
            raise self._get_error
        return self._get_response

    def set_batch_response(self, resp):
        self._batch_response = resp

    def set_batch_error(self, err):
        self._batch_error = err

    def _exec_batch(self):
        if self._batch_error:
            raise self._batch_error
        return self._batch_response


class GmailLabelsMock:
    """Simula users().labels() en Gmail API."""

    def __init__(self):
        self._list_response = {"labels": []}
        self._list_error = None

        self._create_response = {}
        self._create_error = None

        self.list = Mock()
        self.list.return_value.execute = self._exec_list

        self.create = Mock()
        self.create.return_value.execute = self._exec_create

    def set_list_response(self, labels):
        self._list_response = {"labels": labels}

    def set_list_error(self, err):
        self._list_error = err

    def _exec_list(self):
        if self._list_error:
            raise self._list_error
        return self._list_response

    def set_create_response(self, resp):
        self._create_response = resp

    def set_create_error(self, err):
        self._create_error = err

    def _exec_create(self):
        if self._create_error:
            raise self._create_error
        return self._create_response


class GmailServiceMock:
    """Servicio Gmail completo (users().labels(), users().messages() )."""

    def __init__(self):
        self.labels_mock = GmailLabelsMock()
        self.messages_mock = GmailMessagesMock()

        users = Mock()
        users.labels.return_value = self.labels_mock
        users.messages.return_value = self.messages_mock

        self.users = Mock(return_value=users)
