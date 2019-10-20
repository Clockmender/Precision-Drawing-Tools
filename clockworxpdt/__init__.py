# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
#
# <pep8 compliant>
#
# ----------------------------------------------------------
# Author: Alan Odom (Clockmender) Copyright © 2019
# ----------------------------------------------------------
#
# ----------------------------------------------
# Define Addon info
# ----------------------------------------------
#
bl_info = {
    "name": "Precision Drawing Tools (PDT)",
    "author": "Alan Odom (Clockmender)",
    "version": (1, 1, 5),
    "blender": (2, 80, 0),
    "location": "View3D > UI > PDT",
    "description": "Precision Drawing Tools for Acccurate Modelling",
    "warning": "",
    "wiki_url": "https://clockmender.uk/blender/precision-drawing-tools/",
    "category": "3D View",
}


# ----------------------------------------------
# Import modules
# ----------------------------------------------
if "bpy" in locals():
    import importlib

    importlib.reload(clockworx_pdt_design)
    importlib.reload(clockworx_pivot_point)
    importlib.reload(clockworx_pdt_menus)
    importlib.relaod(clockworx_pdt_library)
    importlib.relaod(clockworx_pdt_view)
    importlib.reload(pdt_xall)
    importlib.reload(pdt_bix)
    importlib.reload(pdt_etof)
else:
    from . import clockworx_pdt_design
    from . import clockworx_pivot_point
    from . import clockworx_pdt_menus
    from . import clockworx_pdt_library
    from . import clockworx_pdt_view
    from . import pdt_xall
    from . import pdt_bix
    from . import pdt_etof
import bpy
import os
from pathlib import Path
from bpy.types import AddonPreferences, Scene, WindowManager
from bpy.props import (
    FloatVectorProperty,
    IntProperty,
    BoolProperty,
    StringProperty,
    FloatProperty,
    EnumProperty,
    CollectionProperty,
)

from .clockworx_pdt_command import command_run
from .pdt_functions import scale_set
from .pdt_msg_strings import *


# Define Panel classes for updating
#
panels = (
    clockworx_pdt_menus.PDT_PT_Panel1,
    clockworx_pdt_menus.PDT_PT_Panel2,
    clockworx_pdt_menus.PDT_PT_Panel3,
    clockworx_pdt_menus.PDT_PT_Panel4,
    clockworx_pdt_menus.PDT_PT_Panel5,
)


def update_panel(self, context):
    """Update Panels if parameters change.

    This routine is required if the panel layouts are changed by the application.

    Args:
        context: Current Blender bpy.context

    Returns:
        Nothing.
    """

    message = "PDT: Updating Panel locations has failed"
    try:
        for panel in panels:
            if "bl_rna" in panel.__dict__:
                bpy.utils.unregister_class(panel)

        for panel in panels:
            panel.bl_category = context.preferences.addons[__name__].preferences.category
            bpy.utils.register_class(panel)

    except Exception as e:
        print("\n[{}]\n{}\n\nError:\n{}".format(__name__, message, e))
        pass


# List of All Classes in the Add-on to register
#
classes = (
    clockworx_pdt_design.PDT_OT_PlacementAbs,
    clockworx_pdt_design.PDT_OT_PlacementDelta,
    clockworx_pdt_design.PDT_OT_PlacementDis,
    clockworx_pdt_design.PDT_OT_PlacementCen,
    clockworx_pdt_design.PDT_OT_PlacementPer,
    clockworx_pdt_design.PDT_OT_PlacementNormal,
    clockworx_pdt_design.PDT_OT_PlacementInt,
    clockworx_pdt_design.PDT_OT_JoinVerts,
    clockworx_pdt_design.PDT_OT_Angle2,
    clockworx_pdt_design.PDT_OT_Angle3,
    clockworx_pdt_design.PDT_OT_Origin,
    clockworx_pdt_design.PDT_OT_Taper,
    clockworx_pdt_design.PDT_OT_Fillet,
    clockworx_pivot_point.PDT_OT_ModalDrawOperator,
    clockworx_pivot_point.PDT_OT_ViewPlaneRotate,
    clockworx_pivot_point.PDT_OT_ViewPlaneScale,
    clockworx_pivot_point.PDT_OT_PivotToCursor,
    clockworx_pivot_point.PDT_OT_CursorToPivot,
    clockworx_pivot_point.PDT_OT_PivotSelected,
    clockworx_pivot_point.PDT_OT_PivotOrigin,
    clockworx_pivot_point.PDT_OT_PivotWrite,
    clockworx_pivot_point.PDT_OT_PivotRead,
    clockworx_pdt_library.PDT_OT_Append,
    clockworx_pdt_library.PDT_OT_Link,
    clockworx_pdt_library.PDT_OT_LibShow,
    clockworx_pdt_view.PDT_OT_ViewRot,
    clockworx_pdt_view.PDT_OT_vRotL,
    clockworx_pdt_view.PDT_OT_vRotR,
    clockworx_pdt_view.PDT_OT_vRotU,
    clockworx_pdt_view.PDT_OT_vRotD,
    clockworx_pdt_view.PDT_OT_vRoll,
    clockworx_pdt_view.PDT_OT_viso,
    pdt_xall.PDT_OT_IntersectAllEdges,
    pdt_bix.PDT_OT_LineOnBisection,
    pdt_etof.PDT_OT_EdgeToFace,
    clockworx_pdt_menus.PDT_PT_Panel1,
    clockworx_pdt_menus.PDT_PT_Panel4,
    clockworx_pdt_menus.PDT_PT_Panel5,
    clockworx_pdt_menus.PDT_PT_Panel2,
    clockworx_pdt_menus.PDT_PT_Panel3,
)


