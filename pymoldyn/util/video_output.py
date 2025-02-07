#!/usr/bin/env python

import os
import sys

import gr
import numpy as np
from PIL import Image


class GRVideoOutput(object):
    def __init__(self):
        self.is_recording = False

    def begin(self, outfile_name=None):
        self.is_recording = True
        os.environ["GKS_WSTYPE"] = "mov"
        if outfile_name is not None:
            os.environ["GKS_FILEPATH"] = os.path.abspath(outfile_name)

    def write(self, image, device_pixel_ratio=1):
        height, width = image.shape[:2]
        gr.clearws()
        if width > height:
            xmax = 1.0
            ymax = 1.0 * height / width
        else:
            xmax = 1.0 * width / height
            ymax = 1.0

        metric_width, metric_height, pixel_width, pixel_height = gr.inqdspsize()
        meter_per_horizontal_pixel = metric_width / pixel_width
        meter_per_vertical_pixel = metric_height / pixel_height
        gr.setwsviewport(
            0,
            meter_per_horizontal_pixel * width * device_pixel_ratio,
            0,
            meter_per_vertical_pixel * height * device_pixel_ratio,
        )
        gr.setwswindow(0, xmax, 0, ymax)
        gr.setviewport(0, xmax, 0, ymax)
        gr.setwindow(0, xmax, 0, ymax)
        gr.drawimage(
            0,
            xmax,
            0,
            ymax,
            width * device_pixel_ratio,
            height * device_pixel_ratio,
            image.view("uint32"),
        )
        gr.updatews()

    def end(self):
        self.is_recording = False
        gr.emergencyclosegks()


def main(argv):
    if len(argv) < 3:
        print("usage: python video_output.py outfile.mov frame1.png...")
        sys.exit(1)
    argv = list(map(os.path.abspath, argv[1:]))
    outfile_name = argv[0]
    frame_file_names = argv[1:]
    os.chdir(os.path.dirname(frame_file_names[0]))
    video_output = GRVideoOutput()
    video_output.begin(outfile_name)
    for frame_index, frame_file_name in enumerate(frame_file_names):
        image = np.array(Image.open(frame_file_name))
        video_output.write(image)
        sys.stdout.flush()
    video_output.end()


if __name__ == "__main__":
    main(sys.argv)
