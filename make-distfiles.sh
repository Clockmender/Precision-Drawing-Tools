#!/bin/bash
#
# This script creates a folder with PDT python scripts which are ready to be
# copied into the official Blender addons/ git repository and committed.
#
# This file is licensed under the GNU General Public Licence v2
#
# Copyright (c) 2019 Rune Morling (ermo)
#

DIRNAME="precision_drawing_tools/"

if [[ ! -f pdt_design.py ]]; then
    echo "** $0 needs to be run from within the Precision-Drawing-Tools git clone."
    echo ""
    echo "-- Exiting."
    echo ""
    exit 1
fi

if [[ -d "${DIRNAME}"  ]]; then
    echo ""
    echo "** ${DIRNAME} already exists; deleting it ..."
    rm -rf "${DIRNAME}"
fi

echo ""
echo "-- Creating folder ./${DIRNAME} ..."
mkdir -pv "./${DIRNAME}"

echo ""
echo "-- Copying .py script files to ${DIRNAME} ..."
for PYFILE in *.py
    do
        cp -v "${PYFILE}" "${DIRNAME}"
    done

echo ""
echo "-- Contents of ${DIRNAME} :"
ls -lA "${DIRNAME}"

echo ""
echo "Now copy ${DIRNAME} into the clone of the official Blender addons/ git repo"
echo "and git add & git commit the new versions of the PDT files."
echo ""
