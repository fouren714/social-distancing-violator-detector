# Social Distancing Violation Detector with Coral EdgeTPU

This repo contains example code using [GStreamer](https://github.com/GStreamer/gstreamer) 
and codes from [google-coral/examples-camera](https://github.com/google-coral/examples-camera) to
detect social distancing violatiors.

This code works on Linux using a webcam, Raspberry Pi with the Pi Camera, and on the Coral Dev
Board using the Coral Camera or a webcam. For the first two, you also need a Coral
USB/PCIe/M.2 Accelerator.


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
