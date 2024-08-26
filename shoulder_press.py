import matplotlib.pyplot as plt
from datetime import datetime

class shoulder_press:
    #def __init__(self, data, max_height, shoulder_height_L, shoulder_height_R):
    def __init__(self, data, max_height):
        self.position_data = data
        self.fault_tolerance = 10 
        self.joints_of_interest = {
            11: "L shoulder",
            12: "R shoulder",
            13: "L elbow",
            14: "R elbow",
            15: "L wrist",
            16: "R wrist"
        }
        self.expected_max_height = max_height
        #self.shoulder_base_height_left = shoulder_height_L
        #self.shoulder_base_height_right = shoulder_height_R

    #gets
    def get_position_data(self, verbose) -> list:
        """
        return a list of positions [
                                    ...
                                    lm#: posX, posY, posZ
                                    ...
                                    ]
        """
        if verbose:
            print(self.position_data)

        return self.position_data
    
    def get_fault_tolerance(self) -> float:
        """
        fault tolerance will be used at the extremities of each rep. 
        Returning to the exact original position is not practical. 
        """
        return self.fault_tolerance
    
    #sets
    def set_fault_tolerance(self, desired_fault_tolerance):
        """
        This will be a setting that can be changed by the user if they want.
            -> Generally: 
                Lower fault tolerance will require more precision on the user's part to complete "Good" rep. 
                Higher fault tolerance will make the algorithm more leniant to beginner mistakes. 
        """
        self.fault_tolerance = desired_fault_tolerance


    #analysis
    def extract_reps(self):
        #access left and right shoulder coordinates
        anchor_left_shoulder = self.position_data.get(11)[0][1]
        anchor_right_shoulder = self.position_data.get(12)[0][1]
        left_elbow_coordinates = self.position_data.get(13)
        right_elbow_coordinates = self.position_data.get(14)
        rep_count = 0
        currently_in_rep_flag = False
        rep_summited = False
        current_rep = None
        rep_list = []
        for i in range(len(left_elbow_coordinates)): #iterate over left elbow positions
            left_elbow_y = left_elbow_coordinates[i][1]
            right_elbow_y = right_elbow_coordinates[i][1]
            if (anchor_left_shoulder - self.fault_tolerance <= left_elbow_y <= anchor_left_shoulder + self.fault_tolerance*2 and 
                anchor_right_shoulder - self.fault_tolerance <= right_elbow_y <= anchor_right_shoulder + self.fault_tolerance*2):
                if current_rep and current_rep.get_summited():
                #if rep_summited:
                    rep_count += 1
                    rep_list.append(current_rep)
                    rep_count += 1
                    current_rep = None
                if not current_rep:
                    current_rep = rep(rep_ID= rep_count + 1)
            if (self.expected_max_height - self.fault_tolerance*2 <= left_elbow_y and right_elbow_y <= self.expected_max_height):
                #rep_summited = True
                if current_rep: #should always be true when in this clause
                    current_rep.set_summited()

        return len(rep_list)

                

    def validate_form(self, reps_list):
        pass

    def analyze_data(self):
        rep_list = self.extract_reps()
        print(rep_list)
        #self.validate_form(rep_list)

    def imprint_data(self):
        # Filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_filename = f"Formatted_Landmark_Coordinates_{timestamp}.txt"

        # Writing to the text file
        with open(output_filename, 'w') as f:
            f.write("Landmark Coordinates Report\n")
            f.write(f"Generated on: {datetime.now()}\n")
            f.write("="*50 + "\n\n")

            for lm_id, coords in self.position_data.items():
                f.write(f"Landmark ID: {lm_id} ({self.joints_of_interest[lm_id]})\n")
                f.write("Coordinates:\n")
                for i, coord in enumerate(coords):
                    f.write(f"  Frame {i + 1}: (X: {coord[0]}, Y: {coord[1]}, Z: {coord[2]})\n")
                f.write("\n")
            
            f.write("="*50 + "\n")
            f.write("End of Report\n")

        print(f"Formatted data has been written to {output_filename}")

    def graph_data(self):
        for lm_id, coords in self.position_data.items():
            #Unpack the coordinates into separate lists
            x_coords = [coord[0] for coord in coords if coord is not None]
            y_coords = [coord[1] for coord in coords if coord is not None]
            z_coords = [coord[2] for coord in coords if coord is not None]
            #Create a new figure for each landmark
            plt.figure(figsize=(10, 6))
            #Plot X, Y, and Z coordinates over time (frame index)
            plt.plot(x_coords, label='X Coordinate', marker='o')
            plt.plot(y_coords, label='Y Coordinate', marker='o')
            plt.plot(z_coords, label='Z Coordinate', marker='o')
            #Adding titles and labels
            joint_name = self.joints_of_interest.get(lm_id, '')
            plt.title(f'Landmark {joint_name} #{lm_id} Coordinates Over Time')
            plt.xlabel('Frame Index')
            plt.ylabel('Coordinate Value')
            plt.legend()
            #Show the plot
            plt.show()

class rep(): 
    def __init__(self, rep_ID):
        self.start_pos = (None, None, None)
        self.good_form = True #assumed to be true, unless other wise proven false. 
        self.rep_num = rep_ID #each rep is given an ID for graphing purposes later on in the application. (i.e rep 1 , rep 2, rep 3  , rep 4 etc...)
        #self.expected_max_height = self.update_max_height(data) #this needs to be compared to z coordinate everytime. If reached (within a margin), means that rep can be counted once original position is reached again.
        self.summited  = False #default is false, until proven true. y coordinate  = max height. 
        self.reason_for_failure = None #will be set as a string explanation of why it it labeled as "bad". 
        self.rep_position_data = []

    def get_expected_max_height(self) -> int:
        return self.expected_max_height

    def get_summited(self) -> bool:
        return self.summited

    def get_rep_num(self) -> int:
        return self.rep_num

    def get_form_flag(self) -> str:
        if(self.good_form):
            return ("good")
        else:
            return ("bad")
        
    def get_travel_data(self) -> list:
        return self.rep_position_data
    
    def set_start_pos(self, start_position) -> None:
        self.start_pos = start_position
    
    def set_rep_num(self, rep_ID) -> None:
        self.rep_num = rep_ID
    
    def set_summited(self) -> None:
        self.summited = True

    def set_reason(self, reason) -> None:
        self.reason_for_failure = reason

    def reset_good_form(self) -> None:
        self.good_form = False

    def update_position_list(self, tuple) -> None:
        self.rep_position_data.append(tuple)

    #def update_max_height(self, data) -> None:
    #    max_height = 0.0 #start at 0. Update as we iterate. 
    #    for i in range(len(data)): #go through given position data. 
    #        if(data[i] > max_height): #compare heights. 
    #            max_height = data[i] #replace temp_max_height with new highest. 
    #    self.expected_max_height = max_height #update max height variable. 