def enumlist_objects(self, context):
    """Populate Objects List from Parts Library.

    Creates list of objects that optionally have search string contained in them
    to populate variable pdt_lib_objects enumerator.

    Args:
        context: Current Blender bpy.context

    Returns:
        list of Object Names.
    """

    scene = context.scene
    path = os.path.join(str(Path(__file__).parents[0]), "parts_library.blend")
    if Path(path).is_file():
        with bpy.data.libraries.load(path) as (data_from, data_to):
            if len(scene.pdt_obsearch) == 0:
                object_names = [ob for ob in data_from.objects]
            else:
                object_names = [ob for ob in data_from.objects if scene.pdt_obsearch in ob]
        items = []
        for ob in object_names:
            items.append((ob, ob, ""))
        return items
    else:
        return [("MISSING","Library is Missing","")]


def enumlist_collections(self, context):
    """Populate Collections List from Parts Library.

    Creates list of collections that optionally have search string contained in them
    to populate variable pdt_lib_collections enumerator

    Args:
        context: Current Blender bpy.context

    Returns:
        list of Collections Names.
    """

    scene = context.scene
    path = os.path.join(str(Path(__file__).parents[0]), "parts_library.blend")
    if Path(path).is_file():
        with bpy.data.libraries.load(path) as (data_from, data_to):
            if len(scene.pdt_cosearch) == 0:
                object_names = [ob for ob in data_from.collections]
            else:
                object_names = [ob for ob in data_from.collections if scene.pdt_cosearch in ob]
        items = []
        for ob in object_names:
            items.append((ob, ob, ""))
        return items
    else:
        return [("MISSING","Library is Missing","")]


def enumlist_materials(self, context):
    """Populate Materials List from Parts Library.

    Creates list of materials that optionally have search string contained in them
    to populate variable pdt_lib_materials enumerator.

    Args:
        context: Current Blender bpy.context

    Returns:
        list of Object Names.
    """

    scene = context.scene
    path = os.path.join(str(Path(__file__).parents[0]), "parts_library.blend")
    if Path(path).is_file():
        with bpy.data.libraries.load(path) as (data_from, data_to):
            if len(scene.pdt_masearch) == 0:
                object_names = [ob for ob in data_from.materials]
            else:
                object_names = [ob for ob in data_from.materials if scene.pdt_masearch in ob]
        items = []
        for ob in object_names:
            items.append((ob, ob, ""))
        return items
    else:
        return [("MISSING","Library is Missing","")]


