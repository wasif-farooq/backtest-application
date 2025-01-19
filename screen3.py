from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QPushButton, QHBoxLayout,
    QCalendarWidget, QLineEdit, QPlainTextEdit
)
from PyQt5.QtCore import QDate, QThread, pyqtSignal
import os
import json
import time
import traceback
import pandas as pd
from binance_data import BinanceData


class DownloadWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, binance_data, start_time, end_time, file_name, symbol):
        super().__init__()
        self.binance_data = binance_data
        self.start_time = start_time
        self.end_time = end_time
        self.file_name = file_name
        self.symbol = symbol

    def run(self):
        """Perform the download operation in a separate thread."""
        current_start_time = self.start_time
        all_data = []

        try:
            while current_start_time < self.end_time:
                self.log_signal.emit(
                    f"Fetching data from {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(current_start_time / 1000))}..."
                )
                chunk_data = self.binance_data.fetch_kline_data(
                    start_time=current_start_time, end_time=self.end_time, limit=500
                )
                if not chunk_data:
                    self.log_signal.emit(
                        f"No more data available for {self.symbol}."
                    )
                    break

                all_data.extend(chunk_data)
                current_start_time = chunk_data[-1][0] + 1

                # Introduce a small delay to avoid hitting API rate limits
                time.sleep(1)

            if all_data:
                self.binance_data.process_and_save_data(all_data)
                self.finished_signal.emit(
                    {"symbol": self.symbol, "file": self.file_name})
            else:
                self.log_signal.emit(f"No data found for {self.symbol}.")
        except Exception as e:
            error_msg = f"Error during download: {e}\n{traceback.format_exc()}"
            self.error_signal.emit(error_msg)


class Screen3(QWidget):
    def __init__(self, mainWindow, parent=None):
        super().__init__(parent)
        self.mainWindow = mainWindow
        self.added_symbols = []
        self.download_threads = []
        self.load_symbols()

        # Main layout
        self.main_layout = QVBoxLayout(self)

        # Back button
        self.backButton = QPushButton("Back")
        self.main_layout.addWidget(self.backButton)
        self.backButton.clicked.connect(self.goBack)

        # Log panel for download logs
        self.log_text_edit = QPlainTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.main_layout.addWidget(QLabel("Download Logs:"))
        self.main_layout.addWidget(self.log_text_edit)

        # Form layout for adding symbols
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Full calendars for selecting start and end dates
        self.start_date_calendar = QCalendarWidget()
        self.end_date_calendar = QCalendarWidget()

        # Set default dates to current date
        self.start_date_calendar.setSelectedDate(QDate.currentDate())
        self.end_date_calendar.setSelectedDate(QDate.currentDate())

        # Input fields for symbol and file name
        self.symbol_edit = QLineEdit()
        self.file_name = QLineEdit()

        # Adding widgets to the form layout
        form_layout.addRow("Start Date:", self.start_date_calendar)
        form_layout.addRow("End Date:", self.end_date_calendar)
        form_layout.addRow("Symbol:", self.symbol_edit)
        form_layout.addRow("File Name:", self.file_name)

        # Button to add symbols
        self.add_symbol_button = QPushButton("Add Symbol")
        form_layout.addRow(self.add_symbol_button)

        # Adding the form layout to the main layout
        self.main_layout.addLayout(form_layout)

        # Section for listing added symbols
        self.symbols_layout = QVBoxLayout()
        self.main_layout.addLayout(self.symbols_layout)

        # Connect button signal
        self.add_symbol_button.clicked.connect(self.add_symbol)

        # Update symbol list on initialization
        self.update_symbol_list()

    def load_symbols(self):
        """Load added symbols from a JSON file."""
        try:
            with open('added_symbols.json', 'r') as f:
                self.added_symbols = json.load(f)
        except Exception:
            self.added_symbols = []

    def save_symbols(self):
        """Save added symbols to a JSON file."""
        with open('added_symbols.json', 'w') as f:
            json.dump(self.added_symbols, f)

    def add_symbol(self):
        """Add a new symbol and fetch its data using a worker thread."""
        start_date = self.start_date_calendar.selectedDate().toPyDate()
        end_date = self.end_date_calendar.selectedDate().toPyDate()
        symbol = self.symbol_edit.text().strip().upper()
        file_name = self.file_name.text().strip()

        interval = "1m"

        if not symbol:
            self.log_text_edit.appendPlainText("Symbol cannot be empty.")
            return

        if not file_name:
            self.log_text_edit.appendPlainText("File name cannot be empty.")
            return

        self.log_text_edit.appendPlainText(
            f"Starting download for {symbol} ...")

        start_time = int(time.mktime(start_date.timetuple()) * 1000)
        end_time = int(time.mktime(end_date.timetuple()) * 1000)

        API_URL = "https://fapi.binance.com"
        csv_file_name = f"data/{symbol}--{file_name}.csv"
        binance_data = BinanceData(
            api_url=API_URL,
            symbol=symbol,
            interval=interval,
            file=csv_file_name
        )

        # Create and start the download worker thread
        worker = DownloadWorker(binance_data, start_time,
                                end_time, csv_file_name, symbol)
        worker.log_signal.connect(self.log_text_edit.appendPlainText)
        worker.finished_signal.connect(self.on_download_finished)
        worker.error_signal.connect(self.on_download_error)
        # Keep reference to avoid garbage collection
        self.download_threads.append(worker)
        worker.start()

    def on_download_finished(self, result):
        """Handle the completion of a download."""
        symbol = result["symbol"]
        file_name = result["file"]
        self.log_text_edit.appendPlainText(
            f"Data fetched and saved for {symbol}.")

        existing = next(
            (s for s in self.added_symbols if s["file"] == file_name), None)
        if not existing:
            self.added_symbols.append({"symbol": symbol, "file": file_name})
        else:
            existing["file"] = file_name

        self.save_symbols()
        self.update_symbol_list()

    def on_download_error(self, error_msg):
        """Handle errors during the download."""
        self.log_text_edit.appendPlainText(error_msg)

    def update_symbol_list(self):
        """Update the list of added symbols."""
        while self.symbols_layout.count():
            child = self.symbols_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for symbol_info in self.added_symbols:
            h_layout = QHBoxLayout()
            label = QLabel(f"{symbol_info['symbol']} - {symbol_info['file']}")
            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(
                lambda checked, s=symbol_info: self.delete_symbol(s))
            h_layout.addWidget(label)
            h_layout.addWidget(delete_button)
            self.symbols_layout.addLayout(h_layout)

    def delete_symbol(self, symbol_info):
        """Delete a symbol and its associated file."""
        file_path = symbol_info["file"]
        if os.path.exists(file_path):
            os.remove(file_path)
        self.added_symbols = [
            s for s in self.added_symbols if s != symbol_info]
        self.save_symbols()
        self.update_symbol_list()

    def goBack(self):
        """Navigate back to the previous screen."""
        if hasattr(self.mainWindow, 'screen1'):
            self.mainWindow.screen1.refreshCandleFiles()
            self.mainWindow.stack.setCurrentWidget(self.mainWindow.screen1)
