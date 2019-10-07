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
import bpy
from bpy.types import Operator, Panel, PropertyGroup, SpaceView3D
from mathutils import Vector, Matrix
from math import pi
from .pdt_functions import viewCoords, draw3D, drawCallback3D


class PDT_OT_ModalDrawOperator(bpy.types.Operator):
    """Show/Hide Pivot Point"""

    bl_idname = "pdt.modaldraw"
    bl_label = "PDT Modal Draw"

    _handle = None  # keep function handler

    @staticmethod
    def handle_add(self, context):
        """Draw Pivot Point Graphic if not displayed.

        Draws 7 element Pivot Point Graphic

        Args:
            context: Current Blender bpy.context

        Returns:
            Nothing.
        """

        if PDT_OT_ModalDrawOperator._handle is None:
            PDT_OT_ModalDrawOperator._handle = SpaceView3D.draw_handler_add(drawCallback3D, (self, context),
                                                                        'WINDOW',
                                                                        'POST_VIEW')
            context.window_manager.pdt_run_opengl = True

    @staticmethod
    def handle_remove(self, context):
        """Remove Pivot Point Graphic if displayed.

        Removes 7 element Pivot Point Graphic

        Args:
            context: Current Blender bpy.context

        Returns:
            Nothing.
        """

        if PDT_OT_ModalDrawOperator._handle is not None:
            SpaceView3D.draw_handler_remove(PDT_OT_ModalDrawOperator._handle, 'WINDOW')
        PDT_OT_ModalDrawOperator._handle = None
        context.window_manager.pdt_run_opengl = False

    def execute(self, context):
        """Pivot Point Show/Hide Button Function.

        Operational execute function for Show/Hide Pivot Point function

        Args:
            context: Current Blender bpy.context

        Returns:
            Status Set.
        """

        if context.area.type == 'VIEW_3D':
            if context.window_manager.pdt_run_opengl is False:
                self.handle_add(self, context)
                context.area.tag_redraw()
            else:
                self.handle_remove(self, context)
                context.area.tag_redraw()

            return {'FINISHED'}
        else:
            self.report({'ERROR'},
                        "View3D not found, cannot run operator")

        return {'CANCELLED'}


class PDT_OT_ViewPlaneRotate(Operator):
    """Rotate Selected Vertices about Pivot Point in View Plane"""

    bl_idname = "pdt.viewplanerot"
    bl_label = "PDT View Rotate"

    def execute(self,context):
        """Rotate Selected Vertices about Pivot Point.

        Rotates any selected vertices about the Pivot Point
        in View Oriented coordinates, works in any view orientation.

        Args:
            context: Current Blender bpy.context

        Notes:
            Uses pdt_pivotloc, pdt_pivotang scene variables

        Returns:
            Status Set.
        """

        scene = context.scene
        obj = bpy.context.view_layer.objects.active
        if obj == None:
            self.report({'ERROR'},
                    "Select 1 Object")
            return {"FINISHED"}
        if obj.mode != 'EDIT':
            self.report({'ERROR'},
                    "Only in Works on Vertices in Edit Mode")
            return {"FINISHED"}
        bm = bmesh.from_edit_mesh(obj.data)
        v1 = Vector((0,0,0))
        v2 = viewCoords(0,0,1)
        axis = (v2 - v1).normalized()
        rot = Matrix.Rotation((scene.pdt_pivotang*pi/180), 4, axis)
        verts = verts=[v for v in bm.verts if v.select]
        bmesh.ops.rotate(bm, cent=scene.pdt_pivotloc-obj.matrix_world.decompose()[0], matrix=rot, verts=verts)
        bmesh.update_edit_mesh(obj.data)
        return {"FINISHED"}


