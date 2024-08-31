import ctypes
import threading
import pystray
from pystray import MenuItem as item, Menu as menu
from PIL import Image
import time
import os
import sys
from plyer import notification

class SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("i64Size", ctypes.c_int64),
        ("i64NumItems", ctypes.c_int64)
    ]

def resource_path(relative_path):
    """ Получает путь к ресурсам, поддерживает работу с PyInstaller. """
    try:
        # Путь к ресурсу в режиме сборки
        base_path = sys._MEIPASS
    except AttributeError:
        # Путь к ресурсу в режиме разработки
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_icon(icon_path):
    return Image.open(resource_path(icon_path))

def show_notification(title, message, icon_path=None):
    notification.notify(
        title=title,
        message=message,
        app_icon=icon_path,  # Можно оставить пустым или указать путь к иконке
        timeout=5  # Время отображения уведомления
    )

def empty_recycle_bin(icon, item):
    SHEmptyRecycleBin = ctypes.windll.shell32.SHEmptyRecycleBinW
    flags = 0x01  # SHERB_NOCONFIRMATION
    bin_path = ctypes.create_unicode_buffer(260)
    ctypes.windll.shell32.SHGetFolderPathW(0, 0x0005, 0, 0, bin_path)
    result = SHEmptyRecycleBin(None, bin_path, flags)

    if result == 0 or result == -2147418113:
        show_notification("Корзина", "Корзина успешно очищена.", resource_path("icons/minibin-kt-empty.ico"))
        update_icon()
    else:
        show_notification("Корзина", f"Произошла ошибка при очистке корзины. Код ошибки: {result}", "icons/minibin-kt-full.ico")

def exit_program(icon, item):
    icon.stop()

def update_icon():
    if is_recycle_bin_empty():
        tray_icon.icon = load_icon("icons/minibin-kt-empty.ico")
    else:
        tray_icon.icon = load_icon("icons/minibin-kt-full.ico")

def is_recycle_bin_empty():
    rbinfo = SHQUERYRBINFO()
    rbinfo.cbSize = ctypes.sizeof(SHQUERYRBINFO)
    result = ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(rbinfo))

    if result != 0:
        print("Ошибка при запросе состояния корзины.")
        return False

    return rbinfo.i64NumItems == 0

def periodic_update():
    while True:
        update_icon()
        time.sleep(3)

def create_tray_icon():
    menu_options = (item("Очистить корзину", empty_recycle_bin), item("Выход", exit_program))
    tray_menu = menu(*menu_options)
    global tray_icon

    initial_empty = is_recycle_bin_empty()
    tray_icon = pystray.Icon("name", load_icon("icons/minibin-kt-empty.ico") if initial_empty else load_icon("icons/minibin-kt-full.ico"), "Minibin от King Triton", tray_menu)
    return tray_icon

if __name__ == "__main__":
    tray_icon = create_tray_icon()
    threading.Thread(target=periodic_update, daemon=True).start()
    tray_icon.run()