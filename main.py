import database_setup
import window_monitor
import gui
import tkinter as tk
import threading


def main():
    # Setup the database
    database_setup.setup_database()

    root = tk.Tk()
    app = gui.LoggerUI(root)

    # Set up callback for updating the GUI with logs
    def log_callback(time_stamp, message):
        app.add_log(time_stamp, message)

    # Functions to control monitoring
    def toggle_monitoring():
        if window_monitor.is_paused:
            window_monitor.start_monitoring()
            app.start_pause_button.config(text="Pause")
        else:
            window_monitor.pause_monitoring()
            app.start_pause_button.config(text="Start")

    def stop_monitoring():
        app.stop_logging()
        monitor_thread.join()  # Wait for the thread to finish
        root.quit()

    def partial_time():
        app.partial()

    # Start a thread to monitor window changes
    monitor_thread = threading.Thread(target=window_monitor.monitor_window_changes, args=(log_callback,))
    monitor_thread.start()

    # Link GUI buttons to monitoring functions
    app.start_pause_button.config(command=toggle_monitoring)
    app.stop_button.config(command=stop_monitoring)
    app.partial_button.config(command=partial_time)

    root.protocol("WM_DELETE_WINDOW", stop_monitoring)

    root.mainloop()


if __name__ == "__main__":
    main()
