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
from bpy.types import Operator
from bpy.props import FloatProperty

from .pdt_msg_strings import *

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

        Notes:
            Uses pdt_lib_objects, pdt_lib_collections & pdt_lib_materials

        Returns:
            Status Set.
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

        Notes:
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
