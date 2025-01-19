import os
import pandas as pd
import plotly.graph_objects as go
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QFormLayout,
    QLabel,
    QSizePolicy,
    QHeaderView,
    QPushButton,
    QDialog,
    QVBoxLayout,
    QFileDialog
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from tempfile import NamedTemporaryFile


class Screen2(QWidget):
    def __init__(self, mainWindow, parent=None):
        super().__init__(parent)
        self.mainWindow = mainWindow

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(10)

        # Back button
        self.backButton = QPushButton("Back")
        self.backButton.clicked.connect(self.goBack)
        self.layout.addWidget(self.backButton)

        self.userInfoLayout = QFormLayout()
        self.layout.addLayout(self.userInfoLayout)

        # Stats and trades tables
        self.statsTable = QTableWidget()
        self.tradesTable = QTableWidget()

        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.statsTable.setSizePolicy(size_policy)
        self.tradesTable.setSizePolicy(size_policy)

        self.layout.addWidget(self.statsTable)
        self.layout.addWidget(self.tradesTable)

        # Export to CSV button
        self.exportButton = QPushButton("Export to CSV")
        self.exportButton.clicked.connect(self.exportToCSV)
        self.layout.addWidget(self.exportButton)

    def updateUserInputs(self, formData):
        while self.userInfoLayout.count():
            child = self.userInfoLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        for key, value in formData.items():
            self.userInfoLayout.addRow(QLabel(f"{key}: "), QLabel(str(value)))

    def updateTable(self, stats, trades_df):
        # Update monthly stats table
        self.trades_df = trades_df  # Save trades_df for export functionality

        if stats:
            headers = list(stats[0].keys())
            num_data_rows = len(stats)
            self.statsTable.setColumnCount(len(headers))
            self.statsTable.setRowCount(num_data_rows + 1)
            self.statsTable.setHorizontalHeaderLabels(headers)

            header_stats = self.statsTable.horizontalHeader()
            header_stats.setSectionResizeMode(QHeaderView.Stretch)

            totals = {}
            for key in headers:
                if isinstance(stats[0][key], (int, float)):
                    totals[key] = 0
                else:
                    totals[key] = None

            for r, row in enumerate(stats):
                for c, key in enumerate(headers):
                    value = row[key]
                    self.statsTable.setItem(r, c, QTableWidgetItem(str(value)))
                    if totals[key] is not None:
                        totals[key] += value

            footer_row = num_data_rows
            for c, key in enumerate(headers):
                if totals[key] is not None:
                    self.statsTable.setItem(
                        footer_row, c, QTableWidgetItem("Total: " + str(totals[key])))
                else:
                    self.statsTable.setItem(
                        footer_row, c, QTableWidgetItem(""))

        # Update trades table with "View Chart" button
        if trades_df is not None and not trades_df.empty:
            trade_headers = list(trades_df.columns) + ["Actions"]
            num_trade_rows = trades_df.shape[0]
            self.tradesTable.setColumnCount(len(trade_headers))
            self.tradesTable.setRowCount(num_trade_rows)
            self.tradesTable.setHorizontalHeaderLabels(trade_headers)

            header_trades = self.tradesTable.horizontalHeader()
            header_trades.setSectionResizeMode(QHeaderView.Stretch)

            for r in range(num_trade_rows):
                for c, col in enumerate(trades_df.columns):
                    value = trades_df.iloc[r][col]
                    self.tradesTable.setItem(
                        r, c, QTableWidgetItem(str(value)))

                # Add "View Chart" button in the last column
                view_button = QPushButton("View Chart")
                view_button.clicked.connect(
                    lambda checked, row=r: self.viewCandleChart(
                        trades_df.iloc[row]["Datetime"],  # Trade open time
                        trades_df.iloc[row]["Close_Time"]  # Trade close time
                    )
                )
                self.tradesTable.setCellWidget(
                    r, len(trade_headers) - 1, view_button)

    def viewCandleChart(self, open_time, close_time):
        # Fetch the selected Candle File from Screen1
        candle_file = self.mainWindow.screen1.candleFileCombo.currentText()
        if not candle_file or not os.path.exists(candle_file):
            return

        try:
            # Load candle data
            candle_data = pd.read_csv(candle_file, parse_dates=["Datetime"])

            # Find the indices for the open_time and close_time
            open_idx = candle_data[candle_data['Datetime']
                                   == pd.to_datetime(open_time)].index
            close_idx = candle_data[candle_data['Datetime']
                                    == pd.to_datetime(close_time)].index

            if not open_idx.empty and not close_idx.empty:
                open_idx = open_idx[0]
                close_idx = close_idx[0]

                # Adjust to include 30 candles before and after
                start_idx = max(open_idx - 30, 0)
                end_idx = min(close_idx + 30, len(candle_data) - 1)

                # Filter the data for the expanded range
                filtered_data = candle_data.iloc[start_idx:end_idx + 1].copy()
            else:
                return

            if filtered_data.empty:
                return

            # Create the candle chart
            self.showCandleChart(
                filtered_data, open_time=open_time, close_time=close_time)
        except Exception as e:
            return

    def showCandleChart(self, filtered_data, open_time=None, close_time=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Candle Chart")
        dialog.showMaximized()  # Show dialog in full screen

        # Generate the candlestick chart using Plotly
        fig = go.Figure(data=[
            go.Candlestick(
                x=filtered_data['Datetime'],
                open=filtered_data['Open'],
                high=filtered_data['High'],
                low=filtered_data['Low'],
                close=filtered_data['Close'],
                increasing_line_color='limegreen',
                decreasing_line_color='tomato',
            )
        ])

        # Add scatter points for open and close trade times
        if open_time:
            fig.add_trace(
                go.Scatter(
                    x=[pd.to_datetime(open_time)],
                    y=[filtered_data.loc[filtered_data['Datetime'] ==
                                         pd.to_datetime(open_time), 'High'].iloc[0]],
                    mode="markers+text",
                    name="Trade Open",
                    text=["Open"],
                    textposition="top center",
                    marker=dict(color="blue", size=10, symbol="circle"),
                )
            )
        if close_time:
            fig.add_trace(
                go.Scatter(
                    x=[pd.to_datetime(close_time)],
                    y=[filtered_data.loc[filtered_data['Datetime'] ==
                                         pd.to_datetime(close_time), 'High'].iloc[0]],
                    mode="markers+text",
                    name="Trade Close",
                    text=["Close"],
                    textposition="top center",
                    marker=dict(color="red", size=10, symbol="circle"),
                )
            )

        # Update layout for dark theme and better visuals
        fig.update_layout(
            title="Candle Chart with Trade Points",
            xaxis_title="Datetime",
            yaxis_title="Price",
            template="plotly_dark",  # Apply the dark theme
            xaxis_rangeslider_visible=False,
            font=dict(color="white"),
        )

        # Save the chart as an HTML file
        with NamedTemporaryFile(delete=False, suffix=".html") as tmp:
            fig.write_html(tmp.name)
            chart_file = tmp.name

        # Display the chart in a QWebEngineView
        web_view = QWebEngineView()
        web_view.setUrl(QUrl.fromLocalFile(chart_file))
        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.addWidget(web_view)
        dialog.exec_()

        # Cleanup temporary HTML file
        os.remove(chart_file)

    def exportToCSV(self):
        if self.trades_df is None or self.trades_df.empty:
            return

        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Trades to CSV", "", "CSV Files (*.csv);;All Files (*)", options=options
        )
        if file_path:
            try:
                self.trades_df.to_csv(file_path, index=False)
                print(f"Trades saved successfully to {file_path}")
            except Exception as e:
                print(f"Failed to save trades: {e}")

    def goBack(self):
        # Reset form fields on Screen1
        self.mainWindow.screen1.capitalSpin.setValue(0)
        self.mainWindow.screen1.leverageSpin.setValue(0)
        self.mainWindow.screen1.makerFeesSpin.setValue(0)
        self.mainWindow.screen1.takerFeesSpin.setValue(0)
        self.mainWindow.screen1.tpPercentSpin.setValue(0)
        self.mainWindow.screen1.slPercentSpin.setValue(0)
        self.mainWindow.screen1.candleFileCombo.setCurrentIndex(0)
        self.mainWindow.screen1.fileLabel.setText("No file selected")

        # Reset the Submit button state
        self.mainWindow.screen1.submitButton.setEnabled(True)
        self.mainWindow.screen1.submitButton.setText("Submit")

        # Navigate back to Screen1
        self.mainWindow.stack.setCurrentWidget(self.mainWindow.screen1)