def register():
    """Register Classes and Create Scene Variables.

    Operates on the classes list defined above.
    """

    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)

    Scene.pdt_delta_x = FloatProperty(
        name="X Coord", default=0.0, precision=5, description=PDT_DES_XDELTA, unit="LENGTH"
    )
    Scene.pdt_delta_y = FloatProperty(
        name="Y Coord", default=0.0, precision=5, description=PDT_DES_YDELTA, unit="LENGTH"
    )
    Scene.pdt_delta_z = FloatProperty(
        name="Z Coord", default=0.0, precision=5, description=PDT_DES_ZDELTA, unit="LENGTH"
    )
    Scene.pdt_distance = FloatProperty(
        name="Distance", default=0.0, precision=5, description=PDT_DES_OFFDIS, unit="LENGTH"
    )
    Scene.pdt_angle = FloatProperty(
        name="Angle", min=-180, max=180, default=0.0, precision=5, description=PDT_DES_OFFANG
    )
    Scene.pdt_percent = FloatProperty(
        name="Percent", default=0.0, precision=5, description=PDT_DES_OFFPER
    )
    Scene.pdt_plane = EnumProperty(
        items=(
            ("XZ", "Front(X-Z)", "Use X-Z Plane"),
            ("XY", "Top(X-Y)", "Use X-Y Plane"),
            ("YZ", "Right(Y-Z)", "Use Y-Z Plane"),
            ("LO", "View", "Use View Plane"),
        ),
        name="Working Plane",
        default="XZ",
        description=PDT_DES_WORPLANE,
    )
    Scene.pdt_select = EnumProperty(
        items=(
            ("REL", "Current", "Moved Relative to Current Position"),
            (
                "SEL",
                "Selected",
                "Moved Relative to Selected Object, or Vertex, Cursor & Pivot Only",
            ),
        ),
        name="Move Mode",
        default="SEL",
        description=PDT_DES_MOVESEL,
    )
    Scene.pdt_operate = EnumProperty(
        items=(
            ("CU", "Cursor", "Ths Function will Move the Cursor"),
            ("PP", "Pivot", "Ths Function will Move the Pivot Point"),
            ("MV", "Move", "This function will Move Vertices, or Objects"),
            ("NV", "New Vertex", "This function will Add a New Vertex"),
            ("EV", "Extrude Vertices", "This function will Extrude Vertices Only in EDIT Mode"),
            ("SE", "Split Edges", "This function will Split Edges Only in EDIT Mode"),
            (
                "DG",
                "Duplicate Geometry",
                "This function will Duplicate Geometry in EDIT Mode (Delta & Direction Only)",
            ),
            (
                "EG",
                "Extrude Geometry",
                "This function will Extrude Geometry in EDIT Mode (Delta & Direction Only)",
            ),
        ),
        name="Operation",
        default="CU",
        description=PDT_DES_OPMODE,
    )
    Scene.pdt_taper = EnumProperty(
        items=(
            ("RX-MY", "RotX-MovY", "Rotate X - Move Y"),
            ("RX-MZ", "RotX-MovZ", "Rotate X - Move Z"),
            ("RY-MX", "RotY-MovX", "Rotate Y - Move X"),
            ("RY-MZ", "RotY-MovZ", "Rotate Y - Move Z"),
            ("RZ-MX", "RotZ-MovX", "Rotate Z - Move X"),
            ("RZ-MY", "RotZ-MovY", "Rotate Z - Move Y"),
        ),
        name="Axes",
        default="RX-MY",
        description=PDT_DES_ROTMOVAX,
    )
    Scene.pdt_flipangle = BoolProperty(
        name="Flip Angle", default=False, description=PDT_DES_FLIPANG
    )
    Scene.pdt_flippercent = BoolProperty(
        name="Flip %", default=False, description=PDT_DES_FLIPPER
    )
    Scene.pdt_extend = BoolProperty(
        name="Trim/Extend All", default=False, description=PDT_DES_TRIM
    )
    Scene.pdt_lib_objects = EnumProperty(
        items=enumlist_objects, name="Objects", description=PDT_DES_LIBOBS
    )
    Scene.pdt_lib_collections = EnumProperty(
        items=enumlist_collections, name="Collections", description=PDT_DES_LIBCOLS
    )
    Scene.pdt_lib_materials = EnumProperty(
        items=enumlist_materials, name="Materials", description=PDT_DES_LIBMATS
    )
    Scene.pdt_lib_mode = EnumProperty(
        items=(
            ("OBJECTS", "Objects", "Use Objects"),
            ("COLLECTIONS", "Collections", "Use Collections"),
            ("MATERIALS", "Materials", "Use Materials"),
        ),
        name="Mode",
        default="OBJECTS",
        description=PDT_DES_LIBMODE,
    )
    Scene.pdt_obsearch = StringProperty(
        name="Search", default="", description=PDT_DES_LIBSER
    )
    Scene.pdt_cosearch = StringProperty(
        name="Search", default="", description=PDT_DES_LIBSER
    )
    Scene.pdt_masearch = StringProperty(
        name="Search", default="", description=PDT_DES_LIBSER
    )
    Scene.pdt_xrot = FloatProperty(name="X Rot", default=0, unit="ROTATION")
    Scene.pdt_yrot = FloatProperty(name="Y Rot", default=0, unit="ROTATION")
    Scene.pdt_zrot = FloatProperty(name="Z Rot", default=0, unit="ROTATION")
    Scene.pdt_oborder = EnumProperty(
        items=(
            ("1,2,3,4", "1,2,3,4", "Objects 1 & 2 are First Line"),
            ("1,3,2,4", "1,3,2,4", "Objects 1 & 3 are First Line"),
            ("1,4,2,3", "1,4,2,3", "Objects 1 & 4 are First Line"),
        ),
        name="Order",
        default="1,2,3,4",
        description=PDT_DES_OBORDER,
    )
    Scene.pdt_vrotangle = FloatProperty(name="View Rotate Angle", default=10, max=180, min=-180)
    Scene.pdt_command = StringProperty(
        name="Command",
        default="CA0,0,0",
        update=command_run,
        description=PDT_DES_VALIDLET,
    )
    Scene.pdt_error = StringProperty(name="Error", default="")
    Scene.pdt_pivotloc = FloatVectorProperty(
        name="Pivot Location",
        default=(0.0, 0.0, 0.0),
        subtype="XYZ",
        description=PDT_DES_PPLOC,
    )
    Scene.pdt_pivotscale = FloatVectorProperty(
        name="Pivot Scale", default=(1.0, 1.0, 1.0), subtype="XYZ", description=PDT_DES_PPSCALEFAC
    )
    Scene.pdt_pivotsize = FloatProperty(
        name="Pivot Factor", min=0.4, max=2, default=1, precision=1, description=PDT_DES_PPSIZE
    )
    Scene.pdt_pivotwidth = IntProperty(
        name="Width", min=1, max=5, default=2, description=PDT_DES_PPWIDTH
    )
    Scene.pdt_pivotang = FloatProperty(name="Pivot Angle", min=-180, max=180, default=0.0)
    Scene.pdt_pivotdis = FloatProperty(name="Pivot Dist",
        default=0.0,
        min = 0,
        update=scale_set,
        description=PDT_DES_PIVOTDIS,
        )
    Scene.pdt_pivotalpha = FloatProperty(
        name="Alpha",
        min=0.2,
        max=1,
        default=0.6,
        precision=1,
        description=PDT_DES_PPTRANS,
    )
    Scene.pdt_pivotshow = BoolProperty()
    Scene.pdt_filletrad = FloatProperty(
        name="Fillet Radius", min=0.0, default=1.0, description=PDT_DES_FILLETRAD
    )
    Scene.pdt_filletnum = IntProperty(
        name="Fillet Segments", min=1, default=4, description=PDT_DES_FILLETSEG
    )
    Scene.pdt_filletpro = FloatProperty(
        name="Fillet Profile", min=0.0, max=1.0, default=0.5, description=PDT_DES_FILLETPROF
    )
    Scene.pdt_filletbool = BoolProperty(
        name="Use Verts",
        default=True,
        description=PDT_DES_FILLETVERTS,
    )

    # OpenGL flag
    #
    wm = WindowManager
    # Register Internal OpenGL Property
    #
    wm.pdt_run_opengl = BoolProperty(default=False)


