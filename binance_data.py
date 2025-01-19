# binance_data.py
import datetime
import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv
from data_handler import DataHandler

# Load environment variables from .env file
load_dotenv()


class BinanceData:
    def __init__(self, api_url: str, symbol: str, interval: str, file: str):
        self.api_url = api_url
        self.symbol = symbol.upper()
        self.interval = interval
        self.data_handler = DataHandler(file)

    def fetch_kline_data(self, start_time: int = None, end_time: int = None, limit: int = 500):
        endpoint = f"{self.api_url}/fapi/v1/klines"
        params = {
            "symbol": self.symbol,
            "interval": self.interval,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            print(f"Kline data fetched successfully for {self.symbol}.")
            return data
        except requests.RequestException as e:
            print(f"Error during API request: {e}")
            return []

    def process_and_save_data(self, kline_data):
        if not kline_data:
            print("No data to process.")
            return

        for kline in kline_data:
            utc_dt = pd.to_datetime(int(kline[0]), unit="ms", utc=True)
            gmt_plus_5_dt = utc_dt.tz_convert("Asia/Karachi")

            row = {
                "Datetime": gmt_plus_5_dt,
                "Open": float(kline[1]),
                "High": float(kline[2]),
                "Low": float(kline[3]),
                "Close": float(kline[4]),
                "Volume": float(kline[5]),
            }
            self.data_handler.upsert(row)

        self.data_handler.data.sort_values(
            by="Datetime", ascending=True, inplace=True)
        self.data_handler.save_data()
        print("Data sorted and saved successfully.")
