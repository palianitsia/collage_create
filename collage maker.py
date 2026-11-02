import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSpinBox, QComboBox, QSlider, QFileDialog,
    QListWidget, QListWidgetItem, QGroupBox, QColorDialog, QSplitter,
    QMessageBox, QCheckBox, QScrollArea, QFrame
)
from PyQt6.QtGui import QPixmap, QImage, QIcon, QAction, QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QSize, QTimer
from PIL import Image, ImageDraw, ImageOps
import io


class CollageMaker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Collage Maker")
        self.resize(1200, 800)

        self.images = []  # Lista di PIL.Image
        self.bg_color = "#FFFFFF"
        self.border_color = "#000000"
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.update_preview)

        self.init_ui()

    # ---------------- UI ----------------
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Colonna sinistra: controlli
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Lista immagini
        img_group = QGroupBox("Immagini")
        img_layout = QVBoxLayout(img_group)
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(80, 80))
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        img_layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Aggiungi")
        btn_add.clicked.connect(self.add_images)
        btn_remove = QPushButton("🗑 Rimuovi")
        btn_remove.clicked.connect(self.remove_selected)
        btn_clear = QPushButton("❌ Svuota")
        btn_clear.clicked.connect(self.clear_images)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_remove)
        btn_layout.addWidget(btn_clear)
        img_layout.addLayout(btn_layout)
        left_layout.addWidget(img_group)

        # Layout collage
        layout_group = QGroupBox("Layout")
        layout_layout = QVBoxLayout(layout_group)

        layout_layout.addWidget(QLabel("Modalità:"))
        self.layout_combo = QComboBox()
        self.layout_combo.addItems([
            "Griglia", "Orizzontale", "Verticale", "Mosaico casuale"
        ])
        self.layout_combo.currentIndexChanged.connect(self.schedule_preview)
        layout_layout.addWidget(self.layout_combo)

        layout_layout.addWidget(QLabel("Colonne:"))
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 10)
        self.cols_spin.setValue(3)
        self.cols_spin.valueChanged.connect(self.schedule_preview)
        layout_layout.addWidget(self.cols_spin)

        layout_layout.addWidget(QLabel("Larghezza finale (px):"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(200, 5000)
        self.width_spin.setValue(1200)
        self.width_spin.setSingleStep(100)
        self.width_spin.valueChanged.connect(self.schedule_preview)
        layout_layout.addWidget(self.width_spin)

        layout_layout.addWidget(QLabel("Spaziatura (px):"))
        self.gap_spin = QSpinBox()
        self.gap_spin.setRange(0, 100)
        self.gap_spin.setValue(10)
        self.gap_spin.valueChanged.connect(self.schedule_preview)
        layout_layout.addWidget(self.gap_spin)

        layout_layout.addWidget(QLabel("Padding esterno (px):"))
        self.pad_spin = QSpinBox()
        self.pad_spin.setRange(0, 100)
        self.pad_spin.setValue(20)
        self.pad_spin.valueChanged.connect(self.schedule_preview)
        layout_layout.addWidget(self.pad_spin)

        layout_layout.addWidget(QLabel("Arrotondamento angoli (px):"))
        self.round_spin = QSpinBox()
        self.round_spin.setRange(0, 100)
        self.round_spin.setValue(0)
        self.round_spin.valueChanged.connect(self.schedule_preview)
        layout_layout.addWidget(self.round_spin)

        left_layout.addWidget(layout_group)

        # Stile
        style_group = QGroupBox("Stile")
        style_layout = QVBoxLayout(style_group)

        style_layout.addWidget(QLabel("Colore sfondo:"))
        self.btn_bg = QPushButton()
        self.btn_bg.clicked.connect(self.choose_bg_color)
        self.set_color_button(self.btn_bg, self.bg_color)
        style_layout.addWidget(self.btn_bg)

        style_layout.addWidget(QLabel("Bordo immagine (px):"))
        self.border_spin = QSpinBox()
        self.border_spin.setRange(0, 50)
        self.border_spin.setValue(0)
        self.border_spin.valueChanged.connect(self.schedule_preview)
        style_layout.addWidget(self.border_spin)

        style_layout.addWidget(QLabel("Colore bordo:"))
        self.btn_border = QPushButton()
        self.btn_border.clicked.connect(self.choose_border_color)
        self.set_color_button(self.btn_border, self.border_color)
        style_layout.addWidget(self.btn_border)

        self.chk_bw = QCheckBox("Bianco e nero")
        self.chk_bw.stateChanged.connect(self.schedule_preview)
        style_layout.addWidget(self.chk_bw)

        left_layout.addWidget(style_group)

        left_layout.addStretch()
        splitter.addWidget(left_panel)

        # Colonna destra: anteprima
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        preview_group = QGroupBox("Anteprima")
        preview_layout = QVBoxLayout(preview_group)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.preview_label = QLabel("Aggiungi immagini per iniziare...")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background: #2b2b2b; color: #aaa;")
        self.scroll.setWidget(self.preview_label)
        preview_layout.addWidget(self.scroll)
        right_layout.addWidget(preview_group)

        # Azioni
        actions = QHBoxLayout()
        btn_save = QPushButton("💾 Salva Collage")
        btn_save.clicked.connect(self.save_collage)
        actions.addWidget(btn_save)
        right_layout.addLayout(actions)

        splitter.addWidget(right_panel)
        splitter.setSizes([380, 820])

        self.statusBar().showMessage("Pronto")

    # ---------------- Gestione immagini ----------------
    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Seleziona immagini", "",
            "Immagini (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        for f in files:
            try:
                img = Image.open(f).convert("RGBA")
                self.images.append({"path": f, "image": img})
                item = QListWidgetItem(os.path.basename(f))
                item.setIcon(QIcon(QPixmap(f).scaled(
                    80, 80, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )))
                self.list_widget.addItem(item)
            except Exception as e:
                QMessageBox.warning(self, "Errore", f"Impossibile caricare {f}: {e}")
        self.schedule_preview()

    def remove_selected(self):
        for item in sorted(self.list_widget.selectedItems(),
                           key=lambda i: self.list_widget.row(i), reverse=True):
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)
            del self.images[row]
        self.schedule_preview()

    def clear_images(self):
        self.list_widget.clear()
        self.images.clear()
        self.preview_label.clear()
        self.preview_label.setText("Aggiungi immagini per iniziare...")
        self.schedule_preview()

    # ---------------- Colori ----------------
    def set_color_button(self, button, color):
        button.setText(color)
        button.setStyleSheet(
            f"background-color: {color}; color: "
            f"{'black' if self.is_light(color) else 'white'}; padding: 6px;"
        )

    def is_light(self, hex_color):
        c = QColor(hex_color)
        return (c.red() * 299 + c.green() * 587 + c.blue() * 114) / 1000 > 128

    def choose_bg_color(self):
        color = QColorDialog.getColor(QColor(self.bg_color), self, "Sfondo")
        if color.isValid():
            self.bg_color = color.name()
            self.set_color_button(self.btn_bg, self.bg_color)
            self.schedule_preview()

    def choose_border_color(self):
        color = QColorDialog.getColor(QColor(self.border_color), self, "Bordo")
        if color.isValid():
            self.border_color = color.name()
            self.set_color_button(self.btn_border, self.border_color)
            self.schedule_preview()

    # ---------------- Preview ----------------
    def schedule_preview(self):
        self.preview_timer.start(120)

    def update_preview(self):
        if not self.images:
            self.preview_label.setText("Aggiungi immagini per iniziare...")
            return
        try:
            collage = self.build_collage(preview=True)
            buf = io.BytesIO()
            collage.save(buf, format="PNG")
            qimg = QImage.fromData(buf.getvalue())
            pixmap = QPixmap.fromImage(qimg)
            # Scala per adattare al widget
            avail = self.scroll.viewport().size()
            scaled = pixmap.scaled(
                avail.width() - 20, avail.height() - 20,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled)
            self.statusBar().showMessage(
                f"Anteprima: {collage.width}x{collage.height} - "
                f"{len(self.images)} immagini"
            )
        except Exception as e:
            self.statusBar().showMessage(f"Errore anteprima: {e}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.schedule_preview()

    # ---------------- Costruzione collage ----------------
    def build_collage(self, preview=False):
        n = len(self.images)
        cols = self.cols_spin.value()
        gap = self.gap_spin.value()
        pad = self.pad_spin.value()
        round_radius = self.round_spin.value()
        border_w = self.border_spin.value()
        target_w = self.width_spin.value() if not preview else min(self.width_spin.value(), 800)

        # Prepara immagini (apply B/N)
        processed = []
        for entry in self.images:
            img = entry["image"].copy()
            if self.chk_bw.isChecked():
                img = ImageOps.grayscale(img).convert("RGBA")
            processed.append(img)

        mode = self.layout_combo.currentText()

        if mode == "Orizzontale":
            return self._layout_horizontal(processed, target_w, gap, pad,
                                           round_radius, border_w)
        elif mode == "Verticale":
            return self._layout_vertical(processed, target_w, gap, pad,
                                         round_radius, border_w)
        elif mode == "Mosaico casuale":
            return self._layout_mosaic(processed, target_w, gap, pad,
                                       round_radius, border_w)
        else:
            return self._layout_grid(processed, target_w, cols, gap, pad,
                                     round_radius, border_w)

    def _apply_round(self, img, radius):
        if radius <= 0:
            return img
        mask = Image.new("L", img.size, 0)
        d = ImageDraw.Draw(mask)
        d.rounded_rectangle([0, 0, img.size[0] - 1, img.size[1] - 1],
                            radius=radius, fill=255)
        out = Image.new("RGBA", img.size, (0, 0, 0, 0))
        out.paste(img, (0, 0), mask)
        return out

    def _apply_border(self, img, width, color):
        if width <= 0:
            return img
        # Espande canvas con bordo
        new_w = img.width + width * 2
        new_h = img.height + width * 2
        out = Image.new("RGBA", (new_w, new_h), color)
        out.paste(img, (width, width), img)
        return out

    def _prepare_tile(self, img, target_w, target_h, round_radius, border_w):
        """Ridimensiona a riempimento del box, ritaglia centrato."""
        scaled = ImageOps.fit(img, (target_w, target_h), Image.Resampling.LANCZOS)
        if border_w > 0:
            scaled = self._apply_border(scaled, border_w, self.border_color)
        scaled = self._apply_round(scaled, round_radius)
        return scaled

    def _layout_grid(self, imgs, target_w, cols, gap, pad, round_radius, border_w):
        n = len(imgs)
        rows = (n + cols - 1) // cols

        # Calcola dimensioni celle
        inner_w = target_w - 2 * pad - gap * (cols - 1)
        cell_w = inner_w // cols
        cell_h = cell_w  # quadrato

        total_h = 2 * pad + rows * cell_h + gap * (rows - 1)

        canvas = Image.new("RGBA", (target_w, total_h), self.bg_color)

        for i, img in enumerate(imgs):
            r, c = divmod(i, cols)
            tile = self._prepare_tile(img, cell_w, cell_h, round_radius, border_w)
            x = pad + c * (cell_w + gap)
            y = pad + r * (cell_h + gap)
            # Se bordo: tile è più grande, centro
            if border_w > 0:
                x -= border_w
                y -= border_w
                x = max(pad + c * (cell_w + gap) - border_w,
                        pad + c * (cell_w + gap) - border_w)
            canvas.paste(tile, (x, y), tile)

        return canvas

    def _layout_horizontal(self, imgs, target_w, gap, pad, round_radius, border_w):
        n = len(imgs)
        inner_w = target_w - 2 * pad - gap * (n - 1)
        cell_w = max(50, inner_w // n)
        # Altezza basata sull'aspect medio
        avg_ratio = sum(im.height / im.width for im in imgs) / n
        cell_h = int(cell_w * avg_ratio)
        total_h = 2 * pad + cell_h

        canvas = Image.new("RGBA", (target_w, total_h), self.bg_color)
        for i, img in enumerate(imgs):
            tile = self._prepare_tile(img, cell_w, cell_h, round_radius, border_w)
            x = pad + i * (cell_w + gap)
            y = pad
            if border_w > 0:
                x -= border_w
                y -= border_w
            canvas.paste(tile, (x, y), tile)
        return canvas

    def _layout_vertical(self, imgs, target_w, gap, pad, round_radius, border_w):
        n = len(imgs)
        inner_w = target_w - 2 * pad
        cell_w = inner_w
        # Altezza basata su aspect ratio, limitata
        heights = []
        for im in imgs:
            h = int(cell_w * (im.height / im.width))
            h = min(h, int(cell_w * 1.5))
            heights.append(h)
        total_h = 2 * pad + sum(heights) + gap * (n - 1)

        canvas = Image.new("RGBA", (target_w, total_h), self.bg_color)
        y = pad
        for i, img in enumerate(imgs):
            tile = self._prepare_tile(img, cell_w, heights[i], round_radius, border_w)
            x = pad
            if border_w > 0:
                x -= border_w
                y -= border_w
            canvas.paste(tile, (x, y), tile)
            y += heights[i] + gap
        return canvas

    def _layout_mosaic(self, imgs, target_w, gap, pad, round_radius, border_w):
        import random
        random.seed(42)  # coerente tra preview e salvataggio
        n = len(imgs)
        cols = max(2, self.cols_spin.value())

        # Griglia con span variabili (tipo masonry / mosaic)
        inner_w = target_w - 2 * pad - gap * (cols - 1)
        cell_w = inner_w // cols
        cell_h = cell_w

        # Genera posizioni con span casuali
        grid = [[False] * cols for _ in range(n * 2 + 4)]
        placements = []

        for idx in range(n):
            placed = False
            for r in range(len(grid)):
                if placed:
                    break
                for c in range(cols):
                    # Prova span 2x2, 2x1, 1x2, 1x1
                    for span_r, span_c in [(2, 2), (2, 1), (1, 2), (1, 1)]:
                        if c + span_c > cols:
                            continue
                        if self._area_free(grid, r, c, span_r, span_c):
                            placements.append((r, c, span_r, span_c, idx))
                            self._fill_area(grid, r, c, span_r, span_c)
                            placed = True
                            break
                    if placed:
                        break

        rows_used = max(p[0] + p[2] for p in placements)
        total_h = 2 * pad + rows_used * cell_h + gap * (rows_used - 1)
        canvas = Image.new("RGBA", (target_w, total_h), self.bg_color)

        for (r, c, sr, sc, idx) in placements:
            w = cell_w * sc + gap * (sc - 1)
            h = cell_h * sr + gap * (sr - 1)
            tile = self._prepare_tile(imgs[idx], w, h, round_radius, border_w)
            x = pad + c * (cell_w + gap)
            y = pad + r * (cell_h + gap)
            if border_w > 0:
                x -= border_w
                y -= border_w
            canvas.paste(tile, (x, y), tile)

        return canvas

    def _area_free(self, grid, r, c, sr, sc):
        for rr in range(r, r + sr):
            if rr >= len(grid):
                return False
            for cc in range(c, c + sc):
                if cc >= len(grid[0]) or grid[rr][cc]:
                    return False
        return True

    def _fill_area(self, grid, r, c, sr, sc):
        for rr in range(r, r + sr):
            for cc in range(c, c + sc):
                grid[rr][cc] = True

    # ---------------- Salvataggio ----------------
    def save_collage(self):
        if not self.images:
            QMessageBox.information(self, "Info", "Aggiungi almeno un'immagine.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Salva Collage", "collage.png",
            "PNG (*.png);;JPEG (*.jpg);;WEBP (*.webp)"
        )
        if not path:
            return
        try:
            collage = self.build_collage(preview=False)
            # Rimuovi trasparenze per JPEG
            if path.lower().endswith((".jpg", ".jpeg")):
                collage = collage.convert("RGB")
            collage.save(path)
            self.statusBar().showMessage(f"Salvato: {path}")
            QMessageBox.information(self, "Successo",
                                    f"Collage salvato in:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore salvataggio: {e}")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = CollageMaker()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
