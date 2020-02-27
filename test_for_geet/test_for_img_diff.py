#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   test_for_img_diff.py    
@Auther  :  will_kkc 
@data    :  2020/1/13 15:20
@descr   :
'''

from PIL import ImageChops, PngImagePlugin ,Image
import numpy as np
A = 'bg_img0.png'
B = 'fullbg0.png'


img1 = Image.open(A)
img2 = Image.open(B)

img1 = img1.convert("RGB")
img2 = img2.convert("RGB")


def compute_gap(img1, img2):
	table = []
	for i in range(256):
		if i < 50:
			table.append(0)
		else:
			table.append(1)
	diff = ImageChops.difference(img1, img2)
	diff = diff.convert("L")
	diff = diff.point(table, '1')
	return diff



d = compute_gap(img1, img2)
# d.show()
print(d.size)
# im = np.array(d)
# np.savetxt("new1.csv", im, delimiter=',',fmt='%d')
# print(im)