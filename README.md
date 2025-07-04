# Hazardous_Object_Detection
A model to detect hazardous objects and guide visualy impaired
The zip folder consists of 3 directories
1)detection_model :
Contains codes for client -server system that uses detection model to guide the user in correct and safe direction .
2)model_training :
Contains the training information for the model .
3)simulation :
Contains the codes for a simulation that demonstrates the working of this system .

The detection_model folder consists of a 3 files:
1) best.pt :
It is the model that gave the best evaluation metrics in the training of YOLOv8 .
2)server.py :
It is the python script that runs on the server . The server  device must have a camera for this to run .
3)client.py :
It is the python script that runs on the client . The client must know the IP address of the sever .

How to run client server system :
If you want to run client and server on the same laptop or PC :  
1) Open 2 terminals
2)Enter detection_model directory in both terminals .
3)Run server.py on the first terminal . The port used is 12345 . If the port is occupied the port must first be freed . If server doesnt show any port error , it means server is listening for requests and ready to service clients .
4)Run client.py on the second terminal . The server should now start a video window and maintain information and send to the client and the client will start a new window to show the instructions sent by the server .
5) Ensure that volume is sufficient enough to listen to instructions sent by server .

If you want to run client and server on 2 different laptops or PC  :
1)Open a terminal on each device
2)Enter the detection_model directory in both the terminals .
3)In the PC you want to use as client , modify the line 15 of the ‘client.py’
server_ip = '127.0.0.1'
instead of ‘127.0.0.1’ replace with the ip address of the server .
4)Run server.py on the server terminal . The port used is 12345 . If the port is occupied the port must first be freed . If server doesnt show any port error , it means server is listening for requests and ready to service clients .
5)Run client.py on the client terminal . The server should now start a video window and maintain information and send to the client and the client will start a new window to show the instructions sent by the server .
6) Ensure that volume is sufficient enough to listen to instructions sent by server .

How to run the simulation :
Navigate to the simulation directory and run simulation.py .


How to see the model training information :
Enter the model_training directory
It has the following files with the given information :
1) evaluation_comparison : Evaluation metrics of custom trained YOLOv8 compared with evaluation metrics of pretrained YOLOv8 from ultralyitcs .


2) training_result : Contains evaluation metrics for each epoch .

3) yolov8n.onnx : An onnx file of the YOLOv8 architecture used . This file is not needed to be opened , it is just an input to the plot_model_architecture.py

4) plot_model_architecture.py : Run this file to view the architecture of YOLOv8 used for training the model .

5) train_model.py : Contains the code for the training the model . This code needs not be run unless you want to train a model . The code also has the code to download the required dataset so this code can be run even if the dataset is not already downloaded .



