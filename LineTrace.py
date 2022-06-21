import cv2
import numpy as np

class LineTrace:
    def __init__(self): #クラスが呼び出されるとまずここが呼び出され初期値の設定等を行う
        self.trim_y = 165 #カメラから取得した画像を切り取る際のy座標
        self.trim_h = 45 #カメラから取得した映像を切り取る際の切り取る縦の範囲
        self.th = 40 #黒い線と白い床面を見分けるための閾値
        self.i_max = 255 #閾値を超えた画素は全てこの値(白)として扱われる
        self.LB_x1 = 145 #十字認識エリアのx座標
        self.LB_x2 = 155 
        self.LB_y1 = 0 #十字認識エリアのy座標
        self.LB_y2 = self.trim_h 
        self.RB_x1 = 225 
        self.RB_x2 = 235
        self.RB_y1 = 0 
        self.RB_y2 = self.trim_h 
        self.Kp = 1.250 #PID制御を行うためのPゲイン
        self.Ki = 0.005 #PID制御を行うためのIゲイン
        self.Kd = 0.600 #PID制御を行うためのDゲイン
        self.L_PWM_old = 0 #ひとつ前のPWMの値
        self.R_PWM_old = 0 
        self.L_e1 = 0 #前回の制御時の偏差
        self.L_e2 = 0 #前々回の制御時の偏差
        self.R_e1 = 0 #
        self.R_e2 = 0 
        self.L_PWM = 0 #左車輪のPWM
        self.R_PWM = 0 #右車輪のPWM
        self.L_e = 0 #偏差
        self.R_e = 0 
        self.Goal = 190 #目標値
        self.cx_old = self.Goal
        
    def adjust(self,img, alpha=1.0, beta=0.0):#画像のコントラストと明度に補正をかける(alpha:0.0~2.0,beta:-100.0~100.0の範囲をとる)
        # 積和演算を行う。
        dst = alpha * img + beta
        # [0, 255] でクリップし、uint8 型にする。
        return np.clip(dst, 0, 255).astype(np.uint8)
    
    def LineTrace(self,frame):
        Slip = "None"
        frame = cv2.resize(frame,dsize=None,fx=0.5,fy=0.5)#処理の高速化のため画像のサイズを縮小
        #ret,frame = cv2.threshold(frame,self.th,self.i_max,cv2.THRESH_OTSU + cv2.THRESH_BINARY_INV)#画像を二値化(白黒の画像に変換する様なもの)
        frame = cv2.adaptiveThreshold(frame,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY_INV,51,20)#画像を二値化(白黒の画像に変換する様なもの).こっちの方が反射光の影響とか受けないから良さげ
        frame = cv2.medianBlur(frame,5)
        #print(ret)
        frame = frame[self.trim_y:self.trim_y+self.trim_h,]#画像を必要な大きさに切り取り
        LB1 = frame[self.LB_y1:self.LB_y2,self.LB_x1:self.LB_x2]#十字認識エリアの指定
        RB1 = frame[self.RB_y1:self.RB_y2,self.RB_x1:self.RB_x2]
        cv2.rectangle(frame,(self.LB_x1,self.LB_y1),(self.LB_x2,self.LB_y2),(0,0,255),1)#十字認識エリアを可視化
        cv2.rectangle(frame,(self.RB_x1,self.RB_y1),(self.RB_x2,self.RB_y2),(0,0,255),1)
        Det_LB = cv2.countNonZero(LB1) #左ブロックエリアの白ピクセルカウント
        Det_RB = cv2.countNonZero(RB1) #右ブロックエリアの白ピクセルカウント
        cnts,_ = cv2.findContours(frame,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)#黒線の輪郭を抽出
        if len(cnts) != 0:
            cnts = max(cnts,key=lambda x: cv2.contourArea(x))#最も面積の大きい輪郭を抽出
            x,y,w,h = cv2.boundingRect(cnts)#抽出した要素の情報を取得
            m = cv2.moments(cnts)#抽出した要素の重心を計算
            if m['m00'] > 0:
                cx = int(m['m10']/m['m00'])#重心のx座標
                cy = int(m['m01']/m['m00'])#重心のy座標
                if Det_RB > 0 and Det_LB > 0:#十字の認識
                    Slip = "Cross"
                    cx = self.cx_old + 10
                cv2.circle(frame,(cx,cy),5,(0,255,0),-1)#重心の描画
                err = cx - w//2
                self.L_PWM_old = self.L_PWM
                self.R_PWM_old = self.R_PWM
                self.L_e2 = self.L_e1
                self.R_e2 = self.R_e1
                self.L_e1 = self.L_e
                self.R_e1 = self.R_e
                self.L_e = self.Goal - err#偏差を取得
                self.R_e = self.Goal - err
                #各要素を計算しそれらに各ゲインとの乗算を行い制御量を算出
                self.L_PWM = self.L_PWM_old + self.Kp * (self.L_e-self.L_e1) + self.Ki * self.L_e + self.Kd * ((self.L_e-self.L_e1) - (self.L_e1-self.L_e2))
                self.R_PWM = self.R_PWM_old + self.Kp * (self.R_e-self.R_e1) + self.Ki * self.R_e + self.Kd * ((self.R_e-self.R_e1) - (self.R_e1-self.R_e2))
                self.cx_old = cx
        L = round(100 + self.L_PWM)#PWMの最大値から制御量を差し引きモーターに送るPWMの値を算出
        R = round(100 - self.R_PWM)
        #cv2.imshow("trace",frame)
        return L,R,Slip#左PWM,右PWM,十字を認識したかどうか(default:"None",十字認識時:"Cross"が格納)
