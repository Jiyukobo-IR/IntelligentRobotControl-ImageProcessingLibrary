import matplotlib.pyplot as plt
import numpy as np
import openpyxl
import serial
import cv2
import numpy as np
import statistics
class CorrectionValueSearch:#環境に合わせたadjust関数の補正値を検出するシステム
    def HoughBallScanTest(self,img,alpha,beta):
        img_blur = cv2.GaussianBlur(img,(9,9),0)
        img_adjust = self.adjust(img_blur,alpha,beta)
        gray = cv2.cvtColor(img_adjust,cv2.COLOR_BGR2GRAY)
        #cv2.imshow("gray",gray)
        circles = cv2.HoughCircles(gray,cv2.HOUGH_GRADIENT,dp=1.3,minDist=40,param1=100,param2=40,maxRadius=110)
        #circles = cv2.HoughCircles(gray,cv2.HOUGH_GRADIENT,dp=1.3,minDist=120,param1=100,param2=40,maxRadius=90)
        if circles is not None:
            circles = np.uint16(np.around(circles))
        return circles      
    
    def SearchColorBallTest(self):
        cap=cv2.VideoCapture(0)
        while True:
            _,frame = cap.read()
            frame = cv2.resize(frame,dsize=(640,480))
            cv2.imshow("",frame)
            if cv2.waitKey(1) != -1:
                cv2.destroyAllWindows()
                break
        AverageCount = []
        for alpha in np.arange(0.1,2.1,0.1):#adjustの補正値を全パターンしらみ潰しで試し、各パターンのボール検出数を記録する
            for beta in np.arange(-90.0,101.0,1.0):
                ScanCount = []
                for a in range(5):
                    print(alpha,beta,a)
                    circles = self.HoughBallScanTest(frame,alpha,beta)
                    circlePosition = [[-1,-1,-1]]
                    count = 0
                    if circles is not None:
                        for circle in circles[0,:]:
                            flag = True
                            for position in circlePosition:
                                if circle[0] >= position[0] - position[2] and circle[0] <= position[0] + position[2]:
                                    if circle[1] >= position[1] - position[2] and circle[1] <= position[1] + position[2]:
                                        flag = False
                                        break
                            if flag:
                                circlePosition.append([circle[0],circle[1],circle[2]])
                                count = count + 1
                    ScanCount.append(count)
                AverageCount.append([alpha,beta,statistics.mean(ScanCount)])
        cv2.destroyAllWindows()
        return AverageCount
    
    def adjust(self,img, alpha=1.0, beta=0.0):
        # 積和演算を行う。
        dst = alpha * img + beta
        # [0, 255] でクリップし、uint8 型にする。
        return np.clip(dst, 0, 255).astype(np.uint8)
    
ball = CorrectionValueSearch()
wb = openpyxl.Workbook()
fig = plt.figure()
sheet = wb.active
sheet.title = "ScanAverage"
Scan = []
index = []
fig = plt.figure(dpi=200)
ser = serial.Serial('/dev/ttyACM0',115200,timeout=0.1)
ser.write(str.encode("Test_\n"))
res = ball.SearchColorBallTest()
for i in range(len(res)):
    sheet['A'+str(i+1)] = ""+str(res[i][0])
    sheet['B'+str(i+1)] = ""+str(res[i][1])
    sheet['C'+str(i+1)] = ""+str(res[i][2])
    Scan.append(res[i][2])
    index.append(i)
plt.plot(index,Scan)#結果を線グラフにする(縦:ボール認識数,横:配列の要素番号)
plt.xticks(np.arange(0,4001,step=500))
fig.savefig("img.png")
wb.save("Data.xlsx")#結果をExelデータとして保存する
#出力されるグラフとExelのデータを見比べてどの辺りの補正値がその環境に合っているかを手動で探る