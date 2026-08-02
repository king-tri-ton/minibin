"""Windows theme detection and built-in tray icon selection."""

import winreg


PERSONALIZE_KEY = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
VALID_ICON_STATES = {"empty", "full"}
VALID_THEMES = {"light", "dark"}


def _read_theme(value_names):
	try:
		key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, PERSONALIZE_KEY)
		try:
			for value_name in value_names:
				try:
					value, _ = winreg.QueryValueEx(key, value_name)
					return "light" if int(value) else "dark"
				except FileNotFoundError:
					continue
		finally:
			winreg.CloseKey(key)
	except (FileNotFoundError, OSError, ValueError, TypeError):
		pass

	return "light"


def get_windows_theme():
	"""Return the taskbar theme, falling back to the app theme."""
	return _read_theme(("SystemUsesLightTheme", "AppsUseLightTheme"))


def get_windows_app_theme():
	"""Return the app/menu theme, falling back to the taskbar theme."""
	return _read_theme(("AppsUseLightTheme", "SystemUsesLightTheme"))


def default_icon_path(icon_state, theme=None):
	"""Return the bundled icon path for a recycle-bin state and theme."""
	if icon_state not in VALID_ICON_STATES:
		raise ValueError(f"Unsupported recycle-bin state: {icon_state}")

	selected_theme = theme or get_windows_theme()
	if selected_theme not in VALID_THEMES:
		raise ValueError(f"Unsupported Windows theme: {selected_theme}")

	return f"icons/minibin-kt-{selected_theme}-{icon_state}.ico"
