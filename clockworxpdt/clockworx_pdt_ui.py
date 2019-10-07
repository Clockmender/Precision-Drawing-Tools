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
# Author: Alan Odom (Clockmender)
# ----------------------------------------------------------
#
import bpy
from bpy.types import Operator, Panel, PropertyGroup
from mathutils import Vector, Quaternion
from bpy.props import FloatProperty
import bmesh
import numpy as np
from math import sin, cos, tan, acos, pi, sqrt

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
)


# FIXME
# Since many of the error messages appear to be duplicates, maybe we should
# add them as string constants such ERR_MSG_FACE_SELECTED = "(...)" ?
#
# For instance:
#
# ERR_MSG_FACE_SELECTED = "I'm afraid I can't do that, Dave: You have a have a Face selected; this would have ruined the Topology"
# (this is a reference to HAL 9000 from Stanley Kubrick's '2001: A Space Odyssey')
#
# To be included in v1.1.5 after more research.


class PDT_OT_PlacementAbs(Operator):
    """Use Absolute, or Global Placement"""

    bl_idname = "pdt.absolute"
    bl_label = "Absolute Mode"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Manipulates Geometry, or Objects by Absolute (World) Coordinates.

        - Reads pdt_operate from Operation Mode Selector as 'data'
        - Reads pdt_delta_x, pdt_delta_y & pdt_delta_z scene variables to:
        -- set position of CUrsor      (CU)
        -- set postion of Pivot Point  (PP)
        -- MoVe geometry/objects       (MV)
        -- Extrude Vertices            (EV)
        -- Split Edges                 (SE)
        -- add a New Vertex            (NV)

        Invalid Options result in self.report Error.

        Local vector variable 'vector_delta' is used to reposition features.
        """

        scene = context.scene
        data = scene.pdt_operate
        x_loc = scene.pdt_delta_x
        y_loc = scene.pdt_delta_y
        z_loc = scene.pdt_delta_z

        vector_delta = Vector((x_loc, y_loc, z_loc))
        if data not in ["CU", "PP", "NV"]:
            obj = context.view_layer.objects.active
            if obj == None:
                self.report({"ERROR"}, "Select at least 1 Object")  # FIXME
                return {"FINISHED"}
            obj_loc = obj.matrix_world.decompose()[0]
            if obj.mode == "EDIT":
                bm = bmesh.from_edit_mesh(obj.data)
            verts = [v for v in bm.verts if v.select]
            if len(verts) == 0:
                self.report({"ERROR"}, "Nothing Selected!")  # FIXME
                return {"FINISHED"}
        if data == "CU":
            scene.cursor.location = vector_delta
            scene.cursor.rotation_euler = (0, 0, 0)
        elif data == "PP":
            scene.pdt_pivotloc = vector_delta
        elif data == "MV":
            if obj.mode == "EDIT":
                for v in verts:
                    v.co = vector_delta - obj_loc
                bm.select_history.clear()
                bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts if v.select], dist=0.0001)
                bmesh.update_edit_mesh(obj.data)
            elif obj.mode == "OBJECT":
                for ob in context.view_layer.objects.selected:
                    ob.location = vector_delta
        elif data == "SE" and obj.mode == "EDIT":
            edges = [e for e in bm.edges if e.select]
            if len(edges) != 1:
                self.report({"ERROR"}, "Select Only One Edge")  # FIXME
                return {"FINISHED"}
            geom = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1)
            new_verts = [v for v in geom["geom_split"] if isinstance(v, bmesh.types.BMVert)]
            nVert = new_verts[0]
            nVert.co = vector_delta - obj_loc
            for v in [v for v in bm.verts if v.select]:
                v.select_set(False)
            nVert.select_set(True)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        elif data == "NV" and obj.mode == "EDIT":
            vNew = vector_delta - obj_loc
            nVert = bm.verts.new(vNew)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        elif data == "EV" and obj.mode == "EDIT":
            vNew = vector_delta - obj_loc
            nVert = bm.verts.new(vNew)
            for v in [v for v in bm.verts if v.select]:
                nEdge = bm.edges.new([v, nVert])
                v.select_set(False)
            nVert.select_set(True)
            bm.select_history.clear()
            bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts if v.select], dist=0.0001)
            bmesh.update_edit_mesh(obj.data)
        else:
            self.report({"ERROR"}, data + " is Not a Valid Absolute Option!")  # FIXME
        return {"FINISHED"}


class PDT_OT_PlacementDelta(Operator):
    """Use Delta, or Incremental Placement"""

    bl_idname = "pdt.delta"
    bl_label = "Delta Mode"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Manipulates Geometry, or Objects by Delta Offset (Increment).

        - Reads pdt_operate from Operation Mode Selector as 'data'
        - Reads pdt_select, pdt_plane, pdt_delta_x, pdt_delta_y & pdt_delta_z scene variables to:
        -- set position of CUrsor       (CU)
        -- set position of Pivot Point  (PP)
        -- MoVe geometry/objects        (MV)
        -- Extrude Vertices             (EV)
        -- Split Edges                  (SE)
        -- add a New Vertex             (NV)
        -- Duplicate Geometry           (DG)
        -- Extrude Geometry             (EG)

        Invalid Options result in self.report Error.

        Local vector variable 'vector_delta' used to reposition features.
        """

        scene = context.scene
        x_loc = scene.pdt_delta_x
        y_loc = scene.pdt_delta_y
        z_loc = scene.pdt_delta_z
        mode_s = scene.pdt_select
        data = scene.pdt_operate

        if scene.pdt_plane == "LO":
            vector_delta = viewCoords(x_loc, y_loc, z_loc)
        else:
            vector_delta = Vector((x_loc, y_loc, z_loc))
        if mode_s == "REL" and data == "CU":
            scene.cursor.location = scene.cursor.location + vector_delta
        elif mode_s == "REL" and data == "PP":
            scene.pdt_pivotloc = scene.pdt_pivotloc + vector_delta
        else:
            obj = context.view_layer.objects.active
            if obj == None:
                self.report({"ERROR"}, "Select at least 1 Object")  # FIXME
                return {"FINISHED"}
            obj_loc = obj.matrix_world.decompose()[0]
            if obj.mode == "EDIT":
                bm = bmesh.from_edit_mesh(obj.data)
                if data not in ["MV", "SE", "EV", "DG", "EG"]:
                    if len(bm.select_history) >= 1:
                        actV = checkSelection(1, bm, obj)
                        if actV == None:
                            self.report({"ERROR"}, "Work in Vertex Mode")  # FIXME
                            return {"FINISHED"}
                    else:
                        self.report({"ERROR"}, "Select at least 1 Vertex Individually")  # FIXME
                        return {"FINISHED"}
            if data not in ["CU", "PP", "NV"]:
                verts = [v for v in bm.verts if v.select]
                if len(verts) == 0:
                    self.report({"ERROR"}, "Nothing Selected!")
                    return {"FINISHED"}
            if data == "CU":
                if obj.mode == "EDIT":
                    scene.cursor.location = obj_loc + actV + vector_delta
                elif obj.mode == "OBJECT":
                    scene.cursor.location = obj_loc + vector_delta
            elif data == "PP":
                if obj.mode == "EDIT":
                    scene.pdt_pivotloc = obj_loc + actV + vector_delta
                elif obj.mode == "OBJECT":
                    scene.pdt_pivotloc = obj_loc + vector_delta
            elif data == "MV":
                if obj.mode == "EDIT":
                    bmesh.ops.translate(bm, verts=verts, vec=vector_delta)
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
                elif obj.mode == "OBJECT":
                    for ob in context.view_layer.objects.selected:
                        ob.location = obj_loc + vector_delta
            elif data == "SE" and obj.mode == "EDIT":
                edges = [e for e in bm.edges if e.select]
                faces = [f for f in bm.faces if f.select]
                if len(faces) != 0:
                    self.report(
                        {"ERROR"}, "You have a Face Selected, this would have ruined the Topology"
                    )  # FIXME
                    return {"FINISHED"}
                if len(edges) < 1:
                    self.report({"ERROR"}, "Select at least 1 Edge")
                    return {"FINISHED"}
                geom = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1)
                new_verts = [v for v in geom["geom_split"] if isinstance(v, bmesh.types.BMVert)]
                bmesh.ops.translate(bm, verts=new_verts, vec=vector_delta)
                for v in [v for v in bm.verts if v.select]:
                    v.select_set(False)
                for v in new_verts:
                    v.select_set(False)
                bmesh.update_edit_mesh(obj.data)
                bm.select_history.clear()
            elif data == "NV" and obj.mode == "EDIT":
                vNew = actV + vector_delta
                nVert = bm.verts.new(vNew)
                bmesh.update_edit_mesh(obj.data)
                bm.select_history.clear()
            elif data == "EV" and obj.mode == "EDIT":
                for v in [v for v in bm.verts if v.select]:
                    nVert = bm.verts.new(v.co)
                    nVert.co = nVert.co + vector_delta
                    nEdge = bm.edges.new([v, nVert])
                    v.select_set(False)
                    nVert.select_set(True)
                bmesh.update_edit_mesh(obj.data)
                bm.select_history.clear()
            elif data == "DG" and obj.mode == "EDIT":
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
            elif data == "EG" and obj.mode == "EDIT":
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
                self.report({"ERROR"}, data + " is Not a Valid Delta Option!")  # FIXME
        return {"FINISHED"}


