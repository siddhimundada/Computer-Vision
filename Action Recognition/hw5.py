# -*- coding: utf-8 -*-
"""Mundada_Siddhi_112684006_hw5.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1WKZ0oHeQjypYe-p4wXGgAnjdTntB0hkP

# Action Recognition @ UCF101  
**Due date: 11:59 pm on Nov. 19, 2019 (Tuesday)**

## Description
---
In this homework, you will be doing action recognition using Recurrent Neural Network (RNN), (Long-Short Term Memory) LSTM in particular. You will be given a dataset called UCF101, which consists of 101 different actions/classes and for each action, there will be 145 samples. We tagged each sample into either training or testing. Each sample is supposed to be a short video, but we sampled 25 frames from each videos to reduce the amount of data. Consequently, a training sample is an image tuple that forms a 3D volume with one dimension encoding *temporal correlation* between frames and a label indicating what action it is.

To tackle this problem, we aim to build a neural network that can not only capture spatial information of each frame but also temporal information between frames. Fortunately, you don't have to do this on your own. RNN — a type of neural network designed to deal with time-series data — is right here for you to use. In particular, you will be using LSTM for this task.

Instead of training an end-to-end neural network from scratch whose computation is prohibitively expensive, we divide this into two steps: feature extraction and modelling. Below are the things you need to implement for this homework:
- **{35 pts} Feature extraction**. Use any of the [pre-trained models](https://pytorch.org/docs/stable/torchvision/models.html) to extract features from each frame. Specifically, we recommend not to use the activations of the last layer as the features tend to be task specific towards the end of the network. 
    **hints**: 
    - A good starting point would be to use a pre-trained VGG16 network, we suggest first fully connected layer `torchvision.models.vgg16` (4096 dim) as features of each video frame. This will result into a 4096x25 matrix for each video. 
    - Normalize your images using `torchvision.transforms` 
    ```
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    prep = transforms.Compose([ transforms.ToTensor(), normalize ])
    prep(img)
    The mean and std. mentioned above is specific to Imagenet data
    
    ```
    More details of image preprocessing in PyTorch can be found at http://pytorch.org/tutorials/beginner/data_loading_tutorial.html
    
- **{35 pts} Modelling**. With the extracted features, build an LSTM network which takes a **dx25** sample as input (where **d** is the dimension of the extracted feature for each frame), and outputs the action label of that sample.
- **{20 pts} Evaluation**. After training your network, you need to evaluate your model with the testing data by computing the prediction accuracy **(5 points)**. The baseline test accuracy for this data is 75%, and **10 points** out of 20 is for achieving test accuracy greater than the baseline. Moreover, you need to compare **(5 points)** the result of your network with that of support vector machine (SVM) (stacking the **dx25** feature matrix to a long vector and train a SVM).
- **{10 pts} Report**. Details regarding the report can be found in the submission section below.

Notice that the size of the raw images is 256x340, whereas your pre-trained model might take **nxn** images as inputs. To solve this problem, instead of resizing the images which unfavorably changes the spatial ratio, we take a better solution: Cropping five **nxn** images, one at the image center and four at the corners and compute the **d**-dim features for each of them, and average these five **d**-dim feature to get a final feature representation for the raw image.
For example, VGG takes 224x224 images as inputs, so we take the five 224x224 croppings of the image, compute 4096-dim VGG features for each of them, and then take the mean of these five 4096-dim vectors to be the representation of the image.

In order to save you computational time, you need to do the classification task only for **the first 25** classes of the whole dataset. The same applies to those who have access to GPUs. **Bonus 10 points for running and reporting on the entire 101 classes.**


## Dataset
Download **dataset** at [UCF101](http://vision.cs.stonybrook.edu/~yangwang/public/UCF101_images.tar)(Image data for each video) and the **annos folder** which has the video labels and the label to class name mapping is included in the assignment folder uploaded. 


UCF101 dataset contains 101 actions and 13,320 videos in total.  

+ `annos/actions.txt`  
  + lists all the actions (`ApplyEyeMakeup`, .., `YoYo`)   
  
+ `annots/videos_labels_subsets.txt`  
  + lists all the videos (`v_000001`, .., `v_013320`)  
  + labels (`1`, .., `101`)  
  + subsets (`1` for train, `2` for test)  

+ `images/`  
  + each folder represents a video
  + the video/folder name to class mapping can be found using `annots/videos_labels_subsets.txt`, for e.g. `v_000001` belongs to class 1 i.e. `ApplyEyeMakeup`
  + each video folder contains 25 frames  



## Some Tutorials
- Good materials for understanding RNN and LSTM
    - http://blog.echen.me
    - http://karpathy.github.io/2015/05/21/rnn-effectiveness/
    - http://colah.github.io/posts/2015-08-Understanding-LSTMs/
- Implementing RNN and LSTM with PyTorch
    - [LSTM with PyTorch](http://pytorch.org/tutorials/beginner/nlp/sequence_models_tutorial.html#sphx-glr-beginner-nlp-sequence-models-tutorial-py)
    - [RNN with PyTorch](http://pytorch.org/tutorials/intermediate/char_rnn_classification_tutorial.html)
"""

