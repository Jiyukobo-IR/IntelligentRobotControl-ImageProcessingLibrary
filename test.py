import cv2
import ColorBallSearch
import serial
import LineTrace
ball = ColorBallSearch.ColorBallSearch()
trace = LineTrace.LineTrace()
cap = cv2.VideoCapture(0)
FindColor = "None"
while True:
    _,frame = cap.read()
    color_frame = cv2.resize(frame,dsize=(640,480))
    gray_frame = cv2.cvtColor(color_frame,cv2.COLOR_BGR2GRAY)   
    L_PWM,R_PWM,Slip = trace.LineTrace(gray_frame)
    cor,color_frame,x,y = ball.SearchColorBall(color_frame,FindColor)
    FindColor = cor
    cv2.imshow("",color_frame)
    if cv2.waitKey(1) != -1:
        ser.write(str.encode("End_\r\n"))
        break
