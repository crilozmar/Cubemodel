#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger("icecube.LedDisplay")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)


from time import sleep

import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__))+"/../steamshovel")

from LedDisplay import DisplayManager, DisplayController

manager = DisplayManager()

import argparse
parser = argparse.ArgumentParser(description="Test IceCube LED display")
parser.add_argument(
        "-m"
      , "--mode"
      , choices=["string", "rgb"]
      , help="Test string per string or display RGB loop"
      , required=True
)
parser.add_argument("-d", "--duration", type=float, help="Duration of a single frame. Defaults to 1/25.", default=1./25)
parser.add_argument("-c", "--count", type=int, help="Number of frames to render. Defaults to 0, or 1 if offset is not 0.", default=0)
parser.add_argument("-o", "--offset", type=int, help="Initial frame offset number. Defaults to 0.", default=0)
parser.add_argument("-p", "--persist", action="store_true", help="If present, do not clear display after last frame.", default=False)
args = parser.parse_args(sys.argv[1:])

initial_offset = args.offset
frame_count = args.count
duration = args.duration


class OMKey:
  def __init__(self, string, om):
    self.string = string
    self.om = om

import colorsys

#
# Draw an HSV loop to the display
#
def draw_hsv(display, offset):
  pixel_size = display.led_class.DATA_LENGTH
  rgb_to_data = display.led_class.float_to_led_data
  buffer_length = display.buffer_length
  frame = bytearray(buffer_length)

  if os.getenv("VIRTUAL_DEVICES") is None:
    lightness = 0.1
  else:
    lightness = 0.5

  if display.data_type == DisplayController.DATA_TYPE_IC_STRING:
    pixel_offset = offset%60
    for pixel in range(60):
      hue = float(pixel-pixel_offset)/60
      if hue < 0:
        hue += 1
      data = rgb_to_data(colorsys.hls_to_rgb(hue, lightness, 1.0))
      for string_offset in range(display.string_count):
        buffer_offset = string_offset*60+pixel
        frame[buffer_offset*pixel_size:(buffer_offset+1)*pixel_size] = data

  elif display.data_type == DisplayController.DATA_TYPE_IT_STATION:
    pixel_offset = offset%display.string_count
    for pixel in range(display.string_count):
      hue = (pixel-pixel_offset)/display.string_count
      if hue < 0:
        hue += 1
      data = rgb_to_data(colorsys.hls_to_rgb(hue, lightness, 1.0))
      buffer_offset = pixel_size*pixel_offset
      frame[pixel*pixel_size:(pixel+1)*pixel_size] = data

  return frame


def draw_loop(display, offset):
  "Light up one string (nr. `offset`) of the detector"
  pixel_size = display.led_class.DATA_LENGTH
  rgb_to_data = display.led_class.float_to_led_data
  buffer_length = display.buffer_length
  frame = bytearray(buffer_length)

  if os.getenv("VIRTUAL_DEVICES") is None:
    pixel_data = rgb_to_data((0.1, 0.1, 0.1))
  else:
    pixel_data = rgb_to_data((1, 1, 1))

  if display.data_type == DisplayController.DATA_TYPE_IC_STRING:
    string_offset = offset % display.string_count
    string = display.string_range[0]-1 + string_offset
    pixel_offset = display.getLedIndex(OMKey(string+1, 1))
    for pixel in range(pixel_offset, pixel_offset+60):
      buffer_offset = pixel*pixel_size
      frame[buffer_offset:buffer_offset+pixel_size] = pixel_data

  elif display.data_type == DisplayController.DATA_TYPE_IT_STATION:
    pixel = offset % display.string_count
    frame[pixel*pixel_size:(pixel+1)*pixel_size] = pixel_data

  return frame

if len(manager.displays) and (frame_count > 0 or initial_offset > 0):
  for display in manager.displays:
    print("Opening display")
    display.open()

  if initial_offset > 0:
    if frame_count > 0:
      frame_range = range(initial_offset-1, initial_offset-1+frame_count)
    else:
      frame_range = range(initial_offset-1, initial_offset)
  else:
    frame_range = range(0, frame_count)

  for offset in frame_range:
    logger.debug("{} frames to go".format(frame_count-offset))
    for display in manager.displays:
      if args.mode == 'string':
        frame = draw_loop(display, offset)
      elif args.mode == 'rgb':
        frame = draw_hsv(display, offset)
      else:
        frame = bytearray(display.buffer_length)

      display.transmitDisplayBuffer(frame)
 
    sleep(duration)

  for display in manager.displays:
    logger.debug("Clearing display")
    if not args.persist:
      clear_frame = bytearray(display.buffer_length)
      display.transmitDisplayBuffer(clear_frame)
    display.close()

