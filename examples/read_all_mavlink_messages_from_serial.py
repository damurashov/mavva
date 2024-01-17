import mavva.connectivity
import mavva.snippet
import os


def main():
    serial = os.getenv("MAVVA_SERIAL", "/dev/ttyUSB0")
    baudrate = os.getenv("MAVVA_BAUDRATE", 115200)
    connection = mavva.connectivity.make_serial_mavlink_connection(serial, baudrate)
    print(serial, baudrate)
    reader = mavva.connectivity.ThreadedMavlinkConnectionReader(connection)
    logger = mavva.snippet.LoggingMessageHandler()
    reader.add_message_handler(logger)
    reader.start()

    while True:
        pass


if __name__ == "__main__":
    main()
