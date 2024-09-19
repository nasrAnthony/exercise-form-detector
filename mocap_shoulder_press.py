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
from mocap_general import Mocap_General

unity_exe_path = ".\\Unity Animator Entity\\MotionCapture.exe" #need normpath here
batch_file_path = ".\\run_unity_engine_no_engine.bat"
exercise_name = "Shoulder press"

class Shoulder_press_mocap(Mocap_General):
    def __init__(self):

        #current analysis coordinates
        self.left_shoulder_coords = None #11
        self.right_shoulder_coords = None #12
        self.left_elbow_coords = None #13 
        self.right_elbow_coords = None #14
        self.left_wrist_coords = None #15
        self.right_wrist_coords = None #16
        self.offset_Y = None
        self.bad_form_captured = False
        self.lm_exercise_map = { 
        # 11 : self.left_shoulder_coords lowkey this better... 
            exercise_name: {
                "L shoulder": 11, 
                "R shoulder": 12, 
                "L elbow" : 13, 
                "R elbow": 14, 
                "L wrist": 15,
                "R wrist": 16
            }
        }
        self.bad_form_list = []
        self.bad_form = False
        self.animate_flag = False
        self.delay = 3
        self.set_number = None
        self.bad_form_pics_path = ".\\bad-form-bin\\Shoulder-press"
        self.env_flag = False #false to start so we can setup the proper destination folders for bad form snapshots... 

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
        if self.set_number and not self.env_flag: #check if we are part of a split
            self.bad_form_pics_path = self.bad_form_pics_path + f"_setnumber{self.set_number}"
            self.env_flag = True
        if not os.path.exists(self.bad_form_pics_path):
            os.makedirs(self.bad_form_pics_path)
        time_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(self.bad_form_pics_path, f"bad_form_{time_stamp}.png")
        if 'R' in resonsibles:
            og_y_coord_R = (self.right_elbow_coords[1] - self.offset_Y)*(-1)
            cv2.circle(img, (self.right_elbow_coords[0], og_y_coord_R), radius=28, color=(0, 0, 255), thickness=2)
        if 'L' in resonsibles:
            og_y_coord_L = (self.left_elbow_coords[1] - self.offset_Y)*(-1)
            cv2.circle(img, (self.left_elbow_coords[0], og_y_coord_L), radius=28, color=(0, 0, 255), thickness=2)
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
        self.left_wrist_coords and
        self.right_wrist_coords):
            #right
            a = np.array(self.right_shoulder_coords) 
            b = np.array(self.right_elbow_coords)
            c = np.array(self.right_wrist_coords)
            #left
            d = np.array(self.left_shoulder_coords) 
            e = np.array(self.left_elbow_coords)
            f = np.array(self.left_wrist_coords)
            
            radians_R= np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
            radians_L = np.arctan2(f[1]-e[1], f[0]-e[0]) - np.arctan2(d[1]-e[1], d[0]-e[0])
            angle_R, angle_L = np.abs(radians_R*180.0/np.pi), np.abs(radians_L*180.0/np.pi)

            #adjust
            if angle_R > 180.0: 
                angle_R = 360 - angle_R
            if angle_L > 180.0:
                angle_L = 360 - angle_L

            if (angle_R >= 160 or angle_R < 40) or (angle_L >= 160 or angle_L < 40):
                reason = "" 
                responsibles = []
                if angle_R >= 160:
                    reason += "Your right arm went too high and extended your forearms!\n"
                    responsibles.append('R')
                if angle_R < 40:
                    reason += "Your right elbow went too low!\n"
                    responsibles.append('R')
                if angle_L >= 160:
                    reason += "Your left arm went too high and extended your forearms!\n"
                    responsibles.append('L')
                if angle_L < 40:
                    reason += "Your left elbow went too low!\n"
                    responsibles.append('L')
                if not self.bad_form_captured:
                    self.save_bad_form_snapshot(img, reason, responsibles)
            else:
                self.bad_form_captured = False
        else:
            return(f"Not enough data yet :D")
    
    def run_mocap(self, run_from_split):
        if not run_from_split: #get options from command line
            ARGS = self.fetch_arguments()
            run_time, self.animate_flag, self.delay, self.set_number = ARGS[0], ARGS[1], ARGS[2], ARGS[3]
        elif run_from_split:  #get options from function call
            run_time, self.animate_flag =  run_from_split[0], run_from_split[1]
            self.delay, self.set_number = run_from_split[2], run_from_split[3]
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
                for i in range(0, len(lmList)):
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
                            case 15:
                                self.left_wrist_coords = [lm[0], ycoord, lm[2]] #x y z
                            case 16:
                                self.right_wrist_coords = [lm[0], ycoord, lm[2]] #x y z
                        self.angle_analysis(raw_image)
                        lmString += f'landmark #{i}: ({lm[0]}, {ycoord}, {lm[2]})\n'
                        landmark_coords.get(i).append((lm[0], img_height - lm[1], lm[2])) #x, y, z
                anim_list.append(anim_string)
                posList.append(lmString)

            #Close the video feed if the user presses the 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            if time.time() - start_time > run_time:
                break
        
            #Show the live video feed with pose estimation
            cv2.imshow("Image", img)

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
    sp = Shoulder_press_mocap()
    sp.run_mocap()
    if sp.animate_flag:
        print("Running the animator now!")
        sp.run_unity_animator()