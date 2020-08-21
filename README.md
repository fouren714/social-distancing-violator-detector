# Social Distancing Violation Detector with Coral EdgeTPU

This repo contains example code using [GStreamer](https://github.com/GStreamer/gstreamer) 
and codes from [google-coral/examples-camera](https://github.com/google-coral/examples-camera) to
detect social distancing violatiors.

This code works on Linux using a webcam, Raspberry Pi with the Pi Camera, and on the Coral Dev
Board using the Coral Camera or a webcam. 
**Note:** You'll need a Coral [USB/PCIe M.2 Accelerator](https://coral.ai/products/) since running this on CPU is too slow and won't be fast enough for real time. 

<div align="center">
  <img src="https://github.com/Namburger/social-distancing-violator-detector/blob/master/assets/sdv_ssdlite_mobiledet_resized.gif" width="450">
</div>

## Set up your device

1.  Clone this Git repo onto your computer or Dev Board:

    ```
    git clone https://github.com/namburger/social-distance-violation-detector
    ```

2.  Install requirements (this should works for most linux platforms):

    ```
    ./install_requirements.sh
    ```

## Run

```
python3 sdv_detection.py
```

By default it'll use the coral's camera but you can also try it on the test video:

```
python3 sdv_detection.py --videosrc ./test_video.mp4
``` 
