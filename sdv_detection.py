# Copyright 2019 Google LLC
#
#  Modified by Nam Vu 06/15/2020
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A demo which runs object detection on camera frames using GStreamer.

Run default object detection:
python3 sdv_detection.py

Choose different camera or video
python3 sdv_detection.py --videosrc ./test_video.mp4

"""
import argparse
import collections
import common
import gstreamer
import numpy as np
import os
import re
import svgwrite
import time
import math

import tflite_runtime.interperter as tflite

Object = collections.namedtuple('Object', ['id', 'score', 'bbox'])

class Point():
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def distance(self, p):
        return math.sqrt((self.x - p.x)**2 + (self.y - p.y)**2)

class Person():
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.width = w
        self.height = h
        self.centroid = Point(((2*x+w)/2), ((2*y+h)/2))
        self.violates = False

    def vs(self, p):
        dist = self.centroid.distance(p.centroid)
        if dist < self.height or dist < p.height:
            print('Violation! p1: {:.2f} p2: {:.2f} dist: {:.2f}'.format(self.height, p.height, dist))
            self.violates = True
            p.violates = True

    def draw(self, dwg):
        color = 'red' if self.violates else 'lightgreen'
        label = 'Too Close' if self.violates else 'Good Distance'
        dwg.add(svgwrite.shapes.Circle(center=(self.centroid.x, self.centroid.y), 
                        r=5, fill='none', stroke=color, stroke_width='3'))
        dwg.add(dwg.rect(insert=(self.x, self.y), size=(self.width, self.height),
                        fill='none', stroke=color, stroke_width='5'))
        dwg.add(dwg.rect(insert=(self.x, self.y - 25), size=(self.width, 25),
                        fill=color, stroke=color, stroke_width='5'))
        shadow_text(dwg, self.x, self.y-5, label, 25)


def shadow_text(dwg, x, y, text, font_size=15):
    dwg.add(dwg.text(text, insert=(x+1, y+1), fill='black', font_size=font_size))
    dwg.add(dwg.text(text, insert=(x, y), fill='white', font_size=font_size))

def generate_svg(src_size, inference_size, inference_box, objs, text_lines):
    dwg = svgwrite.Drawing('', size=src_size)
    src_w, src_h = src_size
    inf_w, inf_h = inference_size
    box_x, box_y, box_w, box_h = inference_box
    scale_x, scale_y = src_w / box_w, src_h / box_h

    for y, line in enumerate(text_lines, start=1):
        shadow_text(dwg, 10, y*20, line)
        
    people = []
    for obj in objs:
        x0, y0, x1, y1 = list(obj.bbox)
        # Relative coordinates.
        x, y, w, h = x0, y0, x1 - x0, y1 - y0
        # Absolute coordinates, input tensor space.
        x, y, w, h = int(x * inf_w), int(y * inf_h), int(w * inf_w), int(h * inf_h)
        # Subtract boxing offset.
        x, y = x - box_x, y - box_y
        # Scale to source coordinate space.
        x, y, w, h = x * scale_x, y * scale_y, w * scale_x, h * scale_y
        # Creates a Person instance
        np = Person(x, y, w, h)
        for p in people:
            p.vs(np)
        people.append(np)

    for p in people:
        p.draw(dwg)

    return dwg.tostring()

class BBox(collections.namedtuple('BBox', ['xmin', 'ymin', 'xmax', 'ymax'])):
    """Bounding box.
    Represents a rectangle which sides are either vertical or horizontal, parallel
    to the x or y axis.
    """
    __slots__ = ()

def get_output(interpreter, score_threshold, top_k, image_scale=1.0):
    """Returns list of detected human."""
    category_ids = common.output_tensor(interpreter, 1)
    boxes = common.output_tensor(interpreter, 0)
    scores = common.output_tensor(interpreter, 2)
   
    def make(i):
        ymin, xmin, ymax, xmax = boxes[i]
        return Object(
            id=int(category_ids[i]),
            score=scores[i],
            bbox=BBox(xmin=np.maximum(0.0, xmin),
                      ymin=np.maximum(0.0, ymin),
                      xmax=np.minimum(1.0, xmax),
                      ymax=np.minimum(1.0, ymax)))
    return [make(i) for i in range(top_k) if category_ids[i] == 0 and scores[i] >= score_threshold]

def main():
    default_model_dir = 'model'
    default_model = 'ssdlite_mobiledet_quant_postprocess_edgetpu.tflite'
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', help='.tflite model path',
                        default=os.path.join(default_model_dir,default_model))
    parser.add_argument('--top_k', type=int, default=3,
                        help='number of categories with highest score to display')
    parser.add_argument('--threshold', type=float, default=0.5,
                        help='classifier score threshold')
    parser.add_argument('--videosrc', help='Which video source to use. ',
                        default='/dev/video0')
    parser.add_argument('--videofmt', help='Input video format.',
                        default='raw',
                        choices=['raw', 'h264', 'jpeg'])
    args = parser.parse_args()

    interpreter = tflite.Interperter(args.model)
    interpreter.allocate_tensors()

    w, h, _ = common.input_image_size(interpreter)
    inference_size = (w, h)
    # Average fps over last 30 frames.
    fps_counter  = common.avg_fps_counter(100)

    def user_callback(input_tensor, src_size, inference_box):
      nonlocal fps_counter
      start_time = time.monotonic()
      common.set_input(interpreter, input_tensor)
      interpreter.invoke()
      # For larger input image sizes, use the edgetpu.classification.engine for better performance
      objs = get_output(interpreter, args.threshold, args.top_k)
      end_time = time.monotonic()
      text_lines = [
          'Inference: {:.2f} ms'.format((end_time - start_time) * 1000),
          'FPS: {} fps'.format(round(next(fps_counter))),
      ]
      print(' '.join(text_lines))
      return generate_svg(src_size, inference_size, inference_box, objs, text_lines)

    result = gstreamer.run_pipeline(user_callback,
                                    src_size=(640, 480),
                                    appsink_size=inference_size,
                                    videosrc=args.videosrc,
                                    videofmt=args.videofmt)

if __name__ == '__main__':
    main()
