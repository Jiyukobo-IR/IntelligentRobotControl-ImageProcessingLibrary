from copy import copy
from re import L
from serial.serialutil import CR
import cv2
import serial
import ColorBallSearch
import LineTrace
import time

ball = ColorBallSearch.ColorBallSearch()
trace = LineTrace.LineTrace()
ser = serial.Serial('/dev/ttyACM0',115200,timeout=0)
cap=cv2.VideoCapture(0)
CrossCount = 0
TurnCount = 0
CatchCount = 0
CatchStartTime = 0
WaitNextCrossTime = 0
WaitChangeSearchModeTime = 0
Cross = False
Trace = False
TraceBack = False
BallSearch = True
Start = False
Wait = True
Find = False
Release = False
Collection = []
cor = "None"
LoseSightColor = "None"
Order_old = "Stop"
FindColor = "None"
ColorBallGoal = ["Blue","Yellow","Red"]
while(1):
    _,frame = cap.read()
    color_frame = cv2.resize(frame,dsize=(640,480))
    if Start:
        if Wait:
            if ser.inWaiting() > 0:
                StringData = ser.readline()
                if StringData == b'Next\r\n' and not Release:
                    if CatchCount >= 15 and CrossCount >= 5:
                        ser.write(str.encode("Finish_\r\n"))
                        break
                    Wait = False
                    
                elif StringData == b'Catch\r\n':
                    Wait = False
                    Collection.append(cor)
                    CatchCount = CatchCount + 1
                    if len(Collection) >= 4 or CatchCount >= 15:
                        break
                        
        elif BallSearch:
            if ser.inWaiting()>0:
                CRSerial = ser.readline()
                if CRSerial == b'Turn\r\n':
                    LoseSightColor = "None"
                    FindColor = "None"
                    Wait = True
                    if CrossCount == 2:
                        CrossCount = 1
                    TurnCount = 0
                    continue
            cor,color_frame,x,y = ball.SearchColorBall(color_frame,FindColor)
            print("cor:"+cor)
            #print("FindColor:"+FindColor)
            #print("LoseSightColor:"+LoseSightColor)
            if cor != "None" and cor != LoseSightColor and x != 0 and y != 0:
                CatchStartTime = time.perf_counter()
                if not Find and x != 0 and y != 0:
                    ser.write(str.encode("Find_\r\n"))
                    Find = True
                    FindColor = cor
                    CatchStartTime = time.perf_counter()
                    if x < ball.x1:
                        ser.write(str.encode("LeftTurn_\r\n"))
                        Order_old = "LeftTurn"
                    elif x > ball.x2:
                        ser.write(str.encode("RightTurn_\r\n"))
                        Order_old = "RightTurn"
                    elif y < ball.y1:
                        ser.write(str.encode("Front_\r\n"))
                        Order_old = "Front"
                    elif y > ball.y2:
                        ser.write(str.encode("Back_\r\n"))
                        Order_old = "Back"
                if x > ball.x1 and x < ball.x2:
                    if y > ball.y1 and y < ball.y2:
                        ser.write(str.encode("Catch_\r\n"))
                        TurnCount = 0
                        FindColor = "None"
                        Find = False
                        Wait = True
                    elif y < ball.y1:
                        ser.write(str.encode("Front_\r\n"))
                        Order_old = "Front"
                    elif y > ball.y2:
                        ser.write(str.encode("Back_\r\n"))
                        Order_old = "Back"
                elif Find:
                    if x < ball.x1:
                        ser.write(str.encode("LeftTurn_\r\n"))
                        Order_old = "LeftTurn"
                    elif x > ball.x2:
                        ser.write(str.encode("RightTurn_\r\n"))
                        Order_old = "RightTurn"
            elif cor == "None" and Find:
                ElapsedTime = time.perf_counter() - CatchStartTime
                if ElapsedTime >=  3:
                    ser.write(str.encode("LoseSight_\r\n"))
                    Order_old = "Stop"
                    LoseSightColor = FindColor
                    FindColor = "None"
                    Find = False
                    Wait = True
                else:
                    ser.write(str.encode(""+Order_old+"_\r\n"))
                    #ser.write(str.encode("Stop_\r\n"))
                
                
                    
    else:
        print("Press the key to start")
        color_frame = cv2.resize(color_frame,dsize=None,fx=0.5,fy=0.5)
        color_frame=color_frame[trace.trim_y:trace.trim_y+trace.trim_h,]
        ret,color_frame = cv2.threshold(color_frame,trace.th,trace.i_max,cv2.THRESH_BINARY_INV)
        cv2.rectangle(color_frame,(trace.LB_x1,trace.LB_y1),(trace.LB_x2,trace.LB_y2),(0,0,255),2)
        cv2.rectangle(color_frame,(trace.RB_x1,trace.RB_y1),(trace.RB_x2,trace.RB_y2),(0,0,255),2)
    
    cv2.imshow("",color_frame)
    if cv2.waitKey(1) != -1:
        if Start == False:
            ser.write(str.encode("Demonstration_\r\n"))
            Start = True
            CrossCount = 2
        else:
            break;

cv2.destroyAllWindows()
ser.write(str.encode("End_\n"))
ser.close()

