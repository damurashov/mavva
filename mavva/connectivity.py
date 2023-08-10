import madsy.log
import pymavlink.dialects.v20
import pymavlink.mavutil
import threading
import time
import unittest


_INTERACTIVE = False
_BAUDRATE = 57600
_SERIAL = "/dev/ttyUSB0"

log = madsy.log.Log(madsy.log.DEBUG, module="connectivity")


def make_serial_mavlink_connection(device=_SERIAL, baud=_BAUDRATE):
    connection = pymavlink.mavutil.mavlink_connection(device=device, baud=baud)

    return connection


def _parse_arguments():
    import argparse

    global _INTERACTIVE
    global _BAUDRATE
    global _SERIAL

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--interactive", "-i", action="store_true")
    parser.add_argument("--serial", "-s", default="/dev/ttyUSB0")
    parser.add_argument("--baudrate", "-b" ,default=115200)
    arguments = parser.parse_args()
    log.debug(arguments)

    # apply arguments
    _BAUDRATE = arguments.baudrate
    _INTERACTIVE = arguments.interactive
    _SERIAL = arguments.serial
    log.debug("_INTERACTIVE", _INTERACTIVE)


class ThreadedMavlinkConnectionReader(threading.Thread):

    def __init__(self, mavlink_connection=None):
        threading.Thread.__init__(self)
        self._mavlink_connection = mavlink_connection
        self._message_handlers = dict()
        self._lock = threading.Lock()

        if mavlink_connection is None:
            self._mavlink_connection = make_serial_mavlink_connection()

        threading.Thread.__init__(self, target=self.run_message_handling,
            daemon=True)

    def add_message_handler(self, message_handler_callable, key=None):
        """
        - `key` must be hashable, or None. if `key` is `None`,
          `hash(message_handler_callable)` will be used;
        - `message_handler_callable` must have signature `def handler(message_type) -> bool`
        """
        if key is None:
            key = message_handler_callable

        self._lock.acquire()
        self._message_handlers[hash(key)] = message_handler_callable
        self._lock.release()

    def remove_message_handler(key):
        self._lock.acquire()
        handler = self._message_handlers.pop(hash(key))
        self._lock.release()

        return handler

    def run_message_handling(self):
        log.info(ThreadedMavlinkConnectionReader.__name__, ":", "Started message handling thread")

        while True:
            received_message = self._mavlink_connection.recv_msg()
            self._lock.acquire()

            if received_message is not None:
                for message_handler in self._message_handlers.values():
                    message_handler(received_message, mavlink_connection)

            self._lock.release()

    def get_cached_message(self, message_type):
        """
        May throw `KeyError`
        """
        return self._mavlink_connection.messages.pop(message_type)


class ThreadedMavlinkConnectionWriter(threading.Thread):

    def __init__(self, mavlink_connection):
        self._senders = dict()
        self._mavlink_connection = mavlink_connection
        self._lock = threading.Lock()
        threading.Thread.__init__(self, target=self.run_mavlink_sending,
            daemon=True)

    def add_sender(self, sender, key):
        """
        `key` must be hashable
        `sender(mavlink_connection)` sends MAVLink message over provided
        MAVLink connection.
        """
        self._lock.acquire()
        self._senders[hash(key)] = sender
        self._lock.release()

    def remove_sender(self, key):
        self._lock.acquire()
        sender = self._senders.pop(hash(key))
        self._lock.release()

        return sender

    def run_mavlink_sending(self):
        while True:
            self._lock.acquire()

            for sender in self._senders.values():
                sender(self._mavlink_connection)

            self._lock.release()


class PolledSenderDecorator:
    """ Decorator """

    def _try_update_ready(self):
        raise NotImplemented

    def __call__(self, sender, *args, **kwargs):
        def inner_function(*args, **kwargs):
            if self._try_update_ready():
                return sender(*args, **kwargs)

        return inner_function


class TimedPolledSenderDecorator(PolledSender):
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
        import madsy.log

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
        self._log = madsy.log.Log(level=madsy.log.INFO,
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
                self._log.warning("Connection lost")

            time.sleep(self._timeout)

    def try_accept_message(self, mavlink_message):
        """
        Checks whether or not a message will be accepted
        """
        return True

    def on_mavlink_message(self, mavlink_message):
        """
        On a new MAVLink message, it updates the last timestamp
        """
        if self.try_accept_message(mavlink_message):
            self._update_timeout()

            if self._is_notified():
                self._log.info("Connection restored")
                self._set_notified(False)

    def __call__(self, mavlink_message):
        self.on_mavlink_message(mavlink_message)


class HeartbeatWatchdogMessageHandler(WatchdogMessageHandler):

    def try_accept_message(self, mavlink_message):
        return mavlink_message.get_type() == "HEARTBEAT"


class ConnectivityTest(unittest.TestCase):
    def test_read_all(self):
        if not _INTERACTIVE:
            log.info('skipping interactive test')

            return

        def handler(message):
            log.debug(message)

        log.info("Type anything to stop")

        # Create connection
        mavlink_connection = make_serial_mavlink_connection(_SERIAL, _BAUDRATE)

        # Initialize and run connection reader
        reader = ThreadedMavlinkConnectionReader(mavlink_connection)
        reader.add_message_handler(handler, "handler")
        reader.start()

        while True:
            i = input()
            i = i.strip()

            if len(i):
                break


def main():
    import sys
    _parse_arguments()
    sys.argv[1:] = []  # `unittest.main()` reads input arguments too
    unittest.main()


if __name__ == "__main__":
    main()
