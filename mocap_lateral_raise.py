import cv2
import time
import os
import subprocess
import copy
import numpy as np
from datetime import datetime
from cvzone.PoseModule import PoseDetector
from bad_form import Bad_form
from frames_to_vid import build_video_from_frames 
import argparse

#consts
unity_exe_path = ".\\Unity Animator Entity\\MotionCapture.exe" #need normpath here
batch_file_path = ".\\run_unity_engine_no_engine.bat"
bad_form_pics_path = ".\\bad-form-bin\\Lateral-raise"
exercise_name = "Lateral raise"

class Lateral_raise_mocap():
    def __init__(self):

        #current analysis coordinates
        self.left_shoulder_coords = None #11
        self.right_shoulder_coords = None #12
        self.left_elbow_coords = None #13 
        self.right_elbow_coords = None #14
        self.left_hip_coords = None #15
        self.right_hip_coords = None #16
        self.offset_Y = None
        self.bad_form_captured = False
        self.lm_exercise_map = { 
            "Lateral raise": {
                "L shoulder": 11, 
                "R shoulder": 12, 
                "L elbow" : 13, 
                "R elbow": 14, 
                "R hip": 23,
                "L hip": 24
            }
        }
        self.bad_form_list = []
        self.bad_form = False
        self.animate_flag = False
        self.delay = 3

    def run_unity_animator(self):
        try:
            subprocess.run([batch_file_path], check= True)
        except Exception as e:
            print(f"Error executing the Unity Motion Capture animation project: {e}")

        try: 
            time.sleep(10.0) #replace this with more flexible way of detecting unity completion
            build_video_from_frames(fps= 30)
        except Exception as e:
            print(f"Error building video from frames in folder: {e}")

    def save_bad_form_snapshot(self, img, reason, resonsibles):
        self.bad_form_captured = True
        if not os.path.exists(bad_form_pics_path):
            os.makedirs(bad_form_pics_path)
        time_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(bad_form_pics_path, f"bad_form_{time_stamp}.png")
        if 'R' in resonsibles:
            og_y_coord_R = (self.right_shoulder_coords[1] - self.offset_Y)*(-1)
            cv2.circle(img, (self.right_shoulder_coords[0], og_y_coord_R), radius=28, color=(0, 0, 255), thickness=2)
        if 'L' in resonsibles:
            og_y_coord_L = (self.left_shoulder_coords[1] - self.offset_Y)*(-1)
            cv2.circle(img, (self.left_shoulder_coords[0], og_y_coord_L), radius=28, color=(0, 0, 255), thickness=2)
        cv2.imwrite(filename, img)
        #create bad form object
        bf = Bad_form(reason= reason, exercise_name= exercise_name, image_file_path= filename)
        self.bad_form_list.append(bf)

    def angle_analysis(self, img):
        #check LEFT and RIGHT side.. 
        if(
        self.left_shoulder_coords and 
        self.right_shoulder_coords and
        self.left_elbow_coords and
        self.right_elbow_coords and
        self.left_hip_coords and
        self.right_hip_coords):
            #right
            a = np.array(self.right_hip_coords)
            b = np.array(self.right_shoulder_coords)
            c = np.array(self.right_elbow_coords)
            #left
            d = np.array(self.left_hip_coords)
            e = np.array(self.left_shoulder_coords)
            f = np.array(self.left_elbow_coords)
            
            radians_R= np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
            radians_L = np.arctan2(f[1]-e[1], f[0]-e[0]) - np.arctan2(d[1]-e[1], d[0]-e[0])
            angle_R, angle_L = np.abs(radians_R*180.0/np.pi), np.abs(radians_L*180.0/np.pi)

            #adjust
            if angle_R > 180.0: 
                angle_R = 360 - angle_R
            if angle_L > 180.0:
                angle_L = 360 - angle_L

            if angle_R >= 140 or angle_L >= 140:
                reason = "" 
                responsibles = []
                if angle_R > 140:
                    reason += "Your right arm extended too high! Try to stop at a straight level.\n"
                    responsibles.append('R')
                if angle_L > 140:
                    reason += "Your left arm extended too high! Try to stop at a straight level.\n"
                    responsibles.append('L')
                if not self.bad_form_captured:
                    self.save_bad_form_snapshot(img, reason, responsibles)
            else:
                self.bad_form_captured = False
        else:
            return(f"Not enough data yet :D")
        
    def fetch_arguments(self) -> tuple:
        parser = argparse.ArgumentParser()
        parser.add_argument("--time", help="define the time that camera will be on")
        parser.add_argument("--a", action="store_true", help= "Include to run the unity animator exe")
        parser.add_argument("--delay", help="define the time before camera starts")
        args = parser.parse_args()
        if not args.time: 
            time  = 10
        else:
            time = int(args.time)
        if not args.a:
            a = False
        else:
            a = True
        if not args.delay:
            delay = 3 #seconds
        else:
            delay = int(args.delay)
        return (time , a, delay)
    
    
    def run_mocap(self):
        ARGS = self.fetch_arguments()
        run_time, self.animate_flag, self.delay = ARGS[0], ARGS[1], ARGS[2]

        #give delay
        time.sleep(self.delay)

        #get the pertinent landmarks
        exercise_lms = list(self.lm_exercise_map.get(exercise_name, None).values())
        landmark_coords = {id: [] for id in exercise_lms}
        #Initialize the webcam (0 is the default camera)
        cap = cv2.VideoCapture(0)

        #Initialize the PoseDetector
        detector = PoseDetector()
        posList = []
        anim_list = []

        #Get the start time
        start_time = time.time()
        frame_num = 0

        while True:
            success, img = cap.read()
            raw_image = copy.deepcopy(img)
            if not success:
                break  # Exit the loop if the frame was not captured
            
            frame_num += 1
            #Perform pose estimation
            img = detector.findPose(img)
            lmList, bboxInfo = detector.findPosition(img)        
            #If pose information is found, store it
            if bboxInfo:
                anim_string = ''
                lmString = f"{frame_num}\n"
                for i in range(0,len(lmList)):
                    lm = lmList[i]
                    anim_string += f'{lm[0]}, {img.shape[0]-lm[1]},{lm[2]},'
                    img_height = img.shape[0]
                    self.offset_Y = img_height
                    if i in exercise_lms:
                        ycoord = img_height - lm[1]
                        match i:
                            case 11:
                                self.left_shoulder_coords = [lm[0], ycoord, lm[2]] #x y z
                            case 12:
                                self.right_shoulder_coords = [lm[0], ycoord, lm[2]] #x y z
                            case 13:
                                self.left_elbow_coords = [lm[0], ycoord, lm[2]] #x y z
                            case 14:
                                self.right_elbow_coords = [lm[0], ycoord, lm[2]] #x y z
                            case 23:
                                self.right_hip_coords = [lm[0], ycoord, lm[2]] #x y z
                            case 24:
                                self.left_hip_coords = [lm[0], ycoord, lm[2]] #x y z
                        self.angle_analysis(raw_image)
                        lmString += f'landmark #{i}: ({lm[0]}, {ycoord}, {lm[2]})\n'
                        landmark_coords.get(i).append((lm[0], img_height - lm[1], lm[2])) #x, y, z
                anim_list.append(anim_string)
                posList.append(lmString)

            #Show the live video feed with pose estimation
            cv2.imshow("Image", img)
            
            if time.time() - start_time > run_time:
                break
            
            #Close the video feed if the user presses the 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        #Save the captured landmarks to a file
        with open("AnimationFile.txt", 'w') as f:
            time_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            f.write(f"RUN COMPLETE ON {time_stamp}\n")
            f.writelines(["%s\n" % item for item in posList])

        with open("AnimationFileUnityData.txt", 'w') as w:
            w.writelines(["%s\n" % item for item in anim_list])


        #Release the video capture object and close OpenCV windows
        cap.release()
        cv2.destroyAllWindows()

        return landmark_coords

if __name__ == '__main__':
    lr = Lateral_raise_mocap()
    lr.run_mocap()
    if lr.animate_flag:
        print("Running the animator now!")
        lr.run_unity_animator()