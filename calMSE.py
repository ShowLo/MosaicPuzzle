# -*- coding: UTF-8 -*-

import os
import numpy as np
from PIL import Image

def MSE(img1, img2):
    img1 = np.array(img1)
    img2 = np.array(img2)
    return np.sqrt(np.sum((img1 - img2)**2) / img1.size)

if __name__ == "__main__":
    file1 = r'F:\OneDrive\OneDrive - mails.tsinghua.edu.cn\研究生作业\数据可视化\project1\dunhuang\5_yulinku_25_10.jpg'
    file2 = r'F:\github\MosaicPuzzle\test.jpg'
    print('MSE between ' + file1 + ' and ' + file2 + ' is ' + str(MSE(Image.open(file1), Image.open(file2))))
    folder1 = r'F:\class\数据可视化\project1'
    folder2 = r'F:\class\数据可视化\颜色拼图'
    folders = os.listdir(folder1)
    for folder in folders:     
        if os.path.isdir(os.path.join(folder1, folder)):
            files = os.listdir(os.path.join(folder1, folder))
            n = folder.split('_')[-1]
            mse_sum = 0
            count = 0
            for f in files:
                img1 = Image.open(os.path.join(os.path.join(folder1, folder), f))
                img2 = Image.open(os.path.join(os.path.join(folder2, folder), f.split('.')[0] + '-colorPuzzle.jpg'))
                count += 1
                mse_sum += MSE(img1, img2)
            print('No.' + n + ' MSE: ' + str(mse_sum/count))