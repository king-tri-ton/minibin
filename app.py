import ctypes
import sys
import os
import subprocess # --- НОВЫЙ ИМПОРТ ---
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QTimer

# pywin32 нужен для создания ярлыков в Windows
try:
    import win32com.client
    import pythoncom
except ImportError:
    print("Ошибка: для работы функции автозагрузки необходима библиотека pywin32.")
    print("Пожалуйста, установите ее: pip install pywin32")
    win32com = None 

# Определение структуры SHQUERYRBINFO для Windows API
class SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("i64Size", ctypes.c_int64),
        ("i64NumItems", ctypes.c_int64)
    ]

# Функция для получения правильного пути к ресурсам (для PyInstaller)
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Функция для загрузки иконки
def load_icon(icon_path):
    return QIcon(resource_path(icon_path))

# Функция для отображения уведомлений
def show_notification(title, message, icon_path=None):
    tray_icon.showMessage(title, message, load_icon(icon_path), 5000)
    
# --- НОВАЯ ФУНКЦИЯ ---
def open_desktop_icon_settings():
    """ Открывает системное окно "Параметры значков рабочего стола" """
    try:
        # Эта команда напрямую вызывает нужный апплет панели управления
        command = 'rundll32.exe shell32.dll,Control_RunDLL desk.cpl,,0'
        subprocess.Popen(command, shell=True)
    except Exception as e:
        print(f"Не удалось открыть настройки значков рабочего стола: {e}")
        show_notification("Ошибка", "Не удалось открыть системные настройки.", "icons/minibin-kt-full.ico")


def add_to_startup():
    if not win32com:
        show_notification("Ошибка", "Библиотека pywin32 не найдена. Функция недоступна.", "icons/minibin-kt-full.ico")
        return

    executable_path = sys.executable
    app_name = os.path.splitext(os.path.basename(executable_path))[0]
    startup_folder = os.path.join(os.environ['PROGRAMDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'StartUp')
    shortcut_path = os.path.join(startup_folder, f"{app_name}.lnk")

    try:
        pythoncom.CoInitialize()
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(shortcut_path)
        shortcut.TargetPath = executable_path
        shortcut.WorkingDirectory = os.path.dirname(executable_path)
        shortcut.Description = "MiniBin - иконка корзины в системном трее"
        shortcut.IconLocation = executable_path
        shortcut.save()
        show_notification("Автозагрузка", "Программа успешно добавлена в автозагрузку.", "icons/minibin-kt-empty.ico")
    except Exception as e:
        print(f"Ошибка при добавлении в автозагрузку: {e}")
        show_notification("Ошибка прав доступа", "Для этого действия запустите программу от имени администратора.", "icons/minibin-kt-full.ico")
    finally:
        pythoncom.CoUninitialize()

# Функция очистки корзины
def empty_recycle_bin():
    if is_recycle_bin_empty():
        show_notification("Корзина", "Корзина уже пуста.", "icons/minibin-kt-empty.ico")
        return
    SHEmptyRecycleBin = ctypes.windll.shell32.SHEmptyRecycleBinW
    flags = 0x01 | 0x02 | 0x04
    result = SHEmptyRecycleBin(None, None, flags)
    if result == 0:
        show_notification("Корзина", "Корзина успешно очищена.", "icons/minibin-kt-empty.ico")
    else:
        show_notification("Корзина", f"Произошла ошибка при очистке корзины. Код ошибки: {result}", "icons/minibin-kt-full.ico")
    update_icon()

# Функция для открытия корзины
def open_recycle_bin():
    os.startfile("shell:RecycleBinFolder")

# Функция выхода из программы
def exit_program():
    QApplication.quit()

# Обработчик кликов по иконке в трее
def handle_tray_activation(reason):
    if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
        open_recycle_bin()
    elif reason == QSystemTrayIcon.ActivationReason.MiddleClick:
        empty_recycle_bin()

# Функция обновления иконки в трее
def update_icon():
    if is_recycle_bin_empty():
        tray_icon.setIcon(load_icon("icons/minibin-kt-empty.ico"))
    else:
        tray_icon.setIcon(load_icon("icons/minibin-kt-full.ico"))

# Функция для проверки, пуста ли корзина
def is_recycle_bin_empty():
    rbinfo = SHQUERYRBINFO()
    rbinfo.cbSize = ctypes.sizeof(SHQUERYRBINFO)
    result = ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(rbinfo))
    if result != 0:
        print(f"Ошибка при запросе состояния корзины. Код ошибки: {result}")
        return False
    return rbinfo.i64NumItems == 0

# --- Основной блок выполнения ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    tray_icon = QSystemTrayIcon()
    update_icon()

    # --- ИЗМЕНЕНИЯ В МЕНЮ ---
    tray_menu = QMenu()
    open_action = QAction("Открыть корзину", triggered=open_recycle_bin)
    empty_action = QAction("Очистить корзину", triggered=empty_recycle_bin)
    
    # Новые пункты меню для настроек
    startup_action = QAction("Добавить в автозагрузку", triggered=add_to_startup)
    desktop_icons_action = QAction("Настройки значков рабочего стола", triggered=open_desktop_icon_settings)
    
    exit_action = QAction("Выход", triggered=exit_program)

    tray_menu.addAction(open_action)
    tray_menu.addAction(empty_action)
    tray_menu.addSeparator()
    # Добавляем новые пункты в меню
    tray_menu.addAction(startup_action)
    tray_menu.addAction(desktop_icons_action)
    tray_menu.addSeparator()
    tray_menu.addAction(exit_action)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.activated.connect(handle_tray_activation)
    tray_icon.show()

    update_timer = QTimer()
    update_timer.timeout.connect(update_icon)
    update_timer.start(5000)

    sys.exit(app.exec())