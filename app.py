import ctypes
import sys
import os
import threading
import time
import winreg
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction, QCursor
from PyQt6.QtCore import QTimer, QPoint
from settings import SettingsWindow, load_setting, load_icon_path, load_string_setting


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


def load_icon(default_icon_path, icon_type=None):
	"""
	Загружает иконку: сначала пытается загрузить кастомную, если нет - дефолтную
	icon_type: 'empty' или 'full'
	"""
	if icon_type:
		custom_path = load_icon_path(icon_type)
		if custom_path and os.path.exists(custom_path):
			return QIcon(custom_path)

	return QIcon(resource_path(default_icon_path))


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
	size_bytes, num_items = get_recycle_bin_info()
	is_empty = (num_items == 0)
	if is_empty:
		tray_icon.setIcon(load_icon("icons/minibin-kt-empty.ico", "empty"))
	else:
		tray_icon.setIcon(load_icon("icons/minibin-kt-full.ico", "full"))

	if not tray_icon.isVisible():
		tray_icon.hide()
		tray_icon.show()

	if load_setting("show_size_hover", True):
		if is_empty:
			tray_icon.setToolTip("Корзина (Пусто)")
		else:
			tray_icon.setToolTip(f"Корзина\nРазмер: {format_size(size_bytes)}\nФайлов: {num_items}")
	else:
		tray_icon.setToolTip("Корзина")


def format_size(size_bytes):
	if size_bytes == 0:
		return "0 B"
	units = ["B", "KB", "MB", "GB", "TB"]
	i = 0
	size = float(size_bytes)
	while size >= 1024.0 and i < len(units) - 1:
		size /= 1024.0
		i += 1
	return f"{size:.2f} {units[i]}"


def get_recycle_bin_info():
	rbinfo = SHQUERYRBINFO()
	rbinfo.cbSize = ctypes.sizeof(SHQUERYRBINFO)
	result = ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(rbinfo))
	if result != 0:
		return 0, 0
	return rbinfo.i64Size, rbinfo.i64NumItems


def empty_recycle_bin():
	SHEmptyRecycleBin = ctypes.windll.shell32.SHEmptyRecycleBinW

	show_confirmation = load_setting("show_confirmation", False)
	flags = 0x00 if show_confirmation else 0x01

	result = SHEmptyRecycleBin(None, None, flags)
	show_notifications = load_setting("show_notification", True)

	if result == 0 or result == -2147418113:
		if show_notifications:
			icon = load_icon("icons/minibin-kt-empty.ico", "empty")
			tray_icon.showMessage("Корзина", "Корзина успешно очищена.", icon, 5000)
	else:
		if show_notifications:
			tray_icon.showMessage("Корзина", f"Произошла ошибка при очистке корзины. Код ошибки: {result}", load_icon("icons/minibin-kt-full.ico"), 5000)

	QTimer.singleShot(100, update_icon)

if __name__ == "__main__":
	app = QApplication(sys.argv)
	app.setQuitOnLastWindowClosed(False)

	tray_icon = QSystemTrayIcon()
	tray_icon.setIcon(load_icon("icons/minibin-kt-empty.ico", "empty"))

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

	click_timer = QTimer()
	click_timer.setSingleShot(True)

	actions_map = {
		"empty_bin": empty_recycle_bin,
		"open_bin": open_recycle_bin,
		"open_settings": open_settings,
		"none": lambda: None
	}
	
	
	def perform_single_click():
		action_key = load_string_setting("single_click_action", "empty_bin")
		if action_key in actions_map:
			actions_map[action_key]()

	click_timer.timeout.connect(perform_single_click)

	
	def handle_tray_activation(reason):
		if reason == QSystemTrayIcon.ActivationReason.Context:
			icon_geometry = tray_icon.geometry()
			menu_height = tray_menu.sizeHint().height()
			tray_menu.popup(QPoint(icon_geometry.x(), icon_geometry.y() - menu_height))
			
		elif reason == QSystemTrayIcon.ActivationReason.Trigger:
			click_timer.start(250)
			
		elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
			click_timer.stop()
			action_key = load_string_setting("double_click_action", "open_settings")
			if action_key in actions_map:
				actions_map[action_key]()

	tray_icon.activated.connect(handle_tray_activation)
	tray_icon.show()

	update_timer = QTimer()
	update_timer.timeout.connect(update_icon)
	update_timer.start(3000)

	sys.exit(app.exec())
