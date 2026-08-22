import threading
from unittest.mock import MagicMock
import pytest
import anki.errors
from plugin import AnkiConnect


class TestSyncGracefulHandling:
    def setup_method(self):
        self.ac = AnkiConnect()
        self.mock_mw = MagicMock()
        self.mock_mw.pm.sync_auth.return_value = {"hkey": "test_key"}
        self.mock_mw.pm.media_syncing_enabled.return_value = True
        self.mock_mw.media_syncer.is_syncing.return_value = False
        self.ac.window = MagicMock(return_value=self.mock_mw)

    def test_sync_no_auth(self):
        self.mock_mw.pm.sync_auth.return_value = None
        with pytest.raises(Exception, match="sync: auth not configured"):
            self.ac.sync()
        assert not self.ac._sync_lock.locked()

    def test_sync_media_in_progress(self):
        self.mock_mw.media_syncer.is_syncing.return_value = True
        with pytest.raises(Exception, match="sync: media sync is currently in progress"):
            self.ac.sync()
        assert not self.ac._sync_lock.locked()

    def test_sync_concurrent_lock(self):
        self.ac._sync_lock.acquire()
        try:
            with pytest.raises(Exception, match="sync: another sync operation is currently in progress"):
                self.ac.sync()
        finally:
            self.ac._sync_lock.release()

    @pytest.mark.parametrize("error_message", [
        "Your AnkiWeb account is currently being synchronized by another client.",
        "AnkiWeb account locked: sync in progress by another client",
        "Server is busy, please wait a moment",
        "Sync conflict: simultaneous sync detected",
        "Rate limit reached: too many requests",
    ])
    def test_sync_ankiweb_busy_single_client_conflict(self, error_message):
        self.mock_mw.col.sync_collection.side_effect = anki.errors.SyncError(
            error_message,
            None,
            None,
            None,
            anki.errors.SyncErrorKind.OTHER,
        )
        with pytest.raises(Exception, match=f"sync: AnkiWeb sync error \\({error_message}\\)"):
            self.ac.sync()
        assert not self.ac._sync_lock.locked()

    def test_sync_auth_failure_clears_token(self):
        self.mock_mw.col.sync_collection.side_effect = anki.errors.SyncError(
            "invalid auth token",
            None,
            None,
            None,
            anki.errors.SyncErrorKind.AUTH,
        )
        with pytest.raises(Exception, match="sync: authentication failed"):
            self.ac.sync()
        self.mock_mw.pm.clear_sync_auth.assert_called_once()
        assert not self.ac._sync_lock.locked()

    @pytest.mark.parametrize("required_status", [2, 3, 4])
    def test_sync_full_sync_required(self, required_status):
        mock_out = MagicMock()
        mock_out.NO_CHANGES = 0
        mock_out.NORMAL_SYNC = 1
        mock_out.FULL_SYNC = 2
        mock_out.FULL_DOWNLOAD = 3
        mock_out.FULL_UPLOAD = 4
        mock_out.required = required_status

        self.mock_mw.col.sync_collection.return_value = mock_out
        with pytest.raises(Exception, match="sync: full sync required"):
            self.ac.sync()
        assert not self.ac._sync_lock.locked()

    def test_sync_success_normal_flow_and_no_double_sync(self):
        mock_out = MagicMock()
        mock_out.NO_CHANGES = 0
        mock_out.NORMAL_SYNC = 1
        mock_out.required = 1
        mock_out.host_number = 42
        mock_out.new_endpoint = "https://sync42.ankiweb.net"

        self.mock_mw.col.sync_collection.return_value = mock_out
        self.ac.sync()

        self.mock_mw.col.save.assert_called_once()
        self.mock_mw.pm.set_host_number.assert_called_once_with(42)
        self.mock_mw.pm.set_current_sync_url.assert_called_once_with("https://sync42.ankiweb.net")
        self.mock_mw.col._load_scheduler.assert_called_once()
        self.mock_mw.col.models._clear_cache.assert_called_once()
        self.mock_mw.reset.assert_called_once()
        self.mock_mw.toolbar.redraw.assert_called_once()
        self.mock_mw.media_syncer.start_monitoring.assert_called_once()
        # Verify mw.onSync is NEVER called (preventing double sync)
        self.mock_mw.onSync.assert_not_called()
        assert not self.ac._sync_lock.locked()

    def test_sync_backend_network_error_handled_cleanly(self):
        self.mock_mw.col.sync_collection.side_effect = anki.errors.NetworkError(
            "connection reset", None, None, None
        )
        with pytest.raises(Exception, match=r"sync: network error \(connection reset\)"):
            self.ac.sync()
        assert not self.ac._sync_lock.locked()

    def test_sync_headless_missing_optional_gui_elements(self):
        headless_mw = MagicMock(spec=[])
        headless_mw.pm = MagicMock()
        headless_mw.pm.sync_auth.return_value = {"hkey": "headless_key"}
        headless_mw.pm.media_syncing_enabled.return_value = False
        headless_col = MagicMock(spec=[])
        mock_out = MagicMock()
        mock_out.NO_CHANGES = 0
        mock_out.NORMAL_SYNC = 1
        mock_out.required = 0
        mock_out.host_number = 0
        mock_out.new_endpoint = None
        headless_col.sync_collection = MagicMock(return_value=mock_out)
        headless_mw.col = headless_col
        self.ac.window = MagicMock(return_value=headless_mw)

        # Should execute cleanly without raising AttributeError on missing GUI elements
        self.ac.sync()
        assert not self.ac._sync_lock.locked()