# import packages here
import cv2
import numpy as np
import matplotlib.pyplot as plt
import glob
import random 
import time
import torch
import torchvision
import torchvision.transforms as transforms
from torch.autograd import Variable
import torch.nn as nn
import torch.nn.functional as F
from skimage.transform import rotate
import numpy as np
import glob
from torchvision.transforms import *
import pickle

from google.colab import drive
drive.mount('/content/gdrive')

cd '/content/gdrive/My Drive/CSE527-HW5-Fall19'

#!wget 'http://vision.cs.stonybrook.edu/~yangwang/public/UCF101_images.tar'

#!tar -xkf 'UCF101_images.tar' 2>/dev/null

"""---
---
## **Problem 1.** Feature extraction
"""

cd 'annos'

# \*write your codes for feature extraction (You can use multiple cells, this is just a place holder)
Names=[]
with open ("videos_labels_subsets.txt", "r") as myfile:
    data=myfile.readlines()
    Names = [i.strip().split('\t') for i in data[0:3360]]

len(Names)

import random 
random.shuffle(Names)

import operator

folder=list( map(operator.itemgetter(0), Names ))
l2=list( map(operator.itemgetter(1), Names ))
label = [int(i) for i in l2]
l3=list( map(operator.itemgetter(2), Names ))
subset = [int(i) for i in l3]

train_folder=[]
train_label=[]
test_folder=[]
test_label=[]
for i in range(0,3360):
  if(subset[i]==1):
    train_folder.append(folder[i])
    train_label.append(label[i])
  else:
    test_folder.append(folder[i])
    test_label.append(label[i])

train_folder[0]

import torchvision.models as models
import torch.nn as nn

vgg = models.vgg19(pretrained=True)
features = list(vgg.classifier.children())[0]
vgg.classifier = nn.Sequential(features)
print(vgg.classifier)

cd '/content/gdrive/My Drive/CSE527-HW5-Fall19/'

vgg.cuda()
normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
prep = transforms.Compose([ transforms.ToTensor(), normalize ])
torch.no_grad()
f=[]
labels_traindata=[]
n=0
for i in train_folder:
  p="/content/gdrive/My Drive/CSE527-HW5-Fall19/images/"+i+"/*"
  path=[n for n in glob.glob(p)]
  with torch.no_grad():
    for image in path:
      image=cv2.imread(image)
      i1=image[0:224,0:224]
      i2=image[32:256,0:224]
      i3=image[0:224,116:340]
      i4=image[32:256,116:340]
      i5=image[16:240,58:282]
      
      i1=prep(i1)
      i2=prep(i2)
      i3=prep(i3)
      i4=prep(i4)
      i5=prep(i5)

      i1=i1.unsqueeze(0)
      i2=i2.unsqueeze(0)
      i3=i3.unsqueeze(0)
      i4=i4.unsqueeze(0)
      i5=i5.unsqueeze(0)

      i1=i1.cuda()
      i2=i2.cuda()
      i3=i3.cuda()
      i4=i4.cuda()
      i5=i5.cuda()

      f1=vgg(i1)
      f2=vgg(i2)
      f3=vgg(i3)
      f4=vgg(i4)
      f5=vgg(i5)

      mean=(f1+f2+f3+f4+f5)/5
      f.append(mean)

  labels_traindata.append(train_label[n])
  n=n+1

f = [vector.view(-1) for vector in f]

li=[]
for i in range(0,len(f),25):
  feat=f[i:i+25]
  feat1=torch.stack(feat)
  li.append(feat1)

l2=[]
for i in range(0,len(li),8):
  feat=li[i:i+8]
  feat1=torch.stack(feat)
  l2.append(feat1)

l2[0].shape

file = open('train25.pkl','wb')
pickle.dump(l2, file)
file.close()

labels_traindata1=[]
for i in range(0,len(labels_traindata),8):
  feat=np.array(labels_traindata[i:i+8])
  feat1=np.stack(feat)
  labels=feat1.reshape(-1,1)
  l=torch.tensor(labels)
  labels_traindata1.append(l)

