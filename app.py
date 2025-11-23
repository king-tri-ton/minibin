import ctypes
import sys
import os
import threading
import time
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction, QCursor
from PyQt6.QtCore import QTimer, QPoint
import winreg
from settings import SettingsWindow, load_setting

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

def open_recycle_bin():
    os.startfile("shell:RecycleBinFolder")

def open_settings():
    global settings_window
    if 'settings_window' not in globals() or settings_window is None:
        settings_window = SettingsWindow()
    settings_window.show()
    settings_window.raise_()
    settings_window.activateWindow()

def exit_program():
    QApplication.quit()

def update_icon():
    if is_recycle_bin_empty():
        tray_icon.setIcon(load_icon("icons/minibin-kt-empty.ico"))
    else:
        tray_icon.setIcon(load_icon("icons/minibin-kt-full.ico"))
    
    # Принудительное обновление трея для Windows 11
    if not tray_icon.isVisible():
        tray_icon.hide()
        tray_icon.show()

def is_recycle_bin_empty():
    rbinfo = SHQUERYRBINFO()
    rbinfo.cbSize = ctypes.sizeof(SHQUERYRBINFO)
    result = ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(rbinfo))
    if result != 0:
        return False
    return rbinfo.i64NumItems == 0

def empty_recycle_bin():
    SHEmptyRecycleBin = ctypes.windll.shell32.SHEmptyRecycleBinW
    
    show_confirmation = load_setting("show_confirmation", False)
    flags = 0x00 if show_confirmation else 0x01
    
    result = SHEmptyRecycleBin(None, None, flags)
    show_notifications = load_setting("show_notification", True)
    
    if result == 0 or result == -2147418113:
        if show_notifications:
            icon = load_icon("icons/minibin-kt-empty.ico")
            tray_icon.showMessage("Корзина", "Корзина успешно очищена.", icon, 5000)
    else:
        if show_notifications:
            tray_icon.showMessage("Корзина", f"Произошла ошибка при очистке корзины. Код ошибки: {result}", load_icon("icons/minibin-kt-full.ico"), 5000)
    
    # Обновляем иконку с небольшой задержкой для стабильности
    QTimer.singleShot(100, update_icon)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    tray_icon = QSystemTrayIcon()
    tray_icon.setIcon(load_icon("icons/minibin-kt-empty.ico"))
    
    tray_menu = QMenu()
    open_action = QAction("Открыть корзину", triggered=open_recycle_bin)
    empty_action = QAction("Очистить корзину", triggered=empty_recycle_bin)
    settings_action = QAction("Настройки", triggered=open_settings)
    exit_action = QAction("Выход", triggered=exit_program)
    
    tray_menu.addAction(open_action)
    tray_menu.addSeparator()
    tray_menu.addAction(empty_action)
    tray_menu.addAction(settings_action)
    tray_menu.addSeparator()
    tray_menu.addAction(exit_action)
    
    # Функция для показа меню над панелью задач
    def show_tray_menu(reason):
        if reason == QSystemTrayIcon.ActivationReason.Context:
            # Получаем геометрию иконки в трее
            icon_geometry = tray_icon.geometry()
            menu_height = tray_menu.sizeHint().height()
            # Позиционируем меню над иконкой в трее
            tray_menu.popup(QPoint(icon_geometry.x(), icon_geometry.y() - menu_height))
    
    tray_icon.activated.connect(show_tray_menu)
    tray_icon.show()
    
    # Используем QTimer вместо threading для обновления иконки
    update_timer = QTimer()
    update_timer.timeout.connect(update_icon)
    update_timer.start(3000)
    
    sys.exit(app.exec())