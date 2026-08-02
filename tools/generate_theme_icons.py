"""Build monochrome tray icons from Microsoft's Fluent UI SVG sources.

Development requirements: PyQt6 and Pillow. They are not needed by MiniBinKT
at runtime beyond the project's existing PyQt6 dependency.
"""

from io import BytesIO
from pathlib import Path
import struct

from PIL import Image, ImageDraw
from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QGuiApplication, QImage, QPainter
from PyQt6.QtSvg import QSvgRenderer


ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "icons"
SOURCE_DIR = ICON_DIR / "source"
OUTPUT_SIZE = 256
ICO_SIZES = (16, 20, 24, 32, 48, 64, 128, 256)

SOURCE_ICONS = {
	"empty": {
		16: SOURCE_DIR / "fluent-delete-16-regular.svg",
		20: SOURCE_DIR / "fluent-delete-20-regular.svg",
		24: SOURCE_DIR / "fluent-delete-24-regular.svg",
	},
	"full": {
		16: SOURCE_DIR / "fluent-delete-16-filled.svg",
		20: SOURCE_DIR / "fluent-delete-20-filled.svg",
		24: SOURCE_DIR / "fluent-delete-24-filled.svg",
	},
}

THEME_COLORS = {
	"light": "#202020",
	"dark": "#F5F5F5",
}


def render_svg(source_path, color, size=OUTPUT_SIZE):
	svg = source_path.read_text(encoding="utf-8").replace("#212121", color)
	renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
	if not renderer.isValid():
		raise ValueError(f"Invalid SVG: {source_path}")

	image = QImage(size, size, QImage.Format.Format_RGBA8888)
	image.fill(Qt.GlobalColor.transparent)
	painter = QPainter(image)
	renderer.render(painter)
	painter.end()

	bits = image.bits()
	bits.setsize(image.sizeInBytes())
	return Image.frombytes("RGBA", (size, size), bytes(bits), "raw", "RGBA")


def source_for_size(state, size):
	"""Use Microsoft's hand-tuned native SVG for common Windows DPI sizes."""
	sources = SOURCE_ICONS[state]
	if size in sources:
		return sources[size]
	return sources[24]


def save_ico(images_by_size, path):
	"""Write an ICO without resampling its small, pixel-fitted layers.

	Pillow normally derives every ICO layer from the largest bitmap. That made
	the 16 px tray layer soft. Each layer here is rendered from the vector at
	its final size and embedded as its own PNG instead.
	"""
	png_layers = []
	for size in ICO_SIZES:
		stream = BytesIO()
		images_by_size[size].save(stream, format="PNG")
		png_layers.append((size, stream.getvalue()))

	header_size = 6 + 16 * len(png_layers)
	offset = header_size
	entries = []
	for size, png_data in png_layers:
		encoded_size = 0 if size == 256 else size
		entries.append(struct.pack(
			"<BBBBHHII", encoded_size, encoded_size, 0, 0, 1, 32,
			len(png_data), offset
		))
		offset += len(png_data)

	with path.open("wb") as icon_file:
		icon_file.write(struct.pack("<HHH", 0, 1, len(png_layers)))
		icon_file.write(b"".join(entries))
		icon_file.write(b"".join(data for _, data in png_layers))


def build_preview(images):
	preview = Image.new("RGB", (1000, 500), (243, 246, 249))
	draw = ImageDraw.Draw(preview)
	columns = [
		("light", 0, (243, 246, 249), (39, 45, 52)),
		("dark", 500, (32, 32, 32), (238, 245, 249)),
	]

	for theme, left, background, foreground in columns:
		draw.rounded_rectangle((left + 24, 24, left + 476, 476), radius=28, fill=background)
		draw.text((left + 54, 54), f"Microsoft Fluent · {theme.title()}", fill=foreground)
		for index, state in enumerate(("empty", "full")):
			x = left + 72 + index * 220
			icon = images[(theme, state)].resize((180, 180), Image.Resampling.LANCZOS)
			preview.paste(icon, (x, 128), icon)
			draw.text((x + 90, 402), state.title(), fill=foreground, anchor="ma")

	return preview


def build_tray_preview(images):
	preview = Image.new("RGB", (760, 144), (243, 246, 249))
	draw = ImageDraw.Draw(preview)
	sections = [
		("light", 0, (243, 246, 249), (39, 45, 52)),
		("dark", 380, (32, 32, 32), (238, 245, 249)),
	]

	for theme, left, background, foreground in sections:
		draw.rectangle((left, 0, left + 380, 144), fill=background)
		draw.text((left + 20, 18), f"{theme.title()} taskbar · 20 px", fill=foreground)
		for index, state in enumerate(("empty", "full")):
			x = left + 92 + index * 150
			y = 58
			icon = images[(theme, state)].resize((20, 20), Image.Resampling.LANCZOS)
			preview.paste(icon, (x, y), icon)
			draw.text((x + 10, 98), state.title(), fill=foreground, anchor="ma")

	return preview


def main():
	app = QGuiApplication.instance() or QGuiApplication([])
	preview_images = {}
	tray_images = {}

	for theme, color in THEME_COLORS.items():
		for state in SOURCE_ICONS:
			layers = {
				size: render_svg(source_for_size(state, size), color, size)
				for size in ICO_SIZES
			}
			preview_images[(theme, state)] = layers[OUTPUT_SIZE]
			tray_images[(theme, state)] = layers[20]
			save_ico(layers, ICON_DIR / f"minibin-kt-{theme}-{state}.ico")

	build_preview(preview_images).save(ICON_DIR / "theme-preview.png")
	build_tray_preview(tray_images).save(ICON_DIR / "tray-preview.png")
	app.quit()


if __name__ == "__main__":
	main()
