import mavva
import mavva.logging
import threading


class WatchdogMessageHandler(threading.Thread):
    """
    Will call a handler, if there is no MAVLink messages for some amount if
    time. Compatible w/ `ThreadedMavlinkConnectionReader`
    """

    def __init__(self, no_connection_timeout_seconds, on_timeout):
        """
        `no_connection_timeout_seconds` - timeout to wait before issuing a
         callback invocation
        `on_timeout` - a callback having signature `function()`
        """

        self._timeout = no_connection_timeout_seconds
        self._update_timeout()
        self._notify_on_timeout = on_timeout
        threading.Thread.__init__(self, target=self.run_poll_is_timed_out,
            daemon=True)
        self._notified = False  # Whether the subscriber has been notified

        # Initialize logging
        import pathlib
        module_name = pathlib.Path(__file__).stem + '.' \
            + self.__class__.__name__
        mavva.logging = madsy.log.Log(level=madsy.log.INFO,
            module=module_name)

    def _update_timeout(self):
        import time

        self._last_time = time.time()

    def _is_timed_out(self):
        import time

        return time.time() - self._last_time > self._timeout

    def _is_notified(self):
        return self._notified

    def _set_notified(self, notified):
        self._notified = notified

    def run_poll_is_timed_out(self):
        """
        Continuously checks for whether the timeout has been exceeded
        """
        while True:
            if self._is_timed_out() and not self._is_notified():
                self._notify_on_timeout()
                self._set_notified(True)
                mavva.logging.warning("Connection lost")

            time.sleep(self._timeout)

    def try_accept_message(self, mavlink_message):
        """
        Checks whether or not a message will be accepted
        """
        return True

    def on_mavlink_message(self, mavlink_message, mavlink_connection):
        """
        On a new MAVLink message, it updates the last timestamp
        """
        if self.try_accept_message(mavlink_message):
            self._update_timeout()

            if self._is_notified():
                mavva.logging.info("Connection restored")
                self._set_notified(False)

    def __call__(self, mavlink_message, mavlink_connection):
        self.on_mavlink_message(mavlink_message, mavlink_connection)


class PolledSenderDecorator:
    """ Decorator """

    def _try_update_ready(self):
        raise NotImplemented

    def __call__(self, sender, *args, **kwargs):
        def inner_function(*args, **kwargs):
            if self._try_update_ready():
                return sender(*args, **kwargs)

        return inner_function


class TimedPolledSenderDecorator(PolledSenderDecorator):
    """ Decorator """

    def __init__(self, timeout_seconds):
        import time

        self._last_time = time.time()
        self._timeout_seconds = float(timeout_seconds)

    def _try_update_ready(self):
        import time
        now = time.time()

        if now - self._last_time > self._timeout_seconds:
            self._last_time = now

            return True
        else:
            return False
