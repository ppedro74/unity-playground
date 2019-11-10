import cv2
import time
 
if __name__ == '__main__' :
    video = cv2.VideoCapture(0);
     
    # Find OpenCV version
    (major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')
     
    # With webcam get(CV_CAP_PROP_FPS) does not work.
    # Let's see for ourselves.
     
    if int(major_ver)  < 3 :
        fps = video.get(cv2.cv.CV_CAP_PROP_FPS)
        print ("Frames per second using video.get(cv2.cv.CV_CAP_PROP_FPS): {0}".format(fps))
    else:
        print ("fps={0} width={1} height={2}".format(video.get(cv2.CAP_PROP_FPS), 
                                                     video.get(cv2.CAP_PROP_FRAME_WIDTH), 
                                                     video.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        
    fps = 15
    #width = 1280
    #height = 720
    width = 800
    height = 600

    print("set {0} {1} {2}".format(video.set(cv2.CAP_PROP_FPS, fps), 
                    video.set(cv2.CAP_PROP_FRAME_WIDTH, width),
                    video.set(cv2.CAP_PROP_FRAME_HEIGHT, height)))

    print ("fps={0} width={1} height={2}".format(video.get(cv2.CAP_PROP_FPS), 
                                                 video.get(cv2.CAP_PROP_FRAME_WIDTH), 
                                                 video.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    num_frames = 120
     
    print ("Capturing {0} frames".format(num_frames))
 
    start = time.time()
     
    for i in range(0, num_frames):
        ret, frame = video.read()
        if ret:
            #cv2.imshow('Frame', frame)
            ret, jpg = cv2.imencode('.jpg', frame)

     
    end = time.time()
 
    seconds = end - start
    print ("Time taken : {0} seconds".format(seconds))
 
    fps  = num_frames / seconds;
    print ("Estimated frames per second : {0}".format(fps))
 
    video.release()

