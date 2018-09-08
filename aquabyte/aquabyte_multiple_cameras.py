
# ============================================================================
# This sample illustrates how to grab and process images from multiple cameras
# using the CInstantCameraArray class. The CInstantCameraArray class represents
# an array of instant camera objects. It provides almost the same interface
# as the instant camera for grabbing.
# The main purpose of the CInstantCameraArray is to simplify waiting for images and
# camera events of multiple cameras in one thread. This is done by providing a single
# RetrieveResult method for all cameras in the array.
# Alternatively, the grabbing can be started using the internal grab loop threads
# of all cameras in the CInstantCameraArray. The grabbed images can then be processed by one or more
# image event handlers. Please note that this is not shown in this example.
# ============================================================================

import json
import os
import sys
import time

import cv2
from pypylon import genicam
from pypylon import pylon

os.environ["PYLON_CAMEMU"] = "3"

# Number of images to be grabbed.
number_of_images_to_grab = 10
maxCamerasToUse = 2

# The exit code of the sample application.
exitCode = 0

config = json.load(open('/root/config/config.json', 'r'))
farm_base_directory = os.path.join(config['base_directory'], config['farm_name'])
try:

    # get camera details by serial number
    enclosure_details_by_serial_number = {}
    for enclosure in config['enclosures']:
        enclosure_id = enclosure['enclosure_id']
        pen_id = enclosure['pen_id']
        pen_name = enclosure['pen_name']
        for side in ['left', 'right']:
            serial_number = enclosure['{}_camera_details'.format(side)]['serial_number']
            other_camera_serial_number = None
            if side == 'left':
                other_camera_serial_number = enclosure['right_camera_details'.format(side)]['serial_number']
            elif side == 'right':
                other_camera_serial_number = enclosure['left_camera_details'.format(side)]['serial_number']
            ip_address = enclosure['{}_camera_details'.format(side)]['ip_address']
            settings_file = enclosure['{}_camera_details'.format(side)]['settings_file']
            enclosure_details_by_serial_number[serial_number] = {
                'other_camera_serial_number': other_camera_serial_number,
                'side': side,
                'ip_address': ip_address,
                'enclosure_id': enclosure_id,
                'pen_id': pen_id,
                'pen_name': pen_name,
                'settings_file': settings_file
            }



    # Get the transport layer factory as well as all attached devices
    tlFactory = pylon.TlFactory.GetInstance()
    devices = tlFactory.EnumerateDevices()
    if len(devices) == 0:
        raise pylon.RUNTIME_EXCEPTION("No camera present.")

    cameras = pylon.InstantCameraArray(min(len(devices), maxCamerasToUse))

    # Create and attach all Pylon Devices.
    for i, camera in enumerate(cameras):
        camera.Attach(tlFactory.CreateDevice(devices[i]))
        model_name = camera.GetDeviceInfo().GetModelName()
        serial_number = camera.GetDeviceInfo().GetSerialNumber()
        print('Attaching device {} with serial number {}'.format(model_name, serial_number))
        settings_file = enclosure_details_by_serial_number[serial_number]['settings_file']
        camera.Open()
        node_map = camera.GetNodeMap()
        pylon.FeaturePersistence.Load(settings_file, node_map, True)

    # reset the camera timers
    for camera in cameras:
        camera.GevTimestampControlLatchReset()

    time.sleep(1.0)
    cameras.StartGrabbing()

    # start grabbing images
    timestamp_by_serial_number = {serial_number: 0 for serial_number in enclosure_details_by_serial_number.keys()}
    stereo_image_pair_timestamp_ms = None
    for i in range(number_of_images_to_grab):
        if not cameras.IsGrabbing():
            break

        grab_result = cameras.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
        camera_context_value = grab_result.GetCameraContext()
        side = enclosure_details_by_serial_number[serial_number]['side']
        serial_number = cameras[camera_context_value].GetDeviceInfo().GetSerialNumber()
        other_camera_serial_number = enclosure_details_by_serial_number[serial_number]['other_camera_serial_number']
        other_camera_timestamp_ms = timestamp_by_serial_number[other_camera_serial_number]
        timestamp_ms = 8 * grab_result.ChunkTimestamp.Value
        timestamp_by_serial_number[serial_number] = timestamp_ms
        print(abs(timestamp_ms - other_camera_timestamp_ms))
        if abs(timestamp_ms - other_camera_timestamp_ms) > 10e8:
            stereo_image_pair_timestamp_ms = timestamp_ms

        print('Timestamp for stereo image pair (ms) {}: {}'.format(serial_number, stereo_image_pair_timestamp_ms))
        img = grab_result.GetArray()
        f_name = '{}_{}.jpg'.format(side, stereo_image_pair_timestamp_ms)
        image_path = os.path.join(farm_base_directory, f_name)
        print('Writing image to {}'.format(image_path))
        cv2.imwrite(f_name, img)

except genicam.GenericException as e:
    print("An exception occurred.", e.GetDescription())
    exitCode = 1

sys.exit(exitCode)