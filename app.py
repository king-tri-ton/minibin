import ctypes
import sys
import os
import threading
import time
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction

class SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("i64Size", ctypes.c_int64),
        ("i64NumItems", ctypes.c_int64)
    ]

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_icon(icon_path):
    return QIcon(resource_path(icon_path))

def show_notification(title, message, icon_path=None):
    tray_icon.showMessage(title, message, QIcon(resource_path(icon_path)), 5000)

def empty_recycle_bin():
    SHEmptyRecycleBin = ctypes.windll.shell32.SHEmptyRecycleBinW
    flags = 0x01  # SHERB_NOCONFIRMATION
    bin_path = ctypes.create_unicode_buffer(260)
    ctypes.windll.shell32.SHGetFolderPathW(0, 0x0005, 0, 0, bin_path)
    result = SHEmptyRecycleBin(None, bin_path, flags)

    if result == 0 or result == -2147418113:
        show_notification("Корзина", "Корзина успешно очищена.", "icons/minibin-kt-empty.ico")
    else:
        show_notification("Корзина", f"Произошла ошибка при очистке корзины. Код ошибки: {result}", "icons/minibin-kt-full.ico")
    
    update_icon()

def open_recycle_bin():
    os.startfile("shell:RecycleBinFolder")

def exit_program():
    QApplication.quit()

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

def periodic_update():
    while True:
        update_icon()
        time.sleep(3)  # Интервал обновления в секундах

if __name__ == "__main__":
    app = QApplication(sys.argv)

    tray_icon = QSystemTrayIcon()
    tray_icon.setIcon(load_icon("icons/minibin-kt-empty.ico"))

    tray_menu = QMenu()
    open_action = QAction("Открыть корзину", triggered=open_recycle_bin)
    empty_action = QAction("Очистить корзину", triggered=empty_recycle_bin)
    exit_action = QAction("Выход", triggered=exit_program)

    tray_menu.addAction(open_action)
    tray_menu.addAction(empty_action)
    tray_menu.addAction(exit_action)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()

    # Запуск таймера в отдельном потоке
    update_thread = threading.Thread(target=periodic_update, daemon=True)
    update_thread.start()

    sys.exit(app.exec())
