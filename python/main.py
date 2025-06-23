import sys
import json
import tempfile

import qrcode
import os
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QScrollArea,
    QFrame,
    QDateEdit,
    QFileDialog,
    QMessageBox,
    QGroupBox, QHBoxLayout,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QDate
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


class DogInfoApp(QWidget):
    """Dog information collection app with dynamic owner add/remove."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dog Information")
        self.setGeometry(100, 100, 400, 600)

        # Main layout
        self.layout = QVBoxLayout()

        # Dog name
        self.dog_name_input = QLineEdit()
        self.layout.addWidget(QLabel("Dog Name:"))
        self.layout.addWidget(self.dog_name_input)

        # Breed selection with custom input option
        self.layout.addWidget(QLabel("Breed:"))
        self.breed_combo = QComboBox()
        breeds = [
            "Azawakh",
            "Afghan Hound",
            "Borzoi",
            "Deerhound",
            "Irish Wolfhound",
            "Italian Sighthound",
            "Saluki",
            "Sloughi",
            "Greyhound",
            "Magyar Agar",
            "Chart Polski",
            "Galgo Espagnol",
            "Whippet",
            "Pharaoh Hound",
            "Cirneco dell´Etna",
            "Podenco Ibicenco",
            "Podenco Canario",
            "Kazakh Tazy",
            "Other",
        ]
        self.breed_combo.addItems(breeds)
        self.breed_combo.currentIndexChanged.connect(self.toggle_breed_input)
        self.layout.addWidget(self.breed_combo)

        self.breed_input = QLineEdit()
        self.breed_input.setPlaceholderText("Enter breed")
        self.breed_input.setVisible(False)  # Initially hidden
        self.layout.addWidget(self.breed_input)

        # Class selection with custom input option
        self.layout.addWidget(QLabel("Class:"))
        self.class_combo = QComboBox()
        class_options = ["FCI-CACIL class", "FCI-CSS class", "Other"]
        self.class_combo.addItems(class_options)
        self.class_combo.currentIndexChanged.connect(self.toggle_class_input)
        self.layout.addWidget(self.class_combo)

        self.class_input = QLineEdit()
        self.class_input.setPlaceholderText("Enter class")
        self.class_input.setVisible(False)  # Initially hidden
        self.layout.addWidget(self.class_input)

        # Gender selection
        self.layout.addWidget(QLabel("Gender:"))
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Male", "Female"])
        self.layout.addWidget(self.gender_combo)

        # Other dog information fields
        form_layout = QFormLayout()

        self.chip_number_input = QLineEdit()
        self.license_number_input = QLineEdit()
        self.pedigree_number_input = QLineEdit()

        form_layout.addRow("Chip Number:", self.chip_number_input)
        form_layout.addRow("License Number:", self.license_number_input)
        form_layout.addRow("Pedigree Number:", self.pedigree_number_input)

        # Birth Date with QDateEdit (calendar widget)
        self.birth_date_input = QDateEdit()
        self.birth_date_input.setCalendarPopup(True)
        self.birth_date_input.setDate(QDate.currentDate())  # Default to current date
        form_layout.addRow("Birth Date:", self.birth_date_input)

        self.layout.addLayout(form_layout)

        # Scrollable area for multiple owners
        self.owner_scroll_area = QScrollArea()
        self.owner_widget = QWidget()
        self.owner_layout = QVBoxLayout(self.owner_widget)
        self.owner_scroll_area.setWidget(self.owner_widget)
        self.owner_scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.owner_scroll_area)

        # Storage for owner metadata
        self.owners = []  # list of dicts with field widgets
        self.owner_frames = []  # list of QGroupBox widgets for easy removal/renumbering

        # Add initial owner section (cannot be deleted)
        self.add_owner_fields()

        # Button to add more owners
        add_owner_button = QPushButton("Add Second (Next) Owner")
        add_owner_button.clicked.connect(self.add_owner_fields)
        self.layout.addWidget(add_owner_button)

        # Button to generate and save QR code as Image
        save_image_button = QPushButton("Generate and Save QR Code as Image")
        save_image_button.clicked.connect(self.save_as_image)
        self.layout.addWidget(save_image_button)

        # Button to generate and save QR code as PDF
        save_pdf_button = QPushButton("Save as PDF")
        save_pdf_button.clicked.connect(self.save_as_pdf)
        self.layout.addWidget(save_pdf_button)

        # Label to display QR code
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.qr_label)

        # Set main layout
        self.setLayout(self.layout)

    # ────────────────────────────────────────────────────────────
    # Owner helpers
    # ────────────────────────────────────────────────────────────

    def add_owner_fields(self):
        """Create a new owner section. Owner #1 cannot be deleted."""
        owner_index = len(self.owners) + 1

        # Group box for visual separation & easy renumbering
        group = QGroupBox(f"Owner {owner_index}")
        form = QFormLayout(group)

        first_name_input = QLineEdit()
        last_name_input = QLineEdit()
        street_number_input = QLineEdit()
        postal_city_input = QLineEdit()
        country_input = QLineEdit()

        form.addRow("First Name:", first_name_input)
        form.addRow("Last Name:", last_name_input)
        form.addRow("Street and Number:", street_number_input)
        form.addRow("Postal Code and City:", postal_city_input)
        form.addRow("Country:", country_input)

        # Remove button for owners > 1
        if owner_index > 1:
            remove_button = QPushButton("Remove this owner")
            remove_button.setFixedWidth(160)
            remove_button.setStyleSheet("margin-top: 8px; padding: 6px 12px;")
            remove_button.clicked.connect(lambda _, grp=group: self.remove_owner(grp))

            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            btn_layout.addWidget(remove_button)
            btn_layout.addStretch()

            # Use a whole horizontal layout instead of single widget field
            form.addRow(btn_layout)

        self.owner_layout.addWidget(group)
        self.owner_widget.setMinimumHeight(self.owner_widget.sizeHint().height())

        # Store widgets for data extraction and renumbering
        self.owner_frames.append(group)
        self.owners.append(
            {
                "FirstName": first_name_input,
                "LastName": last_name_input,
                "StreetAndNumber": street_number_input,
                "PostalCodeAndCity": postal_city_input,
                "Country": country_input,
            }
        )

    def remove_owner(self, group_box: QGroupBox):
        """Remove the given owner section and renumber others."""
        # Safety: prevent deleting first owner
        index = self.owner_frames.index(group_box)
        if index == 0:
            QMessageBox.warning(self, "Warning", "At least one owner is required.")
            return

        # Remove from layout visually
        self.owner_layout.removeWidget(group_box)
        group_box.deleteLater()

        # Remove from tracking lists
        del self.owner_frames[index]
        del self.owners[index]

        # Renumber remaining owners so titles & remove‑button logic stay consistent
        self.update_owner_titles()

    def update_owner_titles(self):
        """Ensure group titles and remove button visibility are consistent."""
        for idx, group in enumerate(self.owner_frames):
            owner_number = idx + 1
            group.setTitle(f"Owner {owner_number}")
            # Toggle visibility of remove button for first owner
            for i in range(group.layout().rowCount()):
                item = group.layout().itemAt(i, QFormLayout.FieldRole)
                if item and isinstance(item.widget(), QPushButton):
                    item.widget().setVisible(owner_number > 1)

    # ────────────────────────────────────────────────────────────
    # UI toggles
    # ────────────────────────────────────────────────────────────

    def toggle_breed_input(self):
        self.breed_input.setVisible(self.breed_combo.currentText() == "Other")

    def toggle_class_input(self):
        self.class_input.setVisible(self.class_combo.currentText() == "Other")

    # ────────────────────────────────────────────────────────────
    # QR code generation & saving
    # ────────────────────────────────────────────────────────────

    def generate_qr_code(self):
        # Collect dog information
        dog_data = self.collect_data()

        # Convert to JSON string
        json_data = json.dumps(dog_data, ensure_ascii=False, indent=4)

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=3,  # Smaller box size for more compact QR
            border=1,
        )
        qr.add_data(json_data)
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white")

        # Display QR code in the label
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue(), "PNG")
        self.qr_label.setPixmap(pixmap)

        # Save QR code image data for later use
        self.qr_image_data = buffer.getvalue()

    def save_as_image(self):
        # Generate and save QR code as image
        self.generate_qr_code()

        # Ask user for save location
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", "", "PNG Files (*.png)", options=options
        )

        if file_path:
            try:
                # Save the QR code image to the specified location
                with open(file_path, "wb") as image_file:
                    image_file.write(self.qr_image_data)

                # Show success message
                QMessageBox.information(
                    self, "Success", "The image has been saved successfully."
                )

            except Exception as e:
                print(f"An error occurred: {e}")
                QMessageBox.critical(
                    self, "Error", f"An error occurred while saving the image: {e}"
                )

    def save_as_pdf(self):
        # Generate QR code first
        self.generate_qr_code()

        # Ask user for save location
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", "", "PDF Files (*.pdf)", options=options
        )

        if file_path:
            try:
                # Create a temporary file to save the QR code image
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                    temp_file.write(self.qr_image_data)
                    temp_file_path = temp_file.name

                # Create PDF with QR code centered and scaled to fit the page
                c = canvas.Canvas(file_path, pagesize=letter)
                page_width, page_height = letter  # Dimensions of a letter-size page

                # Calculate dimensions to center the QR code and make it as large as possible
                qr_size = min(page_width, page_height) * 0.8  # 80% of the page width/height
                x_position = (page_width - qr_size) / 2
                y_position = (page_height - qr_size) / 2

                # Draw the QR code image
                c.drawImage(temp_file_path, x_position, y_position, width=qr_size, height=qr_size)
                c.showPage()
                c.save()

                # Show success message
                QMessageBox.information(
                    self, "Success", "The PDF file has been saved successfully."
                )

            except Exception as e:
                print(f"An error occurred: {e}")
                QMessageBox.critical(self, "Error", f"An error occurred while saving PDF: {e}")

            finally:
                # Remove the temporary file
                try:
                    os.remove(temp_file_path)
                except Exception as cleanup_error:
                    print(f"Failed to delete temporary file: {cleanup_error}")

    # ────────────────────────────────────────────────────────────
    # Data collection
    # ────────────────────────────────────────────────────────────

    def collect_data(self):
        # Collect and return dog data as dictionary with DogName first
        dog_data = {
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
                        "FirstName": owner["FirstName"].text(),
                        "LastName": owner["LastName"].text(),
                        "StreetAndNumber": owner["StreetAndNumber"].text(),
                        "PostalCodeAndCity": owner["PostalCodeAndCity"].text(),
                        "Country": owner["Country"].text(),
                    }
                    for owner in self.owners
                ],
            }
        }
        return dog_data


# Main application execution
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DogInfoApp()
    window.show()
    sys.exit(app.exec_())
