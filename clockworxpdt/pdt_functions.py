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
import bgl
import blf
import gpu
from mathutils import Vector, Quaternion
from gpu_extras.batch import batch_for_shader
from math import cos, sin, pi
import numpy as np
from .pdt_msg_strings import *


def oops(self, context):
    """Error Routine.

    Displays error message in a popup.

    Args:
        context: Current Blender bpy.context

    Notes:
        Uses pdt_error scene variable
    """

    scene = context.scene
    self.layout.label(text=scene.pdt_error)


def setMode(mode_pl):
    """Sets Active Axes for View Orientation.

    Sets indices of axes for locational vectors

    Args:
        mode_pl: Plane Selector variable as input

    Returns:
        3 Integer indices.
    """

    if mode_pl == "XY":
        # a1 = x a2 = y a3 = z
        return 0, 1, 2
    elif mode_pl == "XZ":
        # a1 = x a2 = z a3 = y
        return 0, 2, 1
    elif mode_pl == "YZ":
        # a1 = y a2 = z a3 = x
        return 1, 2, 0


def setAxis(mode_pl):
    """Sets Active Axes for View Orientation.

    Sets indices for axes from taper vectors

    Args:
        mode_pl: Taper Axis Selector variable as input

    Notes:
        Axis order: Rotate Axis, Move Axis, Height Axis

    Returns:
        3 Integer Indicies.
    """

    if mode_pl == "RX-MY":
        return 0, 1, 2
    elif mode_pl == "RX-MZ":
        return 0, 2, 1
    elif mode_pl == "RY-MX":
        return 1, 0, 2
    elif mode_pl == "RY-MZ":
        return 1, 2, 0
    elif mode_pl == "RZ-MX":
        return 2, 0, 1
    elif mode_pl == "RZ-MY":
        return 2, 1, 0


def checkSelection(num, bm, obj):
    """Check that the Object's select_history has sufficient entries.

    If selection history is not Verts, clears selection and history.

    Args:
        num: The number of entries required for each operation
        bm: The Bmesh from the Object
        obj: The Object

    Returns:
        list of 3D points as Vectors.
    """

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


def updateSel(bm, verts, edges, faces):
    """Updates Vertex, Edge and Face Selections following a function.

    Args:
        bm: Object Bmesh
        verts: New Selection for Vertices
        edges: The Edges on which to operate
        faces: The Faces on which to operate

    Returns:
        Nothing.
    """
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


def viewCoords(x_loc, y_loc, z_loc):
    """Converts input Vector values to new Screen Oriented Vector.

    Args:
        x_loc: X coordinate from vector
        y_loc: Y coordinate from vector
        z_loc: Z coordinate from vector

    Returns:
        Vector adjusted to View's Inverted Tranformation Matrix.
    """

    areas = [a for a in bpy.context.screen.areas if a.type == "VIEW_3D"]
    if len(areas) > 0:
        vm = areas[0].spaces.active.region_3d.view_matrix
        vm = vm.to_3x3().normalized().inverted()
        vl = Vector((x_loc, y_loc, z_loc))
        vw = vm @ vl
        return vw
    else:
        return Vector((0, 0, 0))


def viewCoordsI(x_loc, y_loc, z_loc):
    """Converts Screen Oriented input Vector values to new World Vector.

    Converts View tranformation Matrix to Rotational Matrix

    Args:
        x_loc: X coordinate from vector
        y_loc: Y coordinate from vector
        z_loc: Z coordinate from vector

    Returns:
        Vector adjusted to View's Transformation Matrix.
    """

    areas = [a for a in bpy.context.screen.areas if a.type == "VIEW_3D"]
    if len(areas) > 0:
        vm = areas[0].spaces.active.region_3d.view_matrix
        vm = vm.to_3x3().normalized()
        vl = Vector((x_loc, y_loc, z_loc))
        vw = vm @ vl
        return vw
    else:
        return Vector((0, 0, 0))


def viewDir(dis_v, ang_v):
    """Converts Distance and Angle to View Oriented Vector.

    Converts View Transformation Matrix to Rotational Matrix (3x3)
    Angles are converted to Radians from degrees.

    Args:
        dis_v: Scene distance
        ang_v: Scene angle

    Returns:
        World Vector.
    """

    areas = [a for a in bpy.context.screen.areas if a.type == "VIEW_3D"]
    if len(areas) > 0:
        vm = areas[0].spaces.active.region_3d.view_matrix
        vm = vm.to_3x3().normalized().inverted()
        vl = Vector((0, 0, 0))
        vl.x = dis_v * cos(ang_v * pi / 180)
        vl.y = dis_v * sin(ang_v * pi / 180)
        vw = vm @ vl
        return vw
    else:
        return Vector((0, 0, 0))


