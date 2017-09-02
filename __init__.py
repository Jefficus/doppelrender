############# BEGIN GPL 3.0 LICENSE BLOCK ##############################
#
#  This file is part of Doppelrender.
# 
#  Doppelrender is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
# 
#  Doppelrender is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with Doppelrender. If not, see <http://www.gnu.org/licenses/>.
#
############# END GPL 3.0 LICENSE BLOCK ################################

# <pep8 compliant>

bl_info = {
    "name": "Dopplerender",
    "description": "Smart sequence-rendering that automatically re-uses duplicate frames without re-rendering.",
    "author": "Jefferson Smith",
    "version": (0, 0, 3),
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
        description="Percentage scale of thumbnail size for frame comparison",
        default=5,
        min=1,
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
