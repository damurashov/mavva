"""
Implementations for various frequent pieces of functionality, such as incomming
message logging, etc
"""

import mavva
import mavva.connectivity
import mavva.logging
import mavva.logic


class HeartbeatWatchdogMessageHandler(mavva.logic.WatchdogMessageHandler):

    def try_accept_message(self, mavlink_message):
        return mavlink_message.get_type() == "HEARTBEAT"


class LoggingMessageHandler(mavva.connectivity.MessageHandler):
    def __init__(self, message_types=None):
        self._message_types = message_types

    def _is_mavlink_message_accepted(self, mavlink_message):
        if self._message_types is None:
            return True
        else:
            return mavlink_message.get_type() in self._message_types

    def __call__(self, mavlink_message, mavlink_connection):

        if self._is_mavlink_message_accepted(mavlink_message):
            mavva.logging.info(f"Got message: {mavlink_message}")

