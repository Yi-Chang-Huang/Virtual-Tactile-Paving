import signal
from libs.darknet.yolo_device import YoloDevice
from libs.darknet import utils
from libs.deep_sort.wrapper import DeepSortWrapper
from libs.deep_sort.wrapper import DEEP_SORT_ENCODER_MODEL_PATH_PERSON

# Note: this program can only run on Linux
if __name__ == '__main__':
    # Define the variables
    yolo = YoloDevice(
        video_url="rtsp://192.168.10.100/video1.sdp",
        gpu=False,
        gpu_id=0,
        display_message=True,
        config_file=utils.CONFIG_FILE_YOLO_V4,
        names_file=utils.NAMES_COCO,
        thresh=0.25,
        weights_file=utils.WEIGHTS_YOLO_V4_COCO,
        output_dir="./output",
        #use_polygon=False,
        #vertex=[(0, 0), (0, 216), (384, 261), (384, 0)],
        target_classes=["person"],
        draw_bbox=True,
        draw_polygon=True,
    )

    run = True


    def on_data(frame_id, img, bboxes, img_path):
        """
        When objects are detected, this function will be called.

        Args:
            frame_id:
                the frame number
            img:
                a numpy array which stored the frame
            bboxes:
                A list contains several `libs.darknet.yolo_device.ExtendedBoundingBox` object. The list contains
                all detected objects in a single frame.
            img_path:
                The path of the stored frame. If `output_dir` is None, this parameter will be None too.
        """
        print("==========")
        left_x=430
        left_y=490
        right_x=480
        right_y=480
        matrix=[[]]
        for det in bboxes:
            # You can push these variables to IoTtalk sever
            class_name = det.get_class_name()
            confidence = det.get_confidence()
            center_x, center_y = det.get_center()
            
            if det.get_obj_id()!=None:
                id=det.get_obj_id()
                id=int(id)
                if (center_y-left_y)/(center_x-left_x)>0.5:    #人在格子右方
                    print("靠左")
                    if id>len(matrix)-1:
                        for j in range(id-len(matrix)+2):
                            matrix.append([])
                    matrix[id]=[center_x,center_y]
                elif (center_y-right_y)/(center_x-right_x)<0.5:   #人在格子左方
                    print("靠右")
                    if id>len(matrix)-1:
                        for j in range(id-len(matrix)+2):
                            matrix.append([])
                    matrix[id]=[center_x,center_y]
                else:                                   #人在格子內
                    if id>len(matrix)-1:
                        for j in range(id-len(matrix)+2):
                            matrix.append([])
                    if not matrix[id]:
                        matrix.insert(id,[center_x,center_y])#新的id
                    elif(matrix[id][1]-center_y)/(matrix[id][0]-center_x)<0.4|(matrix[id][1]-center_y)/(matrix[id][0]-center_x)>0.6:  #判斷斜率是否過大
                        print("向右")
                        matrix[id]=[center_x,center_y]
                    else:
                        print("向左")
                        matrix[id]=[center_x,center_y]

            print(class_name, confidence, center_x, center_y, det.get_class_id(), det.get_obj_id())
        print("==========")


    # `yolo.set_listener()` must be before `yolo.start()`
    yolo.set_listener(on_data)
    yolo.enable_tracking(True)
    yolo.add_deep_sort_tracker("person", DeepSortWrapper(encoder_model_path=DEEP_SORT_ENCODER_MODEL_PATH_PERSON))
    yolo.start()


    def signal_handler(sig, frame):
        """
        A simple handler to handle ctrl + c
        """
        global run
        run = False
        # Use `yolo.stop()` to stop the darknet program
        yolo.stop()
        # Use `yolo.join()` to wait for darknet closing
        yolo.join()


    print("press ctrl + c to exit.")
    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()

    while run:
        pass

    print("Exit.")