labels_traindata1[0].shape

file = open('train_label25.pkl','wb')
pickle.dump(labels_traindata1, file)
file.close()

vgg.cuda()
normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
prep = transforms.Compose([ transforms.ToTensor(), normalize ])
torch.no_grad()
f_test=[]
labels_testdata=[]
n=0
for i in test_folder:
  p="/content/gdrive/My Drive/CSE527-HW5-Fall19/images/"+i+"/*"
  path=[n for n in glob.glob(p)]
  with torch.no_grad():
    for image in path:
      image=cv2.imread(image)
      i1=image[0:224,0:224]
      i2=image[32:256,0:224]
      i3=image[0:224,116:340]
      i4=image[32:256,116:340]
      i5=image[16:240,58:282]
      
      i1=prep(i1)
      i2=prep(i2)
      i3=prep(i3)
      i4=prep(i4)
      i5=prep(i5)

      i1=i1.unsqueeze(0)
      i2=i2.unsqueeze(0)
      i3=i3.unsqueeze(0)
      i4=i4.unsqueeze(0)
      i5=i5.unsqueeze(0)

      i1=i1.cuda()
      i2=i2.cuda()
      i3=i3.cuda()
      i4=i4.cuda()
      i5=i5.cuda()

      f1=vgg(i1)
      f2=vgg(i2)
      f3=vgg(i3)
      f4=vgg(i4)
      f5=vgg(i5)

      mean=(f1+f2+f3+f4+f5)/5
      f_test.append(mean)

  labels_testdata.append(test_label[n])
  n=n+1

f_test = [vector.view(-1) for vector in f_test]

list=[]
for i in range(0,len(f_test),25):
  feat=f_test[i:i+25]
  feat1=torch.stack(feat)
  list.append(feat1)

l2_test=[]
for i in range(0,len(list),8):
  feat=list[i:i+8]
  feat1=torch.stack(feat)
  l2_test.append(feat1)

l2_test[0].shape

file = open('test25.pkl','wb')
pickle.dump(l2_test, file)
file.close()

labels_testdata1=[]
for i in range(0,len(labels_testdata),8):
  #feat1=list(labels_testdata[i:i+8])
  feat1=np.array(labels_testdata[i:i+8])
  feat2=np.stack(feat1)
  labels1=feat2.reshape(-1,1)
  l5=torch.tensor(labels1)
  labels_testdata1.append(l5)

labels_testdata1[0].shape

file = open('test_label25.pkl','wb')
pickle.dump(labels_testdata1, file)
file.close()

"""***
***
## **Problem 2.** Modelling

* ##### **Print the size of your training and test data**
"""

file = open('train25.pkl', 'rb')
data1 = pickle.load(file)

file = open('train_label25.pkl', 'rb')
labels_train = pickle.load(file)

file = open('test25.pkl', 'rb')
test = pickle.load(file)

file = open('test_label25.pkl', 'rb')
label_test = pickle.load(file)

# Don't hardcode the shape of train and test data
print('Shape of training data is :', data1[0].shape)
print('Shape of test/validation data is :', test[0].shape)

# \*write your codes for modelling using the extracted feature (You can use multiple cells, this is just a place holder)
d1=[]
for i in range(len(data1)):
  #shape=list(data1[i].size())###
  a,b,c=data1[i].shape
  #d=data1[i].view(shape[1],shape[0],shape[2])###
  d=data1[i].view(b,a,c)
  d1.append(d)

label=[]
for i in range(len(labels_train)):
  labels=labels_train[i].view(-1).long()
  labels=labels-torch.ones(labels.size()).long()###
  label.append(labels)
label[0].shape

test1=[]
for i in range(len(test)):
  a,b,c=test[i].shape
  d=test[i].view(b,a,c)
  test1.append(d)
test1[0].shape

label1=[]
for i in range(len(label_test)):
  #shape=list(labels_train[i].size())
  labels=label_test[i].view(-1).long()
  labels=labels-torch.ones(labels.size()).long()###
  label1.append(labels)

len(label1)

class LSTM(nn.Module):    
    def __init__(self, hidden_dimension, classes):
        super(LSTM, self).__init__()
        self.hidden_dimension = hidden_dimension
        self.lstm = nn.LSTM(4096, hidden_dimension)
        self.hiddenlabel = nn.Linear(hidden_dimension, classes)   

    def forward(self, input_features):
        batch_size = input_features.size()[1]
        lstm_out, last_op = self.lstm(input_features)
        out = self.hiddenlabel(last_op[0].view(batch_size,-1))
        output_labels = F.log_softmax(out, dim=-1)
        return output_labels