class PDT_OT_PlacementDis(Operator):
    """Use Directional, or Distance @ Angle Placement"""

    bl_idname = "pdt.distance"
    bl_label = "Distance@Angle Mode"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Manipulates Geometry, or Objects by Distance at Angle (Direction).

        - Reads pdt_operate from Operation Mode Selector as 'data'
        - Reads pdt_select, pdt_distance, pdt_angle, pdt_plane & pdt_flipangle scene variables to:
        -- set position of CUrsor       (CU)
        -- set position of Pivot Point  (PP)
        -- MoVe geometry/objects        (MV)
        -- Extrude Vertices             (EV)
        -- Split Edges                  (SE)
        -- add a New Vertex             (NV)
        -- Duplicate Geometry           (DG)
        -- Extrude Geometry             (EG)

        Invalid Options result in self.report Error.

        Local vector variable 'vector_delta' used to reposition features.
        """

        scene = context.scene
        dis_v = scene.pdt_distance
        ang_v = scene.pdt_angle
        plane = scene.pdt_plane
        mode_s = scene.pdt_select
        data = scene.pdt_operate
        flip_a = scene.pdt_flipangle
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
            vector_delta[a1] = vector_delta[a1] + (dis_v * cos(ang_v * pi / 180))
            vector_delta[a2] = vector_delta[a2] + (dis_v * sin(ang_v * pi / 180))
        if mode_s == "REL" and data == "CU":
            scene.cursor.location = scene.cursor.location + vector_delta
        elif mode_s == "REL" and data == "PP":
            scene.pdt_pivotloc = scene.pdt_pivotloc + vector_delta
        else:
            obj = context.view_layer.objects.active
            if obj == None:
                self.report({"ERROR"}, "Select at least 1 Object")  # FIXME
                return {"FINISHED"}
            obj_loc = obj.matrix_world.decompose()[0]
            if obj.mode == "EDIT":
                bm = bmesh.from_edit_mesh(obj.data)
                if data not in ["MV", "SE", "EV", "DG", "EG"]:
                    if len(bm.select_history) >= 1:
                        actV = checkSelection(1, bm, obj)
                        if actV == None:
                            self.report({"ERROR"}, "Work in Vertex Mode")
                            return {"FINISHED"}
                    else:
                        self.report({"ERROR"}, "Select at least 1 Vertex Individually")  # FIXME
                        return {"FINISHED"}
            if data not in ["CU", "PP", "NV"]:
                verts = [v for v in bm.verts if v.select]
                if len(verts) == 0:
                    self.report({"ERROR"}, "Nothing Selected?")
                    return {"FINISHED"}
            if data == "CU":
                if obj.mode == "EDIT":
                    scene.cursor.location = obj_loc + actV + vector_delta
                elif obj.mode == "OBJECT":
                    scene.cursor.location = obj_loc + vector_delta
            elif data == "PP":
                if obj.mode == "EDIT":
                    scene.pdt_pivotloc = obj_loc + actV + vector_delta
                elif obj.mode == "OBJECT":
                    scene.pdt_pivotloc = obj_loc + vector_delta
            elif data == "MV":
                if obj.mode == "EDIT":
                    bmesh.ops.translate(bm, verts=verts, vec=vector_delta)
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
                elif obj.mode == "OBJECT":
                    for ob in context.view_layer.objects.selected:
                        ob.location = ob.location + vector_delta
            elif data == "SE" and obj.mode == "EDIT":
                edges = [e for e in bm.edges if e.select]
                faces = [f for f in bm.faces if f.select]
                if len(faces) != 0:
                    self.report(
                        {"ERROR"}, "You have a Face Selected, this would have ruined the Topology"
                    )  # FIXME
                    return {"FINISHED"}
                if len(edges) < 1:
                    self.report({"ERROR"}, "Select at least 1 Edge")  # FIXME
                    return {"FINISHED"}
                geom = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1)
                new_verts = [v for v in geom["geom_split"] if isinstance(v, bmesh.types.BMVert)]
                bmesh.ops.translate(bm, verts=new_verts, vec=vector_delta)
                for v in [v for v in bm.verts if v.select]:
                    v.select_set(False)
                for v in new_verts:
                    v.select_set(False)
                bmesh.update_edit_mesh(obj.data)
                bm.select_history.clear()
            elif data == "NV" and obj.mode == "EDIT":
                vNew = actV + vector_delta
                nVert = bm.verts.new(vNew)
                bmesh.update_edit_mesh(obj.data)
                bm.select_history.clear()
            elif data == "EV" and obj.mode == "EDIT":
                for v in [v for v in bm.verts if v.select]:
                    nVert = bm.verts.new(v.co)
                    nVert.co = nVert.co + vector_delta
                    nEdge = bm.edges.new([v, nVert])
                    v.select_set(False)
                    nVert.select_set(True)
                bmesh.update_edit_mesh(obj.data)
                bm.select_history.clear()
            elif data == "DG" and obj.mode == "EDIT":
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
            elif data == "EG" and obj.mode == "EDIT":
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
                self.report(
                    {"ERROR"}, data + " is Not a Valid Direction Option!"
                )  # FIXME "%s is not a (...)
        return {"FINISHED"}


class PDT_OT_PlacementPer(Operator):
    """Use Percentage Placement"""

    bl_idname = "pdt.percent"
    bl_label = "Percentage Mode"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Manipulates Geometry, or Objects by Percentage between 2 points.

        - Reads pdt_operate from Operation Mode Selector as 'data'
        - Reads pdt_percent, pdt_extend & pdt_flippercent scene variables to:
        -- set position of CUrsor       (CU)
        -- set position of Pivot Point  (PP)
        -- MoVe geometry/objects        (MV)
        -- Extrude Vertices             (EV)
        -- Split edges                  (SE)
        -- add a New vertex             (NV)

        Invalid Options result in self.report Error.

        Local vector variable 'vector_delta' used to reposition features.
        """

        scene = context.scene
        per_v = scene.pdt_percent
        data = scene.pdt_operate
        ext_a = scene.pdt_extend
        flip_p = scene.pdt_flippercent
        obj = context.view_layer.objects.active
        if obj == None:
            self.report({"ERROR"}, "Select at least 1 Object, You didn't select anything")  # FIXME
            return {"FINISHED"}
        if obj.mode == "EDIT":
            bm = bmesh.from_edit_mesh(obj.data)
        obj_loc = obj.matrix_world.decompose()[0]
        vector_delta = getPercent(obj, flip_p, per_v, data, scene)
        if vector_delta == None:
            return {"FINISHED"}

        if data == "CU":
            if obj.mode == "EDIT":
                scene.cursor.location = obj_loc + vector_delta
            elif obj.mode == "OBJECT":
                scene.cursor.location = vector_delta
        elif data == "PP":
            if obj.mode == "EDIT":
                scene.pdt_pivotloc = obj_loc + vector_delta
            elif obj.mode == "OBJECT":
                scene.pdt_pivotloc = vector_delta
        elif data == "MV":
            if obj.mode == "EDIT":
                bm.select_history[-1].co = vector_delta
                bmesh.update_edit_mesh(obj.data)
                bm.select_history.clear()
            elif obj.mode == "OBJECT":
                obj.location = vector_delta
        elif data == "SE" and obj.mode == "EDIT":
            edges = [e for e in bm.edges if e.select]
            if len(edges) != 1:
                self.report(
                    {"ERROR"}, "Select Only One Edge, you selected " + str(len(edges)) + " Edges"
                )  # FIXME
                return {"FINISHED"}
            geom = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1)
            new_verts = [v for v in geom["geom_split"] if isinstance(v, bmesh.types.BMVert)]
            nVert = new_verts[0]
            nVert.co = vector_delta
            for v in [v for v in bm.verts if v.select]:
                v.select_set(False)
            nVert.select_set(True)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        elif data == "NV" and obj.mode == "EDIT":
            nVert = bm.verts.new(vector_delta)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        elif data == "EV" and obj.mode == "EDIT":
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
            self.report({"ERROR"}, data + " is Not a Valid Percent Option!")  # FIXME
        return {"FINISHED"}


