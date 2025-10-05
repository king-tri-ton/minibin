import ctypes
import sys
import os
import threading
import time
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
import winreg

class SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("i64Size", ctypes.c_int64),
        ("i64NumItems", ctypes.c_int64)
    ]

def save_setting(name, value):
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\MiniBinKT")
    winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, int(value))
    winreg.CloseKey(key)

def load_setting(name, default=True):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\MiniBinKT")
        value, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return bool(value)
    except FileNotFoundError:
        return default

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
    flags = 0x01 # SHERB_NOCONFIRMATION
    result = SHEmptyRecycleBin(None, None, flags)

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
        time.sleep(3)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    tray_icon = QSystemTrayIcon()
    tray_icon.setIcon(load_icon("icons/minibin-kt-empty.ico"))

    tray_menu = QMenu()

    open_action = QAction("Открыть корзину", triggered=open_recycle_bin)
    exit_action = QAction("Выход", triggered=exit_program)

    show_notification_flag = load_setting("show_notification")
    toggle_notification_action = QAction("Скрывать уведомление", checkable=True)
    toggle_notification_action.setChecked(not show_notification_flag)

    def toggle_notification():
        new_state = not toggle_notification_action.isChecked()
        save_setting("show_notification", new_state)

    toggle_notification_action.triggered.connect(toggle_notification)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()

    def show_notification_conditional(title, message, icon_path=None):
        if load_setting("show_notification"):
            tray_icon.showMessage(title, message, QIcon(resource_path(icon_path)), 5000)

    def empty_recycle_bin():
        SHEmptyRecycleBin = ctypes.windll.shell32.SHEmptyRecycleBinW
        flags = 0x01 # SHERB_NOCONFIRMATION
        result = SHEmptyRecycleBin(None, None, flags)

        if result == 0 or result == -2147418113:
            show_notification_conditional("Корзина", "Корзина успешно очищена.", "icons/minibin-kt-empty.ico")
        else:
            show_notification_conditional("Корзина", f"Произошла ошибка при очистке корзины. Код ошибки: {result}", "icons/minibin-kt-full.ico")

        update_icon()

    empty_action = QAction("Очистить корзину", triggered=empty_recycle_bin)

    tray_menu.addAction(open_action)
    tray_menu.addSeparator()
    tray_menu.addAction(empty_action)
    tray_menu.addAction(toggle_notification_action)
    tray_menu.addSeparator()
    tray_menu.addAction(exit_action)

    update_thread = threading.Thread(target=periodic_update, daemon=True)
    update_thread.start()

    sys.exit(app.exec())