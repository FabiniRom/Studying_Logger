import time
import pygetwindow as gw
import sqlite3
from datetime import datetime
import pytz
from pycaw.pycaw import AudioUtilities
import re

from timer import Timer, format_time

last_title = None
keep_monitoring = True
is_paused = False
t = Timer()


def log_window_change(title, callback=None):
    conn = sqlite3.connect('window_log.db')
    cursor = conn.cursor()

    current_time = get_current_time()  # Get the current time adjusted to GMT+2

    cursor.execute('INSERT INTO window_changes (timestamp,time_length, window_title) VALUES (?, ?, ?)',
                   (current_time, "0h 0m 0s", title))

    conn.commit()
    conn.close()

    # Callback to update the GUI
    if callback:
        callback(reformat_to_hour_minute(current_time), title, "add")


def log_elapsed_time(elapsed_time, callback=None):
    conn = sqlite3.connect('window_log.db')
    cursor = conn.cursor()
    formatted_elapsed_time = format_time(elapsed_time)
    if elapsed_time < 5:
        cursor.execute("SELECT timestamp, window_title FROM window_changes ORDER BY id DESC LIMIT 1")

        timestamp, window_title = cursor.fetchone()

        cursor.execute("DELETE FROM window_changes WHERE timestamp = ? AND window_title = ?", (timestamp, window_title))

        if callback:
            callback(reformat_to_hour_minute(timestamp), window_title, "remove")
    else:
        cursor.execute('UPDATE window_changes SET time_length = ? WHERE id = (SELECT MAX(id) FROM window_changes)',
                       (formatted_elapsed_time,))

    conn.commit()
    conn.close()


def log_partial_time(elapsed_time, callback=None):
    conn = sqlite3.connect('window_log.db')
    cursor = conn.cursor()
    formatted_elapsed_time = format_time(elapsed_time)

    cursor.execute('UPDATE window_changes SET time_length = ? WHERE id = (SELECT MAX(id) FROM window_changes)',
                   (formatted_elapsed_time,))

    conn.commit()
    conn.close()


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


exceptions = ["Task Switching"]


def format_edge_title(title):
    # First, remove the trailing information starting from " - Personal - Microsoft"
    title = re.sub(r" - Personal - Microsoft.*", "", title)
    # Next, remove the "and x more page(s)" part if present
    title = re.sub(r" and \d+ more pages?", "", title)
    return title


def monitor_window_changes(callback=None):
    global last_title, keep_monitoring, is_paused, t
    while keep_monitoring:
        if not is_paused:
            try:
                if t.is_paused():
                    t.resume()
                current_title = gw.getActiveWindow().title
                # check certain conditions here.
                # change title here.

                if current_title in exceptions:
                    if not t.is_paused():
                        t.pause()
                    continue
                else:
                    if t.is_paused():
                        t.resume()

                if current_title != last_title and current_title != "":
                    formatted_title = format_edge_title(current_title)

                    if last_title is not None:
                        elapsed_time = t.stop()
                        log_elapsed_time(elapsed_time, callback)

                    log_window_change(formatted_title, callback)

                    t.start()

                    last_title = current_title

            except Exception as e:
                # This can happen if there's no active window
                print(f"Error: {e}")
        elif not t.is_paused():
            t.pause()

        time.sleep(0.1)


known_video_patterns = ['YouTube', 'VLC', 'Netflix', 'Prime Video', 'Hulu', 'Webex']


def is_likely_playing_video(window_title):
    for pattern in known_video_patterns:
        if pattern in window_title:
            return True
    return False


def is_audio_playing():
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        interface = session.SimpleAudioVolume
        if interface.GetMute() == 0 and interface.GetMasterVolume() > 0:
            return True
    return False


def start_monitoring():
    if t.is_paused():
        t.resume()
    global is_paused
    is_paused = False


def pause_monitoring():
    global is_paused
    is_paused = True
    t.pause()
    log_partial_time(t.partial())


def partial_display():
    global is_paused
    is_paused = True
    if not t.is_paused():
        t.pause()
    log_partial_time(t.partial())


def stop_monitoring():
    global keep_monitoring
    keep_monitoring = False
