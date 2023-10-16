import time


def format_time(elapsed_time):
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    time_str = f"{hours}h {minutes}m {seconds}s"
    return time_str


class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class"""


class Timer:
    def __init__(self):
        self._start_time = None
        self._pause_timer = None
        self.tot_paused_time = 0

    def start(self):
        """Start a new timer"""
        if self._start_time is not None:
            raise TimerError(f"Timer is running. Use .stop() to stop it")

        self._start_time = time.perf_counter()

    def stop(self):
        """Stop the timer, and report the elapsed time"""
        if self._start_time is None:
            raise TimerError(f"Timer is not running. Use .start() to start it")

        elapsed_time = time.perf_counter() - self._start_time
        self._start_time = None
        elapsed_time -= self.tot_paused_time
        self.tot_paused_time = 0
        return int(elapsed_time)

    def partial(self):
        if self._start_time is None:
            raise TimerError(f"Timer is not running. Use .start() to start it")

        elapsed_time = time.perf_counter() - self._start_time - self.tot_paused_time
        return int(elapsed_time)

    def pause(self):
        """pause the timer"""

        if self._start_time is None:
            raise TimerError(f"Timer is not running. Use .start() to start it")

        if self._pause_timer is not None:
            raise TimerError(f"pause timer is running. Use .resume() to stop it")

        self._pause_timer = time.perf_counter()

    def resume(self):
        """resume the pause timer"""
        if self._pause_timer is None:
            raise TimerError(f"Pause timer is not running. Use .pause() to start it")

        paused_time = time.perf_counter() - self._pause_timer
        self._pause_timer = None
        self.tot_paused_time += int(paused_time)

    def is_paused(self):
        if self._pause_timer is None:
            return 0
        else:
            return 1

