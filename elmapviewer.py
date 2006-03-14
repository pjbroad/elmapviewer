#! /usr/bin/env python

# Eternal Lands Map Viewer
#
# Copyright 2006 Paul Broadhead
# Contact: elmapviewer@twinmoons.clara.co.uk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# Eternal Lands is a FREE MMORPG (massively multiplayer online role
# playing game). This program displays Eternal Lands maps and game data and
# allows the user to navigate the maps using map links.  It was written as
# an experiment in the use of both the Python language and the Pygame
# modules.  It suits my personal use and I release it in the hope it may
# be useful to others.  I am not a Python or Pygame expert as I think you
# can tell from the code :)

# Written using Python 2.3.5 and Pygame 2.3 but other versions should 
# work.  The code was developed on the Debian GNU/Linux operating system
# and tested on Ubuntu Linux.

# Eternal Lands: http://www.eternal-lands.com/
# Python: http://www.python.org
# Pygame: http://www.pygame.org
# Debian GNU/Linux: http://www.debian.org/
# Ubuntu: http://www.ubuntu.com/

import sys, pygame, string, os, shutil

version = 'V0.1 Feb/Mar 2006'

# define some basic colours
blackcolour = 0, 0, 0
redcolour = 255, 0, 0
greencolour = 0, 255, 0
bluecolour = 0, 0, 255
yellowcolour = 255, 255, 0
cyancolour = 0, 255, 255
whitecolour = 255, 255, 255
# and some item colours
pkmapcolour = redcolour
othermapcolour = greencolour
markcolour = 179, 238,  58
markcrosscolour = whitecolour
boxcolour = 58, 95, 205
testboxcolour = cyancolour
helpcolour = 205, 190, 112

# expand ~ and environ vars
def expandfilename(filename):
  filename = os.path.expanduser(filename)
  filename = os.path.expandvars(filename)
  return filename

# read map information from the resource file
# links, names, sizes, types
def readinfo(fname):
  mapinfo = {}
  mapscale = {}
  maptype = {}
  bigmap = {}
  allmaps = []
  fid = open(fname, 'r')
  mapinfolines = fid.readlines()
  currmapname = ''
  for line in mapinfolines:
    if line != '\n' and line[0] != "#":
      w = line.split()
      # new map uses line format "filename: sizeX sizeY [type]"
      if len(w) > 1 and w[1] == '=':
        continue;
      if w[0][len(w[0])-1] == ":":
        currmapname = w[0][:len(w[0])-1]
        allmaps.append(currmapname)
        if len(w) > 2:
          mapscale[currmapname] = (int(w[1]), int(w[2]))
        if len(w) > 3:
          maptype[currmapname] = w[3]
        if len(w) > 4:
          bigmap[currmapname] = w[4]
      # link line format "tlX tlR width height <link map name>"
      else:
        newlink = (((int(w[0]), int(w[1]), int(w[2]), int(w[3])),w[4]),)
        if mapinfo.has_key(currmapname):
          mapinfo[currmapname] += newlink
        else:
          mapinfo[currmapname] = newlink
  for mapname in allmaps:
    if not mapinfo.has_key(mapname):
      newlink = (((0, 0, 0, 0),''),)
      mapinfo[mapname] = newlink
  fid.close()
  return mapinfo, mapscale, maptype, bigmap

