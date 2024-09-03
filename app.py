import ctypes
import threading
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QTimer
from plyer import notification
import os
import sys

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
    notification.notify(
        title=title,
        message=message,
        app_icon=icon_path,
        timeout=5
    )

def empty_recycle_bin():
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
    update_icon()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    tray_icon = QSystemTrayIcon()
    
    initial_empty = is_recycle_bin_empty()
    tray_icon.setIcon(load_icon("icons/minibin-kt-empty.ico") if initial_empty else load_icon("icons/minibin-kt-full.ico"))
    
    tray_menu = QMenu()
    
    empty_action = QAction("Очистить корзину", triggered=empty_recycle_bin)
    exit_action = QAction("Выход", triggered=exit_program)
    
    tray_menu.addAction(empty_action)
    tray_menu.addAction(exit_action)
    
    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()
    
    timer = QTimer()
    timer.timeout.connect(periodic_update)
    timer.start(3000)
    
    sys.exit(app.exec())
