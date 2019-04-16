# -*- coding: UTF-8 -*-

import os
from threading import Thread
from PIL import Image
from functools import reduce
import math
import time

class ColorPuzzle(object):
    '''
    使用聚类得到的主要颜色进行拼图
    Puzzle using the main colours obtained by clustering
    '''
    def __init__(self, source_path, output_path, aim_image_path, width_pixel_num = 1, height_pixel_num = 1):
        '''
        初始化
        源文件路径  输出文件路径  目标图像路径  拼图颜色块在长宽方向上占原图的像素数
        '''
        self.source_path = source_path
        self.output_path = output_path
        self.aim_image_path = aim_image_path
        self.height_pixel_num = height_pixel_num
        self.width_pixel_num = width_pixel_num
        self.clustering_color = self.read_clustering_color()

    def read_clustering_color(self):
        '''
        从文件中读取聚类得到的主要颜色
        Read the main colours obtained by clustering from the file
        '''
        files = os.listdir(self.source_path)
        clustering_color = {}
        for f in files:
            full_path = os.path.join(self.source_path, f)
            if os.path.isfile(full_path):
                tmp = []
                with open(full_path, 'r', encoding='UTF-8') as txt:
                    for line in txt:
                        r, g, b = line.split(']')[0].split('[')[1].split()
                        tmp.append((round(float(r)), round(float(g)), round(float(b))))
                #tmp.pop()
                no = f.split('.')[0].split('_')[1]
                clustering_color[no] = tmp
        return clustering_color

    @staticmethod
    def calculate_avg_RGB(img):
        '''
        计算平均RGB
        Calculate the average RGB
        '''
        if img.mode != 'RGB':
            img = img.convert('RGB')
        pix = img.load()
        avg_r, avg_g, avg_b = 0, 0, 0
        n = 0
        for i in range(img.size[0]):
            for j in range(img.size[1]):
                r, g, b = pix[i, j]
                avg_r += r
                avg_g += g
                avg_b += b
                n += 1
        avg_r /= n
        avg_g /= n
        avg_b /= n
        return (avg_r, avg_g, avg_b)

    @staticmethod
    def RGB_distance(RGB1, RGB2):
        '''
        计算两个RGB颜色之间的色差
        Calculate the chromatic aberration between two RGB colors
        '''
        R1, G1, B1 = RGB1
        R2, G2, B2 = RGB2
        
        r_mean = (R1 + R2) / 2
        R = R1 - R2
        G = G1 - G2
        B = B1 - B2
        return math.sqrt((2+r_mean/256)*(R**2) + 4*(G**2) + (2+(255-r_mean)/256)*(B**2))
        #return math.sqrt((R1 - R2)**2 + (G1 - G2)**2 + (B1 - B2)**2)

    def find_by_RGB(self, sub_block, class_no):
        '''
        根据RGB找到最匹配的颜色
        Find the best matched color according to RGB
        '''
        avg_rgb = self.calculate_avg_RGB(sub_block)
        colors = self.clustering_color[class_no]
        best_match_color = ''
        min_diff = float('inf')
        for color in colors:
            diff = self.RGB_distance(color, avg_rgb)
            if diff < min_diff:
                min_diff = diff
                best_match_color = color
        #print('the color ' + str(avg_rgb) + ' is closed to ' + str(best_match_color))
        return best_match_color
    
    def puzzle_imgs(self, img_paths):
        '''
        拼图
        '''
        for aim_img_path, save_path in img_paths:
            print('Puzzing ' + aim_img_path + ' and saving to ' + save_path)
            aim_img = Image.open(aim_img_path)
            width = aim_img.size[0]
            height = aim_img.size[1]
            # 长宽方向上的像素块数
            w = math.ceil(width / self.width_pixel_num)
            h = math.ceil(height / self.height_pixel_num)
            new_img = Image.new('RGB', (width, height))
            class_no = aim_img_path.split(os.path.sep)[-2].split('_')[-1]
            for i in range(w):
                for j in range(h):
                    left = i * self.width_pixel_num
                    up = j * self.height_pixel_num
                    right = min(width, (i + 1) * self.width_pixel_num)
                    down = min(height, (j + 1) * self.height_pixel_num)
                    box = (left, up, right, down)
                    sub_img = aim_img.crop(box)
                    new_right = (i + 1) * self.width_pixel_num
                    new_down = (j + 1) * self.height_pixel_num
                    new_box = (left, up, new_right, new_down)
                    match_color = self.find_by_RGB(sub_img, class_no)
                    new_img.paste(Image.new('RGB', (self.width_pixel_num, self.height_pixel_num), match_color), new_box)
            new_img.save(save_path)

    def make(self, thread_num = 10):
        '''
        颜色拼图接口
        Interface of Color Puzzle
        '''
        start = time.time()
        print('Color Puzzing...')
        if os.path.isfile(self.aim_image_path):
            self.puzzle_imgs([(self.aim_image_path, self.output_path)])
        elif os.path.isdir(self.aim_image_path):
            thread_puzzle = list()
            for _ in range(thread_num):
                thread_puzzle.append(list())
            files = os.listdir(self.aim_image_path)
            n = 0
            for folder in files:
                folder_path = os.path.join(self.aim_image_path, folder)
                if os.path.isdir(folder_path):
                    imgs = os.listdir(folder_path)
                    output_folder = os.path.join(self.output_path, folder)
                    if not os.path.exists(output_folder):
                        os.makedirs(output_folder)
                    for f in imgs:
                        file_path = os.path.join(folder_path, f)
                        if os.path.isfile(file_path):
                            filename = f.split('.')[0] + '-colorPuzzle.jpg'
                            thread_puzzle[n % thread_num].append((file_path, os.path.join(output_folder, filename)))
                            n += 1
            tmp = list()
            for img_paths in thread_puzzle:
                sub_thread = Thread(target=self.puzzle_imgs, args=(img_paths,))
                sub_thread.start()
                tmp.append(sub_thread)
            for t in tmp:
                t.join()
        print("cost : %fs" % (time.time() - start))

    '''
    def test(self):
        colors = [(122,115,116),(170,106,76),(212,196,183),(193,178,163),(181,170,144),(54,40,43),(103,52,36),(145,128,114),(128,118,110),(180,169,146),(154,136,120),(104,94,72),(151,132,108),(183,160,145),(184,148,133),(139,97,77),(133,109,114),(115,87,92),(140,75,49),(93,49,49),(119,61,49),(137,78,84),(98,73,65),(72,51,50)]
        self.clustering_color['test'] = colors
        aim_img_path = r'F:\OneDrive\OneDrive - mails.tsinghua.edu.cn\研究生作业\数据可视化\project1\dunhuang\5_yulinku_25_10.jpg'
        save_path = 'test.jpg'
        print('Puzzing ' + aim_img_path + ' and saving to ' + save_path)
        aim_img = Image.open(aim_img_path)
        width = aim_img.size[0]
        height = aim_img.size[1]
        # 长宽方向上的像素块数
        w = math.ceil(width / self.width_pixel_num)
        h = math.ceil(height / self.height_pixel_num)
        new_img = Image.new('RGB', (w * self.width_pixel_num, h * self.height_pixel_num))
        class_no = 'test'
        for i in range(w):
            for j in range(h):
                left = i * self.width_pixel_num
                up = j * self.height_pixel_num
                right = min(width, (i + 1) * self.width_pixel_num)
                down = min(height, (j + 1) * self.height_pixel_num)
                box = (left, up, right, down)
                sub_img = aim_img.crop(box)
                match_color = self.find_by_RGB(sub_img, class_no)
                new_right = (i + 1) * self.width_pixel_num
                new_down = (j + 1) * self.height_pixel_num
                new_box = (left, up, new_right, new_down)
                new_img.paste(Image.new('RGB', (self.width_pixel_num, self.height_pixel_num), match_color), new_box)
        new_img.save(save_path)
        '''

if __name__ == "__main__":
    #mp = ColorPuzzle(r'F:\class\数据可视化\project1', r'2.jpg', r'F:\class\数据可视化\project1\cls_0\2_dunhuang_3_1.png', width_pixel_num=1, height_pixel_num=1)
    #mp.test()
    #print(mp.clustering_color)
    mp = ColorPuzzle(r'F:\class\数据可视化\project1', r'F:\class\数据可视化\colorPuzzle', r'F:\class\数据可视化\project1', width_pixel_num=1, height_pixel_num=1)
    mp.make()