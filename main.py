#!/usr/bin/env python

# Author: Ryan Myers
# Models: Jeff Styers, Reagan Heller
#
# Last Updated: 2015-03-13
#
# This tutorial provides an example of creating a character
# and having it walk around on uneven terrain, as well
# as implementing a fully rotatable camera.

from direct.showbase.ShowBase import ShowBase
from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import CollisionHandlerQueue, CollisionRay
from panda3d.core import Filename, AmbientLight, DirectionalLight
from panda3d.core import PandaNode, NodePath, Camera, TextNode
from panda3d.core import CollideMask
from direct.gui.DirectGui import *
from direct.gui.OnscreenText import OnscreenText
from direct.actor.Actor import Actor
import random
import sys
import os
import math
import socket

# Function to put instructions on the screen.
def addButton(posz, scale, msg):
    return DirectButton(text = (msg), text_fg=(255,255,255,255), text_scale=0.5, scale=scale, parent=base.a2dTopLeft, pos=(0.55, 0, -0.55), image="gwButton.jpg", image_scale=(1,0,0.4), image_pos=(0,0,0.1),  frameSize=(-1,1,0,0.5), borderWidth=(0,0), frameColor=(255,0,0,0))

# Function to put instructions on the screen.
def addInstructions(pos, msg):
    return OnscreenText(text=msg, style=1, fg=(1, 1, 1, 1), scale=.05,
                        shadow=(0, 0, 0, 1), parent=base.a2dTopLeft,
                        pos=(0.08, -pos - 0.04), align=TextNode.ALeft)

# Function to put title on the screen.
def addTitle(text):
    return OnscreenText(text=text, style=1, fg=(1, 1, 1, 1), scale=.07,
                        parent=base.a2dBottomRight, align=TextNode.ARight,
                        pos=(-0.1, 0.09), shadow=(0, 0, 0, 1))


