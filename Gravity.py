#
# Using parts of code from Pong.py, copyright Tristam Macdonald 2008.
# 
#
# Distributed under the Boost Software License, Version 1.0
# (see http://www.boost.org/LICENSE_1_0.txt)
#
 
import random, math
 
import pyglet
from pyglet.gl import *
from pyglet.window import mouse
 
# create the window, but keep it offscreen until we are done with setup
windowX = 1280
windowY = 720
window = pyglet.window.Window(1280, 720, visible=False, caption="Oscar's Amazing Gravity Playground")
 
# centre the window on whichever screen it is currently on (in case of multiple monitors)
window.set_location(window.screen.width/2 - window.width/2, window.screen.height/2 - window.height/2)
 
# create a batch to perform all our rendering
batch = pyglet.graphics.Batch()



class Planet(pyglet.sprite.Sprite):
    def __init__(self, input):
        
        pattern = pyglet.image.SolidColorImagePattern((255, 255, 255, 255))
 
        image = pyglet.image.create(8, 8, pattern)
        image.anchor_x, image.anchor_y = 4, 4
 
        pyglet.sprite.Sprite.__init__(self, image, batch=batch)
        
        
        self.x = input[0] 
        self.y = input[1] 
        self.mass = input[2]
        self.vx = input[3]
        self.vy = input[4]

class PlanetControl:
    def __init__(self):
        # a list of tuples with the form (x, y, mass, vx, vy)
        self.planets = [] 
        # If set to True, objects will bounce of the edges of the screen
        self.bounce = False
        # Constants
        self.G = 6.67 # *10^-11
        self.AU = 149567871000 # 1 AU in metres
        # Factors for scale, mass and time
        self.scale = 480000000 # 480 * 10^6 - 1 AU in 400px
        self.mf = 10000000000000 # 10^24 = 10^24 - 10^11 to compensate for G
        self.tf = 100000 # 31536000 for the earth to orbit the sun in 1 second
        
    def create(self, x, y, mass=5.98, vx=0, vy=0):
        # Default mass is equal to the earth
        # planet has the form (x, y, mass, vx, vy)
        planet = (x, y, mass, vx, vy)
        self.planets.append(Planet(planet))
        
    def update(self, dt):
        dt *= self.tf
        for p1 in self.planets:
            resX = 0
            resY = 0
            altered = False
            for p2 in self.planets:
                if p1 != p2:
                    # Get the relative distance between the two planets
                    x = p2.x - p1.x
                    y = p2.y - p1.y
                    
                    # Get the distance between the two planets
                    r = math.sqrt(x**2 + y**2) 
                    
                    if r**2 < 5:
                        self.combine_planets(p1, p2)
                        altered = True
                    else:
                        # Calculate the components of the acceleration and add to the resultant
                        a = (self.G*p2.mass)/ (r)**2
                        
                        # Find the direction the other planet is in
                        angle = math.atan2(y,x)
                        
                        ax = a*math.cos(angle)
                        ay = a*math.sin(angle)
                        resX += ax
                        resY += ay
            
            if not altered:
                
                # delta Momentum = ft, therefore delta Velocity = ft/mass
                p1.vx += resX * dt
                p1.vy += resY * dt
                
                p1.x += p1.vx * dt / self.scale
                p1.y += p1.vy * dt / self.scale
                
                #Bounce the Planets
                if self.bounce:
                    if p1.x > windowX or p1.x < 0:
                        p1.vx = -p1.vx
                        p1.x += p1.vx * dt / self.scale
                    
                    if p1.y > windowY or p1.y < 0:
                        p1.vy = -p1.vy
                        p1.y += p1.vy*dt / self.scale
                else:
                    if p1.x > windowX or p1.x < 0 or p1.y > windowY or p1.y < 0:
                        self.planets.remove(p1)
    
    def combine_planets(self, p1, p2):
        print "Combining Planets..."
        if p1 != p2:
            # Find the total momentum
            p1Mx = p1.mass * p1.vx
            p1My = p1.mass * p1.vy
            p2Mx = p2.mass * p2.vx
            p2My = p2.mass * p2.vy
            
            Mx = p1Mx + p2Mx
            My = p1My + p2My
            
            mass = p1.mass + p2.mass
            vx = Mx / mass
            vy = My / mass
            
            self.planets.remove(p2)
            
            p1.mass = mass
            p1.vx = vx
            p1.vy = vy
