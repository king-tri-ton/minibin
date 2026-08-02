import ctypes
import sys
import os
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QTimer, QPoint
from settings import SettingsWindow, load_setting, load_icon_path, load_string_setting
from theme_icons import default_icon_path, get_windows_app_theme


ICON_UPDATE_INTERVAL_MS = 1000
last_tray_icon_key = None
last_menu_theme = None


MENU_STYLES = {
	"light": """
		QMenu { background-color: #FFFFFF; color: #1F1F1F; border: 1px solid #D8D8D8; padding: 4px; }
		QMenu::item { color: #1F1F1F; background-color: transparent; padding: 6px 28px 6px 8px; border-radius: 4px; }
		QMenu::item:selected { color: #1F1F1F; background-color: #E8E8E8; }
		QMenu::item:disabled { color: #8A8A8A; }
		QMenu::separator { height: 1px; background-color: #E5E5E5; margin: 4px 8px; }
	""",
	"dark": """
		QMenu { background-color: #2C2C2C; color: #FFFFFF; border: 1px solid #454545; padding: 4px; }
		QMenu::item { color: #FFFFFF; background-color: transparent; padding: 6px 28px 6px 8px; border-radius: 4px; }
		QMenu::item:selected { color: #FFFFFF; background-color: #414141; }
		QMenu::item:disabled { color: #858585; }
		QMenu::separator { height: 1px; background-color: #484848; margin: 4px 8px; }
	""",
}

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

def resolve_icon_path(icon_type):
	"""
	Возвращает путь к пользовательской иконке или к встроенной иконке,
	соответствующей текущей светлой/тёмной теме Windows.
	"""
	custom_path = load_icon_path(icon_type)
	if custom_path and os.path.exists(custom_path):
		return custom_path

	return resource_path(default_icon_path(icon_type))


def load_icon(icon_type):
	return QIcon(resolve_icon_path(icon_type))

def open_recycle_bin():
	os.startfile("shell:RecycleBinFolder")


def open_taskbar_settings():
	os.startfile("ms-settings:taskbar")


def open_settings():
	global settings_window
	if 'settings_window' not in globals() or settings_window is None:
		settings_window = SettingsWindow()
	settings_window.show()
	settings_window.raise_()
	settings_window.activateWindow()

def exit_program():
	QApplication.quit()


def update_menu_theme(force=False):
	global last_menu_theme

	theme = get_windows_app_theme()
	if force or theme != last_menu_theme:
		tray_menu.setStyleSheet(MENU_STYLES[theme])
		last_menu_theme = theme

def update_icon(force=False):
	global last_tray_icon_key

	icon_type = "empty" if is_recycle_bin_empty() else "full"
	icon_path = resolve_icon_path(icon_type)
	icon_key = (icon_type, os.path.normcase(os.path.abspath(icon_path)))

	# Не перерисовываем значок каждую секунду: это исключает мерцание в трее.
	if force or icon_key != last_tray_icon_key:
		tray_icon.setIcon(QIcon(icon_path))
		last_tray_icon_key = icon_key

	if not tray_icon.isVisible():
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
			icon = load_icon("empty")
			tray_icon.showMessage("Корзина", "Корзина успешно очищена.", icon, 5000)
	else:
		if show_notifications:
			tray_icon.showMessage("Корзина", f"Произошла ошибка при очистке корзины. Код ошибки: {result}", load_icon("full"), 5000)

	QTimer.singleShot(100, update_icon)

if __name__ == "__main__":
	app = QApplication(sys.argv)
	app.setApplicationName("MiniBinKT")
	app.setOrganizationName("King Triton")
	app.setQuitOnLastWindowClosed(False)

	tray_icon = QSystemTrayIcon()
	tray_icon.setIcon(load_icon("empty"))
	tray_icon.setToolTip("MiniBinKT — корзина")

	tray_menu = QMenu()
	open_action = QAction("Открыть корзину", triggered=open_recycle_bin)
	empty_action = QAction("Очистить корзину", triggered=empty_recycle_bin)
	settings_action = QAction("Настройки", triggered=open_settings)
	taskbar_settings_action = QAction("Показать значок на панели…", triggered=open_taskbar_settings)
	exit_action = QAction("Выход", triggered=exit_program)

	tray_menu.addAction(open_action)
	tray_menu.addSeparator()
	tray_menu.addAction(empty_action)
	tray_menu.addAction(settings_action)
	tray_menu.addAction(taskbar_settings_action)
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
			update_menu_theme()
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
	update_timer.timeout.connect(update_menu_theme)
	update_timer.start(ICON_UPDATE_INTERVAL_MS)
	update_icon(force=True)
	update_menu_theme(force=True)

	sys.exit(app.exec())
