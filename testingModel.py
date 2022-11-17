# Import libraries
from __future__ import print_function, division
import pandas as pd
from skimage import io, transform
import matplotlib.pyplot as plt
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, utils
import warnings
warnings.filterwarnings("ignore")
import os
import sys
import copy
import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.init as init
import torch.nn.functional as F
import torchvision.models as models
from torchvision import transforms
from typing import Iterator, Dict
from torch.nn import Module
from torch.nn import Conv2d
from torch.nn import Linear
from torch.nn import MaxPool2d
from torch.nn import ReLU
from torch.nn import LogSoftmax
from torch import flatten

 

class ClothDataset(Dataset):

    def __init__(self, csv_file, root_dir, transform=None):
        """
        Args:
            csv_file (string): Path to the csv file with annotations of OGP.
            root_dir (string): Directory with all the images.
            transform (callable, optional): Optional transform to be applied
                on a sample.
        """
        self.OGP = pd.read_csv(csv_file)
        self.root_dir = root_dir
        self.transform = transform

    def __len__(self):
        return len(self.OGP)

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()

        img_name = os.path.join(self.root_dir,
                                self.OGP.iloc[idx, 0])
        image = io.imread(img_name)
        image = image.astype('float32')/255.0
        image = np.array([image])
        OGP_pose = self.OGP.iloc[idx, 1:]
        OGP_pose = np.array([OGP_pose])
        OGP_pose = OGP_pose.astype('float').flatten()
        sample = {'image': image, 'OGP_pose': OGP_pose}
        
        if self.transform:
            sample = self.transform(sample)

        return sample
 
      
cloth_dataset = ClothDataset(csv_file='../DataCollection-REDfirst/OGP_dataset_collection_RED.csv',
                                    root_dir='../DataCollection-REDfirst/')
                                    
training_loader = torch.utils.data.DataLoader(cloth_dataset, batch_size=4, shuffle=True, num_workers=2)                                            
        




class GraspEstimationModel(nn.Module):


 def __init__(self):
        super(GraspEstimationModel, self).__init__()
        self.conv1 = nn.Conv2d(in_channels=1, out_channels=64, kernel_size=(11, 11), stride=(2, 2), bias=False)
        self.relu1 = ReLU()
        self.maxpool1 = MaxPool2d(kernel_size=(2, 2), stride=(2, 2))
        self.conv2 = nn.Conv2d(in_channels=64, out_channels=128, kernel_size=(5, 5), bias=False)
        self.relu2 = ReLU()
        self.maxpool2 = MaxPool2d(kernel_size=(2, 2), stride=(2, 2))
        self.conv3 = nn.Conv2d(in_channels=128, out_channels=256, kernel_size=(3, 3), bias=False)
        self.relu3 = ReLU()
        self.conv4 = nn.Conv2d(in_channels=256, out_channels=256, kernel_size=(3, 3), bias=False)
        self.relu4 = ReLU()
        self.conv5 = nn.Conv2d(in_channels=256, out_channels=128, kernel_size=(3, 3), bias=False)
        self.relu5 = ReLU()
        self.maxpool3 = MaxPool2d(kernel_size=(2, 2), stride=(2, 2))
        #this number 15488 is determined by running blender-3.2.1-linux-x64/test.py 
        self.fc1 = nn.Linear(in_features=15488, out_features=2048)
        self.relu6 = ReLU()
        self.fc2 = nn.Linear(in_features=2048, out_features=2048)
        self.relu7 = ReLU()
        #final regression linear layer
        self.fc3 = nn.Linear(in_features=2048, out_features=7)       



 def forward(self, x):
        x = self.conv1(x)
        x = self.relu1(x)
        x = self.maxpool1(x)
        x = self.conv2(x)
        x = self.relu2(x)
        x = self.maxpool2(x)
        x = self.conv3(x)
        x = self.relu3(x)
        x = self.conv4(x)
        x = self.relu4(x)
        x = self.conv5(x)
        x = self.relu5(x)
        x = self.maxpool3(x)       
        x = flatten(x, 1)
        x = self.fc1(x)
        x = self.relu6(x)
        x = self.fc2(x)
        x = self.relu7(x)
        #final layer is regression linear, binary limits 0->1
        output = self.fc3(x)   

        return output

model = GraspEstimationModel()


loss_fn = torch.nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.005)


def train_one_epoch(epoch_index):
    running_loss = 0.
    last_loss = 0.
    
    for i, data in enumerate(training_loader):
        # Every data instance is an input + label pair
        images=data['image']
        labels=data['OGP_pose'].float()
        #print('images ',images.shape)
        #print('labels ', labels)
        #print('labels.view ',labels.view(-1, 1).shape)
        optimizer.zero_grad()
        outputs = model(images)

        # Compute the loss and its gradients
        #print('outputs model(images) ',outputs)
        loss = loss_fn(outputs, labels)
        print(loss)
        loss.backward()

        # Adjust learning weights
        optimizer.step()
        
        # Gather data and report
        running_loss += loss.item()
        if i % 100 == 99:
            last_loss = running_loss / 100 # loss per batch


    return last_loss           



epoch_number = 10
# Make sure gradient tracking is on, and do a pass over the data
model.train()
avg_loss = train_one_epoch(epoch_number)
print(avg_loss)
        
        
        
        
