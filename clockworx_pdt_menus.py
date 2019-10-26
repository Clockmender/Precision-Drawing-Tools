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
from bpy.types import Panel
from .pdt_msg_strings import *
import os
from pathlib import Path

# PDT Panel menus
#
class PDT_PT_Panel1(Panel):
    bl_idname = "PDT_PT_panel1"
    bl_label = "PDT Design"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PDT"

    def draw(self, context):
        layout = self.layout
        cursor = context.scene.cursor
        scene = context.scene
        row = layout.row()
        col = row.column()
        col.prop(scene, "pdt_plane", text=PDT_LAB_PLANE)
        col = row.column()
        col.prop(scene, "pdt_select", text=PDT_LAB_MODE)
        box = layout.box()
        row = box.row()
        row.prop(scene, "pdt_operate", text=PDT_LAB_OPERATION)
        row = box.row()
        col = row.column()
        col.operator("pdt.absolute", icon="EMPTY_AXIS", text=PDT_LAB_ABS)
        col = row.column()
        col.operator("pdt.delta", icon="EMPTY_AXIS", text=PDT_LAB_DEL)
        col = row.column()
        col.operator("pdt.distance", icon="EMPTY_AXIS", text=PDT_LAB_DIR)
        row = box.row()
        col = row.column()
        col.operator("pdt.percent", text=PDT_LAB_PERCENT)
        col = row.column()
        col.operator("pdt.normal", text=PDT_LAB_NOR)
        col = row.column()
        col.operator("pdt.centre", text=PDT_LAB_ARCCENTRE)
        row = box.row()
        col = row.column()
        col.operator("pdt.intersect", text=PDT_LAB_INTERSECT)
        col = row.column()
        col.prop(scene, "pdt_oborder", text=PDT_LAB_ORDER)
        row = box.row()
        col = row.column()
        col.prop(scene, "pdt_flipangle", text=PDT_LAB_FLIPANGLE)
        col = row.column()
        col.prop(scene, "pdt_flippercent", text=PDT_LAB_FLIPPERCENT)
        col = row.column()
        col.prop(scene, "pdt_extend", text=PDT_LAB_ALLACTIVE)
        box = layout.box()
        row = box.row()
        row.label(text=PDT_LAB_VARIABLES)
        row = box.row()
        col = row.column()
        col.prop(scene, "pdt_delta_x", text=PDT_LAB_XVALUE)
        col = row.column()
        col.prop(scene, "pdt_distance", text=PDT_LAB_DISVALUE)
        row = box.row()
        col = row.column()
        col.prop(scene, "pdt_delta_y", text=PDT_LAB_YVALUE)
        col = row.column()
        col.prop(scene, "pdt_angle", text=PDT_LAB_ANGLEVALUE)
        row = box.row()
        col = row.column()
        col.prop(scene, "pdt_delta_z", text=PDT_LAB_ZVALUE)
        col = row.column()
        col.prop(scene, "pdt_percent", text=PDT_LAB_PERCENTS)
        box = layout.box()
        row = box.row()
        row.label(text=PDT_LAB_TOOLS)
        row = box.row()
        col = row.column()
        col.operator("pdt.angle2", text=PDT_LAB_AD2D)
        col = row.column()
        col.operator("pdt.angle3", text=PDT_LAB_AD3D)
        row = box.row()
        col = row.column()
        col.operator("pdt.join", text=PDT_LAB_JOIN2VERTS)
        col = row.column()
        col.operator("pdt.origin", text=PDT_LAB_ORIGINCURSOR)
        row = box.row()
        col = row.column()
        col.prop(scene, "pdt_taper", text=PDT_LAB_TAPERAXES)
        col = row.column()
        col.operator("pdt.taper", text=PDT_LAB_TAPER)
        # New for 1.1.5
        row = box.row()
        col = row.column()
        col.operator("pdt.intersectall", text=PDT_LAB_INTERSETALL)
        col = row.column()
        col.operator("pdt.linetobisect", text=PDT_LAB_BISECT)
        col = row.column()
        col.operator("pdt.edge_to_face", text=PDT_LAB_EDGETOEFACE)
        #
        # Add Fillet Tool
        row = box.row()
        col = row.column()
        col.operator("pdt.fillet", text=PDT_LAB_FILLET)
        col = row.column()
        col.prop(scene, "pdt_filletnum", text=PDT_LAB_SEGMENTS)
        col = row.column()
        col.prop(scene, "pdt_filletbool", text=PDT_LAB_USEVERTS)
        row = box.row()
        col = row.column()
        col.prop(scene, "pdt_filletrad", text=PDT_LAB_RADIUS)
        col = row.column()
        col.prop(scene, "pdt_filletpro", text=PDT_LAB_PROFILE)


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
        split.prop(scene, "pdt_pivotsize", text=PDT_LAB_PIVOTSIZE)
        split.prop(scene, "pdt_pivotwidth", text=PDT_LAB_PIVOTWIDTH)
        split.prop(scene, "pdt_pivotalpha", text=PDT_LAB_PIVOTALPHA)
        row = layout.row()
        row.label(text=PDT_LAB_PIVOTLOCH)
        row = layout.row()
        row.prop(scene, "pdt_pivotloc", text=PDT_LAB_PIVOTLOC)
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
        row = box.row()
        row.operator("pdt.lib_show", text="Show Library File",icon='INFO')


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
