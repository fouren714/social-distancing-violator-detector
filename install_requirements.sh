#!/bin/bash
# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

readonly ARCH="$(uname -m)"
echo "ARCH: ${ARCH}"

PYTHON=$(python3 -V 2>&1 | grep -Po '(?<=Python )(.+)')
echo "PYTHON VERSION: ${PYTHON}"
if [[ -z "$PYTHON" ]]
then
  error "No Python3, please install..."
fi
PYTHON=$(python3 -c 'import platform; major, minor, _= platform.python_version_tuple(); print(major+minor)')
tflite_runtime=https://dl.google.com/coral/python/tflite_runtime-2.1.0.post1-cp${PYTHON}-cp${PYTHON}m-linux_${ARCH}.whl

if grep -s -q "MX8MQ" /sys/firmware/devicetree/base/model; then
  echo "Installing DevBoard specific dependencies"
  sudo apt-get install -y python3-pip python3-edgetpuvision
  sudo pip3 install svgwrite $tflite_runtime
else
  # Install gstreamer 
  sudo apt-get install -y gstreamer1.0-plugins-bad gstreamer1.0-plugins-good python3-gst-1.0 python3-gi gir1.2-gtk-3.0
  pip3 install svgwrite $tflite_runtime

  if grep -s -q "Raspberry Pi" /sys/firmware/devicetree/base/model; then
    echo "Installing Raspberry Pi specific dependencies"
    sudo apt-get install python3-rpi.gpio $tflite_runtime
    # Add v4l2 video module to kernel
    if ! grep -q "bcm2835-v4l2" /etc/modules; then
      echo bcm2835-v4l2 | sudo tee -a /etc/modules
    fi
    sudo modprobe bcm2835-v4l2 
  fi
fi
