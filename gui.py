import math
import re
from datetime import datetime, timedelta
import sqlite3
import tkinter as tk
from tkinter import ttk, scrolledtext

import window_monitor


def compute_and_populate_time_length():
    conn = sqlite3.connect('window_log.db')
    cursor = conn.cursor()

    # Fetch all entries from the database where time_length is NULL
    cursor.execute('SELECT id, timestamp FROM window_changes WHERE time_length IS NULL ORDER BY id')
    entries = cursor.fetchall()

    # Loop through the entries that have an empty time_length column
    for i in range(len(entries)):
        current_id, current_timestamp = entries[i]

        # If it's the last entry, compute time difference against the current time
        if i == len(entries) - 1:
            next_time = datetime.now()
        else:
            _, next_timestamp = entries[i + 1]
            next_time = datetime.strptime(next_timestamp, "%Y-%m-%d %H:%M:%S")

        # Calculate the time difference
        current_time = datetime.strptime(current_timestamp, "%Y-%m-%d %H:%M:%S")
        time_difference = next_time - current_time

        # Extract hours, minutes, and seconds directly from the timedelta object
        hours, remainder = divmod(time_difference.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{hours}h {minutes}m {seconds}s"

        # Update the database with the formatted time difference for the current entry
        cursor.execute('UPDATE window_changes SET time_length = ? WHERE id = ?', (time_str, current_id))

    conn.commit()
    conn.close()


class LoggerUI:

    def __init__(self, root):
        self.partial_window = None
        self.root = root
        self.root.title('Event Logger')

        # Configure the root weights (important for resizing)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Top section for buttons
        self.top_frame = ttk.Frame(root)
        self.top_frame.grid(row=0, column=0, pady=20, sticky="ew")

        # Configure the top frame weights
        self.top_frame.grid_columnconfigure(0, weight=1)
        self.top_frame.grid_columnconfigure(1, weight=1)

        # Start/Pause button
        self.is_paused = True
        self.start_pause_button = ttk.Button(self.top_frame, text="Start", command=self.toggle_start_pause)
        self.start_pause_button.grid(row=0, column=0, padx=20, sticky="ew")

        # Stop button
        self.stop_button = ttk.Button(self.top_frame, text="Stop", command=self.stop_logging)
        self.stop_button.grid(row=0, column=1, padx=20, sticky="ew")

        # display partial button
        self.partial_button = ttk.Button(self.top_frame, text="Partial", command=self.partial)
        self.partial_button.grid(row=0, column=2, padx=20, sticky="ew")

        # Bottom section for event logs
        self.tree = ttk.Treeview(root, columns=('Time', 'Event'), show='headings')
        self.tree.heading('Time', text='Time')
        self.tree.heading('Event', text='Event')
        self.tree.grid(row=1, column=0, pady=20, sticky="nsew")

        # Adding a scrollbar
        self.scrollbar = ttk.Scrollbar(root, orient='vertical', command=self.tree.yview)
        self.scrollbar.grid(row=1, column=1, sticky='ns')
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        # Configure the grid weights for the Treeview
        self.root.grid_rowconfigure(1, weight=5)
        self.root.grid_columnconfigure(0, weight=1)


    def on_closing(self):
        # Destroy any child windows or perform any cleanup here
        # ...
        self.stop_logging()

        # Finally, destroy the main window
        self.root.destroy()


    def toggle_start_pause(self):
            if self.is_paused:
                self.start_pause_button.config(text="Pause")
                # Call the function to start logging here
            else:
                self.start_pause_button.config(text="Start")
                # Call the function to pause logging here
            self.is_paused = not self.is_paused

    def stop_logging(self):
        # Call the function to stop logging here
        window_monitor.stop_monitoring()

    def partial(self):
        window_monitor.pause_monitoring()

        # Display the cumulative time
        self.display_cumulative_time()

    def display_cumulative_time(self):
        # Step 1: Create a new window
        self.partial_window = tk.Toplevel(self.root)
        self.partial_window.title("Cumulative Time Spent Today")

        # Step 2: Call compute_and_populate_time_length method
        compute_and_populate_time_length()

        # Step 3 & 4: Loop over all entries and accumulate the time length for identical window titles
        conn = sqlite3.connect('window_log.db')
        cursor = conn.cursor()
        cursor.execute("SELECT window_title, time_length FROM window_changes WHERE date(timestamp) = date('now')")
        entries = cursor.fetchall()

        time_accumulator = {}
        for window_title, time_str in entries:
            match = re.match(r'(\d+)h (\d+)m (\d+)s', time_str)
            if match:
                hours, minutes, seconds = map(int, match.groups())
            else:
                hours, minutes, seconds = 0, 0, 0
            total_seconds = hours * 3600 + minutes * 60 + seconds

            if window_title in time_accumulator:
                time_accumulator[window_title] += total_seconds
            else:
                time_accumulator[window_title] = total_seconds

        # Convert accumulated seconds back to "Xh Ym Zs" format
        formatted_times = {}
        for window, seconds in time_accumulator.items():
            hours, remainder = divmod(seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            formatted_times[window] = f"{hours}h {minutes}m {seconds}s"

        # Step 5: Display the entries from today with cumulative time, sorted in descending order of time

        # Create a Treeview to display the data
        tree = ttk.Treeview(self.partial_window, columns=("Window", "Cumulative Time"), show="headings")
        tree.heading("Window", text="Window")
        tree.heading("Cumulative Time", text="Cumulative Time")
        tree.pack(fill="both", expand=True)

        # Populate the Treeview with data sorted by descending time
        for window, time in sorted(formatted_times.items(), key=lambda x: x[1], reverse=True):
            tree.insert("", "end", values=(window, time))

        conn.close()

        self.partial_window.protocol("WM_DELETE_WINDOW", self.resume_logging_and_close_window)

    def resume_logging_and_close_window(self):
        window_monitor.start_monitoring()
        self.partial_window.destroy()

    def add_log(self, time_stamp, message):
        self.tree.insert('', '0', values=(time_stamp, message))
