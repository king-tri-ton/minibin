import json
from unittest.mock import mock_open, call
from app import load_settings, save_settings, DEFAULT_SETTINGS

def test_load_settings_returns_defaults_if_file_not_found(mocker):
    mocker.patch("app.os.path.exists", return_value=False)
    settings = load_settings()
    assert settings == DEFAULT_SETTINGS

def test_load_settings_returns_defaults_if_file_is_corrupt(mocker):
    mocker.patch("app.os.path.exists", return_value=True)
    mocker.patch("builtins.open", mock_open(read_data="невалидный json"))
    settings = load_settings()
    assert settings == DEFAULT_SETTINGS

def test_load_settings_loads_from_valid_file(mocker):
    mocker.patch("app.os.path.exists", return_value=True)
    valid_settings = {"clean_by_size_enabled": True, "size_limit_gb": 10}
    valid_json = json.dumps(valid_settings)
    mocker.patch("builtins.open", mock_open(read_data=valid_json))
    settings = load_settings()
    assert settings == valid_settings

def test_save_settings_writes_to_file(mocker):
    """Тест: save_settings правильно вызывает функцию записи в файл."""
    m = mock_open()
    mocker.patch("builtins.open", m)
    
    my_settings = {"test": "value"}
    save_settings(my_settings)

    m.assert_called_once_with('settings.json', 'w', encoding='utf-8')
    
    # --- ИСПРАВЛЕНИЕ: Проверяем итоговый результат, а не количество вызовов ---
    # Собираем все вызовы .write() в одну строку
    handle = m()
    written_data = "".join(c.args[0] for c in handle.write.call_args_list)
    
    # Сравниваем с ожидаемым результатом
    expected_data = json.dumps(my_settings, indent=4)
    assert written_data == expected_data