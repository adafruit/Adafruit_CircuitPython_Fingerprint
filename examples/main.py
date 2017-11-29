from digitalio import DigitalInOut, Direction
import board
import busio
import time
from fingerprint import adafruit_fingerprint

led = DigitalInOut(board.D13)
led.direction = Direction.OUTPUT

uart = busio.UART(board.TX, board.RX, baudrate=57600)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

##################################################


def get_fingerprint():
    print("Waiting for image...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    print("Templating...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    print("Searching...")
    if finger.finger_fast_search() != adafruit_fingerprint.OK:
        return False
    return True

def get_fingerprint_detail():
    print("Getting image...", end="")
    i = finger.get_image()
    if i == adafruit_fingerprint.OK:
        print("Image taken")
    elif i == adafruit_fingerprint.NOFINGER:
        print("No finger detected")
        return False
    elif i == adafruit_fingerprint.IMAGEFAIL:
        print("Imaging error")
        return False
    else:
        print("Other error")
        return False
    
    print("Templating...", end="")
    i = finger.image_2_tz(1)
    if i == adafruit_fingerprint.OK:
        print("Templated")
    elif i == adafruit_fingerprint.IMAGEMESS:
        print("Image too messy")
        return False
    elif i == adafruit_fingerprint.FEATUREFAIL:
        print("Could not identify features")
        return False
    elif i == adafruit_fingerprint.INVALIDIMAGE:
        print("Image invalid")
        return False
    else:
        print("Other error")
        return False
    
    print("Searching...", end="")
    i = finger.finger_fast_search()
    if i == adafruit_fingerprint.OK:        
        print("Found fingerprint!")
        return True
    elif i == adafruit_fingerprint.NOTFOUND:
        print("No match found")
        return False
    else:
        print("Other error")
        return False

    return False    # we shouldnt get here but might as well fail


def enroll_finger(id):
    for fingerimg in range(1,3):
        if fingerimg == 1:
            print("Place finger on sensor...", end="")
        else:
            print("Place same finger again...", end="")

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Image taken")
                break
            elif i == adafruit_fingerprint.NOFINGER:
                print(".", end="")
            elif i == adafruit_fingerprint.IMAGEFAIL:
                print("Imaging error")
                return False
            else:
                print("Other error")
                return False
            
        print("Templating...", end="")
        i = finger.image_2_tz(fingerimg)
        if i == adafruit_fingerprint.OK:
            print("Templated")
        elif i == adafruit_fingerprint.IMAGEMESS:
            print("Image too messy")
            return False
        elif i == adafruit_fingerprint.FEATUREFAIL:
            print("Could not identify features")
            return False
        elif i == adafruit_fingerprint.INVALIDIMAGE:
            print("Image invalid")
            return False
        else:
            print("Other error")
            return False

        if fingerimg == 1:
            print("Remove finger")
            time.sleep(1)
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()
    
    print("Creating model...", end="")
    i = finger.create_model()
    if i == adafruit_fingerprint.OK:
        print("Created")
    elif i == adafruit_fingerprint.ENROLLMISMATCH:
        print("Prints did not match")
        return False
    else:
        print("Other error")
        return False

    print("Storing model #%d..." % id, end="")
    i = finger.store_model(id)
    if i == adafruit_fingerprint.OK:
        print("Stored")
    elif i == adafruit_fingerprint.BADLOCATION:
        print("Bad storage location")
        return False
    elif i == adafruit_fingerprint.FLASHERR:
        print("Flash storage error")
        return False
    else:
        print("Other error")
        return False

    return True


##################################################

def get_num():
    id = 0
    while (id > 127) or (id < 1):
        try:
            id = int(input("Enter ID # from 1-127: "))
        except ValueError:
            pass
    return id


while True:
    print("----------------")
    if finger.read_templates() != adafruit_fingerprint.OK:
        raise RuntimeError('Failed to read templates')
    print("Fingerprint templates:", finger.templates)
    print("e) enroll print")
    print("f) find print")
    print("d) delete print")
    print("----------------")
    c = input("> ")
    
    if c == 'e':
        enroll_finger(get_num())
    if c == 'f':
        if get_fingerprint():
            print("Detected #", finger.finger_id, "with confidence", finger.confidence)
        else:
            print("Finger not found")
    if c == 'd':
        if finger.delete_model(get_num()) == adafruit_fingerprint.OK:
            print("Deleted!")
        else:
            print("Failed to delete")
