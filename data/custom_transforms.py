from torchvision import transforms
import cv2
import torch
import random
import numpy as np

class RandomHorizontalFlip(object):

    def __call__(self, sample):
        if random.random() < 0.5:
            for elem in sample.keys():
                tmp = sample[elem]
                if tmp is None: # this is necessary because of the different batch sizes of the two image sets in the VIGOR validation code
                    continue
                tmp = cv2.flip(tmp, flipCode=1)
                sample[elem] = tmp
        return sample

class ToTensor(object):

    def __call__(self, sample):
        tanh_norm = transforms.Normalize(mean = [0.485, 0.456, 0.406], std = [0.229, 0.224, 0.225])
        for elem in sample.keys():
            tmp = sample[elem]
            tmp = np.array(tmp, dtype=np.float32).transpose((2, 0, 1))
            tmp /= 255.0
            sample[elem] = torch.from_numpy(tmp)
            sample[elem] = tanh_norm(sample[elem])
        return sample


class ToTensorVIGOR(object):

    def __call__(self, sample):
        tanh_norm = transforms.Normalize(mean = [0, 0, 0], std = [1, 1, 1]) # images are already normalized in the VIGOR dataloader
        for elem in sample.keys():
            tmp = sample[elem]
            if tmp is None: # this is necessary because of the different batch sizes of the two image sets in the VIGOR validation code
                continue
            tmp = cv2.cvtColor(tmp, cv2.COLOR_BGR2RGB) # VIGOR dataloader loads images in BGR, we transform it to RGB here for visualization purposes
            tmp = np.array(tmp, dtype=np.float32).transpose((2, 0, 1))
            tmp /= 255.0
            sample[elem] = torch.from_numpy(tmp)
            sample[elem] = tanh_norm(sample[elem])
        return sample