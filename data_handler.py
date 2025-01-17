# data_handler.py
import os
import pandas as pd


class DataHandler:
    _instances = {}

    def __new__(cls, filepath):
        """
        Create a single instance of DataHandler per filepath.
        """
        if filepath not in cls._instances:
            instance = super(DataHandler, cls).__new__(cls)
            cls._instances[filepath] = instance
        return cls._instances[filepath]

    def __init__(self, filepath):
        """
        Initialize the DataHandler class.

        :param filepath: The path to the CSV file.
        """
        if not hasattr(self, "initialized"):  # Prevent reinitialization
            self.filepath = filepath
            self.data = None

            # Ensure the directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Ensure the file exists and initialize it if necessary
            self._ensure_file_exists()

            # Load existing data or initialize an empty DataFrame
            self.load_data()
            self.initialized = True

    def _ensure_file_exists(self):
        """
        Ensure the CSV file exists, creating it with headers if it doesn't.
        """
        if not os.path.exists(self.filepath):
            columns = ["Datetime", "Open", "Close", "High", "Low", "Volume"]
            pd.DataFrame(columns=columns).to_csv(self.filepath, index=False)

    def load_data(self):
        """
        Load data from the CSV file into memory, indexed by Datetime.
        """
        if os.path.exists(self.filepath):
            self.data = pd.read_csv(self.filepath, parse_dates=[
                                    "Datetime"], index_col="Datetime")
        else:
            # This should never happen due to _ensure_file_exists
            self.data = pd.DataFrame(
                columns=["Datetime", "Open", "Close", "High", "Low", "Volume"])

    def get_data(self):
        return self.data

    def save_data(self):
        """
        Save the in-memory data to the CSV file.
        """
        self.data.to_csv(self.filepath)

    def upsert(self, row):
        """
        Update or insert a row of data into the DataFrame.

        :param row: A dictionary representing a single row of data.
        :return: A string indicating whether the record was updated or created ("updated" or "created").
        """
        # Convert Datetime to match DataFrame index
        datetime_index = pd.to_datetime(row["Datetime"])

        if datetime_index in self.data.index:
            # Update the existing record
            self.data.loc[datetime_index] = row
            return "updated"
        else:
            # Append new record
            self.data = pd.concat([self.data, pd.DataFrame(
                [row]).set_index("Datetime")], sort=False)
            return "created"
