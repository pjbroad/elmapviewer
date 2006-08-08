#! /usr/bin/env python

# Eternal Lands Map Viewer
#
# Copyright 2006 Paul Broadhead (a.k.a. bluap)
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
# and also tested on Ubuntu Linux.

# Eternal Lands: http://www.eternal-lands.com/
# Python: http://www.python.org
# Pygame: http://www.pygame.org
# Debian GNU/Linux: http://www.debian.org/
# Ubuntu: http://www.ubuntu.com/

import sys, pygame, string, os, shutil, platform, struct, urllib, math

version = 'v0.4.2 August 2006'

# define some basic colours
blackcolour = 0, 0, 0
redcolour = 255, 0, 0
greencolour = 0, 255, 0
bluecolour = 0, 0, 255
yellowcolour = 255, 255, 0
cyancolour = 0, 255, 255
orangecolour = 255, 185, 15
whitecolour = 255, 255, 255
# and some item colours
pkmapcolour = redcolour
hlmapcolour = orangecolour
othermapcolour = greencolour
markcolour = 179, 238,  58
markcrosscolour = whitecolour
boxcolour = 58, 95, 205
pkboxcolour = redcolour
testboxcolour = cyancolour
helpcolour = 205, 190, 112
functionkeys = { \
  'F1': (pygame.K_F1, ''), 'F2': (pygame.K_F2, ''), 'F3': (pygame.K_F3, ''), \
  'F4': (pygame.K_F4, ''), 'F5': (pygame.K_F5, ''), 'F6': (pygame.K_F6, ''), \
  'F7': (pygame.K_F7, ''), 'F8': (pygame.K_F8, ''), 'F9': (pygame.K_F9, ''), \
  'F10': (pygame.K_F10, ''), 'F11': (pygame.K_F11, ''), 'F12': (pygame.K_F12, ''), \
  'F13': (pygame.K_F13, ''), 'F14': (pygame.K_F14, ''), 'F15': (pygame.K_F15, ''), \
  }
gameminuteevent = pygame.USEREVENT
clockresyncevent = pygame.USEREVENT+1

# expand ~ and environ vars
def expandfilename(filename):
  filename = os.path.expanduser(filename)
  filename = os.path.expandvars(filename)
  filename = os.path.normpath(filename)
  return filename
  

# read the map size from the .elm file assiociated this bmp filename
def readmapsizefromelm(bmpfilename):
  elmfilename = string.replace(bmpfilename,'.bmp','.elm',1)
  if os.access(elmfilename, os.R_OK):
    fid=open(elmfilename,'rb')
    info=fid.read(12)
    fid.close()
    # the file's data is little endian - hopefully this will work for big endian too
    size = struct.unpack('<ii',info[4:])
    return 6*size[0], 6*size[1]
  else:
    return 0, 0


# read map information from the map data files
# links, names, sizes, types
def readinfo(mapdir, fname, userfname):
  mapinfo = {}
  mapscale = {}
  maptype = {}
  parentmap = {}
  allmaps = {}
  maptitle = {}
  # create the initial map list form the elm files
  for elmfile in os.listdir(mapdir):
    if elmfile[len(elmfile)-4:] == '.elm':
      mapname = os.path.basename(string.replace(elmfile,'.elm','.bmp',1))
      allmaps[mapname] = mapname
  for maplinkfile in (fname, userfname):
    if os.access(maplinkfile, os.R_OK):
      currmapname = ''
      for line in open(maplinkfile, 'r'):
        if line != '\n' and line[0] != "#":
          w = line.split()
          # new map uses line format "filename: sizeX sizeY [type]"
          if len(w) > 1 and w[1] == '=':
            continue;
          if w[0][len(w[0])-1] == ":":
            currmapname = w[0][:len(w[0])-1]
            allmaps[currmapname] = currmapname
            if len(w) > 2 and w[1] != '-' and w[2] != '-':
              mapscale[currmapname] = (int(w[1]), int(w[2]))
            if len(w) > 3:
              maptype[currmapname] = w[3]
            if len(w) > 4:
              parentmap[currmapname] = w[4]
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
    # get the scale from the elm file and compare
    sizefromfile = readmapsizefromelm(os.path.join(mapdir, mapname))
    if mapscale.has_key(mapname):
      if mapscale[mapname] != sizefromfile:
        print 'Warning map scale mismatch', mapname, mapscale[mapname], sizefromfile
    elif sizefromfile != (0,0):
      mapscale[mapname] = sizefromfile
  # get map names from the mapinfo.lst file
  mapinfolstfile = expandfilename(os.path.join(mapdir, '../mapinfo.lst'))
  if os.access(mapinfolstfile, os.R_OK):
    for line in open(mapinfolstfile, 'r'):
      w = line.split()
      if len(w) > 7:
        mapfilename = os.path.basename(string.replace(w[5],'.elm','.bmp',1))
        maptitle[mapfilename] = string.join(w[7:],' ')
  return mapinfo, mapscale, maptype, parentmap, maptitle
  