class PDT_OT_PlacementNormal(Operator):
    """Use Normal, or Perpendicular Placement"""

    bl_idname = "pdt.normal"
    bl_label = "Normal Mode"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Manipulates Geometry, or Objects by Normal Intersection between 3 points.

        - Reads pdt_operate from Operation Mode Selector as 'data'
        - Reads pdt_extend scene variable to:
        -- set position of CUrsor       (CU)
        -- set position of Pivot Point  (PP)
        -- MoVe geometry/objects        (MV)
        -- Extrude Vertices             (EV)
        -- Split Edges                  (SE)
        -- add a New Vertex             (NV)

        Invalid Options result in self.report Error.

        Local vector variable 'vector_delta' used to reposition features.
        """

        scene = context.scene
        data = scene.pdt_operate
        ext_a = scene.pdt_extend
        obj = context.view_layer.objects.active
        if obj == None:
            self.report({"ERROR"}, "Select at least 1 Object")  # FIXME
            return {"FINISHED"}
        obj_loc = obj.matrix_world.decompose()[0]
        if obj.mode == "EDIT":
            bm = bmesh.from_edit_mesh(obj.data)
            if len(bm.select_history) == 3:
                actV, othV, lstV = checkSelection(3, bm, obj)
                if actV == None:
                    self.report({"ERROR"}, "Work in Vertex Mode")  # FIXME
                    return {"FINISHED"}
            else:
                self.report({"ERROR"}, "Select 3 Vertices Individually")
                return {"FINISHED"}
        elif obj.mode == "OBJECT":
            objs = context.view_layer.objects.selected
            if len(objs) != 3:
                self.report(
                    {"ERROR"},
                    "Select Exactly 3 Objects, you selected " + str(len(objs)) + " Objects",
                )  # FIXME
                return {"FINISHED"}
            else:
                objs_s = [ob for ob in objs if ob.name != obj.name]
                actV = obj.matrix_world.decompose()[0]
                othV = objs_s[-1].matrix_world.decompose()[0]
                lstV = objs_s[-2].matrix_world.decompose()[0]
        vector_delta = intersect_point_line(actV, othV, lstV)[0]
        if data == "CU":
            if obj.mode == "EDIT":
                scene.cursor.location = obj_loc + vector_delta
            elif obj.mode == "OBJECT":
                scene.cursor.location = vector_delta
        elif data == "PP":
            if obj.mode == "EDIT":
                scene.pdt_pivotloc = obj_loc + vector_delta
            elif obj.mode == "OBJECT":
                scene.pdt_pivotloc = vector_delta
        elif data == "MV":
            if obj.mode == "EDIT":
                if ext_a:
                    for v in [v for v in bm.verts if v.select]:
                        v.co = vector_delta
                    bm.select_history.clear()
                    bmesh.ops.remove_doubles(
                        bm, verts=[v for v in bm.verts if v.select], dist=0.0001
                    )
                else:
                    bm.select_history[-1].co = vector_delta
                    bm.select_history.clear()
                bmesh.update_edit_mesh(obj.data)
            elif obj.mode == "OBJECT":
                context.view_layer.objects.active.location = vector_delta
        elif data == "NV" and obj.mode == "EDIT":
            nVert = bm.verts.new(vector_delta)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        elif data == "EV" and obj.mode == "EDIT":
            vNew = vector_delta
            nVert = bm.verts.new(vNew)
            if ext_a:
                for v in [v for v in bm.verts if v.select]:
                    nEdge = bm.edges.new([v, nVert])
            else:
                nEdge = bm.edges.new([bm.select_history[-1], nVert])
            for v in [v for v in bm.verts if v.select]:
                v.select_set(False)
            nVert.select_set(True)
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        else:
            self.report({"ERROR"}, data + " is Not a Valid Normal Option!")  # FIXME
        return {"FINISHED"}


class PDT_OT_PlacementInt(Operator):
    """Use Intersection, or Convergence Placement"""

    bl_idname = "pdt.intersect"
    bl_label = "Intersect Mode"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Manipulates Geometry, or Objects by Convergance Intersection between 4 points, or 2 Edges.

        - Reads pdt_operate from Operation Mode Selector as 'data'
        - Reads pdt_plane scene variable and operates in Working Plane to:
        -- set position of CUrsor       (CU)
        -- set position of Pivot Point  (PP)
        -- MoVe geometry/objects        (MV)
        -- Extrude Vertices             (EV)
        -- add a New vertex             (NV)

        Invalid Options result in self.report Error.

        Local vector variable 'vector_delta' used to reposition features.
        """

        scene = context.scene
        data = scene.pdt_operate
        plane = scene.pdt_plane
        obj = context.view_layer.objects.active
        if obj == None:
            self.report({"ERROR"}, "Select an Object")  # FIXME
            return {"FINISHED"}
        if obj.mode == "EDIT":
            obj_loc = obj.matrix_world.decompose()[0]
            bm = bmesh.from_edit_mesh(obj.data)
            edges = [e for e in bm.edges if e.select]
            if len(edges) == 2:
                ext_a = True
                va = edges[0].verts[0]
                actV = va.co
                vo = edges[0].verts[1]
                othV = vo.co
                vl = edges[1].verts[0]
                lstV = vl.co
                vf = edges[1].verts[1]
                fstV = vf.co
            elif len(bm.select_history) == 4:
                ext_a = scene.pdt_extend
                va = bm.select_history[-1]
                vo = bm.select_history[-2]
                vl = bm.select_history[-3]
                vf = bm.select_history[-4]
                actV, othV, lstV, fstV = checkSelection(4, bm, obj)
                if actV == None:
                    self.report({"ERROR"}, "Work in Vertex Mode to Select Vertices")  # FIXME
                    return {"FINISHED"}
            else:
                self.report({"ERROR"}, "Select 4 Vertices Individually, or 2 Edges")  # FIXME
                return {"FINISHED"}
            vector_delta, done = intersection(actV, othV, lstV, fstV, plane)
            if not done:
                self.report({"ERROR"}, "Lines Do Not Intersect in " + plane + " Plane")  # FIXME
                return {"FINISHED"}

            if data == "CU":
                scene.cursor.location = obj_loc + vector_delta
            elif data == "PP":
                scene.pdt_pivotloc = obj_loc + vector_delta
            elif data == "NV":
                vNew = vector_delta
                nVert = bm.verts.new(vNew)
                for v in [v for v in bm.verts if v.select]:
                    v.select_set(False)
                for f in bm.faces:
                    f.select_set(False)
                for e in bm.edges:
                    e.select_set(False)
                nVert.select_set(True)
                bmesh.update_edit_mesh(obj.data)
                bm.select_history.clear()
            elif data in ["MV", "EV"]:
                nVert = None
                proc = False

                if (actV - vector_delta).length < (othV - vector_delta).length:
                    if data == "MV":
                        va.co = vector_delta
                        proc = True
                    elif data == "EV":
                        nVert = bm.verts.new(vector_delta)
                        nEdge = bm.edges.new([va, nVert])
                        proc = True
                else:
                    if data == "MV" and ext_a:
                        vo.co = vector_delta
                    elif data == "EV" and ext_a:
                        nVert = bm.verts.new(vector_delta)
                        nEdge = bm.edges.new([vo, nVert])

                if (lstV - vector_delta).length < (fstV - vector_delta).length:
                    if data == "MV" and ext_a:
                        vl.co = vector_delta
                    elif data == "EV" and ext_a:
                        nEdge = bm.edges.new([vl, nVert])
                else:
                    if data == "MV" and ext_a:
                        vf.co = vector_delta
                    elif data == "EV" and ext_a:
                        nEdge = bm.edges.new([vf, nVert])
                bm.select_history.clear()
                bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)

                if not proc and not ext_a:
                    self.report(
                        {"ERROR"},
                        "Active Vertex was not Closest to Intersection and All/Act was not Selected",
                    )  # FIXME
                    bmesh.update_edit_mesh(obj.data)
                    return {"FINISHED"}
                else:
                    for v in bm.verts:
                        v.select_set(False)
                    for f in bm.faces:
                        f.select_set(False)
                    for e in bm.edges:
                        e.select_set(False)

                    if nVert is not None:
                        nVert.select_set(True)
                    for v in bm.select_history:
                        if v is not None:
                            v.select_set(True)
                    bmesh.update_edit_mesh(obj.data)
            else:
                self.report({"ERROR"}, "Not a Valid, or Sensible, Option!")  # FIXME
            return {"FINISHED"}
        elif obj.mode == "OBJECT":
            if len(context.view_layer.objects.selected) != 4:
                self.report({"ERROR"}, "Select Only 4 Objects")  # FIXME
                return {"FINISHED"}
            else:
                order = scene.pdt_oborder.split(",")
                objs = sorted(
                    [ob for ob in context.view_layer.objects.selected], key=lambda x: x.name
                )
                message = (
                    "Original Object Order was: "
                    + objs[0].name
                    + ", "
                    + objs[1].name
                    + ", "
                    + objs[2].name
                    + ", "
                    + objs[3].name
                )
                self.report({"INFO"}, message)

                actV = objs[int(order[0]) - 1].matrix_world.decompose()[0]
                othV = objs[int(order[1]) - 1].matrix_world.decompose()[0]
                lstV = objs[int(order[2]) - 1].matrix_world.decompose()[0]
                fstV = objs[int(order[3]) - 1].matrix_world.decompose()[0]
            vector_delta, done = intersection(actV, othV, lstV, fstV, plane)
            if not done:
                self.report(
                    {"ERROR"}, "Lines Between Objects Do Not Intersect in " + plane + " Plane"
                )  # FIXME
                return {"FINISHED"}
            if data == "CU":
                scene.cursor.location = vector_delta
            elif data == "PP":
                scene.pdt_pivotloc = vector_delta
            elif data == "MV":
                context.view_layer.objects.active.location = vector_delta
                self.report({"INFO"}, "Active Object Moved to Intersection, " + message)
            else:
                self.report({"ERROR"}, data + " is Not a Valid Intersection Option!")  # FIXME
            return {"FINISHED"}


