
# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

# ----------------------------------------------------------
# Author: Alan Odom (Clockmender)
# ----------------------------------------------------------

import bpy
import bmesh
from mathutils import Vector, Quaternion
from math import cos, sin, pi
import numpy as np

# Routine to Display Error Messages.
#
def oops(self, context):
    scene = context.scene
    self.layout.label(text=scene.pdt_error)

def setMode(mode_pl):
    if mode_pl == 'XY':
        # a1 = x a2 = y a3 = z
        return 0, 1, 2
    elif mode_pl == 'XZ':
        # a1 = x a2 = z a3 = y
        return 0, 2, 1
    elif mode_pl == 'YZ':
        # a1 = y a2 = z a3 = x
        return 1, 2, 0

def setAxis(mode_pl):
    # Rotate Axis, Move Axis, Height Axis
    if mode_pl == 'RX-MY':
        return 0, 1, 2
    elif mode_pl == 'RX-MZ':
        return 0, 2, 1
    elif mode_pl == 'RY-MX':
        return 1, 0, 2
    elif mode_pl == 'RY-MZ':
        return 1, 2, 0
    elif mode_pl == 'RZ-MX':
        return 2, 0, 1
    elif mode_pl == 'RZ-MY':
        return 2, 1, 0

def checkSelection(num, bm, obj):
    if len(bm.select_history) < num:
        return None
    else:
        actE = bm.select_history[-1]
    if isinstance(actE, bmesh.types.BMVert):
        actV = actE.co
        if num == 1:
            return actV
        elif num == 2:
            othV = bm.select_history[-2].co
            return actV, othV
        elif num == 3:
            othV = bm.select_history[-2].co
            lstV = bm.select_history[-3].co
            return actV, othV, lstV
        elif num == 4:
            othV = bm.select_history[-2].co
            lstV = bm.select_history[-3].co
            fstV = bm.select_history[-4].co
            return actV, othV, lstV, fstV
    else:
        for f in bm.faces:
            f.select_set(False)
        for e in bm.edges:
            e.select_set(False)
        for v in bm.verts:
            v.select_set(False)
        bmesh.update_edit_mesh(obj.data)
        bm.select_history.clear()
        return None

def updateSel(bm,verts,edges,faces):
    for f in bm.faces:
        f.select_set(False)
    for e in bm.edges:
        e.select_set(False)
    for v in bm.verts:
        v.select_set(False)
    for v in verts:
        v.select_set(True)
    for e in edges:
        e.select_set(True)
    for f in faces:
        f.select_set(True)
    return

def viewCoords(x_loc,y_loc,z_loc):
    areas = [a for a in bpy.context.screen.areas if a.type == 'VIEW_3D']
    if len(areas) > 0:
        vm = areas[0].spaces.active.region_3d.view_matrix
        vm = vm.to_3x3().normalized().inverted()
        vl = Vector((x_loc,y_loc,z_loc))
        vw = vm @ vl
        return vw
    else:
        return Vector((0,0,0))

def viewCoordsI(x_loc,y_loc,z_loc):
    areas = [a for a in bpy.context.screen.areas if a.type == 'VIEW_3D']
    if len(areas) > 0:
        vm = areas[0].spaces.active.region_3d.view_matrix
        vm = vm.to_3x3().normalized()
        vl = Vector((x_loc,y_loc,z_loc))
        vw = vm @ vl
        return vw
    else:
        return Vector((0,0,0))

def viewDir(dis_v,ang_v):
    areas = [a for a in bpy.context.screen.areas if a.type == 'VIEW_3D']
    if len(areas) > 0:
        vm = areas[0].spaces.active.region_3d.view_matrix
        vm = vm.to_3x3().normalized().inverted()
        vl = Vector((0,0,0))
        vl.x = (dis_v * cos(ang_v*pi/180))
        vl.y = (dis_v * sin(ang_v*pi/180))
        vw = vm @ vl
        return vw
    else:
        return Vector((0,0,0))

