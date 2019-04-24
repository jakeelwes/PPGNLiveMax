import os
import math
import pickle
import numpy as np
import tensorflow as tf
import random
import cv2
import time
import datetime
import sys

from PyQt5 import QtWidgets

from osc4py3.as_eventloop import *
from osc4py3 import oscmethod as osm


recording = False

# load birds models
tf.InteractiveSession()
model = "birdsSnapshot1000.pkl"

print("open model %s" % model)
with open(model, 'rb') as file:
    G, D, Gs = pickle.load(file)
finished = False


# from input vector return image
def update(latents):
    # print(latents[0][0])
    labels = np.zeros([latents.shape[0]] + Gs.input_shapes[1][1:])
    images = Gs.run(latents, labels)
    images = np.clip(np.rint((images + 1.0) / 2.0 * 255.0), 0.0, 255.0).astype(np.uint8) # [-1,1] => [0,255]
    images = images.transpose(0, 2, 3, 1) # NCHW => NHWC
    img = np.concatenate([img for img in images], axis=1)
    print(latents)
    return img

# fill with test array before while loop
latents = np.full([1, 512], 0.4)
img = update(latents)

start_time = time.time()
running=True

fullscreen=False

# CV2 Windows (and PyQT get size of screen)
cv2.namedWindow("image", cv2.WINDOW_GUI_NORMAL)

if(fullscreen):
    cv2.setWindowProperty("image",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
else:
    cv2.resizeWindow('image', 600,600)

app = QtWidgets.QApplication(sys.argv)

screen = app.primaryScreen()
print('Screen: %s' % screen.name())
size = screen.size()
print('Size: %d x %d' % (size.width(), size.height()))
rect = screen.availableGeometry()
print('Available: %d x %d' % (rect.width(), rect.height()))

# make dir for saving
if (recording):
    date=datetime.datetime.now()
    dirRoot = '/media/jake/DL/CUSPLive/' #'images/'
    dir = dirRoot+ str(date.month) +'_'+ str(date.day) +'_'+ str(date.hour) +'_'+ str(date.minute)
    os.mkdir(dir)


# OSC Methods
def handlerfunction(*input):
    # Will receive message data unpacked in s, x, ydata
    # print(list(input))
    # replace latents with OSC array
    latents[0] = list(input)
# Start the system.
osc_startup()
# Make server channels to receive packets.
# osc_udp_server("192.168.0.2", 12345, "aservername")
osc_udp_server("0.0.0.0", 9997, "server")
# Associate Python functions with message address patterns, using default
# argument scheme OSCARG_DATAUNPACK.
osc_method("*", handlerfunction)


# Updtae loop
while(running):
    # framratecalc
    tA=time.time()

    # GET OSC
    osc_process()
    # latents[0] = handlerfunction

    img = update(latents)

    # CV2 to upres + add border to image
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # imgx2 = cv2.resize(img, None, fx = 3, fy = 3, interpolation = cv2.INTER_CUBIC)
    imgx2 = cv2.resize(img, (size.height(), size.height()), interpolation = cv2.INTER_CUBIC)
    # imgx2 = cv2.resize(img, (size.height(), size.height()))
    imgf = cv2.copyMakeBorder(imgx2, 0, 0, int((size.width()-size.height())/2), int((size.width()-size.height())/2), cv2.BORDER_CONSTANT, value=[0,0,0])

    int((size.width()-size.height())/2)

    cv2.imshow("image",imgf)

    if (recording):
        cv2.imwrite(dir+'/'+str(tA)+'.jpg', img)

    # Show framerate


    if(fullscreen):
        cv2.setWindowProperty("image",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
    else:
        cv2.resizeWindow('image', 1200,800)

    # Kill program? not working with OSC
    # cv2.waitKey(50)
    k = cv2.waitKey(1) & 0xFF
    if k == ord('m'):
     mode = not mode
    elif k == ord('f'):
     fullscreen = not fullscreen
    elif k == 27:
     break

    # tB=time.time()
    time.sleep(max(1./30 - (time.time() - tA), 0))

    tB=time.time()
    print(str(math.ceil(1/(tB-tA))) + "fps")




cv2.destroyAllWindows()
osc_terminate()
