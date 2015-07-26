# -*- coding:utf-8 -*- 
'''
Created on 2015-6-20

@author: burkun
'''

import cv2, time
#write img to dump, then return the filename
def getImg(cameranum = 0):
    capture = cv2.VideoCapture(cameranum)
    isopen, frame = capture.read()
    filename = "data/" + str(time.time()) + ".jpg"
    if isopen:
        cv2.imwrite(filename, frame)
    capture.release()
    return isopen, filename;
    
    