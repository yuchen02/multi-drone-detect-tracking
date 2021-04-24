# multi-drone-detect-tracking

-   The detection end uses the current PP-YOLO model with a good balance of speed and accuracy, and improves the detection accuracy to 98.96% through improvements such as data enhancement and Mish activation function; in order to enable the system to detect in real time on platforms with limited computing capabilities, ResNet18 is used The backbone network speeds up, and the corresponding detection accuracy is 88.65%.
-   The tracking end adopts the DeepSORT algorithm to make the tracking more robust and reduce the tracking loss caused by occlusion and other reasons.
-   Pyqt is used for interface design, showing the effects of single image detection, video detection and tracking, and real-time camera tracking, realizing real-time tracking of 4 UAVs or more within 500 meters. The minimum detection size in the video test is 7×9 pixels.

## Main interface

![Snipaste_2021-04-24_07-34-04](imgs/Snipaste_2021-04-24_07-34-04.png)

## Result

![YuPigXmCr1](imgs/YuPigXmCr1.gif)

![JW3IWUz4Hx](imgs/JW3IWUz4Hx.gif)

## Image

![0001](output/0001.png)

![0002](output/0002.png)

![mydata-000002](output/mydata-000002.jpg)

![mydata-000200](output/mydata-000200.jpg)

![](output/000051.jpg)



The project is still in progress, and the code will be released later.

## About me

If you have any questions, please contact me via email [1765904103@qq.com].

