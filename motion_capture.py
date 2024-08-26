import cv2
import time
from datetime import datetime
from cvzone.PoseModule import PoseDetector
from shoulder_press import shoulder_press





class Mocap():
    def __init__(self):
        self.lm_exercise_map = {
            "shoulder press": {
                "L shoulder": 11, 
                "R shoulder": 12, 
                "L elbow" : 13, 
                "R elbow": 14, 
                "L wrist": 15,
                "R wrist": 16
            }, 
            #add more to this
        }

        self.max_height = -99999 
        #self.expected_shoulder_height_left = None #11
        #self.expected_shoulder_height_right = None #12

    def run_mocap(self, exercise_name):
        #get the pertinent landmarks
        exercise_lms = list(self.lm_exercise_map.get(exercise_name, None).values())
        landmark_coords = {id: [] for id in exercise_lms}
        #print(landmark_coords)
        
        #Initialize the webcam (0 is the default camera)
        cap = cv2.VideoCapture(0)

        #Initialize the PoseDetector
        detector = PoseDetector()
        posList = []

        #Get the start time
        start_time = time.time()
        frame_num = 0
        #Loop until 10 seconds have passed
        while True:
            success, img = cap.read()
            if not success:
                break  # Exit the loop if the frame was not captured
            
            frame_num += 1
            #Perform pose estimation
            img = detector.findPose(img)
            lmList, bboxInfo = detector.findPosition(img)
            
            #If pose information is found, store it
            if bboxInfo:
                lmString = f"{frame_num}\n"
                for lm in lmList:
                    img_height = img.shape[0]
                    if lm[0] in exercise_lms:
                        ycoord = img_height - lm[2]
                        #if not self.expected_shoulder_height_left and lm[0] == 11:
                        #    self.expected_shoulder_height_left = ycoord
                        #if not self.expected_shoulder_height_right and lm[0] == 12:
                        #    self.expected_shoulder_height_right = ycoord
                        lmString += f'landmark #{lm[0]}: ({lm[1]}, {ycoord}, {lm[3]})\n'
                        if lm[0] in [13, 14] and (ycoord > self.max_height): 
                            #update the new highest point for elbows only
                            self.max_height = ycoord
                        landmark_coords.get(lm[0]).append((lm[1], img_height - lm[2], lm[3])) #x, y, z
                posList.append(lmString)

            #Show the live video feed with pose estimation
            cv2.imshow("Image", img)
            
            #Break the loop if 10 seconds have passed
            if time.time() - start_time > 10:
                break
            
            #Close the video feed if the user presses the 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        #Save the captured landmarks to a file
        with open("AnimationFile.txt", 'w') as f:
            time_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            f.write(f"RUN COMPLETE ON {time_stamp}\n")
            f.writelines(["%s\n" % item for item in posList])

        #Release the video capture object and close OpenCV windows
        cap.release()
        cv2.destroyAllWindows()

        return landmark_coords


if __name__ == '__main__':
    motion_capture = Mocap()
    motion_cap_data = motion_capture.run_mocap("shoulder press")
    sp = shoulder_press(motion_cap_data, motion_capture.max_height)
                        #motion_capture.expected_shoulder_height_left, 
                        #motion_capture.expected_shoulder_height_right)
    sp.graph_data()
    sp.get_position_data(verbose= False)
    sp.imprint_data()
    sp.analyze_data()
    