def euler_to_quaternion(roll, pitch, yaw):
    """Converts Euler Rotation to Quaternion Rotation.

    Args:
        roll: Roll in Euler rotation
        pitch: Pitch in Euler rotation
        yaw: Yaw in Euler rotation

    Returns:
        Quaternion Rotation.
    """

    # fmt: off
    qx = (np.sin(roll/2) * np.cos(pitch/2) * np.cos(yaw/2)
         - np.cos(roll/2) * np.sin(pitch/2) * np.sin(yaw/2))
    qy = (np.cos(roll/2) * np.sin(pitch/2) * np.cos(yaw/2)
         + np.sin(roll/2) * np.cos(pitch/2) * np.sin(yaw/2))
    qz = (np.cos(roll/2) * np.cos(pitch/2) * np.sin(yaw/2)
         - np.sin(roll/2) * np.sin(pitch/2) * np.cos(yaw/2))
    qw = (np.cos(roll/2) * np.cos(pitch/2) * np.cos(yaw/2)
         + np.sin(roll/2) * np.sin(pitch/2) * np.sin(yaw/2))
    # fmt: on
    return Quaternion((qw, qx, qy, qz))


def arcCentre(actV, othV, lstV):
    """Calculates Centre of Arc from 3 Vector Locations using standard Numpy routine

    Args:
        actV: Active vector location
        othV: Other vector location
        lstV: Last vector location

    Returns:
        Vector representing Arc Centre and Float representing Arc Radius.
    """

    A = np.array([actV.x, actV.y, actV.z])
    B = np.array([othV.x, othV.y, othV.z])
    C = np.array([lstV.x, lstV.y, lstV.z])
    a = np.linalg.norm(C - B)
    b = np.linalg.norm(C - A)
    c = np.linalg.norm(B - A)
    # fmt: off
    s = (a+b+c) / 2
    R = a*b*c/4 / np.sqrt(s * (s-a) * (s-b) * (s-c))
    b1 = a*a * (b*b + c*c - a*a)
    b2 = b*b * (a*a + c*c - b*b)
    b3 = c*c * (a*a + b*b - c*c)
    # fmt: on
    P = np.column_stack((A, B, C)).dot(np.hstack((b1, b2, b3)))
    P /= b1 + b2 + b3
    return Vector((P[0], P[1], P[2])), R


def intersection(actV, othV, lstV, fstV, plane):
    """Calculates Intersection Point of 2 Imagined Lines from 4 Vectors.

    Calculates Converging Intersect Location and indication of
    whether the lines are convergent using standard Numpy Routines

    Args:
        actV: Active vector location of first line
        othV: Other vector location of first line
        lstV: Last vector location of 2nd line
        fstV: First vector location of 2nd line
        plane: Working Plane 4 Vector Locations representing 2 lines and Working Plane

    Returns:
        Intersection Vector and Boolean for convergent state.
    """

    if plane == "LO":
        disV = othV - actV
        othV = viewCoordsI(disV.x, disV.y, disV.z)
        disV = lstV - actV
        lstV = viewCoordsI(disV.x, disV.y, disV.z)
        disV = fstV - actV
        fstV = viewCoordsI(disV.x, disV.y, disV.z)
        refV = Vector((0, 0, 0))
        ap1 = (fstV.x, fstV.y)
        ap2 = (lstV.x, lstV.y)
        bp1 = (othV.x, othV.y)
        bp2 = (refV.x, refV.y)
    else:
        a1, a2, a3 = setMode(plane)
        ap1 = (fstV[a1], fstV[a2])
        ap2 = (lstV[a1], lstV[a2])
        bp1 = (othV[a1], othV[a2])
        bp2 = (actV[a1], actV[a2])
    s = np.vstack([ap1, ap2, bp1, bp2])
    h = np.hstack((s, np.ones((4, 1))))
    l1 = np.cross(h[0], h[1])
    l2 = np.cross(h[2], h[3])
    x, y, z = np.cross(l1, l2)
    if z == 0:
        return Vector((0, 0, 0)), False
    nx = x / z
    nz = y / z
    if plane == "LO":
        ly = 0
    else:
        ly = actV[a3]
    # Order Vector Delta
    if plane == "XZ":
        vector_delta = Vector((nx, ly, nz))
    elif plane == "XY":
        vector_delta = Vector((nx, nz, ly))
    elif plane == "YZ":
        vector_delta = Vector((ly, nx, nz))
    elif plane == "LO":
        vector_delta = viewCoords(nx, nz, ly) + actV
    return vector_delta, True


