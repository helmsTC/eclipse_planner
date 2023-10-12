import adafruit_gps
import time
import serial

class GPS:

    def __init__(self):
        uart = serial.Serial("/dev/tty.usbserial-10", baudrate=9600, timeout=10)
        self.gps = adafruit_gps.GPS(uart, debug=False)
        self.gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
        self.gps.send_command(b"PMTK220,1000")

    def get_location(self):
        last_print = time.monotonic()
        while True:
            self.gps.update()
            current = time.monotonic()
            if current - last_print >= 1.0:
                last_print = current
                if not self.gps.has_fix:
                    print("Waiting for fix...")
                    continue
                else:
                    print("Location Identified.")
                    print("lat: ", self.gps.latitude, "lon:", self.gps.longitude)
                    break
        return (self.gps.latitude, self.gps.longitude)
