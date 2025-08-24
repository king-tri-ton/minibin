import ctypes
import ctypes.wintypes
import sys
import os
import subprocess
import json
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QDialog, 
                             QVBoxLayout, QHBoxLayout, QCheckBox, QComboBox, 
                             QLabel, QDialogButtonBox)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QTimer

# pywin32 нужен для создания ярлыков в Windows
try:
    import win32com.client
    import pythoncom
except ImportError:
    print("Ошибка: для работы функций автозагрузки/восстановления необходима библиотека pywin32.")
    print("Пожалуйста, установите ее: pip install pywin32")
    win32com = None 

# --- НОВЫЙ БЛОК: НАСТРОЙКИ ---
SETTINGS_FILE = 'settings.json'
DEFAULT_SETTINGS = {
    "clean_by_size_enabled": False,
    "size_limit_gb": 5,
    "clean_by_age_enabled": False,
    "age_limit_days": 30,
    "cleanup_interval_minutes": 60 
}

# --- НОВЫЙ КЛАСС: ОКНО НАСТРОЕК ---
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки автоочистки")
        self.setWindowIcon(load_icon("icons/minibin-kt-empty.ico"))
        self.setMinimumWidth(350)

        self.settings = load_settings()
        self.interval_map = {
            "15 минут": 15, "1 час": 60, "6 часов": 360, 
            "12 часов": 720, "1 день": 1440, "1 неделя": 10080
        }

        # --- Создание виджетов ---
        self.size_checkbox = QCheckBox("Очищать корзину, если ее размер превышает:")
        self.size_combo = QComboBox()
        self.size_combo.addItems(["1 ГБ", "2 ГБ", "5 ГБ", "10 ГБ", "20 ГБ", "50 ГБ"])
        
        self.age_checkbox = QCheckBox("Удалять файлы старше:")
        self.age_combo = QComboBox()
        self.age_combo.addItems(["7 дней", "14 дней", "30 дней", "60 дней", "90 дней"])

        self.interval_label = QLabel("Проверять каждые:")
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(list(self.interval_map.keys()))

        # Кнопки OK/Отмена
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept_settings)
        self.button_box.rejected.connect(self.reject)

        # --- Компоновка ---
        layout = QVBoxLayout(self)
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(self.size_checkbox)
        size_layout.addWidget(self.size_combo)
        layout.addLayout(size_layout)

        age_layout = QHBoxLayout()
        age_layout.addWidget(self.age_checkbox)
        age_layout.addWidget(self.age_combo)
        layout.addLayout(age_layout)

        interval_layout = QHBoxLayout()
        interval_layout.addWidget(self.interval_label)
        interval_layout.addWidget(self.interval_combo)
        layout.addLayout(interval_layout)

        layout.addWidget(self.button_box)

        self.load_widgets_from_settings()

    def load_widgets_from_settings(self):
        self.size_checkbox.setChecked(self.settings.get("clean_by_size_enabled", False))
        self.size_combo.setCurrentText(f"{self.settings.get('size_limit_gb', 5)} ГБ")
        
        self.age_checkbox.setChecked(self.settings.get("clean_by_age_enabled", False))
        self.age_combo.setCurrentText(f"{self.settings.get('age_limit_days', 30)} дней")

        # Находим ключ (текст) по значению (минутам)
        current_interval_minutes = self.settings.get("cleanup_interval_minutes", 60)
        for text, minutes in self.interval_map.items():
            if minutes == current_interval_minutes:
                self.interval_combo.setCurrentText(text)
                break
    
    def accept_settings(self):
        self.settings["clean_by_size_enabled"] = self.size_checkbox.isChecked()
        self.settings["size_limit_gb"] = int(self.size_combo.currentText().replace(" ГБ", ""))
        
        self.settings["clean_by_age_enabled"] = self.age_checkbox.isChecked()
        self.settings["age_limit_days"] = int(self.age_combo.currentText().replace(" дней", ""))

        self.settings["cleanup_interval_minutes"] = self.interval_map[self.interval_combo.currentText()]
        
        save_settings(self.settings)
        self.accept()

# --- НОВЫЕ ФУНКЦИИ: РАБОТА С НАСТРОЙКАМИ ---
def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass # Если файл поврежден или не читается, вернем настройки по умолчанию
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)
    except IOError as e:
        print(f"Ошибка при сохранении настроек: {e}")

# Определение структуры SHQUERYRBINFO для Windows API
class SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("i64Size", ctypes.c_int64),
        ("i64NumItems", ctypes.c_int64)
    ]