def getPercent(obj, flip_p, per_v, data, scene):
    """Calculates a Percentage Distance between 2 Vectors.

    Calculates a point that lies a set percentage between two given points
    using standard Numpy Routines.

    Works for either 2 vertices for an object in Edit mode
    or 2 selected objects in Object mode.

    Setting pdt_flip to True causes percentage to be measured from second vector.

    Args:
        obj: The Object under consideration
        per_v: FIXME
        data: pdt_flip, pdt_percent scene variables & Operational Mode
        scene: Context Scene

    Returns:
        World Vector.
    """

    if obj.mode == "EDIT":
        bm = bmesh.from_edit_mesh(obj.data)
        verts = [v for v in bm.verts if v.select]
        if len(verts) == 2:
            actV = verts[0].co
            othV = verts[1].co
            if actV is None:
                scene.pdt_error = PDT_ERR_VERT_MODE
                bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return None
        else:
            scene.pdt_error = PDT_ERR_SEL_2_V_1_E + str(len(verts)) + " Vertices"
            bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return None
        p1 = np.array([actV.x, actV.y, actV.z])
        p2 = np.array([othV.x, othV.y, othV.z])
    elif obj.mode == "OBJECT":
        objs = bpy.context.view_layer.objects.selected
        if len(objs) != 2:
            scene.pdt_error = PDT_ERR_SEL_2_OBJS + str(len(objs)) + ")"
            bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return None
        else:
            p1 = np.array(
                [
                    objs[-1].matrix_world.decompose()[0].x,
                    objs[-1].matrix_world.decompose()[0].y,
                    objs[-1].matrix_world.decompose()[0].z,
                ]
            )
            p2 = np.array(
                [
                    objs[-2].matrix_world.decompose()[0].x,
                    objs[-2].matrix_world.decompose()[0].y,
                    objs[-2].matrix_world.decompose()[0].z,
                ]
            )
    p4 = np.array([0, 0, 0])
    p3 = p2 - p1
    if flip_p:
        if data != "MV":
            # fmt: off
            tst = ((p4+p3) * ((100-per_v) / 100)) + p1
            # fmt: on
        else:
            # fmt: off
            tst = ((p4+p3) * (per_v / 100)) + p1
            # fmt: on
    else:
        if data != "MV":
            # fmt: off
            tst = ((p4+p3) * (per_v / 100)) + p1
            # fmt: on
        else:
            # fmt: off
            tst = ((p4+p3) * ((100-per_v) / 100)) + p1
            # fmt: on
    return Vector((tst[0], tst[1], tst[2]))


def objCheck(obj, scene, data):
    """Check Object & Selection Validity.

    Args:
        obj: Active Object
        scene: Active Scene
        data: Operation to check

    Returns:
        Object Bmesh and Validity Boolean.
    """

    if obj is None:
        scene.pdt_error = PDT_ERR_NO_ACT_OBJ
        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return None, False
    if obj.mode == "EDIT":
        bm = bmesh.from_edit_mesh(obj.data)
        if data in ["s", "S"]:
            edges = [e for e in bm.edges]
            if len(edges) < 1:
                scene.pdt_error = PDT_ERR_SEL_1_EDGEM + str(len(edges)) + ")"
                bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return None, False
            else:
                return bm, True
        if len(bm.select_history) >= 1:
            if data not in ["e", "E", "g", "G", "d", "D", "s", "S"]:
                actV = checkSelection(1, bm, obj)
            else:
                verts = [v for v in bm.verts if v.select]
                if len(verts) > 0:
                    actV = verts[0]
                else:
                    actV = None
            if actV is None:
                scene.pdt_error = PDT_ERR_VERT_MODE
                bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return None, False
        elif data in ["c", "C", "n", "N"]:
            scene.pdt_error = PDT_ERR_SEL_1_VERTI + str(len(bm.select_history)) + ")"
            bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return None, False
        return bm, True
    elif obj.mode == "OBJECT":
        return None, True


def disAng(vals, flip_a, plane, scene):
    """Set Working Axes when using Direction command.

    Args:
        vals: Input Arguments (Values)
        flip_a: Whether to flip the angle
        plane: Working Plane
        scene: Current Scene

    Returns:
        Directional Offset as a Vector.
    """

    dis_v = float(vals[0])
    ang_v = float(vals[1])
    if flip_a:
        if ang_v > 0:
            ang_v = ang_v - 180
        else:
            ang_v = ang_v + 180
        scene.pdt_angle = ang_v
    if plane == "LO":
        vector_delta = viewDir(dis_v, ang_v)
    else:
        a1, a2, a3 = setMode(plane)
        vector_delta = Vector((0, 0, 0))
        # fmt: off
        vector_delta[a1] = vector_delta[a1] + (dis_v * cos(ang_v * pi/180))
        vector_delta[a2] = vector_delta[a2] + (dis_v * sin(ang_v * pi/180))
        # fmt: on
    return vector_delta