def euler_to_quaternion(roll, pitch, yaw):
        qx = np.sin(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) - np.cos(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)
        qy = np.cos(roll/2) * np.sin(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.cos(pitch/2) * np.sin(yaw/2)
        qz = np.cos(roll/2) * np.cos(pitch/2) * np.sin(yaw/2) - np.sin(roll/2) * np.sin(pitch/2) * np.cos(yaw/2)
        qw = np.cos(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)

        return Quaternion((qw, qx, qy, qz))

def arcCentre(actV,othV,lstV):
    A = np.array([actV.x, actV.y, actV.z])
    B = np.array([othV.x, othV.y, othV.z])
    C = np.array([lstV.x, lstV.y, lstV.z])
    a = np.linalg.norm(C - B)
    b = np.linalg.norm(C - A)
    c = np.linalg.norm(B - A)
    s = (a + b + c) / 2
    R = a*b*c / 4 / np.sqrt(s * (s - a) * (s - b) * (s - c))
    b1 = a*a * (b*b + c*c - a*a)
    b2 = b*b * (a*a + c*c - b*b)
    b3 = c*c * (a*a + b*b - c*c)
    P = np.column_stack((A, B, C)).dot(np.hstack((b1, b2, b3)))
    P /= b1 + b2 + b3
    return Vector((P[0],P[1],P[2])), R

def intersection(actV,othV,lstV,fstV,plane):
    if plane == 'LO':
        disV = othV-actV
        othV = viewCoordsI(disV.x,disV.y,disV.z)
        disV = lstV-actV
        lstV = viewCoordsI(disV.x,disV.y,disV.z)
        disV = fstV-actV
        fstV = viewCoordsI(disV.x,disV.y,disV.z)
        refV = Vector((0,0,0))
        ap1 = (fstV.x,fstV.y)
        ap2 = (lstV.x,lstV.y)
        bp1 = (othV.x,othV.y)
        bp2 = (refV.x,refV.y)
    else:
        a1,a2,a3 = setMode(plane)
        ap1 = (fstV[a1],fstV[a2])
        ap2 = (lstV[a1],lstV[a2])
        bp1 = (othV[a1],othV[a2])
        bp2 = (actV[a1],actV[a2])
    s = np.vstack([ap1,ap2,bp1,bp2])
    h = np.hstack((s, np.ones((4, 1))))
    l1 = np.cross(h[0], h[1])
    l2 = np.cross(h[2], h[3])
    x, y, z = np.cross(l1, l2)
    if z == 0:
        return Vector((0,0,0)),False
    nx = x/z
    nz = y/z
    if plane == 'LO':
        ly = 0
    else:
        ly = actV[a3]
    # Order Vector Delta
    if plane == 'XZ':
        vector_delta = Vector((nx,ly,nz))
    elif plane == 'XY':
        vector_delta = Vector((nx,nz,ly))
    elif plane == 'YZ':
        vector_delta = Vector((ly,nx,nz))
    elif plane == 'LO':
        vector_delta = viewCoords(nx,nz,ly) + actV
    return vector_delta,True

def getPercent(obj, flip_p, per_v, data, scene):
    if obj.mode == 'EDIT':
        bm = bmesh.from_edit_mesh(obj.data)
        verts = [v for v in bm.verts if v.select]
        if len(verts) == 2:
            actV = verts[0].co
            othV = verts[1].co
            if actV == None:
                scene.pdt_error = "Work in Vertex Mode"
                bpy.context.window_manager.popup_menu(oops, title="Error", icon='ERROR')
                return None
        else:
            scene.pdt_error = "Select 2 Vertices Individually"
            bpy.context.window_manager.popup_menu(oops, title="Error", icon='ERROR')
            return None
        p1 = np.array([actV.x,actV.y,actV.z])
        p2 = np.array([othV.x,othV.y,othV.z])
    elif obj.mode == 'OBJECT':
        objs = bpy.context.view_layer.objects.selected
        if len(objs) != 2:
            scene.pdt_error = "Select Only 2 Objects"
            bpy.context.window_manager.popup_menu(oops, title="Error", icon='ERROR')
            return None
        else:
            p1 = np.array([objs[-1].matrix_world.decompose()[0].x,
                    objs[-1].matrix_world.decompose()[0].y,
                    objs[-1].matrix_world.decompose()[0].z])
            p2 = np.array([objs[-2].matrix_world.decompose()[0].x,
                    objs[-2].matrix_world.decompose()[0].y,
                    objs[-2].matrix_world.decompose()[0].z])
    p4 = np.array([0,0,0])
    p3 = p2-p1
    if flip_p:
        if data != 'MV':
            tst = ((p4 + p3) * ((100 - per_v) / 100)) + p1
        else:
            tst = ((p4 + p3) * (per_v / 100)) + p1
    else:
        if data != 'MV':
            tst = ((p4 + p3) * (per_v / 100)) + p1
        else:
            tst = ((p4 + p3) * ((100 - per_v) / 100)) + p1
    return Vector((tst[0],tst[1],tst[2]))