class PDT_OT_ViewPlaneScale(Operator):
    """Scale Selected Vertices about Pivot Point"""

    bl_idname = "pdt.viewscale"
    bl_label = "PDT View Scale"

    def execute(self,context):
        """Scales Selected Vertices about Pivot Point.

        Scales any selected vertices about the Pivot Point
        in View Oriented coordinates, works in any view orientation

        Args:
            context: Current Blender bpy.context

        Note:
            Uses pdt_pivotloc, pdt_pivotscale scene variables

        Returns:
            Status Set.
        """

        scene = context.scene
        obj = bpy.context.view_layer.objects.active
        if obj == None:
            self.report({'ERROR'},
                    "Select 1 Object")
            return {"FINISHED"}
        if obj.mode != 'EDIT':
            self.report({'ERROR'},
                    "Only in Works on Vertices in Edit Mode")
            return {"FINISHED"}
        bm = bmesh.from_edit_mesh(obj.data)
        verts = verts=[v for v in bm.verts if v.select]
        for v in verts:
            dx = (scene.pdt_pivotloc.x - obj.matrix_world.decompose()[0].x - v.co.x) * (1-scene.pdt_pivotscale.x)
            dy = (scene.pdt_pivotloc.y - obj.matrix_world.decompose()[0].y - v.co.y) * (1-scene.pdt_pivotscale.y)
            dz = (scene.pdt_pivotloc.z - obj.matrix_world.decompose()[0].z - v.co.z) * (1-scene.pdt_pivotscale.z)
            dv = Vector((dx,dy,dz))
            v.co = v.co + dv
        bmesh.update_edit_mesh(obj.data)
        return {"FINISHED"}


class PDT_OT_PivotToCursor(Operator):
    """Set The Pivot Point to Cursor Location"""

    bl_idname = "pdt.pivotcursor"
    bl_label = "PDT Pivot To Cursor"

    def execute(self,context):
        """Moves Pivot Point to Cursor Location.

        Moves Pivot Point to Cursor Location in active scene

        Args:
            context: Current Blender bpy.context

        Returns:
             Status Set.
        """

        scene = context.scene
        scene.pdt_pivotloc = scene.cursor.location
        return {"FINISHED"}

class PDT_OT_CursorToPivot(Operator):
    """Set The Cursor Location to Pivot Point"""

    bl_idname = "pdt.cursorpivot"
    bl_label = "PDT Cursor To Pivot"

    def execute(self,context):
        """Moves Cursor to Pivot Point Location.

        Moves Cursor to Pivot Point Location in active scene

        Args:
            context: Current Blender bpy.context

        Returns:
            Status Set.
        """

        scene = context.scene
        scene.cursor.location = scene.pdt_pivotloc
        return {"FINISHED"}


class PDT_OT_PivotSelected(Operator):
    """Set Pivot Point to Selected Geometry"""
    bl_idname = "pdt.pivotselected"
    bl_label = "PDT Pivot to Selected"

    def execute(self,context):
        """Moves Pivot Point centroid of Selected Geometry.

        Moves Pivot Point centroid of Selected Geometry in active scene
        using Snap_Cursor_To_Selected, then puts cursor back to original location.

        Args:
            context: Current Blender bpy.context

        Returns:
            Status Set.
        """

        scene = context.scene
        obj = bpy.context.view_layer.objects.active
        if obj == None:
            self.report({'ERROR'},
                    "Select 1 Object")
            return {"FINISHED"}
        obj_loc = obj.matrix_world.decompose()[0]
        if obj.mode != 'EDIT':
            self.report({'ERROR'},
                    "Only in Works on Vertices in Edit Mode")
            return {"FINISHED"}
        bm = bmesh.from_edit_mesh(obj.data)
        verts = verts=[v for v in bm.verts if v.select]
        if len(verts) > 0:
            old_cursor_loc = scene.cursor.location.copy()
            bpy.ops.view3d.snap_cursor_to_selected()
            scene.pdt_pivotloc = scene.cursor.location
            scene.cursor.location = old_cursor_loc
            return {"FINISHED"}
        else:
            self.report({'ERROR'},
                    "Nothing Selected!")
            return {"FINISHED"}


class PDT_OT_PivotOrigin(Operator):
    """Set Pivot Point at Object Origin"""

    bl_idname = "pdt.pivotorigin"
    bl_label = "PDT Pivot to Object Origin"

    def execute(self,context):
        """Moves Pivot Point to Object Origin.

        Moves Pivot Point to Object Origin in active scene

        Args:
            context: Current Blender bpy.context

        Returns:
            Status Set.
        """

        scene = context.scene
        obj = bpy.context.view_layer.objects.active
        if obj == None:
            self.report({'ERROR'},
                    "Select 1 Object")
            return {"FINISHED"}
        obj_loc = obj.matrix_world.decompose()[0]
        scene.pdt_pivotloc = obj_loc
        return {"FINISHED"}