import torch.optim as optim
Hidden_dim = 256
Num_classes =25

model1 = LSTM(Hidden_dim,Num_classes)
print(model1)
l_func = nn.NLLLoss()
opt = optim.SGD(model1.parameters(), lr=0.01)

#Training
initial_loss = 0
for e in range(35):
    l_count = 0.0
    for i in range(len(data1)):
        features = d1[i]
        labels = label[i]
        model1.zero_grad()
        outputs = model1(features)
        loss = l_func(outputs, labels)
        loss.backward()
        opt.step()
        l_count += loss.item()
    print('%d Loss: %.3f' %(e+1, l_count/len(data1)))

with torch.no_grad():
        original = 0
        total = 0
        for i in range(len(data1)):
            features = d1[i]
            labels = label[i]
            outputs = model_1(features)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            original += (predicted == labels).sum().item()
accuracy = (original/total)*100
print("Accuracy on the training dataset is:", accuracy)

with torch.no_grad():
        original = 0
        total = 0
        for i in range(len(test)):
            features = test1[i]
            labels = label1[i]
            outputs = model_1(features)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            original += (predicted == labels).sum().item()
accuracy = (original/total)*100
print("Accuracy on the test dataset is:", accuracy)

class LSTM(nn.Module):    
    def __init__(self, hidden_dimension, classes):
        super(LSTM, self).__init__()
        self.hidden_dimension = hidden_dimension
        self.lstm = nn.LSTM(4096, hidden_dimension)
        self.hiddenlabel = nn.Linear(hidden_dimension, classes)   

    def forward(self, input_features):
        batch_size = input_features.size()[1]
        lstm_out, last_op = self.lstm(input_features)
        out = self.hiddenlabel(last_op[0].view(batch_size,-1))
        output_labels = F.log_softmax(out, dim=-1)
        return output_labels

import torch.optim as optim
Hidden_dim = 512
Num_classes =25

model2 = LSTM(Hidden_dim,Num_classes)
print(model1)
l_func = nn.NLLLoss()
opt = optim.SGD(model2.parameters(), lr=0.01)

#Training
initial_loss = 0
for e in range(35):
    l_count = 0.0
    for i in range(len(data1)):
        features = d1[i]
        labels = label[i]
        model2.zero_grad()
        outputs = model2(features)
        loss = l_func(outputs, labels)
        loss.backward()
        opt.step()
        l_count += loss.item()
    print('%d Loss: %.3f' %(e+1, l_count/len(data1)))

with torch.no_grad():
        correct = 0
        total = 0
        for i in range(len(data1)):
            feats = d1[i]
            labels = label[i]
            outputs = model_2(feats)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
acc1 = (correct/total)*100
print("Accuracy on the training dataset is:", acc1,'%')

with torch.no_grad():
        correct = 0
        total = 0
        for i in range(len(test)):
            feats = test1[i]
            labels = label1[i]
            outputs = model_2(feats)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
acc2 = (correct/total)*100
print("Accuracy on the test dataset is:", acc2,'%')

"""---
---
## **Problem 3.** Evaluation
"""

file = open('train_label25.pkl', 'rb')
labels_train = pickle.load(file)

file = open('train25.pkl', 'rb')
data1 = pickle.load(file)

file = open('test25.pkl', 'rb')
test = pickle.load(file)

file = open('test_label25.pkl', 'rb')
label_test = pickle.load(file)

d1=[]
for i in range(len(data1)):
  d2 = data1[i]
  for j in range(d2.size()[0]):
    d1.append(d2[j,:].view(-1))

d1 = torch.stack(d1)
d1 = d1.numpy()
d1.shape

labels_train[0].shape

label_train=[]
for i in range(len(labels_train)):
  labels=labels_train[i].view(-1).long()
  labels=labels-torch.ones(labels.size()).long()###
  label_train.append(labels)
label_train[0].shape

label_tensor = []
for i in range(len(label_train)):
  label_tensor.append(label_train[i].view(-1))
label_tensor = torch.cat(label_tensor).numpy()
label_tensor.shape

from sklearn.metrics import accuracy_score 
from sklearn.svm import LinearSVC
from sklearn.multiclass import OneVsRestClassifier
from sklearn.metrics import accuracy_score

clf =  LinearSVC(random_state=None ,tol=1e-4, loss='squared_hinge', C=0.012)
clf.fit(d1, label_tensor)