# read program variables from the resource file
def readvars(fname):
  mapdir = ''
  userdir = ''
  scale = 1.0
  fullscreen = False
  boxesOn = True
  marksOn = True
  editor = '$EDITOR'
  # create a defaul rc file if none exists
  if not os.access(fname, os.R_OK):
    srcfile = os.path.dirname(sys.argv[0]) + '/example.elmapviewer.rc'
    dstfile = expandfilename('~/.elmapviewer.rc')
    shutil.copyfile(srcfile,dstfile)
    print 'Default ~/.elmapviewer.rc file created, you may need to change some options.'
  fid = open(fname, 'r')
  mapinfolines = fid.readlines()
  for line in mapinfolines:
    if line != '\n' and line[0] != '#':
      w = line.split()
      # variable line format name = value
      if len(w) > 1 and w[1] == '=':
        # location of EL maps
        if w[0] == 'mapdir':
          mapdir = expandfilename(w[2])
          if not os.access(mapdir, os.R_OK):
            print 'Please set the mapdir option in your rc file: ' + rcfile
            sys.exit(-1)
        # location of user map information
        if w[0] == 'userdir':
          userdir = expandfilename(w[2])
        if w[0] == 'scale':
          scale = float(w[2])
        if w[0] == 'fullscreen':
          fullscreen = bool(int(w[2]))
        if w[0] == 'boxesOn':
          boxesOn = bool(int(w[2]))
        if w[0] == 'marksOn':
          marksOn = bool(int(w[2]))
        if w[0] == 'editor':
          editor = expandfilename(w[2])
  fid.close()
  return mapdir, userdir, scale, fullscreen, boxesOn, marksOn, editor

# get the name of the next map in the list
def nextmap(mapinfo, currmap, inc):
  mapnames = mapinfo.keys()
  mapnames.sort()
  next = mapnames.index(currmap) + inc
  if next >= len(mapnames):
    next -= len(mapnames)
  if next < 0:
    next += len(mapnames)
  return mapnames[next]
 
# general text surface maker
def textmake(thetext, colour, scale ):
  if pygame.font:
    font = pygame.font.Font(None, int(21*scale))
    text = font.render(thetext, 1, colour)
    textrec = text.get_rect()
    return text, textrec, font.get_linesize()

# general text surface mover
def textmove(x, y, text, textrec ):
    xymove = [x,y]
    textrec = textrec.move(xymove)
    return textrec

# general text line function
def helptextline(helpsurface, scale, lineoffset, thestring, colour=helpcolour):
  text, textrec, linespace = textmake(thestring, colour, scale)
  textrec = textmove(0,lineoffset, text, textrec ) 
  helpsurface.blit(text,textrec)
  lineoffset += linespace
  return lineoffset

# generate the help information surface
def drawhelp(currmap, scale):
  helpsurface = pygame.Surface((int(128*scale),int(256*scale)))
  lineoffset = helptextline(helpsurface, scale, 0, 'EL Map Viewer')
  lineoffset = helptextline(helpsurface, scale, lineoffset, " i/o - zoom in/out")
  lineoffset = helptextline(helpsurface, scale, lineoffset, " f - full screen")
  lineoffset = helptextline(helpsurface, scale, lineoffset, " b - toggle boxes")
  lineoffset = helptextline(helpsurface, scale, lineoffset, ' l - edit links')
  lineoffset = helptextline(helpsurface, scale, lineoffset, " m - toggle marks")
  lineoffset = helptextline(helpsurface, scale, lineoffset, " e - edit marks")
  lineoffset = helptextline(helpsurface, scale, lineoffset, " r - reload data")
  lineoffset = helptextline(helpsurface, scale, lineoffset, " home - Isla Prima")
  lineoffset = helptextline(helpsurface, scale, lineoffset, " bs - back a map")
  lineoffset = helptextline(helpsurface, scale, lineoffset, " up/down - cycle")
  lineoffset = helptextline(helpsurface, scale, lineoffset, " l-click select")
  lineoffset = helptextline(helpsurface, scale, lineoffset, " r-click draw box")
  lineoffset = helptextline(helpsurface, scale, lineoffset, " ESC - exit")
  if maptype.has_key(currmap) and maptype[currmap] == 'PK':
    colour = pkmapcolour
  else:
    colour = othermapcolour
  lineoffset = helptextline(helpsurface, scale, lineoffset, currmap, colour)
  lineoffset = helptextline(helpsurface, scale, lineoffset, version)
  return helpsurface