# --- НОВАЯ ФУНКЦИЯ: ДВИЖОК АВТООЧИСТКИ ---
def check_auto_cleanup():
    settings = load_settings()
    is_size_enabled = settings.get("clean_by_size_enabled", False)
    is_age_enabled = settings.get("clean_by_age_enabled", False)

    # Если обе опции выключены, ничего не делаем
    if not is_size_enabled and not is_age_enabled:
        return

    # --- Проверка по размеру ---
    if is_size_enabled:
        _, size_bytes = get_recycle_bin_status()
        size_limit_bytes = settings.get("size_limit_gb", 5) * (1024 ** 3)
        if size_bytes > size_limit_bytes:
            show_notification("Автоочистка", f"Размер корзины превысил {settings['size_limit_gb']} ГБ. Начинаю очистку.", "icons/minibin-kt-full.ico")
            empty_recycle_bin()
            # После полной очистки нет смысла проверять файлы по возрасту
            return 
    
    # --- Проверка по возрасту файлов ---
    if is_age_enabled:
        age_limit_days = settings.get("age_limit_days", 30)
        cutoff_date = datetime.now() - timedelta(days=age_limit_days)
        items_to_delete = []

        try:
            pythoncom.CoInitialize()
            shell = win32com.client.Dispatch("Shell.Application")
            recycle_bin = shell.NameSpace(10)
            
            for item in recycle_bin.Items():
                try:
                    deleted_date = item.ModifyDate.replace(tzinfo=None) # Убираем часовой пояс для сравнения
                    if deleted_date < cutoff_date:
                        items_to_delete.append(item)
                except Exception:
                    continue
            
            if items_to_delete:
                count = len(items_to_delete)
                show_notification("Автоочистка", f"Удаляю {count} {get_object_declension(count)} старше {age_limit_days} дней.", "icons/minibin-kt-empty.ico")
                for item in items_to_delete:
                    for verb in item.Verbs():
                        verb_name = verb.Name.replace('&', '')
                        if verb_name in ("Удалить", "Delete"):
                            verb.DoIt()
                            break
                QTimer.singleShot(1000, update_icon)
        except Exception as e:
            print(f"Ошибка при автоочистке по возрасту: {e}")
        finally:
            pythoncom.CoUninitialize()

# --- НОВАЯ ФУНКЦИЯ: ОТКРЫТИЕ ОКНА НАСТРОЕК ---
def open_settings_dialog():
    dialog = SettingsDialog()
    # exec() открывает окно и ждет, пока оно закроется
    if dialog.exec():
        # Если пользователь нажал "OK", перезапускаем таймер автоочистки с новым интервалом
        print("Настройки сохранены, перезапускаю таймер автоочистки.")
        restart_cleanup_timer()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_icon(icon_path):
    return QIcon(resource_path(icon_path))

def show_notification(title, message, icon_path=None):
    tray_icon.showMessage(title, message, load_icon(icon_path), 5000)
    
def open_desktop_icon_settings():
    try:
        command = 'rundll32.exe shell32.dll,Control_RunDLL desk.cpl,,0'
        subprocess.Popen(command, shell=True)
    except Exception as e:
        print(f"Не удалось открыть настройки значков рабочего стола: {e}")
        show_notification("Ошибка", "Не удалось открыть системные настройки.", "icons/minibin-kt-full.ico")

def format_bytes(size_bytes):
    if size_bytes == 0: return "0Б"
    size_name = ("Б", "КБ", "МБ", "ГБ", "ТБ")
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def get_object_declension(count):
    if 10 < count % 100 < 20: return "объектов"
    last_digit = count % 10
    if last_digit == 1: return "объект"
    if 2 <= last_digit <= 4: return "объекта"
    return "объектов"

def add_to_startup():
    if not win32com:
        show_notification("Ошибка", "Библиотека pywin32 не найдена.", "icons/minibin-kt-full.ico")
        return
    # ... (остальной код функции без изменений)
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

def restore_last_deleted_item():
    if is_recycle_bin_empty():
        show_notification("Корзина", "Корзина пуста, нечего восстанавливать.", "icons/minibin-kt-empty.ico")
        return
    latest_item, latest_date = None, None
    try:
        pythoncom.CoInitialize()
        shell = win32com.client.Dispatch("Shell.Application")
        recycle_bin = shell.NameSpace(10)
        for item in recycle_bin.Items():
            try:
                deleted_date = item.ModifyDate
            except Exception: continue
            if latest_date is None or deleted_date > latest_date:
                latest_date, latest_item = deleted_date, item
        if latest_item:
            item_name, restored = latest_item.Name, False
            for verb in latest_item.Verbs():
                verb_name = verb.Name.replace('&', '')
                if verb_name in ("Восстановить", "Restore"):
                    verb.DoIt()
                    restored = True
                    break
            if restored:
                show_notification("Восстановление", f"Объект '{item_name}' успешно восстановлен.", "icons/minibin-kt-empty.ico")
                QTimer.singleShot(1000, update_icon)
            else:
                show_notification("Ошибка", f"Не удалось выполнить действие 'Восстановить' для объекта '{item_name}'.", "icons/minibin-kt-full.ico")
        else: show_notification("Ошибка", "Не удалось найти объект для восстановления.", "icons/minibin-kt-full.ico")
    except Exception as e:
        print(f"Ошибка при восстановлении: {e}")
        show_notification("Ошибка", "Произошла критическая ошибка при попытке восстановления.", "icons/minibin-kt-full.ico")
    finally:
        pythoncom.CoUninitialize()

