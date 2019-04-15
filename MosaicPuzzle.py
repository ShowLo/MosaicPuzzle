# -*- coding: UTF-8 -*-

import os
from threading import Thread
from PIL import Image
from functools import reduce
import math
import time

class MosaicPuzzle(object):
    '''
    马赛克拼图
    '''
    def __init__(self, source_path, output_path, aim_image_path, sub_image_width = 50, sub_image_height = 50, width_pixel_num = 1, height_pixel_num = 1, match_mode = 'RGB'):
        '''
        初始化
        源文件路径  输出文件路径  目标图像路径  子图长宽  子图在长宽方向上占原图的像素数  匹配模式
        '''
        self.source_path = source_path
        self.output_path = output_path
        self.aim_image_path = aim_image_path
        self.sub_image_height = sub_image_height
        self.sub_image_width = sub_image_width
        self.height_pixel_num = height_pixel_num
        self.width_pixel_num = width_pixel_num
        self.match_mode = match_mode
        self.all_image = dict()

    def calculate_key_value(self, img):
        '''
        根据匹配模式计算相应的关键值
        Calculate the corresponding key values according to the matching pattern
        '''
        if self.match_mode == 'RGB':
            return self.calculate_RGB_key(img)
        elif self.match_mode == 'gray':
            return self.calculate_gray_key(img)
        elif self.match_mode == 'hash':
            return self.calculate_hash_key(img)
        else:
            return ''
    
    @staticmethod
    def calculate_RGB_key(img):
        '''
        计算RGB模式对应的关键值
        Calculate the corresponding key values according to the matching pattern of RGB
        '''
        if img.mode != 'RGB':
            img = img.convert('RGB')
        pix = img.load()
        avg_r, avg_g, avg_b = 0, 0, 0
        n = 1
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
        return str(avg_r) + '-' + str(avg_g) + '-' + str(avg_b)

    @staticmethod
    def calculate_gray_key(img):
        '''
        计算gray模式对应的关键值
        Calculate the corresponding key values according to the matching pattern of gray
        '''
        if img.mode != 'L':
            img = img.convert('L')
        return reduce(lambda x, y: x + y, img.getdata()) / (img.size[0] * img.size[1])
    
    def calculate_hash_key(self, img):
        '''
        计算hash模式对应的关键值
        Calculate the corresponding key values according to the matching pattern of hash
        '''
        img = img.resize((8, 8), Image.ANTIALIAS)
        img = img.convert("L")
        avg_gray = self.calculate_gray_key(img)
        hash_key = ''
        for i in img.getdata():
            if i < avg_gray:
                hash_key += '0'
            else:
                hash_key += '1'
        return hash_key

    def read_img(self, file_paths):
        '''
        读取图像并根据匹配模式计算相应的关键值
        Read the image and calculate the corresponding key values according to the matching pattern
        '''
        for file_path in file_paths:
            img = Image.open(file_path)
            key_value = self.calculate_key_value(img)
            img = img.resize((self.sub_image_width, self.sub_image_height), Image.ANTIALIAS)
            self.all_image.update({key_value : img})


    def read_all_img(self, thread_num = 6):
        '''
        多线程读所有图
        Multi-thread reading all images
        '''
        thread_read_img = list()
        for _ in range(thread_num):
            thread_read_img.append(list())
        files = os.listdir(self.source_path)
        n = 0
        for f in files:
            file_path = os.path.join(self.source_path, f)
            if os.path.isfile(file_path):
                thread_read_img[n % thread_num].append(file_path)
                n += 1
        tmp = list()
        for i in thread_read_img:
            sub_thread = Thread(target=self.read_img, args=(i,))
            sub_thread.start()
            tmp.append(sub_thread)
        for t in tmp:
            t.join()


    def find_best_match(self, sub_img):
        '''
        找到与当前像素点最匹配的图片
        Find the picture that is best matched to the current pixel point
        '''
        sub_key = self.calculate_key_value(sub_img)
        if self.match_mode == 'RGB':
            return self.find_by_RGB(sub_key)
        elif self.match_mode == 'gray':
            return self.find_by_gray(sub_key)
        elif self.match_mode == 'hash':
            return self.find_by_hash(sub_key)
        else:
            return ''

    def find_by_RGB(self, sub_key):
        '''
        根据RGB模式找到最匹配的子图
        Find the best matched subgraph according to the matching pattern of RGB
        '''
        sub_r, sub_g, sub_b = sub_key.split("-")
        min_dif = 255
        k = ''
        for key in self.all_image.keys():
            src_r, src_g, src_b = key.split("-")
            cur_dif = abs(float(sub_r) - float(src_r)) + abs(float(sub_g) - float(src_g)) + abs(float(sub_b) - float(src_b))
            if cur_dif < min_dif:
                min_dif = cur_dif
                k = key
        return self.all_image[k]

    def find_by_gray(self, sub_key):
        '''
        根据gray模式找到最匹配的子图
        Find the best matched subgraph according to the matching pattern of gray
        '''
        min_dif = 255
        k = 0
        for key in self.all_image.keys():
            cur_dif = abs(key - sub_key)
            if cur_dif < min_dif:
                k = key
                min_dif = cur_dif
        return self.all_image[k]

    def dif_hash(self, key1, key2):
        '''
        计算两个hash key之间的汉明距离
        Calculate the Hamming distance between two hash keys
        '''
        n = 0
        for i in range(64):
            if key1[i] != key2[i]:
                n += 1
        return n

    def find_by_hash(self, sub_key):
        '''
        根据hash模式找到最匹配的子图
        Find the best matched subgraph according to the matching pattern of hash
        '''
        min_dif = 65
        k = 0
        for key in self.all_image.keys():
            cur_dif = self.dif_hash(sub_key, key)
            if cur_dif < min_dif:
                k = key
                min_dif = cur_dif
        return self.all_image[k]

    def puzzle_imgs(self, img_paths):
        '''
        拼图
        '''
        for aim_img_path, save_path in img_paths:
            print('Puzzing ' + aim_img_path + ' and saving to ' + save_path)
            aim_img = Image.open(aim_img_path)
            width = aim_img.size[0]
            height = aim_img.size[1]
            # 长宽方向上的图片数
            w = math.ceil(width / self.width_pixel_num)
            h = math.ceil(height / self.height_pixel_num)
            # 拼接图片的长宽
            aim_width = w * self.sub_image_width
            aim_height = h * self.sub_image_height
            new_img = Image.new('RGB', (aim_width, aim_height))
            
            for i in range(w):
                for j in range(h):
                    left = i * self.width_pixel_num
                    up = j * self.height_pixel_num
                    right = min(width, (i + 1) * self.width_pixel_num)
                    down = min(height, (j + 1) * self.height_pixel_num)
                    box = (left, up, right, down)
                    sub_img = aim_img.crop(box)
                    match_img = self.find_best_match(sub_img)
                    new_left = i * self.sub_image_width
                    new_up = j * self.sub_image_height
                    new_right = (i + 1) * self.sub_image_width
                    new_down = (j + 1) * self.sub_image_height
                    new_box = (new_left, new_up, new_right, new_down)
                    new_img.paste(match_img, new_box)

            new_img.save(save_path)

    def make(self, thread_num = 6):
        '''
        拼图接口
        interface of puzzle
        '''
        print("Reading images...")
        start = time.time()
        self.read_all_img()
        print("cost : %fs" % (time.time() - start))
        start = time.time()
        print('Puzzing...')
        if os.path.isfile(self.aim_image_path):
            self.puzzle_imgs([(self.aim_image_path, self.output_path)])
        elif os.path.isdir(self.aim_image_path):
            thread_puzzle = list()
            for _ in range(thread_num):
                thread_puzzle.append(list())
            files = os.listdir(self.aim_image_path)
            n = 0
            for f in files:
                file_path = os.path.join(self.aim_image_path, f)
                if os.path.isfile(file_path):
                    filename = f.split('.')[0] + '-puzzle.jpg'
                    thread_puzzle[n % thread_num].append((file_path, os.path.join(self.output_path, filename)))
                    n += 1
            tmp = list()
            for img_paths in thread_puzzle:
                sub_thread = Thread(target=self.puzzle_imgs, args=(img_paths,))
                sub_thread.start()
                tmp.append(sub_thread)
            for t in tmp:
                t.join()
        print("cost : %fs" % (time.time() - start))

if __name__ == "__main__":
    #mp = MosaicPuzzle(r'F:\OneDrive\OneDrive - mails.tsinghua.edu.cn\研究生作业\数据可视化\project1\dunhuang', r'1-rgb.jpg', r'F:\OneDrive\OneDrive - mails.tsinghua.edu.cn\研究生作业\数据可视化\project1\dunhuang\4_dunhuang_251_1.jpg', sub_image_width=50, sub_image_height=50, width_pixel_num=5, height_pixel_num=5, match_mode='RGB')
    mp = MosaicPuzzle(r'F:\OneDrive\OneDrive - mails.tsinghua.edu.cn\研究生作业\数据可视化\project1\dunhuang', r'F:\class\数据可视化\output', r'F:\OneDrive\OneDrive - mails.tsinghua.edu.cn\研究生作业\数据可视化\project1\dunhuang', sub_image_width=50, sub_image_height=50, width_pixel_num=5, height_pixel_num=5, match_mode='RGB')
    mp.make()