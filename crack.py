#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   crack.py    
@Auther  :  will_kkc 
@data    :  2020/1/13 13:57
@descr   :
'''

# -*-coding:utf-8 -*-
import base64
import time
import functools
import numpy as np

from geetest_huakuaiyanzhengma.selenium_spider import SeleniumSpider

from selenium.webdriver import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import PIL.Image as image
from PIL import ImageChops, PngImagePlugin
from io import BytesIO


class Crack(object):
    """
    解决三代极验滑块验证码
    """
    def __init__(self):
        self.url = 'https://www.geetest.com'
        self.browser = SeleniumSpider(path=r"D:\anaconda\envs\py36\Lib\site-packages\selenium\webdriver\chrome\chromedriver", max_window=True)
        self.wait = WebDriverWait(self.browser, 100)
        self.BORDER = 8
        self.table = []

        for i in range(256):
            if i < 50:
                self.table.append(0)
            else:
                self.table.append(1)

    def open(self):
        """
        打开浏览器,并输入查询内容
        """
        self.browser.get(self.url)
        self.browser.get(self.url + "/Sensebot/")
        self.browser.web_driver_wait_ruishu(10, "class", 'experience--area')
        time.sleep(1)
        self.browser.execute_js('document.getElementsByClassName("experience--area")[0].getElementsByTagName("div")'
                                '[2].getElementsByTagName("ul")[0].getElementsByTagName("li")[1].click()')

        time.sleep(1)
        self.browser.web_driver_wait_ruishu(10, "class", 'geetest_radar_tip')

        self.browser.execute_js('document.getElementsByClassName("geetest_radar_tip")[0].click()')

    def check_status(self):
        """
        检测是否需要滑块验证码
        :return:
        """
        self.browser.web_driver_wait_ruishu(10, "class", 'geetest_success_radar_tip_content')
        try:
            time.sleep(0.5)
            message = self.browser.find_element_by_class_name("geetest_success_radar_tip_content").text
            if message == "验证成功":
                return False
            else:
                return True
        except Exception as e:
            return True

    def get_images(self):
        """
        获取验证码图片
        :return: 图片的location信息
        """
        time.sleep(1)
        self.browser.web_driver_wait_ruishu(10, "class", 'geetest_canvas_slice')
        fullgb = self.browser.execute_js('document.getElementsByClassName("geetest_canvas_bg geetest_'
                                             'absolute")[0].toDataURL("image/png")')["value"]

        bg = self.browser.execute_js('document.getElementsByClassName("geetest_canvas_fullbg geetest_fade'
                                         ' geetest_absolute")[0].toDataURL("image/png")')["value"]
        return bg, fullgb


    def get_decode_image(self, filename, location_list):
        """
        解码base64数据
        """
        _, img = location_list.split(",")
        img = base64.decodebytes(img.encode())
        new_im: PngImagePlugin.PngImageFile = image.open(BytesIO(img))
        # new_im.convert("RGB")
        # new_im.save(filename)

        return new_im

    def compute_gap(self, img1, img2):
        """计算缺口偏移 这种方式成功率很高"""
        # 将图片修改为RGB模式
        img1 = img1.convert("RGB")
        img2 = img2.convert("RGB")

        # 计算差值
        diff = ImageChops.difference(img1, img2)

        # 灰度图
        diff = diff.convert("L")

        # 二值化
        diff = diff.point(self.table, '1')

        # 默认给了43
        left = 43

        # 横向43 到 260
        for w in range(left, diff.size[0]):
            lis = []
            # 纵向 0 到 160
            for h in range(diff.size[1]):
                if diff.load()[w, h] == 1:
                    lis.append(w)
                if len(lis) > 5:
                    return w

    def ease_out_quad(self, x):
        return 1 - (1 - x) * (1 - x)

    def ease_out_quart(self, x):
        return 1 - pow(1 - x, 4)

    def ease_out_expo(self, x):
        if x == 1:
            return 1
        else:
            return 1 - pow(2, -10 * x)

    def get_tracks_2(self, distance, seconds, ease_func):
        """
        根据轨迹离散分布生成的数学 生成  # 参考文档  https://www.jianshu.com/p/3f968958af5a
        成功率很高 90% 往上
        :param distance: 缺口位置
        :param seconds:  时间
        :param ease_func: 生成函数
        :return: 轨迹数组
        """
        distance += 20
        tracks = [0]
        offsets = [0]
        for t in np.arange(0.0, seconds, 0.1):
            ease = ease_func
            offset = round(ease(t / seconds) * distance)
            tracks.append(offset - offsets[-1])
            offsets.append(offset)
        # 与前期+20形成铺垫，最后来一个回滑
        tracks.extend([-3, -2, -3, -2, -2, -2, -2, -1, -0, -1, -1, -1])
        return tracks

    def get_track(self, distance):
        """
        根据物理学生成方式   极验不能用 成功率基本为0
        :param distance: 偏移量
        :return: 移动轨迹
        """
        distance += 20
        # 移动轨迹
        track = []
        # 当前位移
        current = 0
        # 减速阈值
        mid = distance * 3 / 5
        # 计算间隔
        t = 0.5
        # 初速度
        v = 0

        while current < distance:
            if current < mid:
                # 加速度为正2
                a = 2
            else:
                # 加速度为负3
                a = -3
            # 初速度v0
            v0 = v
            # 当前速度v = v0 + at
            v = v0 + a * t
            # 移动距离x = v0t + 1/2 * a * t^2
            move = v0 * t + 0.5 * a * (t ** 2)
            # 当前位移
            current += move
            # 加入轨迹
            track.append(round(move))
        track.extend([-3, -3, -2, -2, -2, -2, -2, -1, -1, -1, -1])
        return track

    def move_to_gap(self, track):
        """移动滑块到缺口处"""
        slider = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'geetest_slider_button')))
        ActionChains(self.browser).click_and_hold(slider).perform()

        while track:
            x = track.pop(0)
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
            time.sleep(0.02)

        ActionChains(self.browser).release().perform()

    def crack(self, n):
        # 打开浏览器
        self.open()

        if self.check_status():
            # 保存的图片名字
            bg_filename = 'bg.png'
            fullbg_filename = 'fullbg.png'

            # 获取图片
            bg_location_base64, fullbg_location_64 = self.get_images()

            # 根据位置对图片进行合并还原
            bg_img = self.get_decode_image(bg_filename, bg_location_base64)
            fullbg_img = self.get_decode_image(fullbg_filename, fullbg_location_64)
            # 获取缺口位置
            gap = self.compute_gap(fullbg_img, bg_img)
            print('缺口位置', gap)

            track = self.get_tracks_2(gap - self.BORDER, 1, self.ease_out_quart)
            print("滑动轨迹", track)
            print("滑动距离", functools.reduce(lambda x, y: x+y, track))
            self.move_to_gap(track)

            time.sleep(1)
            if not self.check_status():
                print('验证成功')
                # bg_img.save(f"bg_img{n}.png")
                # fullbg_img.save(f"fullbg{n}.png")
                return True
            else:
                print('验证失败')
                # 保存图片方便调试
                bg_img.save(f"bg_img{n}.png")
                fullbg_img.save(f"fullbg{n}.png")
                return False

        else:
            print("验证成功")
            return True


if __name__ == '__main__':
    print('开始验证')
    crack = Crack()
    # crack.crack(0)
    count = 0
    for i in range(10):
        if crack.crack(i):
            count += 1
    print(f"成功率：{count / 10 * 100}%")
