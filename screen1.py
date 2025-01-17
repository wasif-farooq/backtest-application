import os
import pandas as pd
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QPushButton, QFileDialog,
    QDoubleSpinBox, QCheckBox, QHBoxLayout, QComboBox, QApplication,
    QDialog, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView
)
from PyQt5.QtCore import QTimer


class Screen1(QWidget):
    def __init__(self, mainWindow, parent=None):
        super().__init__(parent)
        self.mainWindow = mainWindow

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        form = QFormLayout()
        form.setSpacing(20)

        # Candle File dropdown with "Show Data" button
        self.candleFileCombo = QComboBox()
        self.refreshCandleFiles()  # Populate dropdown with current files

        self.showDataButton = QPushButton("Show Data")
        self.showDataButton.clicked.connect(self.showCandleData)

        candle_file_layout = QHBoxLayout()
        candle_file_layout.addWidget(self.candleFileCombo)
        candle_file_layout.addWidget(self.showDataButton)
        form.addRow("Candle File:", candle_file_layout)

        self.capitalSpin = QDoubleSpinBox()
        self.capitalSpin.setMaximum(1e9)
        form.addRow("Capital:", self.capitalSpin)

        self.leverageSpin = QDoubleSpinBox()
        self.leverageSpin.setMaximum(1000)
        form.addRow("Leverage:", self.leverageSpin)

        self.makerFeesSpin = QDoubleSpinBox()
        self.makerFeesSpin.setSuffix(" %")
        self.makerFeesSpin.setDecimals(4)  # Allow up to 4 decimal places
        self.makerFeesSpin.setMaximum(100)
        form.addRow("Maker Fees:", self.makerFeesSpin)

        self.takerFeesSpin = QDoubleSpinBox()
        self.takerFeesSpin.setSuffix(" %")
        self.takerFeesSpin.setDecimals(4)  # Allow up to 4 decimal places
        self.takerFeesSpin.setMaximum(100)
        form.addRow("Taker Fees:", self.takerFeesSpin)

        self.tpPercentSpin = QDoubleSpinBox()
        self.tpPercentSpin.setSuffix(" %")
        self.tpPercentSpin.setMaximum(1000)
        form.addRow("TP %:", self.tpPercentSpin)

        self.slPercentSpin = QDoubleSpinBox()
        self.slPercentSpin.setSuffix(" %")
        self.slPercentSpin.setMaximum(1000)
        form.addRow("SL %:", self.slPercentSpin)

        self.withCompoundingCheck = QCheckBox("With Compounding")
        form.addRow(self.withCompoundingCheck)

        self.fileButton = QPushButton("Select File")
        self.fileLabel = QLabel("No file selected")
        fileLayout = QVBoxLayout()
        fileLayout.addWidget(self.fileButton)
        fileLayout.addWidget(self.fileLabel)
        form.addRow("File:", fileLayout)

        layout.addLayout(form)
        self.submitButton = QPushButton("Submit")
        layout.addWidget(self.submitButton)

        # "Add New" button
        self.addNewButton = QPushButton("Add New")
        addNewLayout = QHBoxLayout()
        addNewLayout.addWidget(self.addNewButton)
        layout.addLayout(addNewLayout)

        self.fileButton.clicked.connect(self.selectFile)
        self.submitButton.clicked.connect(self.submitForm)
        self.addNewButton.clicked.connect(self.navigateToScreen3)

        self.selectedFile = None

    def refreshCandleFiles(self):
        self.candleFileCombo.clear()
        candle_files = []
        data_dir = "data"
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith(".csv"):
                    candle_files.append(os.path.join(data_dir, file))
        self.candleFileCombo.addItems(candle_files)

    def selectFile(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", "CSV Files (*.csv);;All Files (*)", options=options
        )
        if filename:
            self.selectedFile = filename
            self.fileLabel.setText(filename)

    def showCandleData(self):
        file_path = self.candleFileCombo.currentText()
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Error", "No valid file selected.")
            return
        try:
            data = pd.read_csv(file_path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load file: {e}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Data in {os.path.basename(file_path)}")
        dialog.setGeometry(100, 100, 1200, 600)  # Set dialog size
        dialog_layout = QVBoxLayout(dialog)
        table = QTableWidget()
        dialog_layout.addWidget(table)

        if not data.empty:
            table.setColumnCount(len(data.columns))
            table.setRowCount(len(data))
            table.setHorizontalHeaderLabels(data.columns)
            table.horizontalHeader().setStretchLastSection(True)  # Stretch the last section
            table.horizontalHeader().setSectionResizeMode(
                QHeaderView.Stretch)  # Stretch all sections

            for row in range(len(data)):
                for col in range(len(data.columns)):
                    item = QTableWidgetItem(str(data.iat[row, col]))
                    table.setItem(row, col, item)

        dialog.exec_()

    def navigateToScreen3(self):
        if hasattr(self.mainWindow, "showScreen3"):
            self.mainWindow.showScreen3()
        else:
            print("MainWindow does not have a method showScreen3.")

    def submitForm(self):
        self.submitButton.setEnabled(False)
        self.submitButton.setText("Loading...")

        data = {
            "Capital": self.capitalSpin.value(),
            "Leverage": self.leverageSpin.value(),
            "MakerFees": self.makerFeesSpin.value(),
            "TakerFees": self.takerFeesSpin.value(),
            "TP_percent": self.tpPercentSpin.value(),
            "SL_percent": self.slPercentSpin.value(),
            "File": self.selectedFile,
            "WithCompounding": self.withCompoundingCheck.isChecked()
        }

        QTimer.singleShot(100, lambda: self.processSubmission(data))

    def processSubmission(self, data):
        self.mainWindow.showScreen2(data)