# Shader for displaying the Pivot Point as Graphics.
#
shader = gpu.shader.from_builtin("3D_UNIFORM_COLOR") if not bpy.app.background else None


def draw3D(coords, type, rgba, context):
    """Draw Pivot Point Graphics.

    Draws either Lines Points, or Tris using defined shader

    Args:
        coords: Input Coordinates List
        type: Graphic Type
        rgba: Colour in RGBA format
        context: Current Blender bpy.context

    Returns:
        Nothing.
    """

    scene = context.scene
    batch = batch_for_shader(shader, type, {"pos": coords})

    try:
        if coords is not None:
            bgl.glEnable(bgl.GL_BLEND)
            shader.bind()
            shader.uniform_float("color", rgba)
            batch.draw(shader)
    except:
        pass


def drawCallback3D(self, context):
    """Create Coordinate List for Pivot Point Graphic.

    Creates coordinates for Pivot Point Graphic consisting of 6 Tris
    and one Point colour coded Red; X axis, Green; Y axis, Blue; Z axis
    and a yellow point based upon screen scale

    Args:
        context: Current Blender bpy.context

    Returns:
        Nothing.
    """

    scene = context.scene
    w = context.region.width
    x = scene.pdt_pivotloc.x
    y = scene.pdt_pivotloc.y
    z = scene.pdt_pivotloc.z
    # Scale it from view
    areas = [a for a in context.screen.areas if a.type == "VIEW_3D"]
    if len(areas) > 0:
        sf = abs(areas[0].spaces.active.region_3d.window_matrix.decompose()[2][1])
    a = w / sf / 10000 * scene.pdt_pivotsize
    b = a * 0.65
    c = a * 0.05 + (scene.pdt_pivotwidth * a * 0.02)
    o = c / 3

    # fmt: off
    # X Axis
    coords = [
        (x, y, z),
        (x+b, y-o, z),
        (x+b, y+o, z),
        (x+a, y, z),
        (x+b, y+c, z),
        (x+b, y-c, z),
    ]
    # fmt: on
    colour = (1.0, 0.0, 0.0, scene.pdt_pivotalpha)
    draw3D(coords, "TRIS", colour, context)
    coords = [(x, y, z), (x+a, y, z)]
    draw3D(coords, "LINES", colour, context)
    # fmt: off
    # Y Axis
    coords = [
        (x, y, z),
        (x-o, y+b, z),
        (x+o, y+b, z),
        (x, y+a, z),
        (x+c, y+b, z),
        (x-c, y+b, z),
    ]
    # fmt: on
    colour = (0.0, 1.0, 0.0, scene.pdt_pivotalpha)
    draw3D(coords, "TRIS", colour, context)
    coords = [(x, y, z), (x, y + a, z)]
    draw3D(coords, "LINES", colour, context)
    # fmt: off
    # Z Axis
    coords = [
        (x, y, z),
        (x-o, y, z+b),
        (x+o, y, z+b),
        (x, y, z+a),
        (x+c, y, z+b),
        (x-c, y, z+b),
    ]
    # fmt: on
    colour = (0.2, 0.5, 1.0, scene.pdt_pivotalpha)
    draw3D(coords, "TRIS", colour, context)
    coords = [(x, y, z), (x, y, z + a)]
    draw3D(coords, "LINES", colour, context)
    # Centre
    coords = [(x, y, z)]
    colour = (1.0, 1.0, 0.0, scene.pdt_pivotalpha)
    draw3D(coords, "POINTS", colour, context)


def scale_set(self, context):
    """Sets Scale by dividing Pivot Distance by System Distance.

    Sets Pivot Point Scale Factors by Measurement

    Args:
        context: Current Blender bpy.context

    Note:
        Uses pdt_pivotdis & pdt_distance scene variables

    Returns:
        Status Set.
    """

    scene = context.scene
    sys_dis = scene.pdt_distance
    scale_dis = scene.pdt_pivotdis
    if scale_dis > 0:
        scale_fac = scale_dis / sys_dis
        scene.pdt_pivotscale = Vector((scale_fac, scale_fac, scale_fac))
