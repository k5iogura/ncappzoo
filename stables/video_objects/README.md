# NCS Asynchronous features

## Differences btn Video and Camera prediction  
***Prediction from Video stream file***  
opencv returns all frames from Video stream.  
Therefore NCS must predict all frames.  

***Prediction from Camera stream***  
opencv returns snapshot when read() method was called.  
Therefore NCS can skip frames during prediction.  

***Concluson***  
- Skip frames of Video stream during prediction.  
- Calculate skip count from prediction time of NCS.  
If prediction FPS was 10FPS then skip 2frames from Video or Camera stream because standard of "real-time" is about 33FPS.  
- Calcuration Example:  
SkipFrames = (Stream_FPS - Prediction_FPS) / Prediction_FPS  
ex.  
Video Frame Rate:= 33 FPS  
Prediction Rate := 10 FPS  
Skip 2.3Frames/Prediction    
- How to skip frames
```
pre_res = None
skip    = 0
while:
    if skip++ < 2:
      if pre_res: overlay( pre_res, img = read() )
      show_image( img )
      continue
    skip = 0
    pre_res = cur_res = infer ( img = read() )
    overlay( img, cur_res )
    show_image( img ) 
```
see bellow two samples,
```
// example.1
for skip++ < 2:
      start = time.time()
      img = read()
      loading = time.time() - start
      
      start = time.time()
      LoadTensor( img )
      initation = time.time() - start
      
      start = time.time()
      GetResultNCS()
      getResult   = time.time()
```
```
// example.2 with sleeping 80 msec
for skip++ < 2:
      start = time.time()
      img = read()
      loading = time.time() - start
      
      start = time.time()
      LoadTensor( img )
      initation = time.time() - start
      
      time.sleep( 0.80 )  // <- sleeping 80msec
      
      start = time.time()
      GetResultNCS()
      getResult   = time.time()
```
Result of 2 samples bellow,
```
// console example.1
loading/initiation/getResult=0.002346	0.026716	0.095926
loading/initiation/getResult=0.007289	0.019355	0.098965
```
**Example.1** seems like that GetResult needs **96~99 msec** with prediction.  
```
// console example.2
loading/initiation/getResult=0.020041	0.026221	0.011638
loading/initiation/getResult=0.003283	0.029655	0.013215
```
**Example.2** seems like that GetResult needs **12~13 msec** with prediction **in spite of sleeping 80msec too!**. Therefore I **can insert something proccess** inside of initiate and getResult without extra elapsed time and something proccess should be loading images.  

- Ideas  
Above 2 results mean that data load into NCS and network forwarding in NCS are asyncronous controllable. In a example bellow loading image and show image are asynchronous.  
```
// Synchronous image loading and prediction
    image_source = $(load image from image source)
    initiation_NCS( image_source )
    result_pre = result = getresult_NCS()
    overlay_result_on_image( result_pre, image_source )
    imshow( image_source )
```
```  
// Asynchronous image loading and network forwarding
  for i in 3:
    image_source[i] = $(load image from image source)
    if i is 0:
      initiation_NCS( image_source[0] )
      
  result_pre = None
  for i in 3:
    if i is 0:
      result_pre = result = getresult_NCS()
    overlay_result_on_image( result_pre, image_source[i] )
    imshow( image_source[i] )
```  
2 result FPS bellow,  
actual video resolution: 960.0 x 540.0
```
// synchronous prediction
Frames per Second: 7.2
```
```
// asynchronous prediction
Frames per Second: 18.7  
```

***Notice Exception***  
Prevent occurrence of exception about all api call in spite of device open or close.  
In many stuation type of exception is "(mvncStatus.ERROR: -2,)", but I can not know reason of exception from this message.  

Always should use try and except mechanism of python at calling NCS api if not so, you will amaze a long time.  


