""" second attempt at a verlet curtain
    Aamod Atre Oct 31 2021 """

#!/usr/bin/python3
import os
import glob
import subprocess
subprocess.run("rm -rf ./Clips/*.jpeg", shell = True)

""" python3 dependencies """
from PIL import Image
import numpy as np
import pygame 
from scipy.spatial.distance import euclidean as edist

class curtain(object):
    def __init__(self,args):
        """ physical parameters """

        self.damp = 0.8         # dampening
        self.gravity = 0.599
        self.friction = 0.999
        
        """ simulation parameters """
        self.min_dist = args.min_dist
        self.radius = 1
        self.tmax = 1500
        self.time = 0

        self.point = self.point_generator(args.width, args.height, args.size, args.side)
        self.stick = self.stick_generator(args.width, args.height, self.point)
        self.run_pygame(args)
        self.animate()
    def point_generator(self, width, height, size, side):
        begin = size/2. - (width * side)/2.
        point = np.zeros((height,width,5), dtype = np.float64) # xf, yf, xi, yi, pinning_bool

        for h in range(height):
            for w in range(width):
                point[h,w] = [begin+w*side, 50+h*side, begin+w*side, 50+h*side, h == 0]
        point = np.reshape(point,(height*width,5))
        return point

    def stick_generator(self,width, height, point):
        # hidden = False
        stick = []
        for h in range(height):
            for w in range(width):
                
                if w+1 in range(width):
                    stick.append([point[w+(h*width)],point[w+(h*width)+1],edist(point[w+(h*width)][:2],point[w+(h*width)+1][:2])]) # ,hidden])
                
                if h+1 in range(height):
                    stick.append([point[w+(h*width)],point[w+(h*width)+width],edist(point[w+(h*width)][:2],point[w+(h*width)+width][:2])]) #,hidden])
        return stick
    
    def run_pygame(self,args):
        pygame.init()
        RUN = True
        disp = pygame.display.set_mode((args.size,args.size))
        pygame.display.set_caption("Weaving...")

        while RUN:
            keys = pygame.key.get_pressed()
            for event in pygame.event.get():
                if event.type == pygame.QUIT or keys[pygame.K_ESCAPE]:
                    RUN = False
                elif event.type == pygame.MOUSEMOTION:
                    (mx,my) = event.pos
                    # print(f"the mouse position is {mx}, {my}")

            self.update_points(mx, my)
            for _ in range(args.constrain):
                """The loop is inserted to maintain the square perfectly"""
                self.update_sticks()
                self.constrain_points(args.size)
            
            points = []
            for each in self.point:
                points.append([round(p) for p in each])
            self.render(disp, points)
            pygame.image.save(disp, "./Clips/Curtain_{}_{:07}.jpeg".format(args.size,pygame.time.get_ticks()))
        pygame.quit()
    
    def render(self, disp, points):
        disp.fill((255, 255, 255))
        for each in self.stick:
            pygame.draw.aaline(disp, (0,0,0), (each[0][0],each[0][1]),(each[1][0],each[1][1]))

        for each in points:
            pygame.draw.circle(disp, (0,0,0), (each[0],each[1]), self.radius)
        pygame.display.update()

    def update_points(self,mx, my):
        for each in self.point:
            if not each[-1]: # If point not hidden

                # verlet
                vx = self.friction*((each[0] - each[2]))
                vy = self.friction*((each[1] - each[3]))
                each[2] = each[0]
                each[3] = each[1]
                each[0] += vx
                each[1] += vy
                each[1] = (each[1]+self.gravity)

                # For mouse interactions
                dx = each[0] - mx
                dy = each[1] - my
                dist = np.sqrt(dx*dx + dy*dy)
                if dist < self.min_dist:
                    fx = 2*(self.min_dist/(0.000000001+ dx))
                    fy = 2*(self.min_dist/(0.000000001+ dy))
                    each[0] += fx
                    each[1] += fy


    def update_sticks(self):
        for each in self.stick:
            dx = each[1][0] - each[0][0]
            dy = each[1][1] - each[0][1]
            distance = np.sqrt(dx*dx+dy*dy)
            difference = each[2] - distance
            percent = difference / (2*distance)
            offsetx = dx*percent
            offsety = dy*percent
            if not each[0][-1]:		
                each[0][0] -= offsetx
                each[0][1] -= offsety
            if not each[1][-1]:
                each[1][0] += offsetx
                each[1][1] += offsety		
        
    def constrain_points(self, size):
        """ Introduced to improve the boundary conditions:
		Simple boundary conditions can prevent the spehere from 
		leaving the screen, but the readjusted sticks may still 
		be placed outside. Thus an iterative process is required"""
    
        for each in self.point:
            if not each[-1]:
                vx = self.friction*((each[0] - each[2]))
                vy = self.friction*((each[1] - each[3]))

                if  each[0] > 2*size-1:
                    each[0] = 2*size-1
                    each[2] = each[0] + (vx*self.damp)
                elif each[0]< 0:
                    each[0] = 0
                    each[2] = each[0] + (vx*self.damp)
                if  each[1]> size-1:
                    each[1] = size-1 
                    each[3] = each[1] + (vy*self.damp)
                elif each[1] < 0:
                    each[1] = 0
                    each[3] = each[1] +(vy*self.damp)
    
    def animate(self):
        # filepaths
        cwd = os.getcwd()
        fp_in = cwd + "/Clips/*.jpeg"
        fp_out = cwd + "/curtain.gif"
        ti = int(sorted(glob.glob(fp_in))[0].split('_')[-1].split('.')[0])
        tf = int(sorted(glob.glob(fp_in))[-1].split('_')[-1].split('.')[0])
        
        # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#gif
        img, *imgs = [Image.open(f) for f in sorted(glob.glob(fp_in))]
        img.save(fp=fp_out, format='GIF', append_images=imgs,
                save_all=True, duration=(tf - ti)/1000., loop=0)

class args(object):
    def __init__(self):
        # warning - don't exceed 50
        self.width = 24  # width of the curtain
        self.height = 27 # height of the curtain
        self.size = 600 # size of the pop-up --> some bugs here, won't accept small values
        self.side = 12   # side of each square

        self.constrain = 5 # change this to make things funkier
        self.min_dist = 8



if __name__ == "__main__":
    a = args()
    c = curtain(a)
    """ Press ESC to Exit """



