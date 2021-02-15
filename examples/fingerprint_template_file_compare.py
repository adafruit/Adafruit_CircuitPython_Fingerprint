import serial
import adafruit_fingerprint


# import board
# uart = busio.UART(board.TX, board.RX, baudrate=57600)

# If using with a computer such as Linux/RaspberryPi, Mac, Windows with USB/serial converter:
uart = serial.Serial("COM4", baudrate=57600, timeout=1)

# If using with Linux/Raspberry Pi and hardware UART:
# uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)

# If using with Linux/Raspberry Pi 3 with pi3-disable-bte
# uart = serial.Serial("/dev/ttyAMA0", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

##################################################


def sensor_reset():
    """Reset sensor"""
    print("Resetting sensor...")
    if finger.soft_reset() != adafruit_fingerprint.OK:
        print("Unable to reset sensor!")
    print("Sensor is reset.")


# pylint: disable=too-many-branches
def fingerprint_check_file():
    """Compares a new fingerprint template to an existing template stored in a file
       This is useful when templates are stored centrally (i.e. in a database)"""
    print("Waiting for finger print...")
    finger.set_led(color=3, mode=1)
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    print("Templating...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False

    print("Loading file template...", end="", flush=True)
    with open('template0.dat', 'rb') as f:
        data = f.read()
    finger.send_fpdata(list(data), "char", 2)

    i = finger.compare_templates()
    if i == adafruit_fingerprint.OK:
        finger.set_led(color=2, speed=150, mode=6)
        print("Fingerprint match template in file.")
        return True
    else:
        if i == adafruit_fingerprint.NOMATCH:
            finger.set_led(color=1, mode=2, speed=20, cycles=10)
            print("Templates do not match!")
        else:
            print("Other error!")
        return False


def enroll_save_to_file():
    """Take a 2 finger images and template it, then store it in a file"""
    finger.set_led(color=3, mode=1)
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            print("Place finger on sensor...", end="", flush=True)
        else:
            print("Place same finger again...", end="", flush=True)

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Image taken")
                break
            if i == adafruit_fingerprint.NOFINGER:
                print(".", end="", flush=True)
            elif i == adafruit_fingerprint.IMAGEFAIL:
                finger.set_led(color=1, mode=2, speed=20, cycles=10)
                print("Imaging error")
                return False
            else:
                finger.set_led(color=1, mode=2, speed=20, cycles=10)
                print("Other error")
                return False

        print("Templating...", end="", flush=True)
        i = finger.image_2_tz(fingerimg)
        if i == adafruit_fingerprint.OK:
            print("Templated")
        else:
            if i == adafruit_fingerprint.IMAGEMESS:
                finger.set_led(color=1, mode=2, speed=20, cycles=10)
                print("Image too messy")
            elif i == adafruit_fingerprint.FEATUREFAIL:
                finger.set_led(color=1, mode=2, speed=20, cycles=10)
                print("Could not identify features")
            elif i == adafruit_fingerprint.INVALIDIMAGE:
                finger.set_led(color=1, mode=2, speed=20, cycles=10)
                print("Image invalid")
            else:
                finger.set_led(color=1, mode=2, speed=20, cycles=10)
                print("Other error")
            return False

        if fingerimg == 1:
            print("Remove finger")
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()

    print("Creating model...", end="", flush=True)
    i = finger.create_model()
    if i == adafruit_fingerprint.OK:
        print("Created")
    else:
        if i == adafruit_fingerprint.ENROLLMISMATCH:
            finger.set_led(color=1, mode=2, speed=20, cycles=10)
            print("Prints did not match")
        else:
            finger.set_led(color=1, mode=2, speed=20, cycles=10)
            print("Other error")
        return False

    print("Downloading template...")
    data = finger.get_fpdata("char", 1)
    with open("template0.dat", "wb") as f:
        f.write(bytearray(data))
    finger.set_led(color=2, speed=150, mode=6)
    print("Template is saved in template0.dat file.")

    return True


# initialize LED color
led_color = 1
led_mode = 3

finger.set_led(color=3, mode=2, speed=10, cycles=10)

while True:
    # Turn on LED
    #finger.set_led(color=led_color, mode=led_mode)
    print("----------------")
    if finger.read_templates() != adafruit_fingerprint.OK:
        raise RuntimeError("Failed to read templates")
    print("Fingerprint templates: ", finger.templates)
    if finger.count_templates() != adafruit_fingerprint.OK:
        raise RuntimeError("Failed to read templates")
    print("Number of templates found: ", finger.template_count)
    if finger.set_sysparam(6, 2) != adafruit_fingerprint.OK:
        raise RuntimeError("Unable to set package size to 128!")
    if finger.read_sysparam() != adafruit_fingerprint.OK:
        raise RuntimeError("Failed to get system parameters")
    print("Package size (x128):", finger.data_packet_size)
    print("Size of template library: ", finger.library_size)
    print("e) enroll print and save to file")
    print("c) compare print to file")
    print("r) soft reset")
    print("x) quit")
    print("----------------")
    c = input("> ")

    if c == "x" or c == "q":
        print("Exiting fingerprint example program")
        # turn off LED
        finger.set_led(mode=4)
        raise SystemExit
    elif c == "e":
        enroll_save_to_file()
    elif c == "c":
        fingerprint_check_file()
    elif c == "r":
        sensor_reset()
    else:
        print("Invalid choice: Try again")