# read program variables from the resource file
def readvars(fname):
  mapdir = ''
  userdir = ''
  scale = 1.0
  fullscreen = False
  boxesOn = True
  marksOn = True
  editor = '$EDITOR'
  markfontsize = 21
  statusfontsize = 21
  mainborder = [10, 10]
  noesc = False
  copyexec = ''
  showgametime = False
  # create a default rc file if none exists
  if not os.access(fname, os.R_OK):
    srcfile = os.path.dirname(sys.argv[0]) + '/example.elmapviewer.rc'
    dstfile = expandfilename('~/.elmapviewer.rc')
    shutil.copyfile(srcfile,dstfile)
    print 'Default ~/.elmapviewer.rc file created, you may need to change some options.'
  for line in open(fname, 'r'):
    if line != '\n' and line[0] != '#':
      w = line.split(None,2)
      # variable line format name = value
      if len(w) > 2 and w[1] == '=':
        w[2] = w[2].rstrip()
        # location of EL maps
        if w[0] == 'mapdir':
          mapdir = expandfilename(w[2])
          if not os.access(mapdir, os.R_OK):
            print 'Please set the mapdir option in your rc file: ' + rcfile
            print 'Current value [' + mapdir + ']'
            sys.exit(-1)
        # location of user map information
        elif w[0] == 'userdir':
          userdir = expandfilename(w[2])
        elif w[0] == 'scale':
          scale = float(w[2])
        elif w[0] == 'fullscreen':
          fullscreen = bool(int(w[2]))
        elif w[0] == 'boxesOn':
          boxesOn = bool(int(w[2]))
        elif w[0] == 'marksOn':
          marksOn = bool(int(w[2]))
        elif w[0] == 'editor':
          editor = expandfilename(w[2])
        elif w[0] == 'markfontsize':
          markfontsize = int(w[2])
        elif w[0] == 'statusfontsize':
          statusfontsize = int(w[2])
        elif w[0] == 'mainborderx':
          mainborder[0] = int(w[2])
        elif w[0] == 'mainbordery':
          mainborder[1] = int(w[2])
        elif w[0] == 'noesc':
          noesc = bool(int(w[2]))
        elif w[0] == 'copytoclipboard':
          copyexec = w[2]
        elif w[0] == 'showgametime':
          showgametime = bool(int(w[2]))
        elif functionkeys.has_key(w[0]):
          keycode = functionkeys[w[0]][0]
          functionkeys[w[0]] = (keycode,w[2])
  return mapdir, userdir, scale, fullscreen, boxesOn, marksOn, editor, \
    markfontsize, statusfontsize, mainborder, noesc, copyexec, showgametime

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
  
# common find routine for search functions - allows ^
def searchfind(tosearch, searchtext):
  if len(searchtext) > 0 and searchtext[0] == '^':
    if len(searchtext) > 1:
      return tosearch.lower().find(searchtext[1:], 0) == 0
    else:
      return False
  else:
    return tosearch.lower().find(searchtext, 0) != -1
 
# general text surface maker
def textmake(thetext, colour, scale, fontsize ):
  font = pygame.font.Font(None, int(fontsize*scale))
  text = font.render(thetext, 1, colour)
  textrec = text.get_rect()
  return text, textrec, font.get_linesize()

# general text surface mover
def textmove(x, y, text, textrec ):
    xymove = [x,y]
    textrec = textrec.move(xymove)
    return textrec

# common function between standard and search status lines
def genstatusline(screen, scale, coordwidth, fulltext, colour, statusfontsize):
  statusline, rec, linesize = textmake(fulltext, colour, scale, statusfontsize)
  # and move to its in screen location
  xymove = [coordwidth, screen.get_size()[1] - statusline.get_size()[1]]
  statusrect = rec.move(xymove)
  # as we're not doing a full screen update, we need to clear old text
  rectcoord = (0, 0, screen.get_size()[0]-coordwidth, statusline.get_size()[1])
  blankrec = pygame.Rect(rectcoord).move(xymove)
  # draw the blank, then the text, then update display
  screen.fill(blackcolour, blankrec)
  screen.blit(statusline, statusrect)
  pygame.display.update(blankrec)
  return
  
