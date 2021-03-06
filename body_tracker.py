#!/usr/bin/env python
"""
= = = = =    STRESS AND FALL DETECTION    = = = = =

This is based on Lucas Kanade sparse optical flow algorithm.

This script serves two purposes:
1. Patient's distress recognition:
    Using optical flow approach, we track the direction of flow of
    corner points in an image. Rapid movements of patient's body
    result in quick fluctuations in the optical flow. This suggests
    that the patient cound be in distress.

2. Detect whether the patient fell from bed:
    We can consider the patient's bed as our region of interest. If the
    optical flow moves out of this region, we can say that the patient has
    fallen from the bed.

- - - - -
Press ENTER to start
To stop press ESC
"""

import numpy as np
import cv2
from time import clock



lk_params = dict( winSize  = (15, 15),
                  maxLevel = 2,
                  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

feature_params = dict( maxCorners = 500,
                       qualityLevel = 0.3,
                       minDistance = 7,
                       blockSize = 7 )

class BodyTracker(object):
    def __init__(self):
        self.track_len = 10
        self.detect_interval = 5
        self.tracks = []
        self.cam = cv2.VideoCapture(0)
        self.frame_idx = 0

    def run(self):
	count=0
        while True:
            ret, frame = self.cam.read()
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            vis = frame.copy()

            if len(self.tracks) > 0:
                img0, img1 = self.prev_gray, frame_gray
                p0 = np.float32([tr[-1] for tr in self.tracks]).reshape(-1, 1, 2)
                p1, st, err = cv2.calcOpticalFlowPyrLK(img0, img1, p0, None, **lk_params)
                p0r, st, err = cv2.calcOpticalFlowPyrLK(img1, img0, p1, None, **lk_params)
                d = abs(p0-p0r).reshape(-1, 2).max(-1)
                good = d < 1
                new_tracks = []
                for tr, (x, y), good_flag in zip(self.tracks, p1.reshape(-1, 2), good):
                    if not good_flag:
                        continue
                    tr.append((x, y))
                    if len(tr) > self.track_len:
                        del tr[0]
                    new_tracks.append(tr)
                    cv2.circle(vis, (x, y), 2, (0, 255, 0), -1)
                self.tracks = new_tracks
                cv2.polylines(vis, [np.int32(tr) for tr in self.tracks], False, (0, 255, 0))
                #draw_str(vis, (20, 20), 'track count: %d' % len(self.tracks))

            if self.frame_idx % self.detect_interval == 0:
                mask = np.zeros_like(frame_gray)
                mask[:] = 255
                for x, y in [np.int32(tr[-1]) for tr in self.tracks]:
                    cv2.circle(mask, (x, y), 5, 0, -1)
                p = cv2.goodFeaturesToTrack(frame_gray, mask = mask, **feature_params)
                if p is not None:
                    for x, y in np.float32(p).reshape(-1, 2):
                        self.tracks.append([(x, y)])

            self.frame_idx += 1
            self.prev_gray = frame_gray
            cv2.imshow('lk_track', vis)
	    mask=cv2.inRange(vis,(0,255,0),(0,255,0))
	    op=cv2.bitwise_and(vis,vis,mask=mask)
	    cv2.imshow('op',op)

	    if count is 0:

	         count=count+1
		 normal=int(np.sum(op)/10000)
		 temp=normal
	    else:
	   	temp=int(np.sum(op)/10000)
	    count=count+1
	    if count==18:
		normal=normal+temp
	    elif count>18:
		count=count-1

	    #print 'normal=',normal,'temp=',temp
	    if temp<=normal-1:
		print "[ ALERT ] The patient Fell from bed."
		break

	    elif temp>normal-1 and temp<=normal+28:
	    	print "Normal"
	    else:
		print 'Stress'

            ch = 0xFF & cv2.waitKey(1)
            if ch == 27:
                break

def main():
    BodyTracker().run()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    print __doc__
    raw_input()
    main()