class PDT_OT_PlacementCen(Operator):
    """Use Placement at Arc Centre"""

    bl_idname = "pdt.centre"
    bl_label = "Centre Mode"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Manipulates Geometry, or Objects to an Arc Centre defined by 3 points on an Imaginary Arc.

        Valid Options for pdt_operate; CU PP MV NV EV
        - Reads pdt_operate from Operation Mode Selector as 'data'
        - Reads pdt_extend scene variable to:
        -- set position of CUrsor       (CU)
        -- set position of Pivot Point  (PP)
        -- MoVe geometry/objects        (MV)
        -- Extrude Vertices             (EV)
        -- add a New vertex             (NV)

        Invalid Options result in self.report Error.

        Local vector variable 'vector_delta' used to reposition features.
        """

        scene = context.scene
        data = scene.pdt_operate
        ext_a = scene.pdt_extend
        obj = context.view_layer.objects.active

        if obj == None:
            self.report(
                {"ERROR"}, "Select 1 Object to work in Edit Mode, or 3 to work in Object Mode"
            )  # FIXME
            return {"FINISHED"}
        if obj.mode == "EDIT":
            obj = context.view_layer.objects.active
            obj_loc = obj.matrix_world.decompose()[0]
            bm = bmesh.from_edit_mesh(obj.data)
            verts = [v for v in bm.verts if v.select]
            if len(verts) == 3:
                actV = verts[0].co
                othV = verts[1].co
                lstV = verts[2].co
            else:
                self.report({"ERROR"}, "Select Exactly 3 Vertices")  # FIXME
                return {"FINISHED"}
            vector_delta, radius = arcCentre(actV, othV, lstV)
            if str(radius) == "inf":
                self.report({"ERROR"}, "Points all lie in a Straight Line")  # FIXME
                return {"FINISHED"}
            scene.pdt_distance = radius
            if data == "CU":
                scene.cursor.location = obj_loc + vector_delta
            elif data == "PP":
                scene.pdt_pivotloc = obj_loc + vector_delta
            elif data == "NV":
                vNew = vector_delta
                nVert = bm.verts.new(vNew)
                for v in [v for v in bm.verts if v.select]:
                    v.select_set(False)
                nVert.select_set(True)
                bmesh.update_edit_mesh(obj.data)
                bm.select_history.clear()
            elif data == "MV":
                if obj.mode == "EDIT":
                    if ext_a:
                        for v in [v for v in bm.verts if v.select]:
                            v.co = vector_delta
                        bm.select_history.clear()
                        bmesh.ops.remove_doubles(
                            bm, verts=[v for v in bm.verts if v.select], dist=0.0001
                        )
                    else:
                        bm.select_history[-1].co = vector_delta
                        bm.select_history.clear()
                    bmesh.update_edit_mesh(obj.data)
                elif obj.mode == "OBJECT":
                    context.view_layer.objects.active.location = vector_delta
            elif data == "EV":
                nVert = bm.verts.new(vector_delta)
                if ext_a:
                    for v in [v for v in bm.verts if v.select]:
                        nEdge = bm.edges.new([v, nVert])
                        v.select_set(False)
                    nVert.select_set(True)
                    bm.select_history.clear()
                    bmesh.ops.remove_doubles(
                        bm, verts=[v for v in bm.verts if v.select], dist=0.0001
                    )
                    bmesh.update_edit_mesh(obj.data)
                else:
                    nEdge = bm.edges.new([bm.select_history[-1], nVert])
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
            else:
                self.report({"ERROR"}, "Not a Valid, or Sensible, Option!")  # FIXME
            return {"FINISHED"}
        elif obj.mode == "OBJECT":
            if len(context.view_layer.objects.selected) != 3:
                self.report({"ERROR"}, "Select Only 3 Objects")
                return {"FINISHED"}
            else:
                actV = context.view_layer.objects.selected[0].matrix_world.decompose()[0]
                othV = context.view_layer.objects.selected[1].matrix_world.decompose()[0]
                lstV = context.view_layer.objects.selected[2].matrix_world.decompose()[0]
                vector_delta, radius = arcCentre(actV, othV, lstV)
                scene.pdt_distance = radius
                if data == "CU":
                    scene.cursor.location = vector_delta
                elif data == "PP":
                    scene.pdt_pivotloc = vector_delta
                elif data == "MV":
                    context.view_layer.objects.active.location = vector_delta
                else:
                    self.report({"ERROR"}, "Not a Valid, or Sensible, Option!")  # FIXME
                return {"FINISHED"}


class PDT_OT_JoinVerts(Operator):
    """Join 2 Free Vertices into an Edge"""

    bl_idname = "pdt.join"
    bl_label = "Join 2 Vertices"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Joins 2 Free Vertices that do not form part of a Face.

        Joins two vertices that do not form part of a single face
        It is designed to close open Edge Loops, where a face is not required
        or to join two disconnected Edges.

        Args:
            context: Current Blender bpy.context

        Returns:
            Status Set.
        """

        scene = context.scene
        obj = context.view_layer.objects.active
        if obj == None:
            self.report({"ERROR"}, "Select an Object")  # FIXME
            return {"FINISHED"}
        if obj.mode == "EDIT":
            bm = bmesh.from_edit_mesh(obj.data)
            verts = [v for v in bm.verts if v.select]
            if len(verts) == 2:
                try:
                    nEdge = bm.edges.new([verts[-1], verts[-2]])
                    bmesh.update_edit_mesh(obj.data)
                    bm.select_history.clear()
                    return {"FINISHED"}
                except ValueError:
                    self.report({"ERROR"}, "Vertices are already connected")  # FIXME
                    return {"FINISHED"}
            else:
                self.report({"ERROR"}, "Select exactly 2 Vertices")  # FIXME
                return {"FINISHED"}
        else:
            self.report({"ERROR"}, "Only works in Edit Mode")
            return {"FINISHED"}


