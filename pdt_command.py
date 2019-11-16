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
#
# ----------------------------------------------------------
# Author: Alan Odom (Clockmender) Copyright © 2019
# ----------------------------------------------------------
#
import bpy
from bpy.types import Operator, Panel, PropertyGroup
from mathutils import Vector
import bmesh
import numpy as np
from math import *
from mathutils.geometry import intersect_point_line
from .pdt_functions import (
    setMode,
    checkSelection,
    setAxis,
    updateSel,
    viewCoords,
    viewCoordsI,
    viewDir,
    euler_to_quaternion,
    arcCentre,
    intersection,
    getPercent,
    oops,
    disAng,
    objCheck,
)
from .pdt_msg_strings import *

def pdt_help(self, context):
    self.layout.label(text="Primary Letters (Available Secondary Letters):")
    self.layout.label(text="C c: Cursor (A a, D d, I i, P p)")
    self.layout.label(text="D d: Duplicate Geometry (D d, I i)")
    self.layout.label(text="E e: Extrude Geometry (D d, I i)")
    self.layout.label(text="F f: Fillet (V v, E e)")
    self.layout.label(text="G g: Grab (Move) (A a, D d, I i, P p)")
    self.layout.label(text="N n: New Vertex (A a, D d, I i, P p)")
    self.layout.label(text="M m: Maths Functions (X x, Z z, D d, A a, P p)")
    self.layout.label(text="P p: Pivot Point (A a, D d, I i, P p)")
    self.layout.label(text="V v: Extrude Vetice Only (A a, D d, I i, P p)")
    self.layout.label(text="S s: Split Edges (A a, D d, I i, P p)")
    self.layout.label(text="?: Quick Help")
    self.layout.label(text="")
    self.layout.label(text="Secondary Letters:")
    self.layout.label(text="A a: Absolute (Global) Coords e.g. 1,3,2")
    self.layout.label(text="D d: Delta (Incremental) Coords, e.g. 0.5,0,1.2")
    self.layout.label(text="I i: Directional (Polar) Coords e.g. 2.6,45")
    self.layout.label(text="P p: Percent e.g. 67.5")
    self.layout.label(text="Additions for Maths:")
    self.layout.label(text="X x, Y y, Z z: Send Input to X, Y & Z Inputs")
    self.layout.label(text="D d, A a: Send input to Distance, or Angle Inputs")
    self.layout.label(text="Additions for Fillet:")
    self.layout.label(text="V v: Fillet Vertices")
    self.layout.label(text="E e: Fillet Edges")
    self.layout.label(text="")
    self.layout.label(text="Example:")
    self.layout.label(text="ed0.5,,0.6 - Extrude Geometry Delta 0.5 in X, 0.6 in Z")

