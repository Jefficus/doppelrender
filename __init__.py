# ##### BEGIN CC BY 4.0 LICENSE BLOCK #####
#
# This work is licensed under the Creative Commons Attribution 4.0 International License.
# To view a copy of this license, visit http://creativecommons.org/licenses/by/4.0/ or 
# send a letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.
#
# ##### END CC BY 4.0 LICENSE BLOCK #####

# <pep8 compliant>

bl_info = {
    "name": "Dopplerender",
    "description": "Smart sequence-rendering that automatically copies duplicate frames without re-rendering.",
    "author": "Jefferson Smith",
    "version": (0, 0, 2),
    "blender": (2, 7, 8),
    "location": "Properties > Scene > Render",
    "category": "Render",
    "warning": "",
    "support": 'COMMUNITY'
    }

if "bpy" in locals():
    import imp
    if "dopplerender" in locals():
        imp.reload(dopplerender)

import bpy
import os
import tempfile
from . import dopplerender


def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.dopplerender_thumbsize = bpy.props.FloatProperty(
        name="Thumbnail Reduction",
        description="Percentage scale of render size for comparison thumbnails",
        default=5,
        min=0,
        max=100,
        subtype='PERCENTAGE')

    bpy.types.Scene.dopplerender_thumbpath = bpy.props.StringProperty(
        name="Thumbnail Render Directory",
        subtype='FILE_PATH',
        default=os.path.join(tempfile.gettempdir(), "dopthumbs", "tiny####.png"))

    bpy.types.Scene.dopplerender_copytype = bpy.props.EnumProperty(
        items=[('SYMLINK', "Symlink", "Symbolic Link duplicate frame files"),
               ('COPY', "Copy", "Copy duplicate frame files")],
        name="Frame copying",
        description="Frame duplication method",
        default='COPY'
    )


def unregister():
    del bpy.types.Scene.dopplerender_copytype
    del bpy.types.Scene.dopplerender_thumbpath
    del bpy.types.Scene.dopplerender_thumbsize
    bpy.utils.unregister_module(__name__)
