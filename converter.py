import cv2 as cv
import numpy as np
import logging
import sys
from maina import *

def is_there_a_note(frame, p):  # p : (y, x)
    result = True
    MAX_ERROR = 50
    # px (in order to avoid recongnizing bar lines as notes)
    min_note_height = 3
    empty_color = (0, 0, 0)

    for i in range(-(min_note_height // 2), min_note_height // 2 + 1):
        # opencv frames get (y, x) coordinates
        pixel_color = frame[p[0] + i][p[1]]

        if not ((abs(pixel_color[0] - empty_color[0]) > MAX_ERROR
                 or abs(pixel_color[1] - empty_color[1]) > MAX_ERROR
                 or abs(pixel_color[2] - empty_color[2]) > MAX_ERROR)):

            result = False

    return result


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    lane_start = 735
    lane_end = 1180
    lane_height = 600
    lane_count = 4
    frame_count = 1

    cv.namedWindow('Image', cv.WINDOW_NORMAL)
    vid_capture = cv.VideoCapture('vid.mp4')

    if (vid_capture.isOpened() == False):
        logging.error("Error opening the video file")
        raise RuntimeError

    fps = vid_capture.get(cv.CAP_PROP_FPS)
    print(fps)

    note_start_frame = [0, 0, 0, 0]

    file = open('test.osu', '+w')

    create_header(file, lane_count)
    start_note_section(file)

    while (vid_capture.isOpened()):
        ret, frame = vid_capture.read()

        if ret == False:
            break
        # if ret == True:
        #    cv.imshow('Frame',frame)

        # frame = cv.imread('sample.png')

        height, width, channels = frame.shape

        cv.line(frame, (lane_start, 0), (lane_start, height), (0, 0, 255), 10)
        cv.line(frame, (lane_end, 0), (lane_end, height), (0, 0, 255), 10)

        for i in range(lane_count):
            lane_width = lane_end - lane_start
            x = int((lane_start + lane_width / 4 * i +
                    lane_start + lane_width / 4 * (i + 1))/2)
            p = (height - lane_height, x)
            is_there_a_note_flag = is_there_a_note(frame, p)

            if is_there_a_note_flag == True:
                if note_start_frame[i] == 0:
                    note_start_frame[i] = frame_count

                print('▇', end=' ')
            else:
                print(' ', end=' ')

                if note_start_frame[i] != 0:
                    # if long note
                    if (frame_count - note_start_frame[i]) / fps > 0.05:
                        cv.circle(frame, (p[1], p[0]), 50, (255, 0, 255), -1)
                        create_LN(file, lane_count, i + 1,int(note_start_frame[i] / fps * 1000), int(frame_count / fps * 1000))
                        print('LN')
                    else:  # if regular note
                        cv.circle(frame, (p[1], p[0]), 15, (0, 255, 0), -1)
                        create_RN(file, lane_count, i + 1, int(note_start_frame[i] / fps * 1000))
                else:
                    cv.circle(frame, (p[1], p[0]), 15, (0, 0, 255), -1)

                note_start_frame[i] = 0

        print('')

        cv.imshow('Image', frame)
        cv.waitKey(1)
        # time.sleep(10)
        # cv.destroyAllWindows()
        frame_count += 1

    file.close()