d1_test=[]
for i in range(len(test)):
  d2 = test[i]
  for j in range(d2.size()[0]):
    d1_test.append(d2[j,:].view(-1))

d1_test = torch.stack(d1_test)
d1_test = d1_test.numpy()
d1_test.shape

label_test1=[]
for i in range(len(label_test)):
  #shape=list(labels_train[i].size())
  labels=label_test[i].view(-1).long()
  #label.append(label1[i])
  labels=labels-torch.ones(labels.size()).long()
  label_test1.append(labels)

label_tensor1 = []
for i in range(len(label_test1)):
  label_tensor1.append(label_test1[i].view(-1))
label_tensor1 = torch.cat(label_tensor1).numpy()
label_tensor1.shape

labels_predicted1 = clf.predict(d1)
accuracy = accuracy_score(label_tensor, labels_predicted1)
print("The predicted accuracy is {:.2f}%".format(accuracy*100))

labels_predicted = clf.predict(d1_test)
accuracy1 = accuracy_score(label_tensor1, labels_predicted)
print("The predicted accuracy is {:.2f}%".format(accuracy1*100))

# \*write your codes for evaluation (You can use multiple cells, this is just a place holder)

"""* ##### **Print the train and test accuracy of your model**"""

# Don't hardcode the train and test accuracy
print('Training accuracy of LSTM model1 is  :',99.79,'%')
print('Test accuracy of LSTM model1 is :' ,77.49,'%' )

# Don't hardcode the train and test accuracy
print('Training accuracy of LSTM model1 is  :',acc1,'%')
print('Test accuracy of LSTM model1 is :' ,acc2,'%' )

"""* ##### **Print the train and test and test accuracy of SVM**"""

# Don't hardcode the train and test accuracy
print('Training accuracy is %2.3f :', accuracy*100,'%')
print('Test accuracy is %2.3f :' ,accuracy1*100,'%')

"""## **Problem 4.** Report

## **Bonus**

* ##### **Print the size of your training and test data**
"""

# Don't hardcode the shape of train and test data
print('Shape of training data is :', )
print('Shape of test/validation data is :', )

"""* ##### **Modelling and evaluation**"""

#Write your code for modelling and evaluation

"""## Submission
---
**Runnable source code in ipynb file and a pdf report are required**.

The report should be of 3 to 4 pages describing what you have done and learned in this homework and report performance of your model. If you have tried multiple methods, please compare your results. If you are using any external code, please cite it in your report. Note that this homework is designed to help you explore and get familiar with the techniques. The final grading will be largely based on your prediction accuracy and the different methods you tried (different architectures and parameters).

Please indicate clearly in your report what model you have tried, what techniques you applied to improve the performance and report their accuracies. The report should be concise and include the highlights of your efforts.
The naming convention for report is **Surname_Givenname_SBUID_report*.pdf**

When submitting your .zip file through blackboard, please
-- name your .zip file as **Surname_Givenname_SBUID_hw*.zip**.

This zip file should include:
```
Surname_Givenname_SBUID_hw*
        |---Surname_Givenname_SBUID_hw*.ipynb
        |---Surname_Givenname_SBUID_hw*.pdf
        |---Surname_Givenname_SBUID_report*.pdf
```

For instance, student Michael Jordan should submit a zip file named "Jordan_Michael_111134567_hw5.zip" for homework5 in this structure:
```
Jordan_Michael_111134567_hw5
        |---Jordan_Michael_111134567_hw5.ipynb
        |---Jordan_Michael_111134567_hw5.pdf
        |---Jordan_Michael_111134567_report*.pdf
```

The **Surname_Givenname_SBUID_hw*.pdf** should include a **google shared link**. To generate the **google shared link**, first create a folder named **Surname_Givenname_SBUID_hw*** in your Google Drive with your Stony Brook account. 

Then right click this folder, click ***Get shareable link***, in the People textfield, enter two TA's emails: ***bo.cao.1@stonybrook.edu*** and ***sayontan.ghosh@stonybrook.edu***. Make sure that TAs who have the link **can edit**, ***not just*** **can view**, and also **uncheck** the **Notify people** box.

Colab has a good feature of version control, you should take advantage of this to save your work properly. However, the timestamp of the submission made in blackboard is the only one that we consider for grading. To be more specific, we will only grade the version of your code right before the timestamp of the submission made in blackboard. 

You are encouraged to post and answer questions on Piazza. Based on the amount of email that we have received in past years, there might be dealys in replying to personal emails. Please ask questions on Piazza and send emails only for personal issues.

Be aware that your code will undergo plagiarism check both vertically and horizontally. Please do your own work.
"""