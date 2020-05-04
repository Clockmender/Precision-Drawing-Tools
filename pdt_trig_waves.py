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
# -----------------------------------------------------------------------
# Author: Alan Odom (Clockmender), Rune Morling (ermo) Copyright (c) 2019
# -----------------------------------------------------------------------
#
import bpy
import bmesh
from math import sin, cos, tan, pi
from mathutils import Vector
from .pdt_functions import (
    oops,
    set_mode,
    view_coords,
)

class PDT_OT_WaveGenerator(bpy.types.Operator):
    """Generate Trig Waves in Active Object"""
    bl_idname = "pdt.wave_generator"
    bl_label = "Generate Waves"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        pg = context.scene.pdt_pg
        return pg.trig_obj is not None

    def execute(self, context):
        """Generate Trig Waves in Active Object.

        Args:
            context: Blender bpy.context instance.

        Note:
            Uses all the PDT trig_* variables.

        Returns:
            Nothing.
        """

        pg = context.scene.pdt_pg
        plane = pg.plane
        # H, V, D
        a1, a2, a3 = set_mode(plane)
        for obj in bpy.data.objects:
            obj.select_set(state=False)
        context.view_layer.objects.active = pg.trig_obj
        x_inc = pg.trig_len / pg.trig_res

        if pg.trig_del:
            bpy.ops.object.mode_set(mode='EDIT')
            for v in pg.trig_obj.data.vertices:
                v.select = True
            bpy.ops.mesh.delete(type='VERT')
            bpy.ops.object.mode_set(mode='OBJECT')

        if pg.trig_obj.mode != "EDIT":
            bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(pg.trig_obj.data)

        for i in range((pg.trig_res * pg.trig_cycles) + 1):
            if pg.trig_type == "sin":
                if pg.trig_abs:
                    z_val = abs(sin((i / pg.trig_res) * pi) * pg.trig_amp)
                else:
                    z_val = sin((i / pg.trig_res) * pi) * pg.trig_amp
            elif pg.trig_type == "cos":
                if pg.trig_abs:
                    z_val = abs(cos((i / pg.trig_res) * pi) * pg.trig_amp)
                else:
                    z_val = cos((i / pg.trig_res) * pi) * pg.trig_amp
            else:
                if pg.trig_abs:
                    z_val = abs(tan((i / pg.trig_res) * pi) * pg.trig_amp)
                else:
                    z_val = tan((i / pg.trig_res) * pi) * pg.trig_amp

                if abs(z_val) > pg.trig_tanmax:
                    if z_val >= 0:
                        z_val = pg.trig_tanmax
                    else:
                        if pg.trig_abs:
                            z_val = pg.trig_tanmax
                        else:
                            z_val = -pg.trig_tanmax

            vert_loc = Vector(pg.trig_off)
            vert_loc[a1] = vert_loc[a1] + (i * x_inc)
            vert_loc[a2] = vert_loc[a2] + z_val
            if plane == "LO":
                vert_loc = view_coords(vert_loc[a1], vert_loc[a2], vert_loc[a3])
            vertex_new = bm.verts.new(vert_loc)
            bm.verts.ensure_lookup_table()
            if i > 0:
                bm.edges.new([bm.verts[-2], vertex_new])

        bmesh.update_edit_mesh(pg.trig_obj.data)
        bpy.ops.object.mode_set(mode='OBJECT')

        return {"FINISHED"}
