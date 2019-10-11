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
from bpy.types import Panel

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
        row = layout.row()
        col = row.column()
        col.prop(scene, "pdt_plane", text="Plane")
        col = row.column()
        col.prop(scene, "pdt_select", text="Mode")
        box = layout.box()
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


class PDT_PT_Panel2(Panel):
    bl_idname = "PDT_PT_panel2"
    bl_label = "PDT Pivot Point"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PDT"

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        row = layout.row()
        split = row.split(factor=0.4, align=True)
        if context.window_manager.pdt_run_opengl is False:
            icon = "PLAY"
            txt = "Show"
        else:
            icon = "PAUSE"
            txt = "Hide"
        split.operator("pdt.modaldraw", icon=icon, text=txt)
        split.prop(scene, "pdt_pivotsize", text="")
        split.prop(scene, "pdt_pivotwidth", text="")
        split.prop(scene, "pdt_pivotalpha", text="")
        row = layout.row()
        row.label(text="Pivot Point Location")
        row = layout.row()
        row.prop(scene, "pdt_pivotloc", text="")
        row = layout.row()
        col = row.column()
        col.operator("pdt.pivotselected", icon="EMPTY_AXIS", text="Selection")
        col = row.column()
        col.operator("pdt.pivotcursor", icon="EMPTY_AXIS", text="Cursor")
        col = row.column()
        col.operator("pdt.pivotorigin", icon="EMPTY_AXIS", text="Origin")
        row = layout.row()
        col = row.column()
        col.operator("pdt.viewplanerot", icon="EMPTY_AXIS", text="Rotate")
        col = row.column()
        col.prop(scene, "pdt_pivotang", text="Angle")
        row = layout.row()
        col = row.column()
        col.operator("pdt.viewscale", icon="EMPTY_AXIS", text="Scale")
        col = row.column()
        col.operator("pdt.cursorpivot", icon="EMPTY_AXIS", text="Cursor To Pivot")
        row = layout.row()
        col = row.column()
        col.prop(scene, "pdt_pivotdis", text="Scale Distance")
        col = row.column()
        col.prop(scene, "pdt_distance", text="System Distance")
        row = layout.row()
        row.label(text="Pivot Point Scale Factors")
        row = layout.row()
        row.prop(scene, "pdt_pivotscale", text="")
        row = layout.row()
        col = row.column()
        col.operator("pdt.pivotwrite", icon="FILE_TICK", text="PP Write")
        col = row.column()
        col.operator("pdt.pivotread", icon="FILE", text="PP Read")


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


class PDT_PT_Panel4(Panel):
    bl_idname = "PDT_PT_panel4"
    bl_label = "PDT View Control"
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


class PDT_PT_Panel5(Panel):
    bl_idname = "PDT_PT_panel5"
    bl_label = "PDT Command Line"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PDT"

    def draw(self, context):
        layout = self.layout
        cursor = context.scene.cursor
        scene = context.scene
        row = layout.row()
        col = row.column()
        col.prop(scene, "pdt_plane", text="Plane")
        col = row.column()
        col.prop(scene, "pdt_select", text="Mode")
        row = layout.row()
        row.label(text="Comand Line, uses Plane & Mode Options")
        row = layout.row()
        row.prop(scene, "pdt_command", text="")
