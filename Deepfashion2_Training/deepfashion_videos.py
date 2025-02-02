import cv2
import os
import sys
from lib import utils
from lib import model as modellib
from lib.config import Config
import lib.model as modellib
from lib.model import MaskRCNN
import uuid
import argparse
import skimage
import colorsys
import tensorflow as tf
import numpy as np
import shutil
import random
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--input", required=True)
args = vars(ap.parse_args())
path_video = args["input"]


class TestConfig(Config):
    NAME = "Deepfashion2"
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1
    NUM_CLASSES = 1 + 13
config = TestConfig()


model = modellib.MaskRCNN(mode="inference", config=config, model_dir='/content/drive/My Drive/')
model.load_weights('/content/gdrive/MyDrive/MaxTap/mask_rcnn_deepfashion2_0100.h5', by_name=True)

class_names = ['short_sleeved_shirt', 'long_sleeved_shirt', 'short_sleeved_outwear', 'long_sleeved_outwear', 'vest', 'sling', 
               'shorts', 'trousers', 'skirt', 'short_sleeved_dress', 'long_sleeved_dress',
               'vest_dress', 'sling_dress','']

def random_colors(N):
    np.random.seed(1)
    colors = [tuple(255 * np.random.rand(3)) for _ in range(N)]
    return colors


colors = random_colors(len(class_names))
class_dict = {
    name: color for name, color in zip(class_names, colors)
}


def apply_mask(image, mask, color, alpha=0.5):
    """apply mask to image"""
    for n, c in enumerate(color):
        image[:, :, n] = np.where(
            mask == 1,
            image[:, :, n] * (1 - alpha) + alpha * c,
            image[:, :, n]
        )
    return image


def display_instances(image, boxes, masks, ids, names, scores, img_name):
    n_instances = boxes.shape[0]
    print("no of potholes in frame :",n_instances)
    if not n_instances:
        print('NO INSTANCES TO DISPLAY')
    else:
        assert boxes.shape[0] == masks.shape[-1] == ids.shape[0]

    for i in range(n_instances):
        if not np.any(boxes[i]):
            continue

        y1, x1, y2, x2 = boxes[i]
        label = names[ids[i]]
        color = class_dict[label]
        score = scores[i] if scores is not None else None
        caption = '{} {:.2f}'.format(label, score) if score else label
        random_name = str(uuid.uuid4())
        mask = masks[:, :, i]  
        image = apply_mask(image, mask, color)
        random_name = str(uuid.uuid4())
        
        if(score >= 0.90):
          image = cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
          image = cv2.putText(image, caption, (x1, y1), cv2.FONT_HERSHEY_COMPLEX, 0.7, color, 2)
          cv2.imwrite("/content/detected/" + str(img_name) + ".jpg", image) 

    return image

	
stream = cv2.VideoCapture(path_video)
frame_width = int(stream.get(3)) 
frame_height = int(stream.get(4)) 

size = (frame_width, frame_height) 
out = cv2.VideoWriter('output.avi',cv2.VideoWriter_fourcc(*'MJPG'), 10, size)
i=0

while (stream.isOpened()):
    ret , frame = stream.read()
    print("Frame",i)
    i+=1

    if ret == True:
		    results = model.detect([frame], verbose=0)
		    r = results[0]
		    masked_image = display_instances(frame, r['rois'], r['masks'], r['class_ids'], class_names, r['scores'], i)
		    out.write(masked_image)
        # if(cv2.waitKey(1) & 0xFF == ord('q')):
		    #     break
    else:
      break

    
stream.release()
out.release()
# cv2.destroyWindow("masked_image")