# draw the status line including the current map name
def updatestatusline(screen, scale, coordwidth, mapname, statustext, statusfontsize):
  # colour code PK maps
  extrastat = ''
  if maptype.has_key(mapname) and maptype[mapname] == 'PK':
    colour = pkmapcolour
    extrastat = ' (PK)'
  elif maptype.has_key(mapname) and maptype[mapname] == 'HL':
    colour = hlmapcolour
    extrastat = ' (HL)'
  else:
    colour = othermapcolour
  # get the text surface
  fulltext = mapname + extrastat + ':  ' + statustext
  genstatusline(screen, scale, coordwidth, fulltext, colour, statusfontsize)
  return

# draw the search status line
def updatesearchline(screen, scale, coordwidth, mapname, marksearch, searchtext, statusfontsize):
  fulltext = mapname + ": "
  if marksearch:
    fulltext += "mark"
  else:
    fulltext += "map"
  fulltext += " search "
  if searchmatchingmaps == []:
    fulltext += "(none)"
  else:
    fulltext += "(map " + str(currentsearchmapindex+1) + " of " + str(len(searchmatchingmaps)) + ")"
  fulltext += ": " + searchtext + "_"
  colour = whitecolour
  genstatusline(screen, scale, coordwidth, fulltext, colour, statusfontsize)
  return
  
# clear and redraw the map coords
def updatecoord(screen, scale, coordwidth, coordtext, statusfontsize):
  # get the text and move to its in screen location
  coords, rec, linesize = textmake(coordtext, whitecolour, scale, statusfontsize)
  xymove = [0, screen.get_size()[1] - coords.get_size()[1]]
  rect = rec.move(xymove)
  # as we're not doing a full screen update, we need to clear old text
  rectcoord = (0, 0, coordwidth, coords.get_size()[1])
  blankrec = pygame.Rect(rectcoord).move(xymove)
  # draw the blank, then the text, then update display
  screen.fill(blackcolour, blankrec)
  screen.blit(coords, rect)
  pygame.display.update(blankrec)

# general text line function
def helptextline(helpsurface, menuoptions, scale, lineoffset, thestring, key=0):
  helpfontsize = 21
  text, textrec, linespace = textmake(thestring, helpcolour, scale, helpfontsize)
  textrec = textmove(0,lineoffset, text, textrec ) 
  helpsurface.blit(text,textrec)
  lineoffset += linespace
  if key != 0:
    menuoptions.append(( textrec, key ))
  return menuoptions, lineoffset

# generate the help information surface
def drawhelp(scale):
  helpsurface = pygame.Surface((int(128*scale),int(256*scale)))
  lineoffset = 0
  menuoptions = []
  if searchmode:
    if marksearch:
      menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, " Search marks")
    else:
      menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, " Search mapname")
    menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, " ^ matches start")
    menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, " up/down")
    menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, "   - cycle maps")
    menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, " ESC - end search")
  else:
    menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, " i - zoom in", pygame.K_i)
    menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, " o - zoom out", pygame.K_o)
    menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, " f - full screen", pygame.K_f)
    menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, " b - toggle boxes", pygame.K_b)
    menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, " l - edit links", pygame.K_l)
    menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, " m - toggle marks", pygame.K_m)
    menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, " e - edit marks", pygame.K_e)
    menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, " c - edit config", pygame.K_c)
    menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, " r - reload data", pygame.K_r)
    menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, " bs - back a map", pygame.K_BACKSPACE)
    menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, " up/down - cycle")
    #menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, " Fn jump to map")
    menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, " home/end islands")
    menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, " l-click select")
    menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, " r-click draw box")
    menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, " / \ - search", pygame.K_SLASH)
    if not noesc:
      menuoptions, lineoffset = helptextline(helpsurface, menuoptions, scale, lineoffset, " q - quit", pygame.K_q)
  return menuoptions, helpsurface

# drawhelp stored array of text rec and key options
# scan though for collide and return key option
def getmenukey(menuoptions, mousecoord, sidemapsize):
  xymove = [0, sidemapsize[1]]
  for option in menuoptions:
    realrec = option[0].move(xymove)
    if realrec.collidepoint(mousecoord):
      return option[1]
  return 0

# read the users map marks, coords and text
def readmapmarkers(userdir, currmap):
  markers = []
  markersfile = os.path.join(userdir, string.replace(currmap,'.bmp','.elm.txt',1))
  if os.access(markersfile, os.R_OK):
    for line in open(markersfile, 'r'):
      w = line.split()
      if len(w) > 2:
        markers.append(((int(w[0]),int(w[1])),string.join(w[2:])))
  #print "readmapmarkers: " + currmap
  return markers