# read the users map marks, coords and text
def readmapmarkers(userdir, currmap):
  markers = []
  makersfile = userdir + string.replace(currmap,'.bmp','.elm.txt',1)
  if os.access(makersfile, os.R_OK):
    fid = open(makersfile, 'r')
    markerlines = fid.readlines()
    for line in markerlines:
      w = line.split()
      if len(w) > 2:
        markers.append(((int(w[0]),int(w[1])),string.join(w[2:])))
    fid.close()
  return markers

# display the users map marks
def displaymarkers(markers, thismapscale, screen, mapxoffset, mapsize, scale):
  if thismapscale[0] == 0 or thismapscale[1] == 0:
    print 'No scale for map'
    return
  for mark in markers:
    x = mapxoffset + (mark[0][0] * mapsize[0] / thismapscale[0])
    y = (thismapscale[1] - mark[0][1]) * mapsize[1] / thismapscale[1]
    text, textrec, linespace = textmake(mark[1], markcolour, scale)
    textrec = textmove(x, y, text, textrec )
    pygame.draw.line(screen, markcrosscolour, (x-5, y), (x+5, y), 1)
    pygame.draw.line(screen, markcrosscolour, (x, y-5), (x, y+5), 1)
    screen.blit(text,textrec)

# check sound and font usage and initialise pygame
if not pygame.font: print 'Warning, fonts disabled'
if not pygame.mixer: print 'Warning, sound disabled'
pygame.init()

# set default window title and cursor type
pygame.display.set_caption("Eternal Lands Map Viewer", "elmapviewer")
pygame.mouse.set_cursor(*pygame.cursors.arrow)
#print pygame.display.Info()

# get the resource file name and read the data
if len(sys.argv) > 1:
  rcfile = sys.argv[1]
else:
  rcfile = '~/.elmapviewer.rc'
rcfile = expandfilename(rcfile)

mapdatafile = os.path.dirname(sys.argv[0]) + '/mapdata'

mapdir, userdir, scale, fullscreen, boxesOn, marksOn, editor = readvars(rcfile)
mapinfo, mapscale, maptype, bigmap = readinfo(mapdatafile)
  
normalcursor = True           # holds current cursor state, set to alternative when over links
mainmapname = 'startmap.bmp'  # the map about to be displayed
homemap = mainmapname         # the start map
lastmap = ''                  # the last map displayed, cleared to force redraw

sidemapname = bigmap['startmap.bmp']  # the current side map

hotspot = []                  # list of links for current map
backmap = []                  # list of previous maps visited
markbox = []                  # right click twice to form a box and see coords for links

mapxoffset = 0                # X offset of main map in pixels, calculated later
screensize = (0,0)            # current screen size, calculates from map sizes and scale


