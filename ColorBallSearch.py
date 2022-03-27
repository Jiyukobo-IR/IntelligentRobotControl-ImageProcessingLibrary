import numpy as np
import cv2

class ColorBallSearch:#画像処理によるボールの認識クラス
    def __init__(self):
        #ボールキャッチエリアの座標指定
        #ボールキャッチエリアの四角の中にボールの中心座標が入ればそのボールは掴めると判断する
        self.x1 = 390#ボールキャッチエリアのx座標
        self.x2 = 410
        self.y1 = 285#ボールキャッチエリアのy座標
        self.y2 = 320
        
        self.pos_old = [0,0,0]#認識したボール(ロックオンしたボール)の座標と半径
        self.trimming_y = 150 #カメラ映像の上部を切り取り、見える範囲を調整する。
     
    def HoughBallScan(self,img):#ハフ変換によるボールの検出
        img_blur = cv2.GaussianBlur(img,(9,9),0)#ブラー処理をかけボールの輪郭をぼかす
        
        #画像のコントラストと明度に補正をかけボールの検出精度を向上させる
        img_adjust = self.adjust(img_blur,alpha=2.0,beta=-55.0)#alphaとbetaの値はCorrectionValueSearch.pyを使って求める
        gray = cv2.cvtColor(img_adjust,cv2.COLOR_BGR2GRAY)#画像をグレースケール化
        
        #ハフ変換によるボールの検出を行う。HoughCirclesの詳しい情報は自分で調べること
        circles = cv2.HoughCircles(gray,cv2.HOUGH_GRADIENT,dp=1.3,minDist=40,param1=100,param2=40,maxRadius=110)
        if circles is not None:#ボールが検出できればそれをuint16にキャストする
            circles = np.uint16(np.around(circles))
        return circles
    
    def adjust(self,img, alpha=1.0, beta=0.0):#画像のコントラストと明度に補正をかける(alpha:0.0~2.0,beta:-100.0~100.0の範囲をとる)
        # 積和演算を行う。
        dst = alpha * img + beta
        # [0, 255] でクリップし、uint8 型にする。
        return np.clip(dst, 0, 255).astype(np.uint8)
    
    def red_range(self,img,SearchColor): #各色の領域をマスクする関数
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV) #BGRをHSV色空間に変換
        
        #各色の領域を閾値でフィルタリング
        red_min = np.array([0,120,100]) #色相(Hue)、彩度(Saturation)、明度(Value)
        red_max = np.array([2,255,255])
        blue_min = np.array([90,230,70])
        blue_max = np.array([120,255,150])
        yellow_min = np.array([20,160,90])
        yellow_max = np.array([30,210,140])
        mask = []
        if SearchColor == "Yellow":
            mask = cv2.inRange(hsv, yellow_min, yellow_max) #hsvの各ドットについてyellow_minからyellow_maxの範囲内ならtrue
            
        elif SearchColor == "Red":
            mask = cv2.inRange(hsv, red_min, red_max) #hsvの各ドットについてred_minからred_maxの範囲内ならtrue
            
        elif SearchColor == "Blue":
            mask = cv2.inRange(hsv, blue_min, blue_max) #hsvの各ドットについてblue_minからblue_maxの範囲内ならtrue
        return mask
    
    def SearchColorBall(self,frame,findcolor):#ボールの検出とそれに応じた処理を行う。findcolorの中にはロックオンしているボールの色を指定する
        Color = ["Blue","Red","Yellow"]
        Find = "None"
        #cv2.imshow("beforetrim",frame)
        if findcolor  == "None":
            frame = frame[self.trimming_y:,]
        #cv2.imshow("aftertrim",frame)
        circles = self.HoughBallScan(frame)
        if circles is None:#ボールが見つからなかった場合はここに入る
            Find = "None"
            return Find,frame,0,0
        
        for circle in circles[0,:]:#circlesの各要素を抽出しfor文を回す
            circleimg = frame.copy()
            h,w = circleimg.shape[:2]
            Houghmask = np.zeros((h,w),dtype=np.uint8)#画像を真っ黒に上塗りする
            cv2.circle(Houghmask,(circle[0],circle[1]),circle[2],255,-1)#型抜きの要領で黒塗りの画像からボールの部分だけを抽出
            circleimg[Houghmask==0] = [0,0,0]
            circleimg = np.array(circleimg)
            if findcolor == "None":#ロックオンしているボールが存在しない時(ボール探索時)はこの中に入る
                for cor in Color:
                    mask = self.red_range(circleimg,cor) #frameデータをnp配列に変換。
                    if len(mask) == 0:
                        continue
                    #領域のカタマリである「ブロブ」を識別し、データを格納する。すごくありがたい機能。
                    nLabels, labelimages, data, center = cv2.connectedComponentsWithStats(mask)
                    blob_count = nLabels - 1 #ブロブの数。画面領域全体を1つのブロブとしてカウントするので、-1する。
                    if blob_count >= 1:
                        cv2.circle(circleimg,(circle[0],circle[1]),circle[2],(40,165,255),1)#認識したボールをマーキング
                        cv2.circle(circleimg,(circle[0],circle[1]),2,(0,255,0),1)
                        Find = cor
                        cv2.rectangle(circleimg,(self.x1,self.y2),(self.x2,self.y1),(0,255,0),2)#ボールのキャッチエリアを可視化する。この四角の中にボールの中心座標が入ればそのボールは掴めると判断する
                        self.pos_old = [circle[0],circle[1]+self.trimming_y,circle[2]]#認識したボールの座標と半径を記憶する
                        return Find,circleimg,circle[0],circle[1]#認識したボールの色,画像データ,認識したボールのx座標,y座標
            else:#ロックオンしているボールが存在する場合この中に入る
                cor = findcolor
                mask = self.red_range(circleimg,cor) #frameデータをnp配列に変換。
                if len(mask) == 0:
                    continue
                #領域のカタマリである「ブロブ」を識別し、データを格納する。すごくありがたい機能。
                nLabels, labelimages, data, center = cv2.connectedComponentsWithStats(mask)
                blob_count = nLabels - 1 #ブロブの数。画面領域全体を1つのブロブとしてカウントするので、-1する。
                
                #前回認識したボールと同一のボールかを確認する。これをしないと同じ色のボールが画像内に映り込んでいる場合にそちらを追いかけようとしてしまう
                if blob_count >= 1 and circle[0]+circle[2] > self.pos_old[0]-self.pos_old[2]-30 and circle[0]-circle[2] < self.pos_old[0]+self.pos_old[2]+30 and circle[1]+circle[2] > self.pos_old[1]-self.pos_old[2]-30 and circle[1]-circle[2] < self.pos_old[1]+self.pos_old[2]+30:
                    self.pos_old = circle
                    cv2.circle(circleimg,(circle[0],circle[1]),circle[2],(40,165,255),1)
                    cv2.circle(circleimg,(circle[0],circle[1]),2,(0,255,0),1)
                    Find = cor
                    cv2.rectangle(circleimg,(self.x1,self.y2),(self.x2,self.y1),(0,255,0),2)
                    return Find,circleimg,circle[0],circle[1]
        #ループを抜け切った場合見つからなかった扱いにする
        Find = "None"
        return Find,frame,0,0
