import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta

import app
from app import empty_recycle_bin, restore_last_deleted_item

@pytest.fixture(autouse=True)
def mock_dependencies(mocker):
    mocker.patch("app.show_notification")
    mocker.patch("app.QTimer.singleShot")
    mocker.patch("app.pythoncom.CoInitialize")
    mocker.patch("app.pythoncom.CoUninitialize")
    mocker.patch("app.win32com.client.Dispatch")
    mocker.patch("app.ctypes")

def test_empty_recycle_bin_does_nothing_if_already_empty(mocker):
    mocker.patch("app.is_recycle_bin_empty", return_value=True)
    empty_recycle_bin()
    app.ctypes.windll.shell32.SHEmptyRecycleBinW.assert_not_called()

def test_empty_recycle_bin_calls_api_if_not_empty(mocker):
    mocker.patch("app.is_recycle_bin_empty", return_value=False)
    # --- ИСПРАВЛЕНИЕ: "Мокаем" update_icon, чтобы избежать ошибки с tray_icon ---
    mocker.patch("app.update_icon")
    
    empty_recycle_bin()
    
    app.ctypes.windll.shell32.SHEmptyRecycleBinW.assert_called_once()

def test_restore_last_item_finds_latest_and_restores_it(mocker):
    mocker.patch("app.is_recycle_bin_empty", return_value=False)

    restore_verb_for_older_item = MagicMock(Name="Восстановить")
    restore_verb_for_latest_item = MagicMock(Name="Восстановить")

    older_item = MagicMock()
    older_item.ModifyDate = datetime.now() - timedelta(days=2)
    older_item.Verbs.return_value = [restore_verb_for_older_item]

    latest_item = MagicMock()
    latest_item.ModifyDate = datetime.now() - timedelta(hours=1)
    latest_item.Verbs.return_value = [restore_verb_for_latest_item]

    app.win32com.client.Dispatch.return_value.NameSpace.return_value.Items.return_value = [older_item, latest_item]
    
    restore_last_deleted_item()

    restore_verb_for_latest_item.DoIt.assert_called_once()
    restore_verb_for_older_item.DoIt.assert_not_called()