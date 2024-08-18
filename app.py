# v4
import ctypes
import threading
import pystray
from pystray import MenuItem as item, Menu as menu
from PIL import Image, ImageDraw
import time

class SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("i64Size", ctypes.c_int64),
        ("i64NumItems", ctypes.c_int64)
    ]

def create_image(empty):
    # Создаем изображение с прозрачным фоном
    image = Image.new('RGBA', (32, 64), color=(0, 0, 0, 0))
    dc = ImageDraw.Draw(image)

    # Цвет заливки
    fill_color = (255, 255, 255, 255) if empty else (173, 216, 230, 255)  # Белый для пустой корзины, светло-голубой для заполненной
    
    # Рисуем заливку с прозрачными границами
    dc.rectangle([10, 10, 31, 63], fill=fill_color, outline=(0, 0, 0, 0), width=0)  # Прозрачные границы

    return image

def empty_recycle_bin(icon, item):
    # Функция для очистки корзины
    SHEmptyRecycleBin = ctypes.windll.shell32.SHEmptyRecycleBinW
    flags = 0x01  # SHERB_NOCONFIRMATION
    bin_path = ctypes.create_unicode_buffer(260)
    ctypes.windll.shell32.SHGetFolderPathW(0, 0x0005, 0, 0, bin_path)
    result = SHEmptyRecycleBin(None, bin_path, flags)

    if result == 0 or result == -2147418113:
        print("Корзина успешно очищена.")
        update_icon()
    else:
        print("Произошла ошибка при очистке корзины. Код ошибки:", result)

def exit_program(icon, item):
    icon.stop()

def update_icon():
    # Обновление иконки в зависимости от состояния корзины
    if is_recycle_bin_empty():
        tray_icon.icon = create_image(empty=True)
    else:
        tray_icon.icon = create_image(empty=False)

def is_recycle_bin_empty():
    rbinfo = SHQUERYRBINFO()
    rbinfo.cbSize = ctypes.sizeof(SHQUERYRBINFO)
    result = ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(rbinfo))

    # Если ошибка, считаем корзину непустой
    if result != 0:
        print("Ошибка при запросе состояния корзины.")
        return False

    # Если количество элементов в корзине больше 0, корзина не пуста
    return rbinfo.i64NumItems == 0

def periodic_update():
    while True:
        update_icon()
        time.sleep(10)  # Обновляем каждые 10 секунд

def create_tray_icon():
    menu_options = (item("Очистить корзину", empty_recycle_bin), item("Выход", exit_program))
    tray_menu = menu(*menu_options)
    global tray_icon

    # Сначала проверяем состояние корзины и создаем иконку с соответствующим цветом
    initial_empty = is_recycle_bin_empty()
    tray_icon = pystray.Icon("name", create_image(empty=initial_empty), "Minibin by King Triton", tray_menu)
    return tray_icon

if __name__ == "__main__":
    tray_icon = create_tray_icon()
    threading.Thread(target=periodic_update, daemon=True).start()
    tray_icon.run()
