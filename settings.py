import winreg
import sys
import os
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QPushButton, QLabel, QMessageBox, QApplication, QFileDialog, QHBoxLayout
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




def get_custom_icons_folder():
	"""Возвращает путь к папке с пользовательскими иконками"""
	if getattr(sys, 'frozen', False):
		# Если запущен exe
		base_dir = os.path.dirname(sys.executable)
	else:
		# Если запущен из Python
		base_dir = os.path.dirname(os.path.abspath(__file__))
	
	custom_folder = os.path.join(base_dir, "custom_icons")
	
	# Создаем папку если её нет
	if not os.path.exists(custom_folder):
		os.makedirs(custom_folder)
	
	return custom_folder

def save_icon_path(icon_type, path):
	"""Сохраняет путь к кастомной иконке (icon_type: 'empty' или 'full')"""
	key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\MiniBinKT")
	winreg.SetValueEx(key, f"custom_icon_{icon_type}", 0, winreg.REG_SZ, path)
	winreg.CloseKey(key)

def load_icon_path(icon_type):
	"""Загружает путь к кастомной иконке"""
	try:
		key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\MiniBinKT")
		value, _ = winreg.QueryValueEx(key, f"custom_icon_{icon_type}")
		winreg.CloseKey(key)
		return value
	except (FileNotFoundError, WindowsError):
		return None

def reset_icon(icon_type):
	"""Сбрасывает иконку на дефолтную"""
	try:
		key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\MiniBinKT", 0, winreg.KEY_SET_VALUE)
		winreg.DeleteValue(key, f"custom_icon_{icon_type}")
		winreg.CloseKey(key)
	except (FileNotFoundError, WindowsError):
		pass




class SettingsWindow(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Настройки MiniBinKT")
		self.setFixedSize(420, 500) # 365 x 310
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
				padding: 10px 15px;
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
		
		layout.addSpacing(15)

		section3 = QLabel("Персонализация:")
		section3.setStyleSheet("font-weight: bold; font-size: 10pt;")
		layout.addWidget(section3)

		# Пустая корзина
		empty_layout = QHBoxLayout()
		empty_label = QLabel("Иконка пустой корзины:")
		empty_layout.addWidget(empty_label)
		empty_layout.addStretch()

		self.choose_empty_button = QPushButton("Выбрать")
		self.choose_empty_button.setMaximumWidth(120)
		self.choose_empty_button.clicked.connect(lambda: self.choose_icon('empty'))
		empty_layout.addWidget(self.choose_empty_button)

		self.reset_empty_button = QPushButton("Сбросить")
		self.reset_empty_button.setMaximumWidth(120)
		self.reset_empty_button.clicked.connect(lambda: self.reset_icon('empty'))
		empty_layout.addWidget(self.reset_empty_button)

		layout.addLayout(empty_layout)

		# Полная корзина
		full_layout = QHBoxLayout()
		full_label = QLabel("Иконка полной корзины:")
		full_layout.addWidget(full_label)
		full_layout.addStretch()

		self.choose_full_button = QPushButton("Выбрать")
		self.choose_full_button.setMaximumWidth(120)
		self.choose_full_button.clicked.connect(lambda: self.choose_icon('full'))
		full_layout.addWidget(self.choose_full_button)

		self.reset_full_button = QPushButton("Сбросить")
		self.reset_full_button.setMaximumWidth(120)
		self.reset_full_button.clicked.connect(lambda: self.reset_icon('full'))
		full_layout.addWidget(self.reset_full_button)

		layout.addLayout(full_layout)

		layout.addSpacing(15)

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
		screen = self.screen().availableGeometry()
		window_size = self.size()
		margin = 50
		x = screen.width() - window_size.width() - margin
		y = screen.height() - window_size.height() - margin
		self.move(x, y)

	def choose_icon(self, icon_type):
		"""Открывает диалог выбора иконки"""
		file_path, _ = QFileDialog.getOpenFileName(
			self,
			f"Выберите иконку для {'пустой' if icon_type == 'empty' else 'полной'} корзины",
			"",
			"Иконки (*.ico);;Все файлы (*.*)"
		)
		
		if file_path:
			# Сохраняем путь
			save_icon_path(icon_type, file_path)
			QMessageBox.information(
				self,
				"Иконка изменена",
				"Иконка будет обновлена после перезапуска программы.",
				QMessageBox.StandardButton.Ok
			)

	def reset_icon(self, icon_type):
		"""Сбрасывает иконку на дефолтную"""
		reset_icon(icon_type)
		QMessageBox.information(
			self,
			"Иконка сброшена",
			"Иконка будет восстановлена после перезапуска программы.",
			QMessageBox.StandardButton.Ok
		)

	def closeEvent(self, event):
		event.ignore()
		self.hide()