#            planet = (p1.x, p1.y, mass, vx, vy)
#            self.planets.append(Planet(planet))
            
        else:
            raise ValueError
    
    def reset(self):
        self.planets = []
        self.create(window.width/2,window.height/2,mass=1990000)
        self.create(window.width/2, window.height/2 + 300, vx=3000000, vy=0)
 
addPlanet = False
# In the form (x, y)
newPlanet = [0,0]
mdrag = False
@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    global mdrag, newPlanet
    newPlanet = [x, y]
    mdrag = True

@window.event
def on_mouse_release(x, y, button, modifiers):
    global mdrag
    mdrag = False

mousex, mousey = 0, 0
@window.event
def on_mouse_motion(x, y, dx, dy):
    global mousex, mousey
    mousex = x
    mousey = y
# setup a key handler to track keyboard input
keymap = pyglet.window.key.KeyStateHandler()
window.push_handlers(keymap)
 
# setup a stack for our game states
states = []
 
# this game state does nothing until the space bar is pressed
# at which point it returns control to the previous state
class PausedState:
    def update(self, dt):
        if keymap[pyglet.window.key.SPACE]:
            states.pop()
 
# this class plays the actual game
class GameState:
    def __init__(self):
 
        # Create the planet controller
        self.control = PlanetControl()
        self.control.reset()
        
        self.keys = {"UP":False,"SPACE":False}

    # moves the player paddle based on keyboard input
    def handle_player(self, dt):
        if not keymap[pyglet.window.key.UP] and self.keys["UP"]:
            self.reset()
            self.keys["UP"] = False
        if keymap[pyglet.window.key.UP]:
            self.keys["UP"] = True
        if keymap[pyglet.window.key.SPACE]:
            #states.append(PausedState())
            self.control.create(mousex, mousey)
             
    # used to reset the ball and paddle locations between rounds
    def reset(self):
        self.control.reset()
        
    def check_mouse(self):
        global addPlanet
        if mdrag:
            addPlanet = True
            newx, newy = newPlanet[0], newPlanet[1]
            pyglet.graphics.draw(2, pyglet.gl.GL_LINES,
                ('v2f', (mousex, mousey, newx, newy)),
                ('c3B', (0, 0, 255, 0, 255, 0))
            )
        if addPlanet and not mdrag:
            newx = newPlanet[0]
            newy = newPlanet[1]
            print (newx-mousex)*10000
            self.control.create(mousex, mousey, vx=(newx-mousex)*10000, vy=(newy-mousey)*10000)
            
            addPlanet = False
 
    def update(self, dt):
        self.handle_player(dt)
        self.check_mouse()
        self.control.update(dt)
 
# clear the window and draw the scene
fps_display = pyglet.clock.ClockDisplay()
@window.event
def on_draw():
    window.clear()
    fps_display.draw()
 
    batch.draw()
 
# update callback
def update(dt):
    # update the topmost state, if we have any
    if len(states):
        states[-1].update(dt)
    # otherwise quit
    else:
        pyglet.app.exit()
 
# game starts paused
states.append(PausedState())
# setup the inital states
states.append(GameState())
 
# schedule the update function, 60 times per second
pyglet.clock.schedule_interval(update, 1.0/1000)
 
# clear and flip the window, otherwise we see junk in the buffer before the first frame
window.clear()
window.flip()
 
# make the window visible at last
window.set_visible(True)
 
# finally, run the application
pyglet.app.run()
