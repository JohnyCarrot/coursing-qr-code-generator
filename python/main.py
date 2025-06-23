import sys
import json
import tempfile
import os
from io import BytesIO

import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QScrollArea, QDateEdit, QFileDialog, QMessageBox,
    QGroupBox, QHBoxLayout, QSizePolicy
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QDate


class DogInfoApp(QWidget):
    """Dog information collection app with dynamic owner add/remove."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dog Information")
        self.resize(400, 600)                       # len „štartovacia“ veľkosť, nie pevná

        # ───────────────────────── main layout ─────────────────────────
        self.layout = QVBoxLayout(self)

        # Dog name
        self.dog_name_input = QLineEdit()
        self.layout.addWidget(QLabel("Dog Name:"))
        self.layout.addWidget(self.dog_name_input)

        # Breed
        self.layout.addWidget(QLabel("Breed:"))
        self.breed_combo = QComboBox()
        breeds = [
            "Azawakh", "Afghan Hound", "Borzoi", "Deerhound", "Irish Wolfhound",
            "Italian Sighthound", "Saluki", "Sloughi", "Greyhound", "Magyar Agar",
            "Chart Polski", "Galgo Espagnol", "Whippet", "Pharaoh Hound",
            "Cirneco dell´Etna", "Podenco Ibicenco", "Podenco Canario",
            "Kazakh Tazy", "Other",
        ]
        self.breed_combo.addItems(breeds)
        self.breed_combo.currentIndexChanged.connect(self.toggle_breed_input)
        self.layout.addWidget(self.breed_combo)

        self.breed_input = QLineEdit(placeholderText="Enter breed")
        self.breed_input.setVisible(False)
        self.layout.addWidget(self.breed_input)

        # Class
        self.layout.addWidget(QLabel("Class:"))
        self.class_combo = QComboBox()
        self.class_combo.addItems(["FCI-CACIL class", "FCI-CSS class", "Other"])
        self.class_combo.currentIndexChanged.connect(self.toggle_class_input)
        self.layout.addWidget(self.class_combo)

        self.class_input = QLineEdit(placeholderText="Enter class")
        self.class_input.setVisible(False)
        self.layout.addWidget(self.class_input)

        # Gender
        self.layout.addWidget(QLabel("Gender:"))
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Male", "Female"])
        self.layout.addWidget(self.gender_combo)

        # Other dog info
        form_layout = QFormLayout()
        self.chip_number_input = QLineEdit()
        self.license_number_input = QLineEdit()
        self.pedigree_number_input = QLineEdit()
        self.birth_date_input = QDateEdit(calendarPopup=True)
        self.birth_date_input.setDate(QDate.currentDate())

        form_layout.addRow("Chip Number:", self.chip_number_input)
        form_layout.addRow("License Number:", self.license_number_input)
        form_layout.addRow("Pedigree Number:", self.pedigree_number_input)
        form_layout.addRow("Birth Date:", self.birth_date_input)
        self.layout.addLayout(form_layout)

        # ──────────────────────── owners scroll area ────────────────────
        self.owner_scroll_area = QScrollArea()
        self.owner_scroll_area.setWidgetResizable(True)
        self.owner_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.owner_widget = QWidget()
        self.owner_layout = QVBoxLayout(self.owner_widget)
        self.owner_scroll_area.setWidget(self.owner_widget)
        self.layout.addWidget(self.owner_scroll_area)

        # storage
        self.owners = []
        self.owner_frames = []

        # first owner (mandatory)
        self.add_owner_fields()

        # add-owner button
        add_owner_button = QPushButton("Add Second (Next) Owner")
        add_owner_button.clicked.connect(self.add_owner_fields)
        self.layout.addWidget(add_owner_button)

        # save buttons
        save_image_button = QPushButton("Generate and Save QR Code as Image")
        save_image_button.clicked.connect(self.save_as_image)
        self.layout.addWidget(save_image_button)

        save_pdf_button = QPushButton("Save as PDF")
        save_pdf_button.clicked.connect(self.save_as_pdf)
        self.layout.addWidget(save_pdf_button)

        # QR label
        self.qr_label = QLabel(alignment=Qt.AlignCenter)
        self.layout.addWidget(self.qr_label)

    # ───────────────────────── owner helpers ──────────────────────────
    def add_owner_fields(self):
        idx = len(self.owners) + 1
        group = QGroupBox(f"Owner {idx}")
        group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        form = QFormLayout(group)

        fn = QLineEdit()
        ln = QLineEdit()
        street = QLineEdit()
        postal = QLineEdit()
        country = QLineEdit()

        form.addRow("First Name:", fn)
        form.addRow("Last Name:", ln)
        form.addRow("Street and Number:", street)
        form.addRow("Postal Code and City:", postal)
        form.addRow("Country:", country)

        if idx > 1:
            remove_btn = QPushButton("Remove this owner")
            remove_btn.setFixedWidth(160)
            remove_btn.clicked.connect(lambda _, g=group: self.remove_owner(g))

            row = QHBoxLayout()
            row.addStretch()
            row.addWidget(remove_btn)
            row.addStretch()
            form.addRow(row)

        self.owner_layout.addWidget(group)

        self.owner_frames.append(group)
        self.owners.append(
            {"FirstName": fn, "LastName": ln, "StreetAndNumber": street,
             "PostalCodeAndCity": postal, "Country": country}
        )

    def remove_owner(self, group_box: QGroupBox):
        index = self.owner_frames.index(group_box)
        if index == 0:
            QMessageBox.warning(self, "Warning", "At least one owner is required.")
            return

        self.owner_layout.removeWidget(group_box)
        group_box.deleteLater()
        del self.owner_frames[index]
        del self.owners[index]
        self.update_owner_titles()

    def update_owner_titles(self):
        for i, grp in enumerate(self.owner_frames, start=1):
            grp.setTitle(f"Owner {i}")
            for r in range(grp.layout().rowCount()):
                item = grp.layout().itemAt(r, QFormLayout.FieldRole)
                if item and isinstance(item.widget(), QPushButton):
                    item.widget().setVisible(i > 1)

    # ────────────────────────── toggles ───────────────────────────────
    def toggle_breed_input(self):
        self.breed_input.setVisible(self.breed_combo.currentText() == "Other")

    def toggle_class_input(self):
        self.class_input.setVisible(self.class_combo.currentText() == "Other")

    # ──────────────────────── QR & saving ─────────────────────────────
    def generate_qr_code(self):
        data = self.collect_data()
        json_data = json.dumps(data, ensure_ascii=False)

        qr = qrcode.QRCode(version=1,
                           error_correction=qrcode.constants.ERROR_CORRECT_H,
                           box_size=3, border=4)
        qr.add_data(json_data)
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white")

        buf = BytesIO()
        img.save(buf, format="PNG")
        self.qr_image_data = buf.getvalue()

        pix = QPixmap()
        pix.loadFromData(self.qr_image_data, "PNG")
        self.qr_label.setPixmap(pix)

    def save_as_image(self):
        self.generate_qr_code()
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", "", "PNG Files (*.png)"
        )
        if path:
            try:
                with open(path, "wb") as f:
                    f.write(self.qr_image_data)
                QMessageBox.information(self, "Success", "Image saved.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save image: {e}")

    def save_as_pdf(self):
        self.generate_qr_code()
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", "", "PDF Files (*.pdf)"
        )
        if not path:
            return
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(self.qr_image_data)
                tmp_path = tmp.name

            c = canvas.Canvas(path, pagesize=letter)
            w, h = letter
            qr_size = min(w, h) * 0.8
            x = (w - qr_size) / 2
            y = (h - qr_size) / 2
            c.drawImage(tmp_path, x, y, width=qr_size, height=qr_size)
            c.showPage()
            c.save()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save PDF: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    # ─────────────────────── data collection ─────────────────────────
    def collect_data(self):
        return {
            "Dog": {
                "Name": self.dog_name_input.text(),
                "Breed": self.breed_input.text()
                if self.breed_combo.currentText() == "Other"
                else self.breed_combo.currentText(),
                "Class": self.class_input.text()
                if self.class_combo.currentText() == "Other"
                else self.class_combo.currentText(),
                "Gender": self.gender_combo.currentText(),
                "ChipNumber": self.chip_number_input.text(),
                "LicenseNumber": self.license_number_input.text(),
                "PedigreeNumber": self.pedigree_number_input.text(),
                "BirthDate": self.birth_date_input.date().toString("yyyy-MM-dd"),
                "Owners": [
                    {
                        "FirstName": o["FirstName"].text(),
                        "LastName": o["LastName"].text(),
                        "StreetAndNumber": o["StreetAndNumber"].text(),
                        "PostalCodeAndCity": o["PostalCodeAndCity"].text(),
                        "Country": o["Country"].text(),
                    }
                    for o in self.owners
                ],
            }
        }


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DogInfoApp()
    win.show()
    sys.exit(app.exec_())
