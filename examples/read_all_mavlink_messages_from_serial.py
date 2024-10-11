import mavva.connectivity
import mavva.logging
import mavva.snippet
import os


def main():
    serial = os.getenv("MAVVA_SERIAL", "/dev/ttyUSB0")
    baudrate = os.getenv("MAVVA_BAUDRATE", 230400)
    connection = mavva.connectivity.make_serial_mavlink_connection(serial, baudrate)
    #print(serial, baudrate)
    reader = mavva.connectivity.ThreadedMavlinkConnectionReader(connection)
    logger = mavva.snippet.LoggingMessageHandler()
    mavva.logging.set_level(mavva.logging.DEBUG)
    reader.add_message_handler(logger)
    reader.start()

    while True:
        pass


if __name__ == "__main__":
    main()
