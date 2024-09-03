import ctypes
import sys
import os
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer
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
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_icon(icon_path):
    return QIcon(resource_path(icon_path))

def show_notification(title, message, icon_path=None):
    notification.notify(
        title=title,
        message=message,
        app_icon=icon_path,
        timeout=5
    )

def empty_recycle_bin():
    SHEmptyRecycleBin = ctypes.windll.shell32.SHEmptyRecycleBinW
    flags = 0x01
    bin_path = ctypes.create_unicode_buffer(260)
    ctypes.windll.shell32.SHGetFolderPathW(0, 0x0005, 0, 0, bin_path)
    result = SHEmptyRecycleBin(None, bin_path, flags)

    if result == 0 or result == -2147418113:
        show_notification("Корзина", "Корзина успешно очищена.", resource_path("icons/minibin-kt-empty.ico"))
        update_icon()
    else:
        show_notification("Корзина", f"Произошла ошибка при очистке корзины. Код ошибки: {result}", resource_path("icons/minibin-kt-full.ico"))

def update_icon():
    if is_recycle_bin_empty():
        tray_icon.setIcon(load_icon("icons/minibin-kt-empty.ico"))
    else:
        tray_icon.setIcon(load_icon("icons/minibin-kt-full.ico"))

def is_recycle_bin_empty():
    rbinfo = SHQUERYRBINFO()
    rbinfo.cbSize = ctypes.sizeof(SHQUERYRBINFO)
    result = ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(rbinfo))

    if result != 0:
        print("Ошибка при запросе состояния корзины.")
        return False

    return rbinfo.i64NumItems == 0

def create_tray_icon():
    app = QApplication(sys.argv)
    tray_icon = QSystemTrayIcon()
    tray_icon.setIcon(load_icon("icons/minibin-kt-empty.ico"))

    tray_menu = QMenu()

    empty_action = QAction("Очистить корзину")
    empty_action.triggered.connect(empty_recycle_bin)
    tray_menu.addAction(empty_action)

    exit_action = QAction("Выход")
    exit_action.triggered.connect(app.quit)
    tray_menu.addAction(exit_action)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()

    # Timer for periodic updates
    timer = QTimer()
    timer.timeout.connect(update_icon)
    timer.start(3000)  # Update every 3 seconds

    return app

if __name__ == "__main__":
    app = create_tray_icon()
    sys.exit(app.exec())