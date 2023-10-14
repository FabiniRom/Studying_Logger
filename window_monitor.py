import time
import pygetwindow as gw
import sqlite3
from datetime import datetime
import pytz

last_title = None
keep_monitoring = True
is_paused = False


def log_window_change(title, callback=None):
    conn = sqlite3.connect('window_log.db')
    cursor = conn.cursor()
    current_time = get_current_time()  # Get the current time adjusted to GMT+2

    cursor.execute('INSERT INTO window_changes (timestamp, window_title) VALUES (?, ?)', (current_time, title))
    conn.commit()
    conn.close()

    # Callback to update the GUI
    if callback:
        callback(reformat_to_hour_minute(current_time), title)


def get_time_difference(current_time, last_timestamp):
    if last_timestamp:
        last_time = datetime.strptime(last_timestamp[1], "%Y-%m-%d %H:%M:%S")

        # Compute the time difference
        time_difference = current_time - last_time

        # Return the difference in minutes (and potentially hours if it's more than an hour)
        minutes = time_difference.total_seconds() / 60
        hours, remainder_minutes = divmod(minutes, 60)

        return f"{hours:02d}:{minutes:02d}"

    else:
        return None


def reformat_to_hour_minute(input_str):
    try:
        # Parse the input string
        dt = datetime.strptime(input_str, '%Y-%m-%d %H:%M:%S')
        # Return the formatted string
        return dt.strftime('%H:%M:%S')
    except ValueError:
        # Handle incorrect format or any other parsing issues
        return "Invalid Format"


def get_current_time():
    """Returns the current time adjusted to GMT+2."""
    local_tz = pytz.timezone('Etc/GMT-2')
    return datetime.now(local_tz).strftime('%Y-%m-%d %H:%M:%S')


def monitor_window_changes(callback=None):
    global last_title, keep_monitoring, is_paused

    while keep_monitoring:
        if not is_paused:
            try:
                current_title = gw.getActiveWindow().title
                if current_title != last_title:
                    log_window_change(current_title, callback)
                    last_title = current_title
            except Exception as e:
                # This can happen if there's no active window
                print(f"Error: {e}")

        # Sleep for a short duration before checking again
        time.sleep(0.5)


def start_monitoring():
    global is_paused
    is_paused = False


def pause_monitoring():
    global is_paused
    is_paused = True


def stop_monitoring():
    global keep_monitoring
    keep_monitoring = False
