@echo off
set UnityEnginePath="C:\Program Files\Unity\Hub\Editor\2022.3.44f1\Editor\Unity.exe"
set ProjectPath="C:\Users\User\Desktop\HackNSlash_UNITY\MotionCapture"

%UnityEnginePath% -batchmode -quit -nographics -projectPath %ProjectPath% -executeMethod BuildScript.BuildAndRun -logFile "output_log_run_unity.txt"
