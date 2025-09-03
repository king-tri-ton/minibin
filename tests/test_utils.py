import pytest
from app import format_bytes, get_object_declension

@pytest.mark.parametrize("input_bytes, expected_string", [
    (0, "0Б"),
    (512, "512.0 Б"),
    (2048, "2.0 КБ"),
    (1572864, "1.5 МБ"),
    (2147483648, "2.0 ГБ"),
])
def test_format_bytes(input_bytes, expected_string):
    """Тест: Проверяет правильное форматирование байтов в строки."""
    assert format_bytes(input_bytes) == expected_string

@pytest.mark.parametrize("count, expected_word", [
    (1, "объект"),
    (2, "объекта"),
    (4, "объекта"),
    (5, "объектов"),
    (10, "объектов"),
    (11, "объектов"),
    (19, "объектов"),
    (21, "объект"),
    (22, "объекта"),
    (25, "объектов"),
    (101, "объект"),
])
def test_get_object_declension(count, expected_word):
    """Тест: Проверяет правильное склонение слова 'объект' для разных чисел."""
    assert get_object_declension(count) == expected_word