def command_run(self, context):
    """Run Command String as input into Command Line.

    Args:
        context: Current Blender bpy.context

    Note:
        Uses pdt_command, pdt_error & many other 'scene.pdt_' variables to set PDT menu items, or alter functions

        Command Format; Operation(single letter) Mode(single letter) Values(up to 3 values separated by commas)
        Example; CD0.4,0.6,1.1 - Moves Cursor Delta XYZ = 0.4,0.6,1.1 from Current Position/Active Vertex/Object Origin
        Example; SP35 - Splits active Edge at 35% of separation between edge's vertices

        Valid First Letters (as 'oper' - pdt_command[0])
            C = Cursor, G = Grab(move), N = New Vertex, V = Extrude Vertices Only, E = Extrude geometry
            P = Move Pivot Point, D = Duplicate geometry, S = Split Edges
            Capitals and Lower case letters are both allowed

        Valid Second Letters (as 'mode' - pdt_command[1])
            A = Absolute XYZ, D = Delta XYZ, I = Distance at Angle, P = Percent
            X = X Delta, Y = Y, Delta Z, = Z Delta (Maths Operation only)
            V = Vertex Bevel, G = Geometry Bevel
            Capitals and Lower case letters are both allowed

        Valid Values (pdt_command[2:]) - Only Integers and Floats, missing values are set to 0,
            appropriate length checks are performed as Values is split by commas
            Example; CA,,3 - Cursor to Absolute, is re-interpreted as CA0,0,3

            Exception for Maths Operation, Values section is evaluated as Maths command
            Example; madegrees(atan(3/4)) - sets PDT Angle to smallest angle of 3,4,5 Triangle; (36.8699 degrees)
            This is why all Math functions are imported

    Returns:
        Nothing.
    """

    scene = context.scene
    cmd = scene.pdt_command

    if cmd == "?" or cmd.lower() == "help":
        # fmt: off
        bpy.context.window_manager.popup_menu(pdt_help, title="PDT Command Line - Valid Commands:", icon="INFO")
        # fmt: on
        return

    if len(cmd) < 3:
        scene.pdt_error = PDT_ERR_CHARS_NUM
        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
        return
    else:
        oper = cmd[0]
        # fmt: off
        if oper not in [
            "c", "C",
            "d", "D",
            "e", "E",
            "f", "F",
            "g", "G",
            "n", "N",
            "m", "M",
            "p", "P",
            "v", "V",
            "s", "S",
            "?",
        ]:
            scene.pdt_error = PDT_ERR_BADFLETTER
            bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        mode = cmd[1]
        if mode not in [
            "a", "A",
            "d", "D",
            "e", "E"
            "g", "G",
            "i", "I",
            "p", "P",
            "v", "V",
            "x", "X",
            "y", "Y",
            "z", "Z"
        ]:
            # fmt: on
            scene.pdt_error = PDT_ERR_BADSLETTER
            bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return


        if oper in ["m", "M"]:
            exp = cmd[2:]
            if "," in exp:
                scene.pdt_error = PDT_ERR_NOCOMMAS
                bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            try:
                num = eval(exp)
            except ValueError:
                scene.pdt_error = PDT_ERR_BADMATHS
                bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
            if mode in ["x", "X"]:
                scene.pdt_delta_x = num
            elif mode in ["y", "Y"]:
                scene.pdt_delta_y = num
            elif mode in ["z", "Z"]:
                scene.pdt_delta_z = num
            elif mode in ["d", "D"]:
                scene.pdt_distance = num
            elif mode in ["a", "A"]:
                scene.pdt_angle = num
            elif mode in ["p", "P"]:
                scene.pdt_percent = num
            else:
                scene.pdt_error = f"{mode} {PDT_ERR_NON_VALID} Maths)"
                bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
            return
        else:
            if mode in ["x", "X", "y", "Y", "z", "Z"]:
                scene.pdt_error = PDT_ERR_BADCOORDL
                bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return

        vals = cmd[2:].split(",")
        ind = 0
        for r in vals:
            try:
                number = float(r)
                good = True
            except ValueError:
                vals[ind] = "0"
            ind = ind + 1
        mode_s = scene.pdt_select
        flip_a = scene.pdt_flipangle
        flip_p = scene.pdt_flippercent
        ext_a = scene.pdt_extend
        plane = scene.pdt_plane
        # This bit needs looking at.
        if mode not in ["a", "A"] or (oper in ["s", "S"] and mode in ["a", "A"]):
            obj = bpy.context.view_layer.objects.active
            bm, good = objCheck(obj, scene, oper)
            if obj.mode == "EDIT":
                if len(bm.select_history) < 1 and oper in ["c", "C", "n", "N", "p", "P"]:
                    scene.pdt_error = PDT_ERR_NO_ACT_VERT
                    bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    return
            if good:
                obj_loc = obj.matrix_world.decompose()[0]
            else:
                return

        if oper in ["c", "C", "p", "P"]:
            # Cursor or Pivot Point
            if mode in ["a", "A"]:
                # Absolute Options
                if len(vals) != 3:
                    scene.pdt_error = PDT_ERR_BAD3VALS
                    bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    return
                vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
                if oper in ["c", "C"]:
                    scene.cursor.location = vector_delta
                else:
                    scene.pdt_pivotloc = vector_delta
            elif mode in ["d", "D"]:
                # Delta Options
                if len(vals) != 3:
                    scene.pdt_error = PDT_ERR_BAD3VALS
                    bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    return
                vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
                if mode_s == "REL":
                    if oper in ["c", "C"]:
                        scene.cursor.location = scene.cursor.location + vector_delta
                    else:
                        scene.pdt_pivotloc = scene.pdt_pivotloc + vector_delta
                elif mode_s == "SEL":
                    if obj.mode == "EDIT":
                        if oper in ["c", "C"]:
                            scene.cursor.location = (
                                bm.select_history[-1].co + obj_loc + vector_delta
                            )
                        else:
                            scene.pdt_pivotloc = bm.select_history[-1].co + obj_loc + vector_delta
                    elif obj.mode == "OBJECT":
                        if oper in ["c", "C"]:
                            scene.cursor.location = obj_loc + vector_delta
                        else:
                            scene.pdt_pivotloc = obj_loc + vector_delta
            elif mode in ["i", "I"]:
                # Direction Options
                if len(vals) != 2:
                    scene.pdt_error = PDT_ERR_BAD2VALS
                    bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    return
                vector_delta = disAng(vals, flip_a, plane, scene)
                if mode_s == "REL":
                    if oper in ["c", "C"]:
                        scene.cursor.location = scene.cursor.location + vector_delta
                    else:
                        scene.pdt_pivotloc = scene.pdt_pivotloc + vector_delta
                elif mode_s == "SEL":
                    if obj.mode == "EDIT":
                        if oper in ["c", "C"]:
                            scene.cursor.location = (
                                bm.select_history[-1].co + obj_loc + vector_delta
                            )
                        else:
                            scene.pdt_pivotloc = bm.select_history[-1].co + obj_loc + vector_delta
                    elif obj.mode == "OBJECT":
                        if oper in ["c", "C"]:
                            scene.cursor.location = obj_loc + vector_delta
                        else:
                            scene.pdt_pivotloc = obj_loc + vector_delta
            elif mode in ["p", "P"]:
                # Percent Options
                if len(vals) != 1:
                    scene.pdt_error = PDT_ERR_BAD1VALS
                    bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    return
                vector_delta = getPercent(obj, flip_p, float(vals[0]), oper, scene)
                if vector_delta is None:
                    return
                if obj.mode == "EDIT":
                    if oper in ["c", "C"]:
                        scene.cursor.location = obj_loc + vector_delta
                    else:
                        scene.pdt_pivotloc = obj_loc + vector_delta
                elif obj.mode == "OBJECT":
                    if oper in ["c", "C"]:
                        scene.cursor.location = vector_delta
                    else:
                        scene.pdt_pivotloc = vector_delta
            else:
                scene.pdt_error = f"'{mode}' {PDT_ERR_NON_VALID} '{oper}'"
                bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return

        elif oper in ["g", "G"]:
            # Move Vertices or Objects
            if mode in ["a", "A"]:
                if len(vals) != 3:
                    scene.pdt_error = PDT_ERR_BAD3VALS
                    bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    return
                vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
                if obj.mode == "EDIT":
                    verts = [v for v in bm.verts if v.select]
                    if len(verts) == 0:
                        scene.pdt_error = PDT_ERR_NO_SEL_GEOM
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    for v in verts:
                        v.co = vector_delta - obj_loc
                    bmesh.ops.remove_doubles(
                        bm, verts=[v for v in bm.verts if v.select], dist=0.0001
                    )
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
                elif obj.mode == "OBJECT":
                    for ob in bpy.context.view_layer.objects.selected:
                        ob.location = vector_delta
            elif mode in ["d", "D"]:
                if len(vals) != 3:
                    scene.pdt_error = PDT_ERR_BAD3VALS
                    bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    return
                vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
                if obj.mode == "EDIT":
                    bmesh.ops.translate(
                        bm, verts=[v for v in bm.verts if v.select], vec=vector_delta
                    )
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
                elif obj.mode == "OBJECT":
                    for ob in bpy.context.view_layer.objects.selected:
                        ob.location = obj_loc + vector_delta
            elif mode in ["i", "I"]:
                if len(vals) != 2:
                    scene.pdt_error = PDT_ERR_BAD2VALS
                    bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    return
                vector_delta = disAng(vals, flip_a, plane, scene)
                if obj.mode == "EDIT":
                    verts = [v for v in bm.verts if v.select]
                    if len(verts) == 0:
                        scene.pdt_error = PDT_ERR_NO_SEL_GEOM
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    bmesh.ops.translate(bm, verts=verts, vec=vector_delta)
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
                elif obj.mode == "OBJECT":
                    for ob in bpy.context.view_layer.objects.selected:
                        ob.location = ob.location + vector_delta
            elif mode in ["p", "P"]:
                if obj.mode == "OBJECT":
                    if len(vals) != 1:
                        scene.pdt_error = PDT_ERR_BAD1VALS
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    vector_delta = getPercent(obj, flip_p, float(vals[0]), oper, scene)
                    if vector_delta is None:
                        return
                    ob.location = vector_delta
            else:
                scene.pdt_error = f"'{mode}' {PDT_ERR_NON_VALID} '{oper}'"
                bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return

        elif oper in ["n", "N"]:
            # Add New Vertex
            if obj.mode == "EDIT":
                if mode in ["a", "A"]:
                    if len(vals) != 3:
                        scene.pdt_error = PDT_ERR_BAD3VALS
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
                    vNew = vector_delta - obj_loc
                    nVert = bm.verts.new(vNew)
                    for v in [v for v in bm.verts if v.select]:
                        v.select_set(False)
                    nVert.select_set(True)
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
                elif mode in ["d", "D"]:
                    if len(vals) != 3:
                        scene.pdt_error = PDT_ERR_BAD3VALS
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
                    vNew = bm.select_history[-1].co + vector_delta
                    nVert = bm.verts.new(vNew)
                    for v in [v for v in bm.verts if v.select]:
                        v.select_set(False)
                    nVert.select_set(True)
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
                elif mode in ["i", "I"]:
                    if len(vals) != 2:
                        scene.pdt_error = PDT_ERR_BAD2VALS
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    vector_delta = disAng(vals, flip_a, plane, scene)
                    vNew = bm.select_history[-1].co + vector_delta
                    nVert = bm.verts.new(vNew)
                    for v in [v for v in bm.verts if v.select]:
                        v.select_set(False)
                    nVert.select_set(True)
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
                elif mode in ["p", "P"]:
                    if len(vals) != 1:
                        scene.pdt_error = PDT_ERR_BAD1VALS
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    vector_delta = getPercent(obj, flip_p, float(vals[0]), oper, scene)
                    vNew = vector_delta
                    nVert = bm.verts.new(vNew)
                    for v in [v for v in bm.verts if v.select]:
                        v.select_set(False)
                    nVert.select_set(True)
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
                else:
                    scene.pdt_error = f"'{mode}' {PDT_ERR_NON_VALID} '{oper}'"
                    bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    return
            else:
                scene.pdt_error = PDT_ERR_ADDVEDIT
                bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return

        elif oper in ["s", "S"]:
            # Split Edges
            if obj.mode == "EDIT":
                if mode in ["a", "A"]:
                    if len(vals) != 3:
                        scene.pdt_error = PDT_ERR_BAD3VALS
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
                    edges = [e for e in bm.edges if e.select]
                    if len(edges) != 1:
                        scene.pdt_error = f"{PDT_ERR_SEL_1_EDGE} {len(edges)})"
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    geom = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1)
                    new_verts = [v for v in geom["geom_split"] if isinstance(v, bmesh.types.BMVert)]
                    nVert = new_verts[0]
                    nVert.co = vector_delta - obj_loc
                    for v in [v for v in bm.verts if v.select]:
                        v.select_set(False)
                    nVert.select_set(True)
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
                elif mode in ["d", "D"]:
                    if len(vals) != 3:
                        scene.pdt_error = PDT_ERR_BAD3VALS
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
                    edges = [e for e in bm.edges if e.select]
                    faces = [f for f in bm.faces if f.select]
                    if len(faces) != 0:
                        scene.pdt_error = PDT_ERR_FACE_SEL
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    if len(edges) < 1:
                        scene.pdt_error = f"{PDT_ERR_SEL_1_EDGEM} {len(edges)})"
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    geom = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1)
                    new_verts = [v for v in geom["geom_split"] if isinstance(v, bmesh.types.BMVert)]
                    for v in [v for v in bm.verts if v.select]:
                        v.select_set(False)
                    for v in new_verts:
                        v.select_set(False)
                    bmesh.ops.translate(bm, verts=new_verts, vec=vector_delta)
                    for v in [v for v in bm.verts if v.select]:
                        v.select_set(False)
                    for v in new_verts:
                        v.select_set(False)
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
                elif mode in ["i", "I"]:
                    if len(vals) != 2:
                        scene.pdt_error = PDT_ERR_BAD2VALS
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    vector_delta = disAng(vals, flip_a, plane, scene)
                    edges = [e for e in bm.edges if e.select]
                    faces = [f for f in bm.faces if f.select]
                    if len(faces) != 0:
                        scene.pdt_error = PDT_ERR_FACE_SEL
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    if len(edges) < 1:
                        scene.pdt_error = f"{PDT_ERR_SEL_1_EDGEM} {len(edges)})"
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    geom = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1)
                    new_verts = [v for v in geom["geom_split"] if isinstance(v, bmesh.types.BMVert)]
                    bmesh.ops.translate(bm, verts=new_verts, vec=vector_delta)
                    for v in [v for v in bm.verts if v.select]:
                        v.select_set(False)
                    for v in new_verts:
                        v.select_set(False)
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
                elif mode in ["p", "P"]:
                    if len(vals) != 1:
                        scene.pdt_error = PDT_ERR_BAD1VALS
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    vector_delta = getPercent(obj, flip_p, float(vals[0]), oper, scene)
                    if vector_delta is None:
                        return
                    edges = [e for e in bm.edges if e.select]
                    faces = [f for f in bm.faces if f.select]
                    if len(faces) != 0:
                        scene.pdt_error = PDT_ERR_FACE_SEL
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    if len(edges) < 1:
                        scene.pdt_error = f"{PDT_ERR_SEL_1_EDGEM} {len(edges)})"
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    geom = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1)
                    new_verts = [v for v in geom["geom_split"] if isinstance(v, bmesh.types.BMVert)]
                    nVert = new_verts[0]
                    nVert.co = vector_delta
                    for v in [v for v in bm.verts if v.select]:
                        v.select_set(False)
                    nVert.select_set(True)
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
                else:
                    scene.pdt_error = f"'{mode}' {PDT_ERR_NON_VALID} '{oper}'"
                    bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    return
            else:
                scene.pdt_error = PDT_ERR_SPLITEDIT
                bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return

        elif oper in ["v", "V"]:
            # Extrude Vertices
            if obj.mode == "EDIT":
                if mode in ["a", "A"]:
                    if len(vals) != 3:
                        scene.pdt_error = PDT_ERR_BAD3VALS
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
                    vNew = vector_delta - obj_loc
                    nVert = bm.verts.new(vNew)
                    for v in [v for v in bm.verts if v.select]:
                        nEdge = bm.edges.new([v, nVert])
                        v.select_set(False)
                    nVert.select_set(True)
                    bmesh.ops.remove_doubles(
                        bm, verts=[v for v in bm.verts if v.select], dist=0.0001
                    )
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
                elif mode in ["d", "D"]:
                    if len(vals) != 3:
                        scene.pdt_error = PDT_ERR_BAD3VALS
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
                    verts = [v for v in bm.verts if v.select]
                    if len(verts) == 0:
                        scene.pdt_error = PDT_ERR_NO_SEL_GEOM
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    for v in verts:
                        nVert = bm.verts.new(v.co)
                        nVert.co = nVert.co + vector_delta
                        nEdge = bm.edges.new([v, nVert])
                        v.select_set(False)
                        nVert.select_set(True)
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
                elif mode in ["i", "I"]:
                    if len(vals) != 2:
                        scene.pdt_error = PDT_ERR_BAD2VALS
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    vector_delta = disAng(vals, flip_a, plane, scene)
                    verts = [v for v in bm.verts if v.select]
                    if len(verts) == 0:
                        scene.pdt_error = PDT_ERR_NO_SEL_GEOM
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    for v in verts:
                        nVert = bm.verts.new(v.co)
                        nVert.co = nVert.co + vector_delta
                        nEdge = bm.edges.new([v, nVert])
                        v.select_set(False)
                        nVert.select_set(True)
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
                elif mode in ["p", "P"]:
                    vector_delta = getPercent(obj, flip_p, float(vals[0]), oper, scene)
                    verts = [v for v in bm.verts if v.select]
                    if len(verts) == 0:
                        scene.pdt_error = PDT_ERR_NO_SEL_GEOM
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    nVert = bm.verts.new(vector_delta)
                    if ext_a:
                        for v in [v for v in bm.verts if v.select]:
                            nEdge = bm.edges.new([v, nVert])
                            v.select_set(False)
                    else:
                        nEdge = bm.edges.new([bm.select_history[-1], nVert])
                    nVert.select_set(True)
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
                else:
                    scene.pdt_error = f"'{mode}' {PDT_ERR_NON_VALID} '{oper}'"
                    bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    return
            else:
                scene.pdt_error = PDT_ERR_EXTEDIT
                bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return

        elif oper in ["e", "E"]:
            # Extrude Geometry
            if obj.mode == "EDIT":
                if mode in ["d", "D"]:
                    if len(vals) != 3:
                        scene.pdt_error = PDT_ERR_BAD3VALS
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
                    verts = [v for v in bm.verts if v.select]
                    if len(verts) == 0:
                        scene.pdt_error = PDT_ERR_NO_SEL_GEOM
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    ret = bmesh.ops.extrude_face_region(
                        bm,
                        geom=(
                            [f for f in bm.faces if f.select]
                            + [e for e in bm.edges if e.select]
                            + [v for v in bm.verts if v.select]
                        ),
                        use_select_history=True,
                    )
                    geom_extr = ret["geom"]
                    verts_extr = [v for v in geom_extr if isinstance(v, bmesh.types.BMVert)]
                    edges_extr = [e for e in geom_extr if isinstance(e, bmesh.types.BMEdge)]
                    faces_extr = [f for f in geom_extr if isinstance(f, bmesh.types.BMFace)]
                    del ret
                    bmesh.ops.translate(bm, verts=verts_extr, vec=vector_delta)
                    updateSel(bm, verts_extr, edges_extr, faces_extr)
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
                elif mode in ["i", "I"]:
                    if len(vals) != 2:
                        scene.pdt_error = PDT_ERR_BAD2VALS
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    vector_delta = disAng(vals, flip_a, plane, scene)
                    verts = [v for v in bm.verts if v.select]
                    if len(verts) == 0:
                        scene.pdt_error = PDT_ERR_NO_SEL_GEOM
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    ret = bmesh.ops.extrude_face_region(
                        bm,
                        geom=(
                            [f for f in bm.faces if f.select]
                            + [e for e in bm.edges if e.select]
                            + [v for v in bm.verts if v.select]
                        ),
                        use_select_history=True,
                    )
                    geom_extr = ret["geom"]
                    verts_extr = [v for v in geom_extr if isinstance(v, bmesh.types.BMVert)]
                    edges_extr = [e for e in geom_extr if isinstance(e, bmesh.types.BMEdge)]
                    faces_extr = [f for f in geom_extr if isinstance(f, bmesh.types.BMFace)]
                    del ret
                    bmesh.ops.translate(bm, verts=verts_extr, vec=vector_delta)
                    updateSel(bm, verts_extr, edges_extr, faces_extr)
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
                else:
                    scene.pdt_error = f"'{mode}' {PDT_ERR_NON_VALID} '{oper}'"
                    bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    return

        elif oper in ["d", "D"]:
            # Duplicate Geometry
            if obj.mode == "EDIT":
                if mode in ["d", "D"]:
                    if len(vals) != 3:
                        scene.pdt_error = PDT_ERR_BAD3VALS
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    vector_delta = Vector((float(vals[0]), float(vals[1]), float(vals[2])))
                    verts = [v for v in bm.verts if v.select]
                    if len(verts) == 0:
                        scene.pdt_error = PDT_ERR_NO_SEL_GEOM
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    ret = bmesh.ops.duplicate(
                        bm,
                        geom=(
                            [f for f in bm.faces if f.select]
                            + [e for e in bm.edges if e.select]
                            + [v for v in bm.verts if v.select]
                        ),
                        use_select_history=True,
                    )
                    geom_dupe = ret["geom"]
                    verts_dupe = [v for v in geom_dupe if isinstance(v, bmesh.types.BMVert)]
                    edges_dupe = [e for e in geom_dupe if isinstance(e, bmesh.types.BMEdge)]
                    faces_dupe = [f for f in geom_dupe if isinstance(f, bmesh.types.BMFace)]
                    del ret
                    bmesh.ops.translate(bm, verts=verts_dupe, vec=vector_delta)
                    updateSel(bm, verts_dupe, edges_dupe, faces_dupe)
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
                elif mode in ["i", "I"]:
                    if len(vals) != 2:
                        scene.pdt_error = PDT_ERR_BAD2VALS
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    vector_delta = disAng(vals, flip_a, plane, scene)
                    verts = [v for v in bm.verts if v.select]
                    if len(verts) == 0:
                        scene.pdt_error = PDT_ERR_NO_SEL_GEOM
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    ret = bmesh.ops.duplicate(
                        bm,
                        geom=(
                            [f for f in bm.faces if f.select]
                            + [e for e in bm.edges if e.select]
                            + [v for v in bm.verts if v.select]
                        ),
                        use_select_history=True,
                    )
                    geom_dupe = ret["geom"]
                    verts_dupe = [v for v in geom_dupe if isinstance(v, bmesh.types.BMVert)]
                    edges_dupe = [e for e in geom_dupe if isinstance(e, bmesh.types.BMEdge)]
                    faces_dupe = [f for f in geom_dupe if isinstance(f, bmesh.types.BMFace)]
                    del ret
                    bmesh.ops.translate(bm, verts=verts_dupe, vec=vector_delta)
                    updateSel(bm, verts_dupe, edges_dupe, faces_dupe)
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
                else:
                    scene.pdt_error = f"'{mode}' {PDT_ERR_NON_VALID} '{oper}'"
                    bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    return
            else:
                scene.pdt_error = PDT_ERR_DUPEDIT
                bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return

        elif oper in ["f", "F"]:
            # Fillet Geometry
            if obj.mode == "EDIT":
                if len(vals) != 3:
                    scene.pdt_error = PDT_ERR_BAD3VALS
                    bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                    return
                else:
                    if mode in ["v", "V"]:
                        vert_bool = True
                    else:
                        vert_bool = False
                    scene = context.scene
                    obj = context.view_layer.objects.active
                    if obj is None:
                        scene.pdt_error = PDT_ERR_NO_ACT_OBJ
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    bm = bmesh.from_edit_mesh(obj.data)
                    verts = [v for v in bm.verts if v.select]
                    if len(verts) == 0:
                        scene.pdt_error = PDT_ERR_SEL_1_VERT
                        bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                        return
                    else:
                        if int(vals[1]) < 1:
                            segs = 1
                        else:
                            segs = int(vals[1])
                        if float(vals[2]) in range(0,1):
                            prof = float(vals[2]),
                        else:
                            prof = 0.5
                        bpy.ops.mesh.bevel(
                            offset_type="OFFSET",
                            offset=float(vals[0]),
                            segments=segs,
                            profile=prof,
                            vertex_only=vert_bool,
                        )
                        return
            else:
                scene.pdt_error = PDT_ERR_FILEDIT
                bpy.context.window_manager.popup_menu(oops, title="Error", icon="ERROR")
                return