class RoamingRalphDemo(ShowBase):

    def __init__(self):
        # Set up the window, camera, etc.
        ShowBase.__init__(self)

        # Used for networking
        self.chosenLatency = 0
        self.socket = socket.socket()
        port = 12345
        self.socket.connect(('127.0.0.1', port))
        print(self.socket.recv(1024))

        # Mouse settings
        self.defaultMousePosition = [0., 0.]
        self.lastMousePosition = self.defaultMousePosition
        self.desiredZoom = 10

        # Set the background color to black
        self.win.setClearColor((1, 1, 1, 1))
        self.win.setClearColorActive(1)

        # This is used to store which keys are currently pressed.
        self.keyMap = {
            "left": 0, "right": 0, "forward": 0, "backward": 0, "cam-left": 0, "cam-right": 0, "cam-multi": 0, "cam-multi-end": 0, "cam-zoom-up": 0, "cam-zoom-down": 0, "chat": 0}

        # Post the instructions
        #self.title = addTitle("Guigui Tutorial: Roaming Ralph (Walking on Uneven Terrain)")
        #self.inst1 = addInstructions(0.06, "[ESC]: Quit")
        #self.inst2 = addInstructions(0.12, "[Left Arrow]: Rotate Ralph Left")
        #self.inst3 = addInstructions(0.18, "[Right Arrow]: Rotate Ralph Right")
        #self.inst4 = addInstructions(0.24, "[Up Arrow]: Run Ralph Forward")
        #self.inst4 = addInstructions(0.30, "[Down Arrow]: Run Ralph Backward")
        #self.inst6 = addInstructions(0.36, "[A]: Rotate Camera Left")
        #self.inst7 = addInstructions(0.42, "[E]: Rotate Camera Right")

        b = addButton(0., .1, "start")

        
        def clearText():
	        self.chatEntry.enterText('')

        def setText(textEntered):
            clearText()
            print(textEntered)

        self.chatEntry = DirectEntry(text = "", width=30, scale=.05, initialText="Type Something", numLines = 2, focus=0, pos=(-1.2, 0, -0.6), command=setText, focusInCommand=clearText)
        #skills = OnscreenImage(image = 'gwSkills.jpg', pos = (0, 0, 0), scale=0.5)
        myFrame = DirectFrame(frameColor=(255, 0, 0, 255),
                      frameSize=(-0.6, 0.6, -0.25, 0.05),
                      pos=(0, 0, -0.88), image = 'gwSkills.jpg', image_scale=(0.7,0,0.12))

        #imageObject = OnscreenImage(image = 'gwButton.jpg', pos = (-0.5, 0, 0.02))

        # Set up the environment
        #
        # This environment model contains collision meshes.  If you look
        # in the egg file, you will see the following:
        #
        #    <Collide> { Polyset keep descend }
        #
        # This tag causes the following mesh to be converted to a collision
        # mesh -- a mesh which is optimized for collision, not rendering.
        # It also keeps the original mesh, so there are now two copies ---
        # one optimized for rendering, one for collisions.

        self.environ = loader.loadModel("models/world")
        self.environ.reparentTo(render)

        # Create the main character, Ralph

        ralphStartPos = self.environ.find("**/start_point").getPos()
        self.ralph = Actor("models/ralph",
                           {"run": "models/ralph-run",
                            "walk": "models/ralph-walk"})
        self.ralph.reparentTo(render)
        self.ralph.setScale(.2)
        self.ralph.setPos(ralphStartPos + (0, 0, 0.5))

        # Create a floater object, which floats 2 units above ralph.  We
        # use this as a target for the camera to look at.

        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(self.ralph)
        self.floater.setZ(2.0)

        # Accept the control keys for movement and rotation

        self.accept("escape", sys.exit)
        self.accept("arrow_left", self.setKey, ["left", True])
        self.accept("arrow_right", self.setKey, ["right", True])
        self.accept("arrow_up", self.setKey, ["forward", True])
        self.accept("arrow_down", self.setKey, ["backward", True])
        self.accept("a", self.setKey, ["cam-left", True])
        self.accept("e", self.setKey, ["cam-right", True])
        self.accept("mouse3", self.setKey, ["cam-multi", True])
        self.accept("wheel_up", self.setKey, ["cam-zoom-up", True])
        self.accept("wheel_down", self.setKey, ["cam-zoom-down", True])
        self.accept("enter", self.setKey, ["chat", True])

        self.accept("arrow_left-up", self.setKey, ["left", False])
        self.accept("arrow_right-up", self.setKey, ["right", False])
        self.accept("arrow_up-up", self.setKey, ["forward", False])
        self.accept("arrow_down-up", self.setKey, ["backward", False])
        self.accept("a-up", self.setKey, ["cam-left", False])
        self.accept("e-up", self.setKey, ["cam-right", False])
        self.accept("mouse3-up", self.setKey, ["cam-multi-end", True])
        #self.accept("mouse2-up", self.setKey, ["cam-zoom", False])
        self.accept("enter-up", self.setKey, ["chat", False])

        taskMgr.add(self.move, "moveTask")

        # Game state variables
        self.isMoving = False

        # Set up the camera
        self.disableMouse()
        self.camera.setPos(self.ralph.getX(), self.ralph.getY() + 20, 2)

        # We will detect the height of the terrain by creating a collision
        # ray and casting it downward toward the terrain.  One ray will
        # start above ralph's head, and the other will start above the camera.
        # A ray may hit the terrain, or it may hit a rock or a tree.  If it
        # hits the terrain, we can detect the height.  If it hits anything
        # else, we rule that the move is illegal.
        self.cTrav = CollisionTraverser()

        self.ralphGroundRay = CollisionRay()
        self.ralphGroundRay.setOrigin(0, 0, 9)
        self.ralphGroundRay.setDirection(0, 0, -1)
        self.ralphGroundCol = CollisionNode('ralphRay')
        self.ralphGroundCol.addSolid(self.ralphGroundRay)
        self.ralphGroundCol.setFromCollideMask(CollideMask.bit(0))
        self.ralphGroundCol.setIntoCollideMask(CollideMask.allOff())
        self.ralphGroundColNp = self.ralph.attachNewNode(self.ralphGroundCol)
        self.ralphGroundHandler = CollisionHandlerQueue()
        self.cTrav.addCollider(self.ralphGroundColNp, self.ralphGroundHandler)

        self.camGroundRay = CollisionRay()
        self.camGroundRay.setOrigin(0, 0, 9)
        self.camGroundRay.setDirection(0, 0, -1)
        self.camGroundCol = CollisionNode('camRay')
        self.camGroundCol.addSolid(self.camGroundRay)
        self.camGroundCol.setFromCollideMask(CollideMask.bit(0))
        self.camGroundCol.setIntoCollideMask(CollideMask.allOff())
        self.camGroundColNp = self.camera.attachNewNode(self.camGroundCol)
        self.camGroundHandler = CollisionHandlerQueue()
        self.cTrav.addCollider(self.camGroundColNp, self.camGroundHandler)

        # Uncomment this line to see the collision rays
        #self.ralphGroundColNp.show()
        #self.camGroundColNp.show()

        # Uncomment this line to show a visual representation of the
        # collisions occuring
        #self.cTrav.showCollisions(render)

        # Create some lighting
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor((.3, .3, .3, 1))
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection((-5, -5, -5))
        directionalLight.setColor((1, 1, 1, 1))
        directionalLight.setSpecularColor((1, 1, 1, 1))
        render.setLight(render.attachNewNode(ambientLight))
        render.setLight(render.attachNewNode(directionalLight))

    # Records the state of the arrow keys
    def setKey(self, key, value):
        self.keyMap[key] = value

    # Accepts arrow keys to move either the player or the menu cursor,
    # Also deals with grid checking and collision detection
    def move(self, task):

        # Get the time that elapsed since last frame.  We multiply this with
        # the desired speed in order to find out with which distance to move
        # in order to achieve that desired speed.
        dt = globalClock.getDt()

        # If the camera-left key is pressed, move camera left.
        # If the camera-right key is pressed, move camera right.
        #if self.keyMap["chat"]:
            
        if self.keyMap["cam-zoom-up"] and self.desiredZoom > 1:
            self.camera.setY(self.camera, +80 * dt)
            self.keyMap["cam-zoom-up"] = False
            self.desiredZoom -= 1
        if self.keyMap["cam-zoom-down"] and self.desiredZoom < 16:
            self.camera.setY(self.camera, -80 * dt)
            self.keyMap["cam-zoom-down"] = False
            self.desiredZoom += 1
        if self.keyMap["cam-left"]:
            self.camera.setX(self.camera, -20 * dt)
        if self.keyMap["cam-right"]:
            self.camera.setX(self.camera, +20 * dt)
        if self.keyMap["cam-multi-end"] and self.keyMap["cam-multi"]:
            self.keyMap["cam-multi"] = False
            self.keyMap["cam-multi-end"] = False
            self.lastMousePosition = self.defaultMousePosition
        if self.keyMap["cam-multi"]:
            # Mouse movements
            md = base.win.getPointer(0)
            mouseX = md.getX()
            mouseY = md.getY()
            newMousePosition = [mouseX, mouseY]
            if self.lastMousePosition != newMousePosition:
                json = "{\"mouse : \"" + str(newMousePosition) + "}"
                #print(json)
            deltaMouseX = newMousePosition[0] - self.lastMousePosition[0]
            deltaMouseY = newMousePosition[0] - self.lastMousePosition[0]
            #print(deltaMouseX)
            if(self.lastMousePosition != self.defaultMousePosition):
                if(deltaMouseX > 0):
                    self.camera.setX(self.camera, deltaMouseX * dt)
                elif(deltaMouseX < 0):
                    self.camera.setX(self.camera, deltaMouseX * dt)
                if(deltaMouseY > 0):
                    self.camera.setY(self.camera, deltaMouseY * dt)
                elif(deltaMouseY < 0):
                    self.camera.setY(self.camera, deltaMouseY * dt)

            self.lastMousePosition = [mouseX, mouseY]

        # save ralph's initial position so that we can restore it,
        # in case he falls off the map or runs into something.

        startpos = self.ralph.getPos()

        # If a move-key is pressed, move ralph in the specified direction.

        if self.keyMap["left"]:
            self.ralph.setH(self.ralph.getH() + 300 * dt)
            self.camera.setX(self.camera, +50 * dt)
        if self.keyMap["right"]:
            self.ralph.setH(self.ralph.getH() - 300 * dt)
            self.camera.setX(self.camera, -50 * dt)
        if self.keyMap["forward"]:
            self.ralph.setY(self.ralph, -25 * dt)
        if self.keyMap["backward"]:
            self.ralph.setY(self.ralph, +25 * dt)

        # If ralph is moving, loop the run animation.
        # If he is standing still, stop the animation.

        if self.keyMap["forward"] or self.keyMap["backward"] or self.keyMap["left"] or self.keyMap["right"]:
            if self.isMoving is False:
                self.ralph.loop("run")
                self.ralph.setPlayRate(1.3, "run")
                self.isMoving = True
        else:
            if self.isMoving:
                self.ralph.stop()
                self.ralph.pose("walk", 5)
                self.isMoving = False

        # If the camera is too far from ralph, move it closer.
        # If the camera is too close to ralph, move it farther.

        camvec = self.ralph.getPos() - self.camera.getPos()
        camvec.setZ(0)
        camdist = camvec.length()
        camvec.normalize()
        if camdist > 20.0:
            self.camera.setPos(self.camera.getPos() + camvec * (camdist - 20))
            camdist = 20.0
        if camdist < 5.0:
            self.camera.setPos(self.camera.getPos() - camvec * (5 - camdist))
            camdist = 5.0

        # Player Collision

        # Normally, we would have to call traverse() to check for collisions.
        # However, the class ShowBase that we inherit from has a task to do
        # this for us, if we assign a CollisionTraverser to self.cTrav.
        self.cTrav.traverse(render)

        # Adjust ralph's Z coordinate.  If ralph's ray hit terrain,
        # update his Z. If it hit anything else, or didn't hit anything, put
        # him back where he was last frame.

        entries = list(self.ralphGroundHandler.getEntries())
        entries.sort(key=lambda x: x.getSurfacePoint(render).getZ())

        if len(entries) > 0 and entries[0].getIntoNode().getName() == "terrain":
            self.ralph.setZ(entries[0].getSurfacePoint(render).getZ())
        else:
            self.ralph.setPos(startpos)

        #print(type(startpos))
        #print(type(self.floater))

        # Network latency
        if self.chosenLatency < 6:
            self.chosenLatency += 1
        else:
            self.chosenLatency = 0
            if self.isMoving:
                networkPosion = [self.ralph.getX(), self.ralph.getY(), self.ralph.getZ()]
                json = "{\"character : \"" + str(networkPosion) + "}"
                #c.send(json)
                #print(json)


        # Keep the camera at one foot above the terrain,
        # or two feet above ralph, whichever is greater.

        entries = list(self.camGroundHandler.getEntries())
        entries.sort(key=lambda x: x.getSurfacePoint(render).getZ())

        if len(entries) > 0 and entries[0].getIntoNode().getName() == "terrain":
            self.camera.setZ(entries[0].getSurfacePoint(render).getZ() + 1.0)
        if self.camera.getZ() < self.ralph.getZ() + 2.0:
            self.camera.setZ(self.ralph.getZ() + 2.0)

        # The camera should look in ralph's direction,
        # but it should also try to stay horizontal, so look at
        # a floater which hovers above ralph's head.
        self.camera.lookAt(self.floater)

        #c.close()
        return task.cont


demo = RoamingRalphDemo()
demo.run()