# display the users map marks
def displaymarkers(markers, thismapscale, screen, mapxoffset, mapsize, \
      scale, statustext, markfontsize, searchmode, marksearch, searchtext):
  if thismapscale[0] == 1000 or thismapscale[1] == 1000:
    statustext += 'Unknown scale, markers offset. '
  elif thismapscale[0] == 0 or thismapscale[1] == 0:
    statustext += 'Invalid scale, marker not displayed. '
    return statustext
  for mark in markers:
    if searchmode and marksearch and searchtext != "" and searchtext != "^":
      if not searchfind(mark[1], searchtext):
        continue
    x = mapxoffset + (mark[0][0] * mapsize[0] / thismapscale[0])
    y = (thismapscale[1] - mark[0][1]) * mapsize[1] / thismapscale[1]
    text, textrec, linespace = textmake(mark[1], markcolour, scale, markfontsize)
    textrec = textmove(x, y, text, textrec )
    pygame.draw.line(screen, markcrosscolour, (x-5, y), (x+5, y), 1)
    pygame.draw.line(screen, markcrosscolour, (x, y-5), (x, y+5), 1)
    screen.blit(text,textrec)
  return statustext

# use the specified url (usually main el site) to get the current game time
def getgametime():
  # game time information
  elweburl = 'http://www.eternal-lands.com'
  starttimestring = 'Game time: '
  endtimestring = '<'
  # 59 game seconds is 60 second normal time
  millisecpergamemillisec = int(0.5 + 1000.0 * 60 * 60.0 / 59.0)
  # (re)start the game minute timer
  pygame.time.set_timer(gameminuteevent, 0)
  pygame.time.set_timer(gameminuteevent, millisecpergamemillisec)
  # read the webpage
  wpage=urllib.urlopen(elweburl)
  pagetext = wpage.read()
  wpage.close()
  # process the page to retrieve the start time
  start = string.find(pagetext, starttimestring)
  end = string.find(pagetext, endtimestring, start)
  timestring = pagetext[start+len(starttimestring):end].split(':')
  return (int(timestring[0]), int(timestring[1]))

# increment the game time by a minute gametime = (hour, minute)
def updategametime(gametime):
  hour = gametime[0]
  minute = gametime[1] + 1
  if minute == 60:
    minute = 0
    hour += 1
    if hour == 6:
      hour = 0
  return (hour, minute)
  
# return a game time string formmatted HH:MM with 0 padding
def timestring(gametime):
  return (str(gametime[0]).rjust(2) + ':' + str(gametime[1]).rjust(2)).replace(' ','0')

# update the window title
def settitle(mainmapname, gametime, basetitle):
  if showgametime: 
    currtitle = ' [Game Time: ' + timestring(gametime) + ']'
  else:
    currtitle = ''
  if maptitle.has_key(mainmapname):
    currtitle += ' [ ' + maptitle[mainmapname] + ' ]'
  currtitle += ' ' + basetitle
  pygame.display.set_caption(currtitle, baseicon)
  
# convert display coords to game map coords
def togamecood(point, mapxoffset, thismainmapsize, thismapscale):
  x = int((float(point[0]-mapxoffset) / thismainmapsize[0] * thismapscale[0]))
  y = int(thismapscale[1] - (float(point[1]) / mainmapsize[1] * thismapscale[1]))
  return (x,y)

# calculate the distance between the two points and return as walking time
def calcdistance(point1, point2, mapxoffset, thismapsize, thismapscale ):
  point1 = togamecood(point1, mapxoffset, thismapsize, thismapscale)
  point2 = togamecood(point2, mapxoffset, thismapsize, thismapscale)
  xdist = point2[0] - point1[0]
  ydist = point2[1] - point1[1]
  # divisor was empirically measured, its not that accurate
  crowflydist = math.sqrt(xdist*xdist + ydist*ydist)/3.32
  minutes = int(crowflydist / 60.0)
  seconds = int(crowflydist - 60 * minutes)
  return 'time to walk ' + str(point1) + '->' + str(point2) + ' ' + \
    (str(minutes).rjust(2) + ':' + str(seconds).rjust(2)).replace(' ','0')

# check font usage and initialise pygame
if not pygame.font:
  print 'Error, fonts not available'
  sys.exit()
pygame.display.init()
pygame.font.init()
pygame.key.set_repeat(500, 100)

# set default window title and cursor type
pygame.mouse.set_cursor(*pygame.cursors.arrow)

# get the resource file name and read the data
if len(sys.argv) > 1:
  rcfile = sys.argv[1]
