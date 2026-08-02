import winreg
import sys
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QCheckBox, QPushButton,
                             QLabel, QMessageBox, QApplication, QFileDialog,
                             QHBoxLayout, QComboBox, QFrame,
                             QStyledItemDelegate, QStyle)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QColor, QPainter
from theme_icons import default_icon_path, get_windows_app_theme

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


class FluentComboItemDelegate(QStyledItemDelegate):
	"""Draw roomy, rounded rows instead of Qt's legacy popup selection."""

	def sizeHint(self, option, index):
		size = super().sizeHint(option, index)
		size.setHeight(34)
		return size

	def paint(self, painter, option, index):
		painter.save()
		painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

		view = option.widget
		text_color = QColor(view.property("popupTextColor") or "#1A1A1A")
		hover_color = QColor(view.property("popupHoverColor") or "#F0F0F0")
		selected = option.state & (
			QStyle.StateFlag.State_Selected | QStyle.StateFlag.State_MouseOver
		)
		if selected:
			painter.setPen(Qt.PenStyle.NoPen)
			painter.setBrush(hover_color)
			painter.drawRoundedRect(option.rect.adjusted(4, 2, -4, -2), 4, 4)

		painter.setPen(text_color)
		text_rect = option.rect.adjusted(12, 0, -8, 0)
		painter.drawText(
			text_rect,
			Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
			str(index.data(Qt.ItemDataRole.DisplayRole)),
		)
		painter.restore()


