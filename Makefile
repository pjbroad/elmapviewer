# Install and uninstall elmapviewer
#
# Copyright 2008-2011 Paul Broadhead (a.k.a. bluap)
# Contact: pjbroad@twinmoons.org.uk
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

BASEDIR = /usr/local
SCRIPTDIR = $(BASEDIR)/bin
MENUDIR = $(BASEDIR)/share/applications
ICONDIR = $(BASEDIR)/share/pixmaps/
DATADIR = $(BASEDIR)/share/elmapviewer

SCRIPTFILE = elmapviewer
DESKTOPFILE = $(SCRIPTFILE).desktop
MAPDATA = mapdata
RCFILE = example.elmapviewer.rc
ICONFILE = elmapviewer.png

all:
	@echo "$(SCRIPTFILE) uses python so nothing to make! Use make install"

install: $(SCRIPTDIR)/$(SCRIPTFILE) $(MENUDIR)/$(DESKTOPFILE) $(DATADIR)/$(MAPDATA) $(DATADIR)/$(RCFILE) $(ICONDIR)/$(ICONFILE)

uninstall:
	@if [ "`id -u`" != "0" ]; then echo "Need to run as root user or prefixed with sudo"; exit 1; fi
	@rm -fv $(SCRIPTDIR)/$(SCRIPTFILE) $(MENUDIR)/$(DESKTOPFILE) $(DATADIR)/$(MAPDATA) $(DATADIR)/$(RCFILE) $(ICONDIR)/$(ICONFILE)
	@if [ -d $(DATADIR) ]; then rmdir -v $(DATADIR); fi

$(SCRIPTDIR)/$(SCRIPTFILE): $(SCRIPTFILE)
	@if [ "`id -u`" != "0" ]; then echo "Need to run as root user or prefixed with sudo"; exit 1; fi
	@mkdir -pv $(SCRIPTDIR)
	@cp -v $(SCRIPTFILE) $(SCRIPTDIR)
	@chmod a+rx $(SCRIPTDIR)/$(SCRIPTFILE)

$(MENUDIR)/$(DESKTOPFILE): $(DESKTOPFILE)
	@if [ "`id -u`" != "0" ]; then echo "Need to run as root user or prefixed with sudo"; exit 1; fi
	@mkdir -pv $(MENUDIR)
	@cp -v $(DESKTOPFILE) $(MENUDIR)
	@chmod a+r $(MENUDIR)/$(DESKTOPFILE)

$(DATADIR)/$(MAPDATA):$(MAPDATA)
	@if [ "`id -u`" != "0" ]; then echo "Need to run as root user or prefixed with sudo"; exit 1; fi
	@mkdir -pv $(DATADIR)
	@cp -v $(MAPDATA) $(DATADIR)
	@chmod a+r $(DATADIR)/$(MAPDATA)

$(DATADIR)/$(RCFILE): $(RCFILE)
	@if [ "`id -u`" != "0" ]; then echo "Need to run as root user or prefixed with sudo"; exit 1; fi
	@mkdir -pv $(DATADIR)
	@cp -v $(RCFILE) $(DATADIR)
	@chmod a+r $(DATADIR)/$(RCFILE)

$(ICONDIR)/$(ICONFILE): $(ICONFILE)
	@if [ "`id -u`" != "0" ]; then echo "Need to run as root user or prefixed with sudo"; exit 1; fi
	@mkdir -pv $(ICONDIR)
	@cp -v $(ICONFILE) $(ICONDIR)
	@chmod a+r $(ICONDIR)/$(ICONFILE)