def unregister():
    """Unregister Classes and Delete Scene Variables.

    Operates on the classes list defined above.
    """

    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)

    # Remove Properties
    del Scene.pdt_delta_x
    del Scene.pdt_delta_y
    del Scene.pdt_delta_z
    del Scene.pdt_distance
    del Scene.pdt_angle
    del Scene.pdt_percent
    del Scene.pdt_plane
    del Scene.pdt_select
    del Scene.pdt_operate
    del Scene.pdt_flipangle
    del Scene.pdt_flippercent
    del Scene.pdt_extend
    del Scene.pdt_taper
    del Scene.pdt_lib_objects
    del Scene.pdt_lib_collections
    del Scene.pdt_lib_materials
    del Scene.pdt_obsearch
    del Scene.pdt_lib_mode
    del Scene.pdt_xrot
    del Scene.pdt_yrot
    del Scene.pdt_zrot
    del Scene.pdt_oborder
    del Scene.pdt_cosearch
    del Scene.pdt_masearch
    del Scene.pdt_vrotangle
    del Scene.pdt_command
    del Scene.pdt_error
    del Scene.pdt_pivotloc
    del Scene.pdt_pivotsize
    del Scene.pdt_pivotang
    del Scene.pdt_pivotdis
    del Scene.pdt_pivotscale
    del Scene.pdt_pivotwidth
    del Scene.pdt_pivotalpha
    del Scene.pdt_pivotshow
    del Scene.pdt_filletrad
    del Scene.pdt_filletnum
    del Scene.pdt_filletpro
    del Scene.pdt_filletbool

    # remove OpenGL data
    clockworx_pivot_point.PDT_OT_ModalDrawOperator.handle_remove(
        clockworx_pivot_point.PDT_OT_ModalDrawOperator, bpy.context
    )
    wm = bpy.context.window_manager
    p = "pdt_run_opengl"
    if p in wm:
        del wm[p]


if __name__ == "__main__":
    register()
