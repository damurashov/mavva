"""
Implementations for various frequent pieces of functionality, such as incomming
message logging, etc
"""

import mavva
import mavva.connectivity
import mavva.logging
import mavva.logic


class HeartbeatWatchdogMessageHandler(WatchdogMessageHandler):

    def try_accept_message(self, mavlink_message):
        return mavlink_message.get_type() == "HEARTBEAT"


class LoggingMessageHandler(mavva.connectivity.MessageHandler):
    def __init__(self, message_types):
        self._message_types = message_types

    def __call__(self, mavlink_message, mavlink_connection):
        if mavlink_message.get_type() in self._message_types:
            mavva.logging.info(f"Got message: {mavlink_message}")