class PDT_OT_Fillet(Operator):
    """Fillet Edges by Vertex, Set Use Verts to False for Extruded Structure"""

    bl_idname = "pdt.fillet"
    bl_label = "Fillet"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        # FIXME docstring

        scene = context.scene
        obj = context.view_layer.objects.active
        if obj == None:
            self.report({"ERROR"}, "Select an Object")  # FIXME
            return {"FINISHED"}
        if obj.mode == "EDIT":
            bm = bmesh.from_edit_mesh(obj.data)
            verts = [v for v in bm.verts if v.select]
            if len(verts) == 0:
                self.report({"ERROR"}, "Select at least 1 vertex")  # FIXME
                return {"FINISHED"}
            else:
                bpy.ops.mesh.bevel(
                    offset_type="OFFSET",
                    offset=scene.pdt_filletrad,
                    segments=scene.pdt_filletnum,
                    profile=scene.pdt_filletpro,
                    vertex_only=scene.pdt_filletbool,
                )
                return {"FINISHED"}


class PDT_OT_Angle2(Operator):
    """Measure Distance and Angle in Working Plane, Also sets Deltas"""

    bl_idname = "pdt.angle2"
    bl_label = "Measure 2D"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Measures Angle and Offsets between 2 Points in View Plane.

        Uses 2 Selected Vertices to set pdt_angle and pdt_distance scene variables
        also sets delta offset from these 2 points using standard Numpy Routines
        Works in Edit and Oject Modes.
        """

        scene = context.scene
        plane = scene.pdt_plane
        flip_a = scene.pdt_flipangle
        obj = context.view_layer.objects.active
        if obj == None:
            self.report({"ERROR"}, "Select an Object")  # FIXME
            return {"FINISHED"}
        if obj.mode == "EDIT":
            bm = bmesh.from_edit_mesh(obj.data)
            verts = [v for v in bm.verts if v.select]
            if len(verts) == 2:
                if len(bm.select_history) == 2:
                    actV, othV = checkSelection(2, bm, obj)
                    if actV == None:
                        self.report({"ERROR"}, "Work in Vertex Mode")  # FIXME
                        return {"FINISHED"}
                else:
                    self.report({"ERROR"}, "Select 2 Vertices Individually")  # FIXME
                    return {"FINISHED"}
            else:
                self.report({"ERROR"}, "Select 2 Vertices Individually")  # FIXME
                return {"FINISHED"}
        elif obj.mode == "OBJECT":
            objs = context.view_layer.objects.selected
            if len(objs) < 2:
                self.report({"ERROR"}, "Select 2 Objects")  # FIXME
                return {"FINISHED"}
            objs_s = [ob for ob in objs if ob.name != obj.name]
            actV = obj.matrix_world.decompose()[0]
            othV = objs_s[-1].matrix_world.decompose()[0]
        if plane == "LO":
            disV = othV - actV
            othV = viewCoordsI(disV.x, disV.y, disV.z)
            actV = Vector((0, 0, 0))
            v0 = np.array([actV.x + 1, actV.y]) - np.array([actV.x, actV.y])
            v1 = np.array([othV.x, othV.y]) - np.array([actV.x, actV.y])
        else:
            a1, a2, a3 = setMode(plane)
            v0 = np.array([actV[a1] + 1, actV[a2]]) - np.array([actV[a1], actV[a2]])
            v1 = np.array([othV[a1], othV[a2]]) - np.array([actV[a1], actV[a2]])
        ang = np.rad2deg(np.arctan2(np.linalg.det([v0, v1]), np.dot(v0, v1)))
        if flip_a:
            if ang > 0:
                scene.pdt_angle = ang - 180
            else:
                scene.pdt_angle = ang + 180
        else:
            scene.pdt_angle = ang
        if plane == "LO":
            scene.pdt_distance = sqrt((actV.x - othV.x) ** 2 + (actV.y - othV.y) ** 2)
        else:
            scene.pdt_distance = sqrt((actV[a1] - othV[a1]) ** 2 + (actV[a2] - othV[a2]) ** 2)
        scene.pdt_delta_x = othV.x - actV.x
        scene.pdt_delta_y = othV.y - actV.y
        scene.pdt_delta_z = othV.z - actV.z
        return {"FINISHED"}


class PDT_OT_Angle3(Operator):
    """Measure Distance and Angle in 3D Space"""

    bl_idname = "pdt.angle3"
    bl_label = "Measure 3D"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Measures Angle and Offsets between 3 Points in World Space, Also sets Deltas.

        Uses 3 Selected Vertices to set pdt_angle and pdt_distance scene variables
        also sets delta offset from these 3 points using standard Numpy Routines
        Works in Edit and Oject Modes.
        """

        scene = context.scene
        plane = scene.pdt_plane
        flip_a = scene.pdt_flipangle
        obj = context.view_layer.objects.active
        if obj == None:
            self.report({"ERROR"}, "Select an Object")
            return {"FINISHED"}
        if obj.mode == "EDIT":
            bm = bmesh.from_edit_mesh(obj.data)
            verts = [v for v in bm.verts if v.select]
            if len(verts) == 3:
                if len(bm.select_history) == 3:
                    actV, othV, lstV = checkSelection(3, bm, obj)
                    if actV == None:
                        self.report({"ERROR"}, "Work in Vertex Mode")
                        return {"FINISHED"}
                else:
                    self.report({"ERROR"}, "Select 3 Vertices Individually")
                    return {"FINISHED"}
            else:
                self.report({"ERROR"}, "Select 3 Vertices Individually")
                return {"FINISHED"}
        elif obj.mode == "OBJECT":
            objs = context.view_layer.objects.selected
            if len(objs) < 2:
                self.report({"ERROR"}, "Select 3 Objects")
                return {"FINISHED"}
            objs_s = [ob for ob in objs if ob.name != obj.name]
            actV = obj.matrix_world.decompose()[0]
            othV = objs_s[-1].matrix_world.decompose()[0]
            lstV = objs_s[-2].matrix_world.decompose()[0]
        ba = np.array([othV.x, othV.y, othV.z]) - np.array([actV.x, actV.y, actV.z])
        bc = np.array([lstV.x, lstV.y, lstV.z]) - np.array([actV.x, actV.y, actV.z])
        cosA = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        ang = np.degrees(np.arccos(cosA))
        if flip_a:
            if ang > 0:
                scene.pdt_angle = ang - 180
            else:
                scene.pdt_angle = ang + 180
        else:
            scene.pdt_angle = ang
        scene.pdt_distance = sqrt(
            (actV.x - othV.x) ** 2 + (actV.y - othV.y) ** 2 + (actV.z - othV.z) ** 2
        )
        scene.pdt_delta_x = othV.x - actV.x
        scene.pdt_delta_y = othV.y - actV.y
        scene.pdt_delta_z = othV.z - actV.z
        return {"FINISHED"}


