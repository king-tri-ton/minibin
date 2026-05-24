import winreg
import sys
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QCheckBox, QPushButton, 
                             QLabel, QMessageBox, QApplication, QFileDialog, 
                             QHBoxLayout, QComboBox, QTabWidget, QWidget)
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

def save_string_setting(name, value):
	key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\MiniBinKT")
	winreg.SetValueEx(key, name, 0, winreg.REG_SZ, str(value))
	winreg.CloseKey(key)

def load_string_setting(name, default="none"):
	try:
		key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\MiniBinKT")
		value, _ = winreg.QueryValueEx(key, name)
		winreg.CloseKey(key)
		return value
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

def save_icon_path(icon_type, path):
	key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\MiniBinKT")
	winreg.SetValueEx(key, f"custom_icon_{icon_type}", 0, winreg.REG_SZ, path)
	winreg.CloseKey(key)

def load_icon_path(icon_type):
	try:
		key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\MiniBinKT")
		value, _ = winreg.QueryValueEx(key, f"custom_icon_{icon_type}")
		winreg.CloseKey(key)
		return value
	except (FileNotFoundError, WindowsError):
		return None

def delete_icon_setting(icon_type):
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
		self.setFixedSize(380, 200)
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
				padding: 8px 12px;
				font-weight: bold;
				font-size: 9pt;
				min-height: 14px;
			}
			QPushButton:hover {
				background-color: #E8F4FF;
			}
			QComboBox {
				background-color: white;
				color: #2E5C8A;
				border: none;
				border-radius: 5px;
				padding: 4px 8px;
				font-size: 9pt;
				min-width: 140px;
			}
			QComboBox QAbstractItemView {
				background-color: white;
				color: #2E5C8A;
				selection-background-color: #E8F4FF;
			}
			/* Стилизация вкладок */
			QTabWidget::pane {
				border: none;
				background: transparent;
			}
			QTabBar::tab {
				background-color: #5596DD;
				color: #E8F4FF;
				border-top-left-radius: 4px;
				border-top-right-radius: 4px;
				padding: 6px 12px;
				font-weight: bold;
				font-size: 9pt;
				margin-right: 2px;
			}
			QTabBar::tab:selected {
				background-color: #69ACF2;
				color: white;
				border-bottom: 2px solid white;
			}
			QTabBar::tab:hover:!selected {
				background-color: #60A1E8;
				color: white;
			}
		""")

		self.init_ui()
		self.load_settings()

	def init_ui(self):
		main_layout = QVBoxLayout()
		main_layout.setSpacing(10)
		main_layout.setContentsMargins(15, 15, 15, 15)

		self.tab_widget = QTabWidget()

		tab_general = QWidget()
		gen_layout = QVBoxLayout(tab_general)
		gen_layout.setSpacing(12)
		gen_layout.setContentsMargins(5, 15, 5, 5)

		self.notification_checkbox = QCheckBox("Уведомления при очистке корзины")
		self.confirmation_checkbox = QCheckBox("Предупреждение перед очисткой")
		self.autostart_checkbox = QCheckBox("Запускать при старте Windows")

		gen_layout.addWidget(self.notification_checkbox)
		gen_layout.addWidget(self.confirmation_checkbox)
		gen_layout.addWidget(self.autostart_checkbox)
		gen_layout.addStretch()
		self.tab_widget.addTab(tab_general, "Основные")

		tab_icons = QWidget()
		icons_layout = QVBoxLayout(tab_icons)
		icons_layout.setSpacing(12)
		icons_layout.setContentsMargins(5, 15, 5, 5)

		empty_layout = QHBoxLayout()
		empty_label = QLabel("Пустая корзина:")
		empty_layout.addWidget(empty_label)
		empty_layout.addStretch()
		self.choose_empty_button = QPushButton("Выбрать")
		self.choose_empty_button.setMaximumWidth(80)
		self.choose_empty_button.clicked.connect(lambda: self.choose_icon('empty'))
		self.reset_empty_button = QPushButton("Сброс")
		self.reset_empty_button.setMaximumWidth(70)
		self.reset_empty_button.clicked.connect(lambda: self.reset_icon('empty'))
		empty_layout.addWidget(self.choose_empty_button)
		empty_layout.addWidget(self.reset_empty_button)
		icons_layout.addLayout(empty_layout)

		full_layout = QHBoxLayout()
		full_label = QLabel("Полная корзина:")
		full_layout.addWidget(full_label)
		full_layout.addStretch()
		self.choose_full_button = QPushButton("Выбрать")
		self.choose_full_button.setMaximumWidth(80)
		self.choose_full_button.clicked.connect(lambda: self.choose_icon('full'))
		self.reset_full_button = QPushButton("Сброс")
		self.reset_full_button.setMaximumWidth(70)
		self.reset_full_button.clicked.connect(lambda: self.reset_icon('full'))
		full_layout.addWidget(self.choose_full_button)
		full_layout.addWidget(self.reset_full_button)
		icons_layout.addLayout(full_layout)
		
		icons_layout.addStretch()
		self.tab_widget.addTab(tab_icons, "Иконки")

		tab_clicks = QWidget()
		clicks_layout = QVBoxLayout(tab_clicks)
		clicks_layout.setSpacing(12)
		clicks_layout.setContentsMargins(5, 15, 5, 5)

		single_layout = QHBoxLayout()
		single_label = QLabel("Один клик:")
		single_layout.addWidget(single_label)
		single_layout.addStretch()
		self.single_click_combo = QComboBox()
		single_layout.addWidget(self.single_click_combo)
		clicks_layout.addLayout(single_layout)

		double_layout = QHBoxLayout()
		double_label = QLabel("Двойной клик:")
		double_layout.addWidget(double_label)
		double_layout.addStretch()
		self.double_click_combo = QComboBox()
		double_layout.addWidget(self.double_click_combo)
		clicks_layout.addLayout(double_layout)
		
		clicks_layout.addStretch()
		self.tab_widget.addTab(tab_clicks, "Взаимодействие")

		self.single_click_combo.currentIndexChanged.connect(self.update_click_combos)
		self.double_click_combo.currentIndexChanged.connect(self.update_click_combos)

		main_layout.addWidget(self.tab_widget)

		save_button = QPushButton("Сохранить настройки")
		save_button.clicked.connect(self.save_settings)
		main_layout.addWidget(save_button, alignment=Qt.AlignmentFlag.AlignCenter)
		
		self.setLayout(main_layout)

	def load_settings(self):
		self.notification_checkbox.setChecked(load_setting("show_notification", True))
		self.confirmation_checkbox.setChecked(load_setting("show_confirmation", False))
		self.autostart_checkbox.setChecked(is_autostart_enabled())

		self.single_click_combo.blockSignals(True)
		self.double_click_combo.blockSignals(True)

		all_items = [
			("Очистить корзину", "empty_bin"),
			("Открыть корзину", "open_bin"),
			("Открыть настройки", "open_settings"),
			("Ничего не делать", "none")
		]

		for text, data in all_items:
			self.single_click_combo.addItem(text, data)
			self.double_click_combo.addItem(text, data)

		single_action = load_string_setting("single_click_action", "empty_bin")
		idx_single = self.single_click_combo.findData(single_action)
		if idx_single != -1:
			self.single_click_combo.setCurrentIndex(idx_single)

		double_action = load_string_setting("double_click_action", "open_settings")
		idx_double = self.double_click_combo.findData(double_action)
		if idx_double != -1:
			self.double_click_combo.setCurrentIndex(idx_double)

		self.single_click_combo.blockSignals(False)
		self.double_click_combo.blockSignals(False)

		self.update_click_combos()

	def update_click_combos(self):
		self.single_click_combo.blockSignals(True)
		self.double_click_combo.blockSignals(True)

		current_single = self.single_click_combo.currentData()
		current_double = self.double_click_combo.currentData()

		all_items = [
			("Очистить корзину", "empty_bin"),
			("Открыть корзину", "open_bin"),
			("Открыть настройки", "open_settings"),
			("Ничего не делать", "none")
		]

		self.single_click_combo.clear()
		for text, data in all_items:
			if data == current_single or data != current_double or data == "none":
				self.single_click_combo.addItem(text, data)

		self.double_click_combo.clear()
		for text, data in all_items:
			if data == current_double or data != current_single or data == "none":
				self.double_click_combo.addItem(text, data)

		idx_single = self.single_click_combo.findData(current_single)
		if idx_single != -1:
			self.single_click_combo.setCurrentIndex(idx_single)

		idx_double = self.double_click_combo.findData(current_double)
		if idx_double != -1:
			self.double_click_combo.setCurrentIndex(idx_double)

		self.single_click_combo.blockSignals(False)
		self.double_click_combo.blockSignals(False)

	def save_settings(self):
		save_setting("show_notification", self.notification_checkbox.isChecked())
		save_setting("show_confirmation", self.confirmation_checkbox.isChecked())
		set_autostart(self.autostart_checkbox.isChecked())

		save_string_setting("single_click_action", self.single_click_combo.currentData())
		save_string_setting("double_click_action", self.double_click_combo.currentData())

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
		file_path, _ = QFileDialog.getOpenFileName(
			self,
			f"Выберите иконку для {'пустой' if icon_type == 'empty' else 'полной'} корзины",
			"",
			"Иконки (*.ico);;Все файлы (*.*)"
		)
		
		if file_path:
			save_icon_path(icon_type, file_path)
			QMessageBox.information(
				self,
				"Иконка изменена",
				"Иконка будет обновлена после перезапуска программы.",
				QMessageBox.StandardButton.Ok
			)

	def reset_icon(self, icon_type):
		delete_icon_setting(icon_type)
		QMessageBox.information(
			self,
			"Иконка сброшена",
			"Иконка будет восстановлена после перезапуска программы.",
			QMessageBox.StandardButton.Ok
		)

	def closeEvent(self, event):
		event.ignore()
		self.hide()