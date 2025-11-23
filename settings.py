import winreg
import sys
import os
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QPushButton, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

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
    except (FileNotFoundError, WindowsError):
        return default

def is_autostart_enabled():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
        winreg.QueryValueEx(key, "MiniBinKT")
        winreg.CloseKey(key)
        return True
    except (FileNotFoundError, WindowsError):
        return False

def set_autostart(enabled):
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
    if enabled:
        exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
        winreg.SetValueEx(key, "MiniBinKT", 0, winreg.REG_SZ, f'"{exe_path}"')
    else:
        try:
            winreg.DeleteValue(key, "MiniBinKT")
        except (FileNotFoundError, WindowsError):
            pass
    winreg.CloseKey(key)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки MiniBinKT")
        self.setFixedSize(500, 300)
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowTitleHint)
        
        self.setWindowIcon(QIcon(resource_path("icons/minibin-settings.ico")))
        
        self.setStyleSheet("""
            QDialog {
                background-color: #69ACF2;
            }
            QLabel {
                color: white;
                font-size: 10pt;
                background: transparent;
            }
            QCheckBox {
                color: white;
                spacing: 8px;
                font-size: 10pt;
                background: transparent;
            }
            QPushButton {
                background-color: white;
                color: #2E5C8A;
                border: none;
                border-radius: 5px;
                padding: 10px 30px;
                font-weight: bold;
                font-size: 10pt;
                min-height: 16px;
            }
            QPushButton:hover {
                background-color: #E8F4FF;
            }
        """)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 25, 30, 25)
        
        title = QLabel("Настройки MiniBinKT")
        title.setStyleSheet("font-weight: bold; font-size: 14pt; color: white;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(10)
        
        section1 = QLabel("Параметры уведомлений:")
        section1.setStyleSheet("font-weight: bold; font-size: 10pt;")
        layout.addWidget(section1)
        
        self.notification_checkbox = QCheckBox("Показывать уведомления при очистке корзины")
        layout.addWidget(self.notification_checkbox)
        
        self.confirmation_checkbox = QCheckBox("Показывать предупреждение перед очисткой")
        layout.addWidget(self.confirmation_checkbox)
        
        layout.addSpacing(15)
        
        section2 = QLabel("Системные настройки:")
        section2.setStyleSheet("font-weight: bold; font-size: 10pt;")
        layout.addWidget(section2)
        
        self.autostart_checkbox = QCheckBox("Добавить программу в автозагрузку")
        layout.addWidget(self.autostart_checkbox)
        
        layout.addStretch()
        
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.setLayout(layout)
    
    def load_settings(self):
        self.notification_checkbox.setChecked(load_setting("show_notification", True))
        self.confirmation_checkbox.setChecked(load_setting("show_confirmation", False))
        self.autostart_checkbox.setChecked(is_autostart_enabled())
    
    def save_settings(self):
        save_setting("show_notification", self.notification_checkbox.isChecked())
        save_setting("show_confirmation", self.confirmation_checkbox.isChecked())
        set_autostart(self.autostart_checkbox.isChecked())
        self.hide()
    
    def showEvent(self, event):
        super().showEvent(event)
        # Позиционируем окно справа снизу экрана
        screen = self.screen().availableGeometry()
        window_size = self.size()
        # Отступы от краев экрана
        margin = 50
        x = screen.width() - window_size.width() - margin
        y = screen.height() - window_size.height() - margin
        self.move(x, y)
    
    def closeEvent(self, event):
        event.ignore()
        self.hide()