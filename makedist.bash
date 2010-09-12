#! /usr/bin/env bash

# get the version number
version="$(grep "^version = " elmapviewer | awk '{print $3}' | cut -c3-)"

# generate HTML from man page
rman -f HTML elmapviewer.6 > elmapviewer.html

# create a version nuber tagged directory
cd ..
ln -sf elmapviewer elmapviewer-${version}

# create the tar file archive
tar cfzhv elmapviewer-${version}.tar.gz --exclude=CVS elmapviewer-${version}/

# create the zip file archive
rm -f elmapviewer-${version}.zip
zip -vD elmapviewer-${version}.zip elmapviewer-${version}/* -x CVS

# clean up
rm -f elmapviewer-${version}