else:
  rcfile = '~/.elmapviewer.rc'
rcfile = expandfilename(rcfile)

mapdatafile = os.path.dirname(sys.argv[0]) + os.sep + 'mapdata'
usermapdatafile = expandfilename('~/.elmapviewer.usermapdata')

mapdir, userdir, scale, fullscreen, boxesOn, marksOn, editor, \
  markfontsize, statusfontsize, mainborder, noesc, copyexec, showgametime = readvars(rcfile)
mapinfo, mapscale, maptype, parentmap, maptitle = readinfo(mapdir, mapdatafile, usermapdatafile)
  
normalcursor = True           # holds current cursor state, set to alternative when over links
mainmapname = 'seridia.bmp'   # the map about to be displayed
homemap = mainmapname         # the start map
lastmap = ''                  # the last map displayed, cleared to force redraw
# window title and icon base
basetitle = 'Eternal Lands Map Viewer: ' + version
baseicon = 'elmapviewer'

sidemapname = parentmap[mainmapname]  # the current side map

hotspot = []                  # list of links for current map
backmap = []                  # list of previous maps visited
markbox = []                  # right click twice to form a box and see coords for links

mapxoffset = 0                # X offset of main map in pixels, calculated later
screensize = (0,0)            # current screen size, calculates from map sizes and scale

coordwidth = 0;
coordtext = ''                # in game map coords, show at bottm left of window
lastcoordtext = '-'

statustext = ''               # status text shown at bottom of window with map name
laststatustext = '-'

searchmode = False
marksearch = False
searchtext = ''
lastsearchtext = '-'
searchmatchingmaps = []
currentsearchmapindex = 0

markersstore = {}

# get the initial game time and start the event timers to keep it up to date
if showgametime:
  gametime = getgametime()
  # resync the clock every hour - one day the tracking will be accurate enough to drop this
  pygame.time.set_timer(clockresyncevent, 1000 * 60 * 60)
else:
  gametime = (0,0)
  
