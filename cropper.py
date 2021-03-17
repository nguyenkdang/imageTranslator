import cv2, os, sys
import numpy as np
from PIL import Image


def filterContours(contours, hierarchy, mini= 4000, maxi= 120000):
    contourDict = {}
    # remove contours whose area is either too large or small
    for i in range(len(contours)):
        
        if cv2.contourArea(contours[i]) < maxi and cv2.contourArea(contours[i]) > mini:
            contourDict[i] = contours[i]
    
    # If there is a contour in another contour, remove external contour
    for i in list(contourDict.keys()):
        index = i
        while hierarchy[0][index][3] > -1:
            parent = hierarchy[0][index][3]
            if parent in contourDict.keys(): contourDict.pop(parent)
            index = parent

    return contourDict

def getContours(image):
    ## attempt to find word bubbles from image
    img = np.array(image)
    #image to gray scale to binary
    grayImg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    binaryImg = cv2.threshold(grayImg,235,255,cv2.THRESH_BINARY)[1]
    
    # Find contours and heirarchy
    contours, hierarchy = cv2.findContours(binaryImg, cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    
    #filter contours 
    contourDict = filterContours(contours, hierarchy)

    return list(contourDict.values())

def getCrop(image, exportEach = None, exportAll=None):
    fn, fe = os.path.splitext(image.filename)
    fn = fn.split('\\')[-1]
    contours =  getContours(image)
    img = np.array(image)
    cropImages = {'image':[], 'left':[], 'top':[]}
    for i, contr in enumerate(contours):
        x, y, w, h = cv2.boundingRect(contr)
        cropImg = image.crop((x, y, x+w, y+h))
        cropImages['image'].append(cropImg)
        cropImages['left'].append(x)
        cropImages['top'].append(y)
        
        if exportEach != None:
            cpath = os.path.join(exportEach, 'Crop{}_{}{}'.format(i, fn, fe))
            cv2.imwrite(cpath, np.array(cropImg))
        
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    if exportAll != None:
        outpath = os.path.join(exportAll, 'Crop_{}{}'.format(fn, fe))
        cv2.imwrite(outpath, img)

    return cropImages