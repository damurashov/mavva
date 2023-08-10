import mavva
import mavva.logging
import pymavlink.dialects.v20
import pymavlink.mavutil
import threading
import time
import unittest


_INTERACTIVE = False
_BAUDRATE = 57600
_SERIAL = "/dev/ttyUSB0"


def make_serial_mavlink_connection(device=_SERIAL, baud=_BAUDRATE):
    connection = pymavlink.mavutil.mavlink_connection(device=device, baud=baud)

    return connection


def make_udp_mavlink_connection_as_server(ip="localhost", port=8001):
    """
    Listens for incoming MAVLink packages on specified port
    """
    connection = pymavlink.mavutil.mavlink_connection(f"udpin:{ip}:{port}")

    return connection


def make_udp_mavlink_connection_as_client(ip="192.168.4.1", port=8001):
    """
    Connects to a specified remote port
    """
    connection = pymavlink.mavutil.mavlink_connection(f"udpout:{ip}:{port}")

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
    mavva.logging.debug(arguments)

    # apply arguments
    _BAUDRATE = arguments.baudrate
    _INTERACTIVE = arguments.interactive
    _SERIAL = arguments.serial
    mavva.logging.debug("_INTERACTIVE", _INTERACTIVE)


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
        mavva.logging.info("Started message handling thread")

        while True:
            received_message = self._mavlink_connection.recv_msg()
            self._lock.acquire()

            if received_message is not None:
                for message_handler in self._message_handlers.values():
                    message_handler(received_message, self._mavlink_connection)

            self._lock.release()

    def get_cached_message(self, message_type):
        """
        May throw `KeyError`
        """
        return self._mavlink_connection.messages.pop(message_type)


class MessageHandler:
    """
    Defines api for entities stored in ThreadedMavlinkConnectionReader
    """

    def __call__(self, received_message, mavlink_connection):
        pass


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


class Sender:
    """
    Defines API for entities stored in ThreadedMavlinkConnectionWriter
    """

    def __call__(self, mavlink_connection):
        pass


class ConnectivityTest(unittest.TestCase):
    def test_read_all(self):
        if not _INTERACTIVE:
            mavva.logging.info('skipping interactive test')

            return

        def handler(message):
            mavva.logging.debug(message)

        mavva.logging.info("Type anything to stop")

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