# loop forever....
while 1:

    # if the map has changed, update the display
    if mainmapname != lastmap:
    
      statustext = ''
      laststatustext = '-'
      lastsearchtext = searchtext + "-" # force a redraw
    
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
      if parentmap.has_key(mainmapname):
        if sidemapname != parentmap[mainmapname]:
          sidemapname = parentmap[mainmapname]
          
      # get and scale the current size map surface
      fullpath = os.path.join(mapdir, sidemapname)
      if not os.access(fullpath, os.R_OK):
        sidemap = pygame.Surface((512, 512))
        statustext += 'Cant load sidemap file. '
      else:
        sidemap = pygame.image.load(fullpath)
      sidemapsize = sidemap.get_size()
      sidemap = pygame.transform.scale(sidemap, (int(sidemapsize[0]*scale/2), int(sidemapsize[1]*scale/2)))
      sidemapsize = sidemap.get_size()
      sidemaprect = sidemap.get_rect()
      
      # get the scaled help text surface
      menuoptions, helpsurface = drawhelp(scale)
      helprect = helpsurface.get_rect()
      
      # get and scale the legend surface
      fullpath = os.path.join(mapdir, "legend.bmp")
      if not os.access(fullpath, os.R_OK):
        legend = pygame.Surface((128, 256))
        statustext += 'Cannot load legend file. '
      else:
        legend = pygame.image.load(fullpath)
      legendsize = legend.get_size()
      legend = pygame.transform.scale(legend, (int(legendsize[0]*scale), int(legendsize[1]*scale)))
      legendrect = legend.get_rect()
      
      # get and scale the main map surface
      fullpath = os.path.join(mapdir, mainmapname)
      if not os.access(fullpath, os.R_OK):
        mainmap = pygame.Surface((512, 512))
        statustext += 'Cannot load main map file. '
      else:
        mainmap = pygame.image.load(fullpath)
      mainmapsize = mainmap.get_size()
      mainmap = pygame.transform.scale(mainmap, (int(mainmapsize[0]*scale), int(mainmapsize[1]*scale)))
      mainmapsize = mainmap.get_size()
      mainmaprect = mainmap.get_rect()
      
      # update font related sizes
      coordwidth = pygame.font.Font(None, int(statusfontsize*scale)).size('000,000  ')[0]
      statusheight = pygame.font.Font(None, int(statusfontsize*scale)).get_height()
      
      # get the screen size
      lastscreensize = screensize
      width = int(sidemapsize[0]+mainmapsize[0]+mainborder[0]*scale)
      height = int(statusheight+mainmapsize[1]+mainborder[1]*scale)
      screensize = width, height
      
      # modify the display mode if it has changed
      if screensize != lastscreensize:
        screen =  pygame.display.set_mode(screensize)
        if fullscreen:
          pygame.display.toggle_fullscreen()
      
      # now we have the screen size, move surfaces into place
      
      # position the legend
      xymove = [int(sidemapsize[0]/2), sidemapsize[1]]
      legendrect = legendrect.move(xymove)
      
      # position the help
      xymove = [0, sidemapsize[1]]
      helprect = helprect.move(xymove)
      
      # get the main map x offset (used later for curser detection) and move it
      mapxoffset = sidemapsize[0]
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
        if hp[0] == (0,0,0,0): # dummy entry
          continue
        rectcoord =  (hp[0][0]*scale, hp[0][1]*scale, hp[0][2]*scale, hp[0][3]*scale)
        cursorbox = pygame.Rect(rectcoord)
        cursorbox = cursorbox.move(mainmapmove)
        if boxesOn:
          if maptype.has_key(hp[1]) and maptype[hp[1]] == 'PK':
            colour = pkboxcolour
          elif maptype.has_key(hp[1]) and maptype[hp[1]] == 'HL':
            colour = hlmapcolour
          else:
            colour = boxcolour
          pygame.draw.rect(screen, colour, cursorbox, 2)
        hotspot.append((cursorbox, hp[1]))
       
      # if user marks are enables, draw them on the main main
      if marksOn or (searchmode and marksearch):
        # read the marks if we have not already done so
        if not markersstore.has_key(mainmapname):
          markersstore[mainmapname] = readmapmarkers(userdir, mainmapname)
        # display the mark using any active filter
        if mapscale.has_key(mainmapname):
          statustext = displaymarkers(markersstore[mainmapname], mapscale[mainmapname], screen, \
            mapxoffset, mainmapsize, scale, statustext, markfontsize, \
            searchmode, marksearch, searchtext )
      
      settitle(mainmapname, gametime, basetitle)

      # draw the new display
      pygame.display.flip()
      
      # remember the current map
      lastmap = mainmapname

    # end if map changed
      
    # if searching, update the search string if it changes
    if searchmode:
      if searchtext != lastsearchtext:
        updatesearchline(screen, scale, coordwidth, mainmapname, marksearch, searchtext, statusfontsize)
        lastsearchtext = searchtext
        
    # update the status line if it changes
    elif laststatustext != statustext:
      updatestatusline(screen, scale, coordwidth, mainmapname, statustext, statusfontsize)
      laststatustext = statustext

    # update the coordinate line if it changes
    if lastcoordtext != coordtext:
      updatecoord(screen, scale, coordwidth, coordtext, statusfontsize)
      lastcoordtext = coordtext
      
