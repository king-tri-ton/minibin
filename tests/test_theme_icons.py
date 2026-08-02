import unittest
from pathlib import Path
from unittest.mock import patch

import theme_icons


class ThemeIconTests(unittest.TestCase):
	@patch("theme_icons.winreg.CloseKey")
	@patch("theme_icons.winreg.QueryValueEx", return_value=(0, 4))
	@patch("theme_icons.winreg.OpenKey", return_value=object())
	def test_dark_system_theme(self, _open_key, _query_value, _close_key):
		self.assertEqual(theme_icons.get_windows_theme(), "dark")

	@patch("theme_icons.winreg.CloseKey")
	@patch("theme_icons.winreg.QueryValueEx", return_value=(1, 4))
	@patch("theme_icons.winreg.OpenKey", return_value=object())
	def test_light_system_theme(self, _open_key, _query_value, _close_key):
		self.assertEqual(theme_icons.get_windows_theme(), "light")

	@patch("theme_icons.winreg.OpenKey", side_effect=FileNotFoundError)
	def test_missing_theme_setting_falls_back_to_light(self, _open_key):
		self.assertEqual(theme_icons.get_windows_theme(), "light")

	@patch("theme_icons.winreg.CloseKey")
	@patch("theme_icons.winreg.QueryValueEx", side_effect=[FileNotFoundError, (0, 4)])
	@patch("theme_icons.winreg.OpenKey", return_value=object())
	def test_apps_theme_is_used_when_system_theme_is_missing(
		self, _open_key, _query_value, _close_key
	):
		self.assertEqual(theme_icons.get_windows_theme(), "dark")

	@patch("theme_icons.winreg.CloseKey")
	@patch("theme_icons.winreg.OpenKey", return_value=object())
	def test_menu_uses_apps_theme_before_system_theme(self, _open_key, _close_key):
		with patch(
			"theme_icons.winreg.QueryValueEx",
			side_effect=lambda _key, name: (0 if name == "AppsUseLightTheme" else 1, 4),
		):
			self.assertEqual(theme_icons.get_windows_app_theme(), "dark")

	def test_icon_path_contains_theme_and_state(self):
		self.assertEqual(
			theme_icons.default_icon_path("full", "dark"),
			"icons/minibin-kt-dark-full.ico",
		)

	def test_invalid_state_is_rejected(self):
		with self.assertRaises(ValueError):
			theme_icons.default_icon_path("half", "light")

	def test_all_bundled_theme_icons_exist(self):
		for theme in ("light", "dark"):
			for state in ("empty", "full"):
				self.assertTrue(Path(theme_icons.default_icon_path(state, theme)).is_file())


if __name__ == "__main__":
	unittest.main()