class PDT_OT_Origin(Operator):
    """Move Object Origin to Cursor Location"""

    bl_idname = "pdt.origin"
    bl_label = "Move Origin"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Sets Object Origin in Edit Mode to Cursor Location.

        Keeps geometry static in World Space whilst moving Object Origin
        Requires cursor location
        Works in Edit and Object Modes.
        """

        scene = context.scene
        obj = context.view_layer.objects.active
        if obj == None:
            self.report({"ERROR"}, "Select an Object")  # FIXME
            return {"FINISHED"}
        obj_loc = obj.matrix_world.decompose()[0]
        cur_loc = scene.cursor.location
        diff_v = obj_loc - cur_loc
        if obj.mode == "EDIT":
            bm = bmesh.from_edit_mesh(obj.data)
            for v in bm.verts:
                v.co = v.co + diff_v
            obj.location = cur_loc
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
        elif obj.mode == "OBJECT":
            for v in obj.data.vertices:
                v.co = v.co + diff_v
            obj.location = cur_loc
        else:
            self.report({"ERROR"}, "Not a Valid, or Sensible, Option!")  # FIXME
        return {"FINISHED"}


class PDT_OT_Taper(Operator):
    """Taper Vertices at Angle in Chosen Axis Mode"""

    bl_idname = "pdt.taper"
    bl_label = "Taper"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Taper Geometry along World Axes.

        Similar to Shear command except that it shears by angle rather than displacement.
        Rotates about World Axes and displaces along World Axes, angle must not exceed +-80 degrees.
        Rotation axis is centred on Active Vertex.
        Works only in Edit mode.

        Args:
            context: Current Blender bpy.context

        Note:
            Uses pdt_taper & pdt_angle scene variables
        """

        scene = context.scene
        tap_ax = scene.pdt_taper
        ang_v = scene.pdt_angle
        obj = context.view_layer.objects.active
        if ang_v > 80 or ang_v < -80:
            self.report({"ERROR"}, "Angle must be in Range -80 to +80")  # FIXME
            return {"FINISHED"}
        if obj == None:
            self.report({"ERROR"}, "Select an Object")  # FIXME
            return {"FINISHED"}
        a1, a2, a3 = setAxis(tap_ax)
        if obj.mode == "EDIT":
            bm = bmesh.from_edit_mesh(obj.data)
            if len(bm.select_history) >= 1:
                rotV = bm.select_history[-1]
                viewV = viewCoords(rotV.co.x, rotV.co.y, rotV.co.z)
            else:
                self.report(
                    {"ERROR"}, "Select at Least 2 Vertices Individually - Active is Rotation Point"
                )  # FIXME
                return {"FINISHED"}
            for v in [v for v in bm.verts if v.select]:
                if scene.pdt_plane == "LO":
                    v_loc = viewCoords(v.co.x, v.co.y, v.co.z)
                    dis_v = sqrt((viewV.x - v_loc.x) ** 2 + (viewV.y - v_loc.y) ** 2)
                    x_loc = dis_v * tan(ang_v * pi / 180)
                    vm = viewDir(x_loc, 0)
                    v.co = v.co - vm
                else:
                    dis_v = sqrt((rotV.co[a3] - v.co[a3]) ** 2 + (rotV.co[a2] - v.co[a2]) ** 2)
                    v.co[a2] = v.co[a2] - (dis_v * tan(ang_v * pi / 180))
            bmesh.update_edit_mesh(obj.data)
            bm.select_history.clear()
            return {"FINISHED"}
        else:
            self.report({"ERROR"}, "Not a Valid, or Sensible, Option!")  # FIXME
            return {"FINISHED"}