# process events

    # get an event from the window
    event = pygame.event.wait()
    mousecoord = pygame.mouse.get_pos()
    mousebuttons = pygame.mouse.get_pressed()
    modkeys = pygame.key.get_mods()
    mouseonmainmap = mainmaprect.collidepoint(mousecoord)
    
    # if exit, then make it so
    if event.type == pygame.QUIT:
      sys.exit()
    
    # update the title with the game time each game minute
    elif showgametime and event.type == gameminuteevent:
      gametime = updategametime(gametime)
      settitle(mainmapname, gametime, basetitle)
        
    # resync the clock with the web now and then
    elif showgametime and event.type == clockresyncevent:
      print 'resync game time, was ', gametime,
      gametime = getgametime()
      print ' now ', gametime
      settitle(mainmapname, gametime, basetitle)
      
    # if the mouse moves
    elif event.type == pygame.MOUSEMOTION:
      # check for cursor changes in link boxes
      inhotspot = False
      for hp in hotspot:
        if hp[0].collidepoint(mousecoord):
          if normalcursor:
            pygame.mouse.set_cursor(*pygame.cursors.diamond)
            normalcursor = False
          inhotspot = True
          break
      # if not in a map hot spot, check for menu option
      if not inhotspot:
        if helprect.collidepoint(mousecoord):
          if getmenukey(menuoptions, mousecoord, sidemapsize) != 0:
            if normalcursor:
              pygame.mouse.set_cursor(*pygame.cursors.diamond)
              normalcursor = False
            inhotspot = True
      # if still no in hotspot, make sure the cursor is normal
      if not inhotspot:
        if not normalcursor:
          pygame.mouse.set_cursor(*pygame.cursors.arrow)
          normalcursor = True
      # update the coordinate display
      if mapscale.has_key(mainmapname) and mouseonmainmap \
       and mapscale[mainmapname][0] != 1000 and mapscale[mainmapname][1] != 1000:
        coords = togamecood(mousecoord, mapxoffset, mainmapsize, mapscale[mainmapname] )
        coordtext = str(coords[0]) + ',' + str(coords[1])
      else:
        coordtext = ''
  
    # if a mouse button is pressed....
    elif event.type == pygame.MOUSEBUTTONDOWN:
    
      # if sidemap left-clicked, switch side and main maps
      if mousebuttons[0] and sidemaprect.collidepoint(mousecoord):
        temp = sidemapname
        sidemapname = mainmapname
        mainmapname = temp
      
      elif mouseonmainmap:
            
        # if main map left-click, check for map link
        if mousebuttons[0]:
          for hp in hotspot:
            if hp[0].collidepoint(mousecoord):
              mainmapname = hp[1]

        # if middle-click in link area, show information about the link
        elif mousebuttons[1]:
          for hp in hotspot:
            if hp[0].collidepoint(mousecoord):
              statustext = 'link info: ' + str(hp)

        # help create new map link areas by drawning a box on the map
        # if right-click form box with next click, then clear on third
        elif mousebuttons[2]:
          # store and draw first 2 click positions 
          if len(markbox) < 2:
            markbox.append(mousecoord)
            pygame.draw.line(screen, testboxcolour, (mousecoord[0]-5, mousecoord[1]), (mousecoord[0]+5, mousecoord[1]), 1)
            pygame.draw.line(screen, testboxcolour, (mousecoord[0], mousecoord[1]-5), (mousecoord[0], mousecoord[1]+5), 1)
            pygame.display.update()
          # if we've already had both and drawn the box, clear it this time
          else:
            lastmap = ''
            markbox = []
          # if now we have the two corners, draw the box and display coords suitable for map link
          if len(markbox) == 2:
            if modkeys == pygame.KMOD_LCTRL or modkeys == pygame.KMOD_RCTRL:
              cursorbox = pygame.Rect(markbox[0][0],markbox[0][1],markbox[1][0]-markbox[0][0], markbox[1][1]-markbox[0][1])
              pygame.draw.rect(screen, testboxcolour, cursorbox, 2)
              statustext = \
                str(int((markbox[0][0]-mapxoffset)/scale)) + ' ' + \
                str(int(markbox[0][1]/scale)) + ' ' +  \
                str(int((markbox[1][0]-markbox[0][0])/scale))  + ' ' +  \
                str(int((markbox[1][1]-markbox[0][1])/scale))  + ' '
              if copyexec != '':
                os.popen(copyexec, 'wb').write(statustext)
            elif mapscale.has_key(mainmapname):
              pygame.draw.line(screen, testboxcolour, markbox[0], markbox[1], 2)
              statustext = calcdistance(markbox[0], markbox[1], mapxoffset, mainmapsize, mapscale[mainmapname] )
            pygame.display.update()

			# call help mapping routine to get keypress from mouse position
			# highlight option box until MOUSEUP
      elif mousebuttons[0] and helprect.collidepoint(mousecoord):
				event = pygame.event.Event(pygame.KEYDOWN, key=getmenukey(menuoptions, mousecoord, sidemapsize))
            
    # process keyboard events - could have been inserted due to a mouse event
    if event.type == pygame.KEYDOWN:
    
      # non search mode, respond to action keys
      if not searchmode:
       
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
          os.spawnv(os.P_NOWAIT, editor, (editor, mapdatafile, usermapdatafile))

        # m - toggle display of user marks
        elif event.key == pygame.K_m:
          marksOn = not marksOn
          lastmap = ''

        # e - edit user marks in external editor
        elif event.key == pygame.K_e:
          markersfile = os.path.join(userdir, string.replace(mainmapname,'.bmp','.elm.txt',1))
          if platform.system() == 'Windows':
            markersfile = '"' + markersfile + '"'
          os.spawnv(os.P_NOWAIT, editor, (editor, markersfile))

        # c - edit user config
        elif event.key == pygame.K_c:
          os.spawnv(os.P_NOWAIT, editor, (editor, rcfile))

        # r - redisplay map, rereading all user data
        elif event.key == pygame.K_r:
          mapinfo, mapscale, maptype, parentmap, maptitle = readinfo(mapdir, mapdatafile, usermapdatafile)
          markersstore = {}
          lastmap = ''

        # home key, go to games start map
        elif event.key == pygame.K_HOME:
          mainmapname = homemap

        # home key, go to games start map
        elif event.key == pygame.K_END:
          mainmapname = "irilion.bmp"

        # backspace go to last visited map
        elif event.key == pygame.K_BACKSPACE and len(backmap) > 0:
          mainmapname = 'pop'

        # up cursor is next map in sequence
        elif event.key == pygame.K_UP:
          mainmapname = nextmap(mapinfo, mainmapname, 1)

        # down cursor is previous map in sequence
        elif event.key == pygame.K_DOWN:
          mainmapname = nextmap(mapinfo, mainmapname, -1)

        # / is search for marks
        elif event.key == pygame.K_SLASH:
          searchmode = True
          marksearch = True
          lastmap = ''

        # \ is search for map name
        elif event.key == pygame.K_BACKSLASH:
          searchmode = True
          marksearch = False
          lastmap = ''

        # exit if Q pressed, quit
        elif event.key == pygame.K_q and not noesc:
            pygame.QUIT
            sys.exit()

        # if its one of the function keys with a map defined, use it
        else:
          for fkey in functionkeys:
            if event.key == functionkeys[fkey][0] and functionkeys[fkey][1] != '':
              mainmapname = functionkeys[fkey][1]

      # search mode, most keys modify search string
      else:
      
        # exit from search mode, clearing state
        if event.key == pygame.K_ESCAPE:
          searchmode = False
          marksearch = False
          lastsearchtext = "-"
          searchtext = ""
          laststatustext = "-"
          statustext = ""
          searchmatchingmaps = []
          currentsearchmapindex = 0
          lastmap = ''
        
        else:
        
          # backspace removed last character from search string
          if event.key == pygame.K_BACKSPACE and len(searchtext) > 0:
            searchtext = searchtext[0:len(searchtext)-1]
            searchmatchingmaps = []
            currentsearchmapindex = 0

          # if have marching maps allow stepping back and forward through
          elif searchmatchingmaps != [] and event.key == pygame.K_DOWN or event.key == pygame.K_UP:
            if event.key == pygame.K_DOWN:
              currentsearchmapindex += 1
              if currentsearchmapindex >= len(searchmatchingmaps):
                currentsearchmapindex = 0
            else:
              currentsearchmapindex -= 1
              if currentsearchmapindex < 0:
                currentsearchmapindex = len(searchmatchingmaps) -1

          # add single letter keypresses to search, translating space so that work as a space
          elif len(pygame.key.name(event.key)) == 1 or event.key == pygame.K_SPACE:
            # trap keyboard differences, some use ^ directly, other don't
            if event.key == pygame.K_6 and ((modkeys & pygame.KMOD_RSHIFT) or (modkeys & pygame.KMOD_LSHIFT)):
              searchtext += "^"
            elif event.key == pygame.K_MINUS and ((modkeys & pygame.KMOD_RSHIFT) or (modkeys & pygame.KMOD_LSHIFT)):
              searchtext += "_"
            elif event.key == pygame.K_SPACE:
              searchtext += " "
            else:
              searchtext += pygame.key.name(event.key).lower()
            searchmatchingmaps = []
            currentsearchmapindex = 0

          # if were are searching marks - the search text is used as a filter on the mark display
          if marksearch:
            # if we do not have a list of maps containing the current search text, get one
            if searchmatchingmaps == [] and searchtext != "":
              mapnames = mapinfo.keys()
              mapnames.sort()
              for testmap in mapnames:
                if not markersstore.has_key(testmap):
                  markersstore[testmap] = readmapmarkers(userdir, testmap)
                markers = markersstore[testmap]
                for mark in markers:
                  marktext = mark[1]
                  if searchfind(marktext, searchtext):
                    searchmatchingmaps.append(testmap)
                    break
              # make sure we stay on the current map is it matches
              if mainmapname in searchmatchingmaps:
                currentsearchmapindex = searchmatchingmaps.index(mainmapname)
            # redisplay the map thus applying the latest filter
            lastmap = ''
              
          # if were searching map names, fill matching map array with matching names
          else:
            # if not matchin map list available, get one
            if searchmatchingmaps == [] and searchtext != "":
              mapnames = mapinfo.keys()
              mapnames.sort()
              marchlist = []
              for testmap in mapnames:
                if searchfind(testmap, searchtext):
                  searchmatchingmaps.append(testmap)
              # make sure we stay on the current map is it matches
              if mainmapname in searchmatchingmaps:
                currentsearchmapindex = searchmatchingmaps.index(mainmapname)

          # change mape if the current index changes
          if searchmatchingmaps != [] and searchmatchingmaps[currentsearchmapindex] != mainmapname:
            mainmapname = searchmatchingmaps[currentsearchmapindex]
