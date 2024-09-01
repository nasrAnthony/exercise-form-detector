import os
import moviepy.video.io.ImageSequenceClip
from datetime import datetime

def build_video_from_frames(fps):
    image_folder='.\\Animation Frames'
    image_files = [os.path.join(image_folder,img)
                    for img in os.listdir(image_folder)
                    if img.endswith(".png")]
    clip = moviepy.video.io.ImageSequenceClip.ImageSequenceClip(image_files, fps=fps)
    time_now = datetime.now().strftime("%Y%m%d_%H%M%S") 
    clip.write_videofile(f'.\\Animation Results\\animation_{time_now}_.mp4')



#if __name__ == "__main__":
#    build_video_from_frames(fps= 30)