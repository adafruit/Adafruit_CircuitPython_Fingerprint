# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
"""
`fingerprint_template_folder_compare_with_file.py`
====================================================

This is an example program to demo storing fingerprint templates in a folder. It also allows
comparing a newly obtained print with one stored in the folder in previous step. This is helpful
when fingerprint templates are stored centrally (not on sensor's flash memory) and shared
between multiple sensors.

* Author(s): itsFDavid

Implementation Notes
--------------------
This program was used on others sensor of fingerprint,
generics and everything turned out to be as expected,
so this program was tested with Raspsberry Pi Zero 2"

"""
import os
import time
from PIL import Image


##################### Settings of serial port

import serial
import adafruit_fingerprint

#import board
#import busio

# import board (if you are using a micropython board)
# uart = busio.UART(board.TX, board.RX, baudrate=57600)

# If using with a computer such as Linux/RaspberryPi, Mac, Windows with USB/serial converter:
# uart = serial.Serial("COM6", baudrate=57600, timeout=1)

# If using with Linux/Raspberry Pi and hardware UART:
uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)

# If using with Linux/Raspberry Pi 3 with pi3-disable-bte
# uart = serial.Serial("/dev/ttyAMA0", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

##################################################


# Carpeta donde se almacenan las plantillas de huellas
FINGERPRINT_FOLDER = "fingerprint/"

##################################################
# Enrrols and verification functions
##################################################