class SettingsWindow(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Настройки MiniBinKT")
		self.setFixedSize(500, 550)
		self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowTitleHint)
		self.current_theme = None
		self.update_window_icon()

		self.init_ui()
		self.apply_theme(force=True)
		self.load_settings()

	def update_window_icon(self):
		theme = get_windows_app_theme()
		icon_path = resource_path(default_icon_path("empty", theme))
		self.setWindowIcon(QIcon(icon_path))

	def apply_theme(self, force=False):
		theme = get_windows_app_theme()
		if not force and theme == self.current_theme:
			return

		if theme == "dark":
			colors = {
				"window": "#202020", "card": "#2B2B2B", "control": "#323232",
				"border": "#414141", "text": "#FFFFFF", "muted": "#C8C8C8",
				"hover": "#3A3A3A", "pressed": "#454545", "accent": "#60CDFF",
				"accent_hover": "#7AD7FF", "accent_text": "#102027",
			}
		else:
			colors = {
				"window": "#F3F3F3", "card": "#FBFBFB", "control": "#FFFFFF",
				"border": "#D9D9D9", "text": "#1A1A1A", "muted": "#5F5F5F",
				"hover": "#F0F0F0", "pressed": "#E8E8E8", "accent": "#0067C0",
				"accent_hover": "#1975C5", "accent_text": "#FFFFFF",
			}

		check_icon = resource_path(f"icons/source/ui-check-{theme}.svg").replace("\\", "/")
		chevron_icon = resource_path(f"icons/source/ui-chevron-{theme}.svg").replace("\\", "/")

		self.setStyleSheet(f"""
			QDialog {{ background-color: {colors['window']}; }}
			QWidget {{ color: {colors['text']}; font-family: "Segoe UI"; font-size: 10pt; }}
			QLabel {{ background: transparent; }}
			QLabel[role="title"] {{ font-size: 17pt; font-weight: 600; }}
			QLabel[role="subtitle"] {{ color: {colors['muted']}; font-size: 9pt; }}
			QLabel[role="sectionTitle"] {{ font-weight: 600; padding-left: 2px; }}
			QFrame[role="card"] {{
				background-color: {colors['card']}; border: 1px solid {colors['border']};
				border-radius: 8px;
			}}
			QCheckBox {{ spacing: 10px; padding: 2px 0; background: transparent; }}
			QCheckBox::indicator {{
				width: 18px; height: 18px; background-color: {colors['control']};
				border: 1px solid {colors['border']}; border-radius: 4px;
			}}
			QCheckBox::indicator:hover {{ background-color: {colors['hover']}; }}
			QCheckBox::indicator:checked {{
				background-color: {colors['accent']}; border-color: {colors['accent']};
				image: url("{check_icon}");
			}}
			QPushButton {{
				background-color: {colors['control']}; color: {colors['text']};
				border: 1px solid {colors['border']}; border-radius: 5px;
				padding: 5px 12px; min-height: 24px;
			}}
			QPushButton:hover {{ background-color: {colors['hover']}; }}
			QPushButton:pressed {{ background-color: {colors['pressed']}; }}
			QPushButton#primaryButton {{
				background-color: {colors['accent']}; color: {colors['accent_text']};
				border-color: {colors['accent']}; font-weight: 600;
			}}
			QPushButton#primaryButton:hover {{ background-color: {colors['accent_hover']}; }}
			QComboBox {{
				background-color: {colors['control']}; color: {colors['text']};
				border: 1px solid {colors['border']}; border-radius: 5px;
				padding: 4px 36px 4px 9px; min-height: 24px;
			}}
			QComboBox:hover {{ background-color: {colors['hover']}; }}
			QComboBox::drop-down {{
				subcontrol-origin: padding; subcontrol-position: top right;
				width: 32px; border: none; background: transparent;
			}}
			QComboBox::down-arrow {{ image: url("{chevron_icon}"); width: 12px; height: 8px; }}
			QComboBox QAbstractItemView {{
				background-color: {colors['control']}; color: {colors['text']};
				border: 1px solid {colors['border']}; border-radius: 7px;
				padding: 4px; outline: 0px;
				selection-background-color: {colors['hover']};
				selection-color: {colors['text']};
			}}
			QComboBox QAbstractItemView::item {{
				min-height: 30px; padding: 2px 9px; border: none; border-radius: 4px;
			}}
			QComboBox QAbstractItemView::item:hover,
			QComboBox QAbstractItemView::item:selected {{
				background-color: {colors['hover']}; color: {colors['text']};
			}}
		""")
		for combo in (self.single_click_combo, self.double_click_combo):
			combo.view().setProperty("popupTextColor", colors["text"])
			combo.view().setProperty("popupHoverColor", colors["hover"])
			combo.view().viewport().update()
		self.current_theme = theme

	def init_ui(self):
		main_layout = QVBoxLayout()
		main_layout.setSpacing(6)
		main_layout.setContentsMargins(20, 16, 20, 16)

		title = QLabel("MiniBinKT")
		title.setProperty("role", "title")
		main_layout.addWidget(title)
		subtitle = QLabel("Настройки корзины и поведения программы")
		subtitle.setProperty("role", "subtitle")
		main_layout.addWidget(subtitle)
		main_layout.addSpacing(8)

		general_title = QLabel("Основное")
		general_title.setProperty("role", "sectionTitle")
		main_layout.addWidget(general_title)
		general_group = QFrame()
		general_group.setProperty("role", "card")
		general_layout = QVBoxLayout(general_group)
		general_layout.setContentsMargins(14, 12, 14, 12)
		general_layout.setSpacing(8)
		self.notification_checkbox = QCheckBox("Уведомления при очистке корзины")
		self.confirmation_checkbox = QCheckBox("Предупреждение перед очисткой")
		self.autostart_checkbox = QCheckBox("Запускать при старте Windows")
		general_layout.addWidget(self.notification_checkbox)
		general_layout.addWidget(self.confirmation_checkbox)
		general_layout.addWidget(self.autostart_checkbox)
		main_layout.addWidget(general_group)
		main_layout.addSpacing(6)

		mouse_title = QLabel("Действия мыши")
		mouse_title.setProperty("role", "sectionTitle")
		main_layout.addWidget(mouse_title)
		mouse_group = QFrame()
		mouse_group.setProperty("role", "card")
		mouse_layout = QVBoxLayout(mouse_group)
		mouse_layout.setContentsMargins(14, 12, 14, 12)
		mouse_layout.setSpacing(10)
		single_layout = QHBoxLayout()
		single_layout.addWidget(QLabel("Один клик"))
		single_layout.addStretch()
		self.single_click_combo = QComboBox()
		self.single_click_combo.setItemDelegate(
			FluentComboItemDelegate(self.single_click_combo)
		)
		self.single_click_combo.setFixedWidth(220)
		self.single_click_combo.setFixedHeight(34)
		single_layout.addWidget(self.single_click_combo)
		mouse_layout.addLayout(single_layout)

		double_layout = QHBoxLayout()
		double_layout.addWidget(QLabel("Двойной клик"))
		double_layout.addStretch()
		self.double_click_combo = QComboBox()
		self.double_click_combo.setItemDelegate(
			FluentComboItemDelegate(self.double_click_combo)
		)
		self.double_click_combo.setFixedWidth(220)
		self.double_click_combo.setFixedHeight(34)
		double_layout.addWidget(self.double_click_combo)
		mouse_layout.addLayout(double_layout)
		main_layout.addWidget(mouse_group)

		self.single_click_combo.currentIndexChanged.connect(self.update_click_combos)
		self.double_click_combo.currentIndexChanged.connect(self.update_click_combos)
		main_layout.addSpacing(6)

		icons_title = QLabel("Иконки корзины")
		icons_title.setProperty("role", "sectionTitle")
		main_layout.addWidget(icons_title)
		icons_group = QFrame()
		icons_group.setProperty("role", "card")
		icons_layout = QVBoxLayout(icons_group)
		icons_layout.setContentsMargins(14, 12, 14, 12)
		icons_layout.setSpacing(10)
		empty_layout = QHBoxLayout()
		empty_label = QLabel("Пустая корзина")
		empty_layout.addWidget(empty_label)
		empty_layout.addStretch()
		self.choose_empty_button = QPushButton("Выбрать")
		self.choose_empty_button.setFixedWidth(96)
		self.choose_empty_button.setFixedHeight(34)
		self.choose_empty_button.clicked.connect(lambda: self.choose_icon('empty'))
		self.reset_empty_button = QPushButton("Сброс")
		self.reset_empty_button.setFixedWidth(82)
		self.reset_empty_button.setFixedHeight(34)
		self.reset_empty_button.clicked.connect(lambda: self.reset_icon('empty'))
		empty_layout.addWidget(self.choose_empty_button)
		empty_layout.addWidget(self.reset_empty_button)
		icons_layout.addLayout(empty_layout)

		full_layout = QHBoxLayout()
		full_label = QLabel("Полная корзина")
		full_layout.addWidget(full_label)
		full_layout.addStretch()
		self.choose_full_button = QPushButton("Выбрать")
		self.choose_full_button.setFixedWidth(96)
		self.choose_full_button.setFixedHeight(34)
		self.choose_full_button.clicked.connect(lambda: self.choose_icon('full'))
		self.reset_full_button = QPushButton("Сброс")
		self.reset_full_button.setFixedWidth(82)
		self.reset_full_button.setFixedHeight(34)
		self.reset_full_button.clicked.connect(lambda: self.reset_icon('full'))
		full_layout.addWidget(self.choose_full_button)
		full_layout.addWidget(self.reset_full_button)
		icons_layout.addLayout(full_layout)
		main_layout.addWidget(icons_group)
		main_layout.addStretch()

		save_button = QPushButton("Сохранить настройки")
		save_button.setObjectName("primaryButton")
		save_button.setFixedWidth(220)
		save_button.setFixedHeight(38)
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
		self.apply_theme()
		self.update_window_icon()
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
				"Иконка будет обновлена автоматически.",
				QMessageBox.StandardButton.Ok
			)

	def reset_icon(self, icon_type):
		delete_icon_setting(icon_type)
		QMessageBox.information(
			self,
			"Иконка сброшена",
			"Встроенная иконка для текущей темы Windows будет восстановлена автоматически.",
			QMessageBox.StandardButton.Ok
		)

	def closeEvent(self, event):
		event.ignore()
		self.hide()