def empty_recycle_bin():
    if is_recycle_bin_empty():
        show_notification("Корзина", "Корзина уже пуста.", "icons/minibin-kt-empty.ico")
        return
    # ... (остальной код функции без изменений)
    SHEmptyRecycleBin = ctypes.windll.shell32.SHEmptyRecycleBinW
    flags = 0x01 | 0x02 | 0x04
    result = SHEmptyRecycleBin(None, None, flags)
    if result == 0:
        show_notification("Корзина", "Корзина успешно очищена.", "icons/minibin-kt-empty.ico")
    else:
        show_notification("Корзина", f"Произошла ошибка при очистке корзины. Код ошибки: {result}", "icons/minibin-kt-full.ico")
    update_icon()

def open_recycle_bin():
    os.startfile("shell:RecycleBinFolder")

def exit_program():
    QApplication.quit()

def handle_tray_activation(reason):
    if reason == QSystemTrayIcon.ActivationReason.DoubleClick: open_recycle_bin()
    elif reason == QSystemTrayIcon.ActivationReason.MiddleClick: empty_recycle_bin()

def update_icon():
    count, size_bytes = get_recycle_bin_status()
    if count == 0:
        tray_icon.setIcon(load_icon("icons/minibin-kt-empty.ico"))
        tray_icon.setToolTip("Корзина пуста")
    else:
        tray_icon.setIcon(load_icon("icons/minibin-kt-full.ico"))
        object_word = get_object_declension(count)
        tooltip_text = f"В корзине: {count} {object_word}\nРазмер: {format_bytes(size_bytes)}"
        tray_icon.setToolTip(tooltip_text)

def get_recycle_bin_status():
    rbinfo = SHQUERYRBINFO()
    rbinfo.cbSize = ctypes.sizeof(SHQUERYRBINFO)
    result = ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(rbinfo))
    if result != 0:
        print(f"Ошибка при запросе состояния корзины. Код ошибки: {result}")
        return 0, 0
    return rbinfo.i64NumItems, rbinfo.i64Size

def is_recycle_bin_empty():
    count, _ = get_recycle_bin_status()
    return count == 0

# --- Глобальные переменные ---
mutex_handle = None
app = None
tray_icon = None
cleanup_timer = None

# --- НОВАЯ ФУНКЦИЯ: ПЕРЕЗАПУСК ТАЙМЕРА АВТООЧИСТКИ ---
def restart_cleanup_timer():
    global cleanup_timer
    if cleanup_timer:
        cleanup_timer.stop()
    
    settings = load_settings()
    interval_ms = settings.get("cleanup_interval_minutes", 60) * 60 * 1000
    
    cleanup_timer = QTimer()
    cleanup_timer.timeout.connect(check_auto_cleanup)
    cleanup_timer.start(interval_ms)

# --- Основной блок выполнения ---
if __name__ == "__main__":
    mutex_name = "{E429B518-24A4-4D64-905D-03225016DE46}-MiniBin"
    ERROR_ALREADY_EXISTS = 183
    mutex_handle = ctypes.windll.kernel32.CreateMutexW(None, True, mutex_name)
    if ctypes.windll.kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    tray_icon = QSystemTrayIcon()
    update_icon()

    # --- ИЗМЕНЕНИЯ В МЕНЮ ---
    tray_menu = QMenu()
    open_action = QAction("Открыть корзину", triggered=open_recycle_bin)
    empty_action = QAction("Очистить корзину", triggered=empty_recycle_bin)
    restore_action = QAction("Восстановить последнее", triggered=restore_last_deleted_item)
    settings_action = QAction("Настроить автоочистку...", triggered=open_settings_dialog) # Новый пункт
    startup_action = QAction("Добавить в автозагрузку", triggered=add_to_startup)
    desktop_icons_action = QAction("Настройки значков рабочего стола", triggered=open_desktop_icon_settings)
    exit_action = QAction("Выход", triggered=exit_program)

    tray_menu.addAction(open_action)
    tray_menu.addAction(empty_action)
    tray_menu.addAction(restore_action)
    tray_menu.addSeparator()
    tray_menu.addAction(settings_action) # Добавлен в меню
    tray_menu.addSeparator()
    tray_menu.addAction(startup_action)
    tray_menu.addAction(desktop_icons_action)
    tray_menu.addSeparator()
    tray_menu.addAction(exit_action)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.activated.connect(handle_tray_activation)
    tray_icon.show()

    # --- ИЗМЕНЕНИЯ В ТАЙМЕРАХ ---
    # Таймер для обновления иконки (частый)
    update_timer = QTimer()
    update_timer.timeout.connect(update_icon)
    update_timer.start(5000)

    # Таймер для автоочистки (редкий, настраиваемый)
    restart_cleanup_timer()

    sys.exit(app.exec())