def get_fingerprint():
    """get image to fingerprint sensor for search, process for a match"""
    print("Wait finger..")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    print("Process image...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    print("Searching coincidences...")
    if finger.finger_search() != adafruit_fingerprint.OK:
        return False
    return True

def get_fingerprint_detail():
    """Get image to fingerprint for process and return errors."""
    print("Wait finger..", end="")
    i = finger.get_image()
    if i == adafruit_fingerprint.OK:
        print("Image captured")
    else:
        print("Error capturing image")
        return False

    print("Process image...", end="")
    i = finger.image_2_tz(1)
    if i == adafruit_fingerprint.OK:
        print("Image processed")
    else:
        print("Error processing image")
        return False

    print("Searching coincidences...", end="")
    i = finger.finger_fast_search()
    if i == adafruit_fingerprint.OK:
        print("¡Fingerprint found!")
        return True
    return False

def enroll_finger(location):
    """Enroll a finger with the fingerprint sensor and store it in the given location specific."""
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            print("Please put your finger on sensor...", end="")
        else:
            print("Put same finger...", end="")

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Image captured")
                break
            if i == adafruit_fingerprint.NOFINGER:
                print(".", end="")
            else:
                print("Error capturing image")
                return False

        print("Process image...", end="")
        i = finger.image_2_tz(fingerimg)
        if i == adafruit_fingerprint.OK:
            print("Imagen procesed")
        else:
            print("Error processing image")
            return False

        if fingerimg == 1:
            print("Remove finger")
            time.sleep(1)
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()

    print("Creating model..", end="")
    i = finger.create_model()
    if i == adafruit_fingerprint.OK:
        print("Model created")
    else:
        print("Error creating model")
        return False

    print("Storing in that location #%d..." % location, end="")
    i = finger.store_model(location)
    if i == adafruit_fingerprint.OK:
        print("Model stored")
    else:
        print("Error storing model")
        return False

    return True

##################################################
# Save and Compare from File Functions
##################################################

def save_fingerprint_image(filename):
    """Scan your fingerprint and save the image to a file."""
    while finger.get_image():
        pass

    img = Image.new("L", (256, 288), "white")
    pixeldata = img.load()
    mask = 0b00001111
    result = finger.get_fpdata(sensorbuffer="image")

    x, y = 0, 0
    for i in range(len(result)):
        pixeldata[x, y] = (int(result[i]) >> 4) * 17
        x += 1
        pixeldata[x, y] = (int(result[i]) & mask) * 17
        if x == 255:
            x = 0
            y += 1
        else:
            x += 1

    if not img.save(filename):
        return True
    return False

def enroll_save_to_file():
    """Scan your fingerprint and save the image to a file"""
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            print("Please put your finger on sensor...", end="")
        else:
            print("Put same finger..", end="")

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Image captured")
                break
            if i == adafruit_fingerprint.NOFINGER:
                print(".", end="")
            else:
                print("Error capturing image")
                return False

        print("Process image...", end="")
        i = finger.image_2_tz(fingerimg)
        if i == adafruit_fingerprint.OK:
            print("Image processed")
        else:
            print("Error processing image")
            return False

        if fingerimg == 1:
            print("Remove finger")
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()

    print("Creating model...", end="")
    i = finger.create_model()
    if i == adafruit_fingerprint.OK:
        print("Model create")
    else:
        print("Error creating model")
        return False

    print("Storing template...")
    data = finger.get_fpdata("char", 1)
    # Guardar la plantilla con un nombre único basado en la hora actual
    filename = os.path.join(FINGERPRINT_FOLDER, f"template_{int(time.time())}.dat")
    with open(filename, "wb") as file:
        file.write(bytearray(data))
    print(f"Template saved on {filename}")

    return True

def fingerprint_check_folder():
    """Compare fingerprint with all files in the fingerprint folder."""
    print("Wait for fingerprint...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    print("Process image...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False

    print("Searching coincidences on the template's folder...", end="")
    found_match = False
    matched_filename = None

    for filename in os.listdir(FINGERPRINT_FOLDER):
        if filename.endswith(".dat"):
            file_path = os.path.join(FINGERPRINT_FOLDER, filename)
            with open(file_path, "rb") as file:
                data = file.read()
            finger.send_fpdata(list(data), "char", 2)
            i = finger.compare_templates()
            if i == adafruit_fingerprint.OK:
                matched_filename = filename
                found_match = True
                break  # Detener la búsqueda después de encontrar una coincidencia

    if found_match:
        print(f"¡Fingerprint match the template in the file {matched_filename}!")
    else:
        print("Not match found")

    return found_match

##################################################
# Main cycle of the program
##################################################

while True:
    print("----------------")
    if finger.read_templates() != adafruit_fingerprint.OK:
        raise RuntimeError("Could not be read the templates")
    print("Templates of fingerprints: ", finger.templates)
    if finger.count_templates() != adafruit_fingerprint.OK:
        raise RuntimeError("Could not be counted the templates")
    print("Number of templates found: ", finger.template_count)
    if finger.read_sysparam() != adafruit_fingerprint.OK:
        raise RuntimeError("Could not be obtained params of system.")
    print("Size of template library ", finger.library_size)
    print("e) Enrrol fingerprint")
    print("f) Search fingerprint")
    print("d) Delete fingerprint")
    print("s) Store image of fingerprint")
    print("cf) Compare template with file")
    print("esf) Enrrol and save in file")
    print("r) Reset library")
    print("q) Exit")
    print("----------------")
    c = input("> ")

    if c == "e":
        enroll_finger(get_num(finger.library_size))
    if c == "f":
        if get_fingerprint():
            print("Fingerprint detected with ID #", finger.finger_id, "and confidence", finger.confidence)
        else:
            print("Fingerprint not found")
    if c == "d":
        """"get_num is a function that returns a number from 0 to 127"""
        if finger.delete_model(get_num(finger.library_size)) == adafruit_fingerprint.OK:
            print("¡Deleted!")
        else:
            print("Error deleting")
    if c == "s":
        if save_fingerprint_image("fingerprint.png"):
            print("Image of fingerpriint")
        else:
            print("Error storing an image")
    if c == "cf":
        fingerprint_check_folder()
    if c == "esf":
        enroll_save_to_file()
    if c == "r":
        if finger.empty_library() == adafruit_fingerprint.OK:
            print("¡Empty Library!")
        else:
            print("Error emptying library")
    if c == "q":
        print("Leavinf of fingerprint program")
        raise SystemExit