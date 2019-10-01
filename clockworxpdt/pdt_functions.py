
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
#
# Common Functions used in more than one place in PDT Operations

import bpy
import bmesh
from mathutils import Vector, Quaternion
from math import cos, sin, pi
import numpy as np

def oops(self, context):
    """Error Routine.

    Uses pdt_error scene variable
    Displays error message in a popup."""
    scene = context.scene
    self.layout.label(text=scene.pdt_error)

def setMode(mode_pl):
    """Sets Active Axes for View Orientation.

    Takes: Plane Selector variable as input
    Sets indices of axes for locational vectors
    Returns: 3 Integer Indicies."""
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
    """Sets Active Axes for View Orientation.

    Takes: Taper Axis Selector variable as input
    Sets indices for axes from taper vectors
    Axis order: Rotate Axis, Move Axis, Height Axis
    Returns: 3 Integer Indicies."""
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
    """Check that the Object's select_history has suffuceint entries.

    Takes: number of entries required for each operation,
    the Bmesh from the Object and the Object
    If selection history is not Verts, clears selection and history
    Returns: list of 3D points as Vectors."""
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
    """Updates Vertex, Edge and Face Selections following a function.

    Takes: Object Bmesh, New Selection for Vertices, Edges and Faces
    Returns: Nothing."""
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
    """Converts input Vector values to new Screen Oriented Vector.

    Takes: X, Y & Z values from a vector
    Returns: Vector adjusted to View's Inverted Tranformation Matrix."""
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
    """Converts Screen Oriented input Vector values to new World Vector.

    Takes: X, Y & Z values from a Vector
    Converts View tranformation Matrix to Rotational Matrix
    Returns: Vector adjusted to View's Transformation Matrix."""
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
    """Converts Distance and Angle to View Oriented Vector.

    Takes: scene distance and angle variables and
    converts them to View Oriented Vector
    Converts View Transformation Matrix to Rotational Matrix (3x3)
    Angles are converted to Radians from degrees
    Returns: World Vector."""
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
    """Converts Euler Rotation to Quaternion Rotation.

    Takes: 3 rotational values from Euler Rotation
    and converts to Quaternion Rotation
    Returns: Quaternion Rotation."""
    qx = np.sin(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) - np.cos(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)
    qy = np.cos(roll/2) * np.sin(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.cos(pitch/2) * np.sin(yaw/2)
    qz = np.cos(roll/2) * np.cos(pitch/2) * np.sin(yaw/2) - np.sin(roll/2) * np.sin(pitch/2) * np.cos(yaw/2)
    qw = np.cos(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)

    return Quaternion((qw, qx, qy, qz))

def arcCentre(actV,othV,lstV):
    """Calculates Centre of Arc from 3 Vector Locations.

    Takes: 3 Vector Locations that lie upon an Arc using
    standard Numpy Routines
    Returns: Vector representing Arc Centre and Float representing Arc Radius."""
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
    """Calculates Intersection Point of 2 Imagined Lines from 4 Vectors.

    Takes: 4 Vector Locations representing 2 lines and Working Plane
    calculates Converging Intersect Location and indication of
    whether the lines are convergent using standard Numpy Routines
    Returns: Intersection Vector and Boolean for convergent state."""
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
    """ Calculates a Percentage Distance between 2 Vectors.

    Takes: Object & pdt_flip, pdt_percent scene variables Operational Mode as 'data' & Context Scene
    Calculates a point that lies a set percentage between two given points
    using standard Numpy Routines, pdt_flip causes percentage to be measured from second vector
    Works for either 2 vertices for an object in Edit mode
    or 2 selected objects in Object mode
    Returns: World Vector."""
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