class PDT_OT_Append(Operator):
    """Append from Library at cursor Location"""

    bl_idname = "pdt.append"
    bl_label = "Append"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Appends Objects from PDT Library file.

        Appended Objects are placed at Cursor Location.

        Args:
            context: Current Blender bpy.context

        Note:
            Uses pdt_lib_objects, pdt_lib_collections & pdt_lib_materials

        Returns: Status Set.
        """

        scene = context.scene
        obj_names = [o.name for o in context.view_layer.objects]
        path = (
            str(bpy.utils.user_resource("SCRIPTS", "addons")) + "/clockworxpdt/parts_library.blend"
        )
        if scene.pdt_lib_mode == "OBJECTS":
            bpy.ops.wm.append(
                filepath=path, directory=path + "/Object", filename=scene.pdt_lib_objects
            )
            for obj in context.view_layer.objects:
                if obj.name not in obj_names:
                    obj.select_set(False)
                    obj.location = Vector(
                        (scene.cursor.location.x, scene.cursor.location.y, scene.cursor.location.z)
                    )
            return {"FINISHED"}
        elif scene.pdt_lib_mode == "COLLECTIONS":
            bpy.ops.wm.append(
                filepath=path, directory=path + "/Collection", filename=scene.pdt_lib_collections
            )
            for obj in context.view_layer.objects:
                if obj.name not in obj_names:
                    obj.select_set(False)
                    obj.location = Vector(
                        (scene.cursor.location.x, scene.cursor.location.y, scene.cursor.location.z)
                    )
            return {"FINISHED"}
        elif scene.pdt_lib_mode == "MATERIALS":
            bpy.ops.wm.append(
                filepath=path, directory=path + "/Material", filename=scene.pdt_lib_materials
            )
            return {"FINISHED"}


class PDT_OT_Link(Operator):
    """Link from Library at Object's Origin"""

    bl_idname = "pdt.link"
    bl_label = "Link"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Links Objects from PDT Library file.

        Linked Objects are placed at Cursor Location

        Args:
            context

        Note:
            Uses pdt_lib_objects, pdt_lib_collections & pdt_lib_materials

        Returns:
            Status Set.
        """

        scene = context.scene
        path = (
            str(bpy.utils.user_resource("SCRIPTS", "addons")) + "/clockworxpdt/parts_library.blend"
        )
        if scene.pdt_lib_mode == "OBJECTS":
            bpy.ops.wm.link(
                filepath=path, directory=path + "/Object", filename=scene.pdt_lib_objects
            )
            obj_names = [o.name for o in context.view_layer.objects]
            for obj in context.view_layer.objects:
                obj.select_set(False)
            return {"FINISHED"}
        elif scene.pdt_lib_mode == "COLLECTIONS":
            bpy.ops.wm.link(
                filepath=path, directory=path + "/Collection", filename=scene.pdt_lib_collections
            )
            obj_names = [o.name for o in context.view_layer.objects]
            for obj in context.view_layer.objects:
                obj.select_set(False)
            return {"FINISHED"}
        elif scene.pdt_lib_mode == "MATERIALS":
            bpy.ops.wm.link(
                filepath=path, directory=path + "/Material", filename=scene.pdt_lib_materials
            )
            return {"FINISHED"}


class PDT_OT_ViewRot(Operator):
    """Rotate View using X Y Z Absolute Rotations"""

    bl_idname = "pdt.viewrot"
    bl_label = "Rotate View"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """View Rotation by Absolute Values.

        Rotations are converted to 3x3 Quaternion Rotation Matrix.
        This is an Absolute Rotation, not an Incremental Orbit.

        Args:
            context: Current Blender bpy.context

        Note:
            Uses pdt_xrot, pdt_yrot, pdt_zrot scene variables

        Returns:
            Status Set.
        """

        scene = context.scene
        areas = [a for a in context.screen.areas if a.type == "VIEW_3D"]
        if len(areas) > 0:
            roll_value = euler_to_quaternion(
                scene.pdt_xrot * pi / 180, scene.pdt_yrot * pi / 180, scene.pdt_zrot * pi / 180
            )
            areas[0].spaces.active.region_3d.view_rotation = roll_value
        return {"FINISHED"}


class PDT_OT_vRotL(Operator):
    """Orbit View to Left by Angle"""

    bl_idname = "pdt.viewleft"
    bl_label = "Rotate Left"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """View Orbit Left by Delta Value.

        Orbits view to the left about its vertical axis

        Args:
            context: Current Blender bpy.context

        Note:
            Uses pdt_vrotangle scene variable

        Returns: Status Set.
        """

        scene = context.scene
        areas = [a for a in context.screen.areas if a.type == "VIEW_3D"]
        if len(areas) > 0:
            bpy.ops.view3d.view_orbit(angle=(scene.pdt_vrotangle * pi / 180), type="ORBITLEFT")
        return {"FINISHED"}


class PDT_OT_vRotR(Operator):
    """Orbit View to Right by Angle"""

    bl_idname = "pdt.viewright"
    bl_label = "Rotate Right"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """View Orbit Right by Delta Value.

        Orbits view to the right about its vertical axis

        Args:
            context: Current Blender bpy.context

        Note:
            Uses pdt_vrotangle scene variable

        Returns:
            Status Set.
        """

        scene = context.scene
        areas = [a for a in context.screen.areas if a.type == "VIEW_3D"]
        if len(areas) > 0:
            bpy.ops.view3d.view_orbit(angle=(scene.pdt_vrotangle * pi / 180), type="ORBITRIGHT")
        return {"FINISHED"}


class PDT_OT_vRotU(Operator):
    """Orbit View to Up by Angle"""

    bl_idname = "pdt.viewup"
    bl_label = "Rotate Up"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """View Orbit Up by Delta Value.

        Orbits view up about its horizontal axis

        Args:
            context: Current Blender bpy.context

        Note:
            Uses pdt_vrotangle scene variable

	Returns:
    	    Status Set.
    	"""

        scene = context.scene
        areas = [a for a in context.screen.areas if a.type == "VIEW_3D"]
        if len(areas) > 0:
            bpy.ops.view3d.view_orbit(angle=(scene.pdt_vrotangle * pi / 180), type="ORBITUP")
        return {"FINISHED"}


class PDT_OT_vRotD(Operator):
    """Orbit View to Down by Angle"""

    bl_idname = "pdt.viewdown"
    bl_label = "Rotate Down"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """View Orbit Down by Delta Value.

        Orbits view down about its horizontal axis

        Args:
            context: Current Blender bpy.context

        Note:
            Uses pdt_vrotangle scene variable

        Returns:
            Status Set.
        """

        scene = context.scene
        areas = [a for a in context.screen.areas if a.type == "VIEW_3D"]
        if len(areas) > 0:
            bpy.ops.view3d.view_orbit(angle=(scene.pdt_vrotangle * pi / 180), type="ORBITDOWN")
        return {"FINISHED"}


class PDT_OT_vRoll(Operator):
    """Roll View by Angle"""

    bl_idname = "pdt.viewroll"
    bl_label = "Roll View"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """View Roll by Delta Value.

        Rolls view about its normal axis

        Args:
            context: Current Blender bpy.context

        Note:
            Uses pdt_vrotangle scene variable

        Returns:
            Status Set.
        """

        scene = context.scene
        areas = [a for a in context.screen.areas if a.type == "VIEW_3D"]
        if len(areas) > 0:
            bpy.ops.view3d.view_roll(angle=(scene.pdt_vrotangle * pi / 180), type="ANGLE")
        return {"FINISHED"}


class PDT_OT_viso(Operator):
    """Isometric View"""

    bl_idname = "pdt.viewiso"
    bl_label = "Isometric View"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        """Set Isometric View.

        Set view orientation to Isometric

        Args:
            context: Current Blender bpy.context

        Returns:
            Status Set.
        """

        scene = context.scene
        areas = [a for a in context.screen.areas if a.type == "VIEW_3D"]
        if len(areas) > 0:
            # Try working this out in your head!
            areas[0].spaces.active.region_3d.view_rotation = Quaternion(
                (0.8205, 0.4247, -0.1759, -0.3399)
            )
        return {"FINISHED"}


# PDT Panel menus
#
class PDT_PT_Panel1(Panel):
    bl_idname = "PDT_PT_panel1"
    bl_label = "PDT Drawing Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PDT"

    def draw(self, context):
        layout = self.layout
        cursor = context.scene.cursor
        scene = context.scene
        box = layout.box()
        row = box.row()
        col = row.column()
        col.prop(scene, "pdt_plane", text="Plane")
        col = row.column()
        col.prop(scene, "pdt_select", text="Mode")
        row = box.row()
        row.prop(scene, "pdt_operate", text="Operation")
        row = box.row()
        col = row.column()
        col.operator("pdt.absolute", icon="EMPTY_AXIS", text="Absolute")
        col = row.column()
        col.operator("pdt.delta", icon="EMPTY_AXIS", text="Delta")
        col = row.column()
        col.operator("pdt.distance", icon="EMPTY_AXIS", text="Direction")
        row = box.row()
        col = row.column()
        col.operator("pdt.percent", text="Percent")
        col = row.column()
        col.operator("pdt.normal", text="Normal")
        col = row.column()
        col.operator("pdt.centre", text="Arc Centre")
        row = box.row()
        col = row.column()
        col.operator("pdt.intersect", text="Intersect")
        col = row.column()
        col.prop(scene, "pdt_oborder", text="Order")
        row = box.row()
        col = row.column()
        col.prop(scene, "pdt_flipangle", text="Flip Angle")
        col = row.column()
        col.prop(scene, "pdt_flippercent", text="Flip %")
        col = row.column()
        col.prop(scene, "pdt_extend", text="All/Active")
        box = layout.box()
        row = box.row()
        row.label(text="Coordinates/Delta Offsets & Other Variables")
        row = box.row()
        col = row.column()
        col.prop(scene, "pdt_delta_x", text="X")
        col = row.column()
        col.prop(scene, "pdt_distance", text="Dis")
        row = box.row()
        col = row.column()
        col.prop(scene, "pdt_delta_y", text="Y")
        col = row.column()
        col.prop(scene, "pdt_angle", text="Ang")
        row = box.row()
        col = row.column()
        col.prop(scene, "pdt_delta_z", text="Z")
        col = row.column()
        col.prop(scene, "pdt_percent", text="%")
        box = layout.box()
        row = box.row()
        row.label(text="Tools")
        row = box.row()
        col = row.column()
        col.operator("pdt.join", text="Join 2 Verts")
        col = row.column()
        col.operator("pdt.origin", text="Origin To Cursor")
        row = box.row()
        col = row.column()
        col.operator("pdt.angle2", text="Set A/D 2D")
        col = row.column()
        col.operator("pdt.angle3", text="Set A/D 3D")
        row = box.row()
        col = row.column()
        col.prop(scene, "pdt_taper", text="")
        col = row.column()
        col.operator("pdt.taper", text="Taper")
        # New for 1.1.5
        row = box.row()
        col = row.column()
        col.operator("pdt.intersectall", text="Intersect All")
        col = row.column()
        col.operator("pdt.linetobisect", text="Bisect")
        col = row.column()
        col.operator("pdt.edge_to_face", text="Edge-Face")
        #
        # Add Fillet Tool
        row = box.row()
        col = row.column()
        col.operator("pdt.fillet", text="Fillet")
        col = row.column()
        col.prop(scene, "pdt_filletnum", text="Segments")
        col = row.column()
        col.prop(scene, "pdt_filletbool", text="Use Verts")
        row = box.row()
        col = row.column()
        col.prop(scene, "pdt_filletrad", text="Radius")
        col = row.column()
        col.prop(scene, "pdt_filletpro", text="Profile")
        #
        box = layout.box()
        row = box.row()
        col = row.column()
        col.label(text="View Rotation")
        col = row.column()
        col.operator("pdt.viewrot", text="Rotate Abs")
        row = box.row()
        col = row.column()
        col.prop(scene, "pdt_xrot")
        col = row.column()
        col.prop(scene, "pdt_yrot")
        col = row.column()
        col.prop(scene, "pdt_zrot")
        row = box.row()
        col = row.column()
        col.prop(scene, "pdt_vrotangle", text="Angle")
        col = row.column()
        col.operator("pdt.viewleft", text="", icon="TRIA_LEFT")
        col = row.column()
        col.operator("pdt.viewright", text="", icon="TRIA_RIGHT")
        col = row.column()
        col.operator("pdt.viewup", text="", icon="TRIA_UP")
        col = row.column()
        col.operator("pdt.viewdown", text="", icon="TRIA_DOWN")
        col = row.column()
        col.operator("pdt.viewroll", text="", icon="RECOVER_LAST")
        row = box.row()
        row.operator("pdt.viewiso", text="Isometric View")
        box = layout.box()
        row = box.row()
        row.label(text="Comand Line, uses Plane & Mode Options")
        row = box.row()
        row.prop(scene, "pdt_command", text="")


class PDT_PT_Panel3(Panel):
    bl_idname = "PDT_PT_panel3"
    bl_label = "PDT Parts Library"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PDT"

    def draw(self, context):
        layout = self.layout
        cursor = context.scene.cursor
        scene = context.scene
        row = layout.row()
        col = row.column()
        col.operator("pdt.append", text="Append")
        col = row.column()
        col.operator("pdt.link", text="Link")
        col = row.column()
        col.prop(scene, "pdt_lib_mode", text="")
        box = layout.box()
        row = box.row()
        col = row.column()
        col.label(text="Objects")
        col = row.column()
        col.prop(scene, "pdt_obsearch")
        row = box.row()
        row.prop(scene, "pdt_lib_objects", text="")
        box = layout.box()
        row = box.row()
        col = row.column()
        col.label(text="Collections")
        col = row.column()
        col.prop(scene, "pdt_cosearch")
        row = box.row()
        row.prop(scene, "pdt_lib_collections", text="")
        box = layout.box()
        row = box.row()
        col = row.column()
        col.label(text="Materials")
        col = row.column()
        col.prop(scene, "pdt_masearch")
        row = box.row()
        row.prop(scene, "pdt_lib_materials", text="")
