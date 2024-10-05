# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
"""
`fingerprint_template_folder_compare_with_file.py`
====================================================

This is an example program to demo storing fingerprint templates in a folder. It also allows
comparing a newly obtained print with one stored in the folder in the previous step. This is helpful
when fingerprint templates are stored centrally (not on sensor's flash memory) and shared
between multiple sensors.

* Author(s): itsFDavid

Implementation Notes
--------------------
This program was used on other fingerprint sensors,
and everything worked as expected, including testing with Raspberry Pi Zero 2.
"""

import os
import time
from PIL import Image
import serial
import adafruit_fingerprint

# If using with a computer such as Linux/RaspberryPi, Mac, Windows with USB/serial converter:
# uart = serial.Serial("COM6", baudrate=57600, timeout=1)

# If using with Linux/Raspberry Pi and hardware UART:
uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

# Folder where fingerprint templates are stored
FINGERPRINT_FOLDER = "fingerprint/"

# Enroll and verification functions
def get_num(max_num):
    """
    Prompts the user to enter a valid template number.
    Ensures that the number is within the available template range.
    """
    while True:
        try:
            num = int(input(f"Enter a template number (0-{max_num}): "))
            if 0 <= num <= max_num:
                return num
            print(f"Please enter a number between 0 and {max_num}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")


def get_fingerprint():
    """Get an image from the fingerprint sensor for search, process for a match."""
    print("Waiting for finger...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass

    print("Processing image...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False

    print("Searching for matches...")
    return finger.finger_search() == adafruit_fingerprint.OK


def enroll_finger(location):
    """Enroll a fingerprint and store it in the specified location."""
    for fingerimg in range(1, 3):
        action = "Place finger on sensor" if fingerimg == 1 else "Same finger again"
        print(action, end="")

        while True:
            if finger.get_image() == adafruit_fingerprint.OK:
                print("Image captured")
                break
            print(".", end="")

        print("Processing image...", end="")
        if finger.image_2_tz(fingerimg) != adafruit_fingerprint.OK:
            print("Error processing image")
            return False

        if fingerimg == 1:
            print("Remove finger")
            time.sleep(1)
            while finger.get_image() != adafruit_fingerprint.NOFINGER:
                pass

    print("Creating model...", end="")
    if finger.create_model() != adafruit_fingerprint.OK:
        print("Error creating model")
        return False

    print(f"Storing model in location #{location}...", end="")
    if finger.store_model(location) != adafruit_fingerprint.OK:
        print("Error storing model")
        return False

    print("Model stored")
    return True


def save_fingerprint_image(filename):
    """Capture a fingerprint and save the image to a file."""
    while finger.get_image() != adafruit_fingerprint.OK:
        pass

    img = Image.new("L", (256, 288), "white")
    pixeldata = img.load()
    mask = 0b00001111
    result = finger.get_fpdata(sensorbuffer="image")

    x, y = 0, 0
    for i, value in enumerate(result):
        pixeldata[x, y] = (int(value) >> 4) * 17
        x += 1
        pixeldata[x, y] = (int(value) & mask) * 17
        if x == 255:
            x = 0
            y += 1
        else:
            x += 1

    img.save(filename)
    return True


def enroll_save_to_file():
    """Capture a fingerprint, create a model, and save it to a file."""
    for fingerimg in range(1, 3):
        action = "Place finger on sensor" if fingerimg == 1 else "Same finger again"
        print(action, end="")

        while True:
            if finger.get_image() == adafruit_fingerprint.OK:
                print("Image captured")
                break
            print(".", end="")

        print("Processing image...", end="")
        if finger.image_2_tz(fingerimg) != adafruit_fingerprint.OK:
            print("Error processing image")
            return False

        if fingerimg == 1:
            print("Remove finger")
            while finger.get_image() != adafruit_fingerprint.NOFINGER:
                pass

    print("Creating model...", end="")
    if finger.create_model() != adafruit_fingerprint.OK:
        print("Error creating model")
        return False

    print("Storing template...")
    data = finger.get_fpdata("char", 1)
    filename = os.path.join(FINGERPRINT_FOLDER, f"template_{int(time.time())}.dat")
    with open(filename, "wb") as file:
        file.write(bytearray(data))
    print(f"Template saved to {filename}")

    return True


def fingerprint_check_folder():
    """Compare a fingerprint with all files in the fingerprint folder."""
    print("Waiting for fingerprint...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass

    print("Processing image...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False

    print("Searching for matches in the template folder...", end="")
    found_match = False
    matched_filename = None

    for filename in os.listdir(FINGERPRINT_FOLDER):
        if filename.endswith(".dat"):
            file_path = os.path.join(FINGERPRINT_FOLDER, filename)
            with open(file_path, "rb") as file:
                data = file.read()
            finger.send_fpdata(list(data), "char", 2)
            if finger.compare_templates() == adafruit_fingerprint.OK:
                matched_filename = filename
                found_match = True
                break  # Stop searching after finding a match

    if found_match:
        print(f"Fingerprint matches the template in the file {matched_filename}!")
    else:
        print("No match found")

    return found_match


# Main program loop
while True:
    print("----------------")
    if finger.read_templates() != adafruit_fingerprint.OK:
        raise RuntimeError("Could not read templates")
    print("Stored fingerprint templates: ", finger.templates)

    if finger.count_templates() != adafruit_fingerprint.OK:
        raise RuntimeError("Could not count templates")
    print("Number of templates found: ", finger.template_count)

    if finger.read_sysparam() != adafruit_fingerprint.OK:
        raise RuntimeError("Could not retrieve system parameters.")
    print("Template library size: ", finger.library_size)

    print("e) Enroll fingerprint")
    print("f) Search fingerprint")
    print("d) Delete fingerprint")
    print("s) Save fingerprint image")
    print("cf) Compare template with file")
    print("esf) Enroll and save to file")
    print("r) Reset library")
    print("q) Exit")
    print("----------------")

    c = input("> ")

    if c == "e":
        enroll_finger(get_num(finger.library_size))
    elif c == "f":
        if get_fingerprint():
            print("Fingerprint detected with ID#",finger.finger_id,"& confidence",finger.confidence)
        else:
            print("Fingerprint not found")
    elif c == "d":
        if finger.delete_model(get_num(finger.library_size)) == adafruit_fingerprint.OK:
            print("Deleted successfully!")
        else:
            print("Error deleting")
    elif c == "s":
        if save_fingerprint_image("fingerprint.png"):
            print("Fingerprint image saved")
        else:
            print("Error saving image")
    elif c == "cf":
        fingerprint_check_folder()
    elif c == "esf":
        enroll_save_to_file()
    elif c == "r":
        if finger.empty_library() == adafruit_fingerprint.OK:
            print("Library cleared")
        else:
            print("Failed to clear library")
    elif c == "q":
        print("Exiting program")
        break
