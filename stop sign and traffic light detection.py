import numpy as np
import cv2
import socket


class ObjectDetection():
    def __init__(self):
        self.red_light = False
        self.green_light = False
        self.yellow_light = False

    def detect(self, cascade_classifier, gray_image, image):

        # y camera coordinate of the target point 'P'
        v = 0

        # minimum value to proceed traffic light state validation
        threshold = 150

        # detection
        cascade_obj = cascade_classifier.detectMultiScale(
            gray_image,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        # draw a rectangle around the objects
        for (x_pos, y_pos, width, height) in cascade_obj:
            cv2.rectangle(image, (x_pos + 5, y_pos + 5), (x_pos + width - 5, y_pos + height - 5), (255, 255, 255), 2)
            v = y_pos + height - 5
            # print(x_pos+5, y_pos+5, x_pos+width-5, y_pos+height-5, width, height)

            # stop sign
            if width / height == 1:
                cv2.putText(image, 'STOP', (x_pos, y_pos - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # traffic lights
            else:
                roi = gray_image[y_pos + 10:y_pos + height - 10, x_pos + 10:x_pos + width - 10]
                mask = cv2.GaussianBlur(roi, (25, 25), 0)
                (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(mask)

                # check if light is on
                if maxVal - minVal > threshold:
                    cv2.circle(roi, maxLoc, 5, (255, 0, 0), 2)

                    # Red light
                    if 1.0 / 8 * (height - 30) < maxLoc[1] < 4.0 / 8 * (height - 30):
                        cv2.putText(image, 'Red', (x_pos + 5, y_pos - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                        self.red_light = True

                    # Green light
                    elif 5.5 / 8 * (height - 30) < maxLoc[1] < height - 30:
                        cv2.putText(image, 'Green', (x_pos + 5, y_pos - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0),
                                    2)
                        self.green_light = True

                        # yellow light
                        # elif 4.0/8*(height-30) < maxLoc[1] < 5.5/8*(height-30):
                        #    cv2.putText(image, 'Yellow', (x_pos+5, y_pos - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                        #    self.yellow_light = True
        return v



class VideoStreamingTest():

    def __init__(self):

        self.server_socket = socket.socket()
        self.server_socket1 = socket.socket()
        self.server_socket.bind(('192.168.1.11', 8000))
        self.server_socket1.bind(('192.168.1.11', 8001))
        self.server_socket.listen(0)
        self.server_socket1.listen(0)
        self.connection, self.client_address = self.server_socket.accept()
        self.connection1,	 self.client_address1 = self.server_socket1.accept()
        self.connection = self.connection.makefile('rb')

        self.streaming()
        # print "abc"
        
    def streaming(self):
        try:

            obj_detection = ObjectDetection()
            stop_cascade = cv2.CascadeClassifier('cascade_models/stop_sign.xml')
            light_cascade = cv2.CascadeClassifier('cascade_models/traffic_light.xml')
            print "Connection from: ", self.client_address
            print "Streaming..."
            print "Press 'q' to exit"

            stream_bytes = ' '
            while True:
                stream_bytes += self.connection.read(1024)
                first = stream_bytes.find('\xff\xd8')
                last = stream_bytes.find('\xff\xd9')
                if first != -1 and last != -1:
                    jpg = stream_bytes[first:last + 2]
                    stream_bytes = stream_bytes[last + 2:]
                    #image = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.CV_LOAD_IMAGE_GRAYSCALE)
                    #image = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    gray = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
                    image = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    half_gray = gray[120:240, :]

                    v_param1 = obj_detection.detect(stop_cascade, gray, image)
                    v_param2 = obj_detection.detect(light_cascade, gray, image)

                    if v_param1 > 0:
                        self.connection1.send("stop")    
                    # else:
                    #     self.connection1.send()
                        
                    cv2.imshow('image', image)
                    

                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
        finally:
            self.connection.close()
            self.server_socket.close()

if __name__ == '__main__':
    VideoStreamingTest()