class PDT_OT_PivotWrite(Operator):
    """Write Pivot Point Location to Object"""

    bl_idname = "pdt.pivotwrite"
    bl_label = "PDT Write PP to Object?"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self,context):
        """Writes Pivot Point Location to Object's Custom Properties.

        Writes Pivot Point Location to Object's Custom Properties
        as Vector to 'PDT_PP_LOC' - Requires Confirmation through dialogue

        Args:
            context: Current Blender bpy.context

        Note:
            Uses pdt_pivotloc scene variable

        Returns:
            Status Set.
        """

        scene = context.scene
        obj = bpy.context.view_layer.objects.active
        if obj == None:
            self.report({'ERROR'},
                    "Select 1 Object")
            return {"FINISHED"}
        obj['PDT_PP_LOC'] = scene.pdt_pivotloc
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        row = self.layout
        row.label(text="Are You Sure About This?")


class PDT_OT_PivotRead(Operator):
    """Read Pivot Point Location from Object"""

    bl_idname = "pdt.pivotread"
    bl_label = "PDT Read PP"

    def execute(self,context):
        """Reads Pivot Point Location from Object's Custom Properties.

        Sets Pivot Point Location from Object's Custom Properties
        using 'PDT_PP_LOC'

        Args:
            context: Current Blender bpy.context

        Note:
            Uses pdt_pivotloc scene variable

        Returns:
            Status Set.
        """

        scene = context.scene
        obj = bpy.context.view_layer.objects.active
        if obj == None:
            self.report({'ERROR'},
                    "Select 1 Object")
            return {"FINISHED"}
        if obj['PDT_PP_LOC'] is not None:
            scene.pdt_pivotloc = obj['PDT_PP_LOC']
            return {"FINISHED"}
        else:
            self.report({'ERROR'},
                    "Custom Property PDT_PP_LOC for this object not found, have you Written it yet?")
            return {"FINISHED"}

# Create the Panel Menu.
#
class PDT_PT_Panel2(Panel):
    bl_idname = "PDT_PT_panel2"
    bl_label = "PDT Pivot Point"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category= 'PDT'

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        row = layout.row()
        split = row.split(factor=0.4, align=True)
        if context.window_manager.pdt_run_opengl is False:
            icon = 'PLAY'
            txt = 'Show'
        else:
            icon = "PAUSE"
            txt = 'Hide'
        split.operator("pdt.modaldraw", icon=icon, text=txt)
        split.prop(scene, 'pdt_pivotsize', text = "")
        split.prop(scene, 'pdt_pivotwidth', text = "")
        split.prop(scene, 'pdt_pivotalpha', text = "")
        row = layout.row()
        row.label(text='Pivot Point Location')
        row = layout.row()
        row.prop(scene, 'pdt_pivotloc', text = "")
        row = layout.row()
        col = row.column()
        col.operator("pdt.pivotselected", icon='EMPTY_AXIS', text="Selection")
        col = row.column()
        col.operator("pdt.pivotcursor", icon='EMPTY_AXIS', text="Cursor")
        col = row.column()
        col.operator("pdt.pivotorigin", icon='EMPTY_AXIS', text="Origin")
        row = layout.row()
        col = row.column()
        col.operator("pdt.viewplanerot", icon='EMPTY_AXIS', text="Rotate")
        col = row.column()
        col.prop(scene, 'pdt_pivotang', text = "Angle")
        row = layout.row()
        col = row.column()
        col.operator("pdt.viewscale", icon='EMPTY_AXIS', text="Scale")
        col = row.column()
        col.operator("pdt.cursorpivot", icon='EMPTY_AXIS', text="Cursor To Pivot")
        row = layout.row()
        row.label(text='Pivot Point Scale Factors')
        row = layout.row()
        row.prop(scene, 'pdt_pivotscale', text = "")
        row = layout.row()
        col = row.column()
        col.operator("pdt.pivotwrite", icon='FILE_TICK', text="PP Write")
        col = row.column()
        col.operator("pdt.pivotread", icon='FILE', text="PP Read")
