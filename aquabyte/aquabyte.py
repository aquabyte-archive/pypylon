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
    optical_inputs = json.load(open('./optical_inputs.json', 'r'))
    print(json.dumps(optical_inputs, indent=4))
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    camera.Open()
    converter = pylon.ImageFormatConverter()
    converter.OutputPixelFormat = pylon.PixelType_BGR8packed
    converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned


    # Print the model name of the camera.
    print("Using device ", camera.GetDeviceInfo().GetModelName())

    # get configuration details
    configuration_details = json.load(open('./config.json', 'r'))
    base_directory = configuration_details['base_directory']
    data_directory = '{}/{}/{}'.format(base_directory, 'fish_id_{}_side_{}'.format(optical_inputs['fish_id'], optical_inputs['side']), 'batch_id_{}'.format(optical_inputs['batch_id']))
    if not os.path.exists(data_directory):
        os.makedirs(data_directory)
    settings_file = configuration_details['settings_file']
    node_map = camera.GetNodeMap()
    pylon.FeaturePersistence.Load(settings_file, node_map, True)

    # save all optical inputs 
    pylon.FeaturePersistence.Save('{}/settings.pfs'.format(data_directory), node_map)
    with open('{}/optical_inputs.json'.format(data_directory), 'w') as f:
        json.dump(optical_inputs, f)

    
    

    # The parameter MaxNumBuffer can be used to control the count of buffers
    # allocated for grabbing. The default value of this parameter is 10.
    camera.MaxNumBuffer = 5

    if optical_inputs['capture_automatic_gain_exposure_image']:
        num_images_auto_calibration = 5
        camera.StartGrabbingMax(num_images_auto_calibration + 1)

        i = 0
        while camera.IsGrabbing():
        # Wait for an image and then retrieve it. A timeout of 5000 ms is used.
            grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                
            if grabResult.GrabSucceeded():
                # Access the image data.
                img = converter.Convert(grabResult).GetArray()
                if i < num_images_auto_calibration:
                    i += 1
                else:
                    timestamp = dt.datetime.fromtimestamp(time.time()).strftime('%Y%m%dT%H%M%S')
                    cv2.imwrite('{}/{}'.format(data_directory, '{}_gain_auto_exposure_auto.jpg'.format(timestamp)), img)
                    print("Auto settings images captured!")
                    break
                grabResult.Release()
            else:
                print("Error: ", grabResult.ErrorCode, grabResult.ErrorDescription)

    # iterate over predefined gain and exposure values

    camera.ExposureAuto.SetValue('Off')
    camera.GainAuto.SetValue('Off')
    exposure_time_abs = camera.ExposureTimeAbs
    gain_raw = camera.GainRaw
    number_of_images_to_capture = len(optical_inputs['exposure_values']) * len(optical_inputs['gain_values']) 
    
    camera.StartGrabbingMax(50)

    exposure_gain_combinations = list(itertools.product(optical_inputs['exposure_values'], optical_inputs['gain_values']))
    print(exposure_gain_combinations)

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
                cv2.imwrite('{}/{}'.format(data_directory, '{}_gain_{}_exposure_{}.jpg'.format(timestamp, gain, exposure)), img)
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
