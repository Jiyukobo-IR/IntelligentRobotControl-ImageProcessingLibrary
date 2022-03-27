import cv2
import ColorBallSearch
ball = ColorBallSearch.ColorBallSearch()
cap = cv2.VideoCapture(0)
FindColor = "None"
while True:
    _,frame = cap.read()
    color_frame = cv2.resize(frame,dsize=(640,480))
    cor,color_frame,x,y = ball.SearchColorBall(color_frame,FindColor)
    FindColor = cor
    print(FindColor)    
    cv2.imshow("",color_frame)
    if cv2.waitKey(1) != -1:
        break