import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta

from app import check_auto_cleanup

@pytest.fixture(autouse=True)
def mock_global_dependencies(mocker):
    """
    Автоматически "мокает" глобальные зависимости, чтобы они не мешали тестам.
    """
    mocker.patch("app.show_notification")
    mocker.patch("app.QTimer.singleShot")
    mocker.patch("app.pythoncom.CoInitialize")
    mocker.patch("app.pythoncom.CoUninitialize")
    # Добавляем мок для win32com, чтобы он не мешал тестам, где он не нужен
    mocker.patch("app.win32com.client.Dispatch")


def test_cleanup_does_nothing_when_disabled(mocker):
    """
    Тест: Проверяет, что функция автоочистки ничего не делает,
    если обе опции в настройках выключены.
    """
    mock_settings = {
        "clean_by_size_enabled": False,
        "clean_by_age_enabled": False
    }
    mocker.patch("app.load_settings", return_value=mock_settings)
    mock_get_status = mocker.patch("app.get_recycle_bin_status")

    check_auto_cleanup()

    mock_get_status.assert_not_called()


def test_cleanup_by_size_triggers_when_limit_exceeded(mocker):
    """
    Тест: Проверяет, что полная очистка корзины запускается,
    когда ее размер превышает установленный лимит.
    """
    mock_settings = {
        "clean_by_size_enabled": True,
        "size_limit_gb": 5,
        "clean_by_age_enabled": False
    }
    mocker.patch("app.load_settings", return_value=mock_settings)
    size_in_bytes = 6 * (1024 ** 3)
    mocker.patch("app.get_recycle_bin_status", return_value=(10, size_in_bytes))
    mock_empty_bin = mocker.patch("app.empty_recycle_bin")

    check_auto_cleanup()

    mock_empty_bin.assert_called_once()


def test_cleanup_by_age_deletes_only_old_files(mocker):
    """
    Тест: Проверяет, что очистка по возрасту удаляет только старые файлы,
    оставляя новые нетронутыми.
    """
    mock_settings = {
        "clean_by_size_enabled": False,
        "clean_by_age_enabled": True,
        "age_limit_days": 30
    }
    mocker.patch("app.load_settings", return_value=mock_settings)

    # --- КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: Создаем НЕЗАВИСИМЫЕ моки для каждого файла ---
    old_item_delete_verb = MagicMock()
    old_item_delete_verb.Name = "Удалить"
    
    new_item_delete_verb = MagicMock()
    new_item_delete_verb.Name = "Удалить"

    # Создаем мок "старого" файла
    old_item = MagicMock()
    old_item.ModifyDate = datetime.now() - timedelta(days=60)
    old_item.Verbs.return_value = [old_item_delete_verb]

    # Создаем мок "нового" файла
    new_item = MagicMock()
    new_item.ModifyDate = datetime.now() - timedelta(days=10)
    new_item.Verbs.return_value = [new_item_delete_verb]

    # Имитируем всю цепочку вызовов win32com
    # Нам нужно получить доступ к моку Dispatch, который мы создали в фикстуре
    mock_dispatch = mocker.patch("app.win32com.client.Dispatch")
    mock_dispatch.return_value.NameSpace.return_value.Items.return_value = [old_item, new_item]
    
    check_auto_cleanup()

    # Проверяем, что DoIt был вызван у "глагола" старого файла
    old_item_delete_verb.DoIt.assert_called_once()
    # А у "глагола" нового файла - НЕ был вызван
    new_item_delete_verb.DoIt.assert_not_called()