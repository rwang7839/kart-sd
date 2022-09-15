import time
import math

import numpy as np
import cv2
import pygame as pg


def project(*args):
    for point in args:
        att = math.pi / 180 * 0.38 * (point[1] + 13)  # + difference between horizon and index at top of image
        azi = math.pi / 180 * 0.38 * (point[0] - 64)  # - half of image width
        dist = 0.7 / math.tan(att)  # dist : distance on ground from camera to px location
        x = dist * math.sin(azi)
        y = dist * math.cos(azi)

        vs_x = round((x + 5.0625) / 0.125)  # Adjust x to move 0 from center to left
        vs_y = round((y - 0.0625) / 0.125)  # Pull y half a vs block down
        vs[vs_y, vs_x] = 1


window = pg.display.set_mode((810, 810))
pg.init()

# Load data
vid_arr = np.loadtxt("center - Copy.csv", dtype="float16", delimiter=",")
steer_arr = vid_arr[:, 0]
vid_arr = np.delete(vid_arr, 0, axis=1)
vid_arr = vid_arr.astype("uint8")

# Init video and vs displays
prev_img_num = -1
img_num = 0

cv2.namedWindow("a", cv2.WINDOW_NORMAL)
cv2.resizeWindow("a", 512, 384)

cv2.namedWindow("b", cv2.WINDOW_NORMAL)
cv2.resizeWindow("b", 512, 384)

car = pg.Surface((70, 110))
pg.draw.rect(car, (0, 0, 0), (0, 0, 70, 110))

vs = np.zeros((70, 81))
prev = False
with open("vs_train.csv", "a") as file:
    while True:
        # Handle key pressed
        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                keys = pg.key.get_pressed()
                if keys[pg.K_d]:
                    img_num += 1
                if keys[pg.K_a]:
                    img_num -= 1

        # Handle mouse click to flip pixels
        buttons = pg.mouse.get_pressed(num_buttons=3)
        x_coord, y_coord = pg.mouse.get_pos()

        x = round((x_coord - 5) / 10)
        y = round((y_coord - 5) / 10)

        if buttons[0]:
            vs[69 - y, x] = 1
        elif buttons[2]:
            vs[69 - y, x] = 0

        if img_num != prev_img_num:
            # Write previous completed image and vs to file
            if prev:
                img = img.reshape(36864)
                vs = vs.reshape(5670)
                full = np.concatenate((img, vs))
                np.savetxt(file, [full], fmt="%.0f", delimiter=",")

            # Get new image
            steer = steer_arr[img_num]
            img = vid_arr[img_num]
            img = img.reshape(96, 128, 3)
            cv2.imshow("a", img)

            edges_img = cv2.Canny(img, 100, 200, apertureSize=3)

            edges_img[:29] = 0
            cv2.imshow("b", edges_img)
            print(steer, img_num)

            # Compute physical x and y for pixels in edges
            vs = np.zeros((70, 81))  # rows, columns
            for px_y, row in enumerate(edges_img[30:]):  # px_y : pixels below horizon
                for px_x, pos in enumerate(row):  # px_x : pixels from left (48 to center)
                    if pos == 255:
                        project((px_x, px_y), (px_x, px_y + 0.2), (px_x, px_y - 0.2),
                                (px_x, px_y + 0.4), (px_x, px_y - 0.4))

            prev_img_num = img_num
            prev = True

        # Display vs
        window.fill((255, 255, 255))
        window.blit(car, (370, 700))
        for n_y, y_row in enumerate(vs):
            for n_x, x in enumerate(y_row):
                if x == 1:
                    rect = pg.Surface((10, 10))
                    pg.draw.rect(rect, (0, 0, 0), (0, 0, 10, 10))
                    window.blit(rect, (10*n_x, 690-(10*n_y)))
        pg.display.update()

        if cv2.waitKey(1) == ord("f"):
            cv2.destroyAllWindows()
            cv2.VideoCapture(0).release()
            break