# loop forever....
while 1:

    # if the map has changed, update the display
    if mainmapname != lastmap:
    
      # handle the back key useage, poping the new map name
      if mainmapname == 'pop':
        mainmapname = backmap.pop()
      else:
        if lastmap != '':
          if len(backmap) > 20:
            backmap.pop(0)
          backmap.append(lastmap)
        
      # clear any marked box
      markbox = []
        
      # always restore the big map to the side map if nolonger the main map
      if bigmap.has_key(mainmapname):
        if sidemapname != bigmap[mainmapname]:
          sidemapname = bigmap[mainmapname]
          
      # get and scale the current size map surface
      sidemap = pygame.image.load(mapdir + sidemapname)
      sidemapsize = sidemap.get_size()
      sidemap = pygame.transform.scale(sidemap, (int(sidemapsize[0]*scale/2), int(sidemapsize[1]*scale/2)))
      sidemapsize = sidemap.get_size()
      sidemaprect = sidemap.get_rect()
      
      # get the scaled help text surface
      helpsurface = drawhelp(mainmapname, scale)
      helpsize = helpsurface.get_size()
      helprect = helpsurface.get_rect()
      
      # get and scale the legend surface
      legend = pygame.image.load(mapdir + "legend.bmp")
      legendsize = legend.get_size()
      legend = pygame.transform.scale(legend, (int(legendsize[0]*scale), int(legendsize[1]*scale)))
      legendsize = legend.get_size()
      legendrect = legend.get_rect()
      
      # get and scale the main map surface
      mainmap = pygame.image.load(mapdir + mainmapname)
      mainmapsize = mainmap.get_size()
      mainmap = pygame.transform.scale(mainmap, (int(mainmapsize[0]*scale), int(mainmapsize[1]*scale)))
      mainmapsize = mainmap.get_size()
      mainmaprect = mainmap.get_rect()
      
      # get the screen size, and modify the display mode if it has changed
      lastscreensize = screensize
      screensize = width, height = sidemapsize[0]+mainmapsize[0], mainmapsize[1]
      if screensize != lastscreensize:
        screen =  pygame.display.set_mode(screensize)
        if fullscreen:
          pygame.display.toggle_fullscreen()
      
      # now we have the screen size, move surfaces into place
      
      # position the legend
      xymove = [screensize[0]-mainmapsize[0]-legendsize[0], screensize[1]-sidemapsize[1]]
      legendrect = legendrect.move(xymove)
      
      # position the help
      xymove = [0, screensize[1]-sidemapsize[1]]
      helprect = helprect.move(xymove)
      
      # get the main map x offset (used later for curser detection) and move it
      mapxoffset = screensize[0]-mainmapsize[0]
      mainmapmove = [mapxoffset, 0]
      mainmaprect = mainmaprect.move(mainmapmove)  
    
      # clear the display and redraw the components
      screen.fill(blackcolour)
      screen.blit(sidemap, sidemaprect)
      screen.blit(mainmap, mainmaprect)
      screen.blit(legend, legendrect)
      screen.blit(helpsurface, helprect)
      
      # get the list of main map links, and optionally draw rectangles for them
      hotspot = []
      for hp in mapinfo[mainmapname]:
        rectcoord =  (hp[0][0]*scale, hp[0][1]*scale, hp[0][2]*scale, hp[0][3]*scale)
        cursorbox = pygame.Rect(rectcoord)
        cursorbox = cursorbox.move(mainmapmove)
        if boxesOn:
          pygame.draw.rect(screen, boxcolour, cursorbox, 2)
        hotspot.append((cursorbox, hp[1]))
       
      # if user marks are enables, draw them on the main main
      if marksOn:
        markers = readmapmarkers(userdir, mainmapname)
        if mapscale.has_key(mainmapname):
          displaymarkers(markers, mapscale[mainmapname], screen, mapxoffset, mainmapsize, scale)
        elif bigmap.has_key(mainmapname):
          print 'No scale for this maps markers'
      
      # draw the new display
      pygame.display.flip()
      
      # remember the current map
      lastmap = mainmapname

    # end if map changed
      
    # get an event from the window
    event = pygame.event.wait()
    
    # if exit, then make it so
    if event.type == pygame.QUIT:
      sys.exit()
      
    # if the mouse moves, check for cursor changes in link boxes
    elif event.type == pygame.MOUSEMOTION:
      inhotspot = False
      for hp in hotspot:
        if hp[0].collidepoint(pygame.mouse.get_pos()):
          if normalcursor:
            pygame.mouse.set_cursor(*pygame.cursors.diamond)
            normalcursor = False
          inhotspot = True
          break
      if not inhotspot:
        if not normalcursor:
          pygame.mouse.set_cursor(*pygame.cursors.arrow)
          normalcursor = True
  
    # if a mouse button is pressed....
    elif event.type == pygame.MOUSEBUTTONDOWN:
      # if sidemap left-clicked, switch side and main maps
      if pygame.mouse.get_pressed()[0] and pygame.mouse.get_pos()[0] < mapxoffset:
        if sidemaprect.collidepoint(pygame.mouse.get_pos()):
          temp = sidemapname
          sidemapname = mainmapname
          mainmapname = temp
            
      # if main map left-click, check for map link
      if pygame.mouse.get_pressed()[0] and pygame.mouse.get_pos()[0] > mapxoffset:
        for hp in hotspot:
          if hp[0].collidepoint(pygame.mouse.get_pos()):
            mainmapname = hp[1]
            
      # if middle-click in link area, show information about the link
      if pygame.mouse.get_pressed()[1] and pygame.mouse.get_pos()[0] > mapxoffset:
        for hp in hotspot:
          if hp[0].collidepoint(pygame.mouse.get_pos()):
            print "link info:", hp
            
      # help create new map link areas by drawning a box on the map
      # if right-click form box with next click, then clear on third
      if pygame.mouse.get_pressed()[2] and pygame.mouse.get_pos()[0] > mapxoffset:
        xycoord = (pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1])
        # store and draw first 2 click positions 
        if len(markbox) < 2:
          markbox.append(xycoord)
          pygame.draw.line(screen, testboxcolour, (xycoord[0]-5, xycoord[1]), (xycoord[0]+5, xycoord[1]), 1)
          pygame.draw.line(screen, testboxcolour, (xycoord[0], xycoord[1]-5), (xycoord[0], xycoord[1]+5), 1)
          pygame.display.update()
        # if we've already had both and drawn the box, clear it this time
        else:
          lastmap = ''
        # if now we have the two corners, draw the box and display coords suitable for map link
        if len(markbox) == 2:
          cursorbox = pygame.Rect(markbox[0][0],markbox[0][1],markbox[1][0]-markbox[0][0], markbox[1][1]-markbox[0][1])
          pygame.draw.rect(screen, testboxcolour, cursorbox, 2)
          pygame.display.update()
          print mainmapname, int((markbox[0][0]-mapxoffset)/scale), int(markbox[0][1]/scale), \
            int((markbox[1][0]-markbox[0][0])/scale), int((markbox[1][1]-markbox[0][1])/scale)

    # process keyboard events
    if event.type == pygame.KEYDOWN:
      
      # i - enlarge window, zoom in
      if event.key == pygame.K_i:
        if screensize[0]+0.1 < 1152:
          scale += 0.1
          lastmap = ''
          
      # o - srink window, zoom out
      elif event.key == pygame.K_o:
        if screensize[0]-0.1 > 600:
          scale -= 0.1
          lastmap = ''
          print scale

      # f - toggle window/full screen
      elif event.key == pygame.K_f:
        fullscreen = not fullscreen
        screensize = (0.0)  # force display mode reset
        lastmap = ''

      # b - toggle drawing of rectangles round link areas
      elif event.key == pygame.K_b:
        boxesOn = not boxesOn
        lastmap = ''
        
      # l - edit map links
      elif event.key == pygame.K_l:
        os.spawnv(os.P_NOWAIT, editor, (editor, mapdatafile))

      # m - toggle display of user marks
      elif event.key == pygame.K_m:
        marksOn = not marksOn
        lastmap = ''

      # e - edit user marks in external editor
      elif event.key == pygame.K_e:
        makersfile = userdir + string.replace(mainmapname,'.bmp','.elm.txt',1)
        os.spawnv(os.P_NOWAIT, editor, (editor, makersfile))

      # r - redisplay map, rereading all user data
      elif event.key == pygame.K_r:
        mapinfo, mapscale, maptype, bigmap = readinfo(mapdatafile)
        lastmap = ''
        
      # home key, go to games start map
      elif event.key == pygame.K_HOME:
        mainmapname = homemap

      # backspace go to last visited map
      elif event.key == pygame.K_BACKSPACE and len(backmap) > 0:
        mainmapname = 'pop'

      # up cursor is next map in sequence
      elif event.key == pygame.K_UP:
        mainmapname = nextmap(mapinfo, mainmapname, 1)

      # down cursor is previous map in sequence
      elif event.key == pygame.K_DOWN:
        mainmapname = nextmap(mapinfo, mainmapname, -1)
          
      # exit if ESC pressed
      elif event.key == pygame.K_ESCAPE:
        pygame.QUIT
        sys.exit()
