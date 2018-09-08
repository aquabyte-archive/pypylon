# ===============================================================================
#    This sample illustrates how to grab and process images using the CInstantCamera class.
#    The images are grabbed and processed asynchronously, i.e.,
#    while the application is processing a buffer, the acquisition of the next buffer is done
#    in parallel.
# 
#    The CInstantCamera class uses a pool of buffers to retrieve image data
#    from the camera device. Once a buffer is filled and ready,
#    the buffer can be retrieved from the camera object for processing. The buffer
#    and additional image data are collected in a grab result. The grab result is
#    held by a smart pointer after retrieval. The buffer is automatically reused
#    when explicitly released or when the smart pointer object is destroyed.
# ===============================================================================

import datetime as dt
import itertools
import json
import sys
import time as time
import os

import cv2
from pypylon import pylon
from pypylon import genicam


exitCode = 0

try:
    # Create an instant camera object with the camera device found first.
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    camera.Open()
    converter = pylon.ImageFormatConverter()
    converter.OutputPixelFormat = pylon.PixelType_BGR8packed
    converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned


    # Print the model name of the camera.
    print("Using device ", camera.GetDeviceInfo().GetModelName())

    # get configuration details
    config = json.load(open('/root/config/config.json', 'r'))
    base_directory = config['base_directory']
    
    farm_data_directory = os.path.join(base_directory, config['farm_name'])
    if not os.path.exists(farm_data_directory):
        os.makedirs(farm_data_directory)
    settings_file = '/root/config/settings.pfs'
    node_map = camera.GetNodeMap()
    pylon.FeaturePersistence.Load(settings_file, node_map, True)

    # save all optical inputs 
    # pylon.FeaturePersistence.Save('{}/settings.pfs'.format(data_directory), node_map)
    # with open('{}/optical_inputs.json'.format(data_directory), 'w') as f:
    #     json.dump(optical_inputs, f, indent=4)

    i = 0
    first_iteration = True
    
    while camera.IsGrabbing():
        # Wait for an image and then retrieve it. A timeout of 5000 ms is used.

        exposure, gain = exposure_gain_combinations[i]
        exposure_time_abs.SetValue(exposure)
        gain_raw.SetValue(gain)

        grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            
        if grabResult.GrabSucceeded():
            # Access the image data.
            img = converter.Convert(grabResult).GetArray()
            if first_iteration:
                first_iteration = False
            else:
                print(exposure_time_abs.GetValue(), gain_raw.GetValue())
                timestamp = dt.datetime.fromtimestamp(time.time()).strftime('%Y%m%dT%H%M%S')
                f_name = '{}/{}'.format(data_directory, '{}_gain_{}_exposure_{}.jpg'.format(timestamp, gain, exposure))
                print('Writing image to {}'.format(f_name))
                cv2.imwrite(f_name, img)
                i += 1
            grabResult.Release()
            if i >= number_of_images_to_capture:
                break
        else:
            print("Error: ", grabResult.ErrorCode, grabResult.ErrorDescription)
        

except genicam.GenericException as e:
    # Error handling.
    print("An exception occurred.")
    print(e.GetDescription())
    exitCode = 1

sys.exit(exitCode)
