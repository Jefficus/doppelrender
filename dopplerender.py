# ##### BEGIN CC BY 4.0 LICENSE BLOCK #####
#
# This work is licensed under the Creative Commons Attribution 4.0 International License.
# To view a copy of this license, visit http://creativecommons.org/licenses/by/4.0/ or 
# send a letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.
#
# ##### END CC BY 4.0 LICENSE BLOCK #####

# <pep8 compliant>

import bpy
import os
import time
import glob
import hashlib
import struct
import shutil

from bpy.props import BoolProperty, FloatProperty, StringProperty, EnumProperty

class DoppleRenderOperator(bpy.types.Operator):
    bl_idname = "render.dopplerender"
    bl_label = "DoppleRender Process"
    bl_options = {'REGISTER'}

    def execute(self, context):
        self.report({'INFO'}, "doppleOp execute()!")
        # print("Dopplerender EXECUTE called.")
        dopplerender_process(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.report({'INFO'}, "doppleOp invoke()!")
        # print("Dopplerender INVOKE called.")
        dopplerender_process(context)
        return {'FINISHED'}

#####################################


def dopplerender_process(context):

    pre_thumbs = time.time()
    render_thumbnails(context)
    post_thumbs = time.time()
    thumb_time = post_thumbs - pre_thumbs

    doppel_sets = checksum_thumbnails(context)
    post_checksums = time.time()
    checksum_time = post_checksums - post_thumbs

    preprocess_time = checksum_time + thumb_time
    unique_frame_count = len(doppel_sets)
    
    render_full(context, doppel_sets, preprocess_time)
    rendercopy_time = time.time() - post_checksums

    print("Timings: thumbnails: %.03f, checksums: %.03f, render %d fully+clone: %.03f" %
          (thumb_time, checksum_time, unique_frame_count, rendercopy_time))
    print("== DoppleRender Finished ==")


def render_thumbnails(context):
    prior_settings = {}

    # Might not need to loop all scenes?
    # Unless... other scenes are being used for various compositing effects?
    # Can just use C.scene for active one.
    for scene in bpy.data.scenes:
        prior_settings[scene.name] = {
            'render.filepath': scene.render.filepath,
            'render.resolution_percentage': scene.render.resolution_percentage,
            'cycles.samples': scene.cycles.samples,
            'cycles.use_animated_seed': scene.cycles.use_animated_seed
        }

    context.scene.render.filepath = context.scene.dopplerender_thumbpath
    context.scene.render.resolution_percentage = context.scene.dopplerender_thumbsize
    context.scene.cycles.samples = 20
    context.scene.cycles.use_animated_seed = False

    bpy.ops.render.render(animation=True)

    for sname in prior_settings.keys():
        sc = bpy.data.scenes[sname]
        settings = prior_settings[sname]
        sc.render.resolution_percentage = settings['render.resolution_percentage']
        sc.cycles.samples = settings['cycles.samples']
        sc.cycles.use_animated_seed = settings['cycles.use_animated_seed']
        sc.render.filepath = settings['render.filepath']


def checksum_thumbnails(context):
    tpath, tpattern = os.path.split(context.scene.dopplerender_thumbpath)
    hashpat = tpattern.count("#") * "#"
    tmatch = tpattern.replace(hashpat, "*")
    tframes = glob.glob(os.path.join(tpath, tmatch))    # list all frames of the current? render.

    thumbnail_digests = {}

    # make image object for first one; reload subsequent thumbnails into same object.
    loadimg = None
    for f in tframes:
        if not loadimg:
            loadimg = bpy.data.images.load(f)
        else:
            loadimg.filepath = f
            loadimg.reload()  # maybe unneeded: setting filepath in pyconsole works already?

        ihash = get_image_hash(loadimg)
        
        if ihash in thumbnail_digests:
            thumbnail_digests[ihash].append(f)
        else:
            thumbnail_digests[ihash] = [f]

    # print(thumbnail_digests)

    sameframe_sets = []
    for thash in thumbnail_digests:
        frame_nums = []
        for filepath in thumbnail_digests[thash]:
            frnum = filepath_to_framenum(filepath)
            if frnum is not None:
                frame_nums.append(frnum)
        sameframe_sets.append(frame_nums)

    return sorted(sameframe_sets)


# uses bpy image object; avoids dependency on PIL/Pillow.
def get_image_hash(img):
    thumb_hash = hashlib.sha256()
    # Ref: https://stackoverflow.com/questions/34794640/python-struct-pack-pack-multiple-datas-in-a-list-or-a-tuple
    pxblob = struct.pack("<%uf" % len(img.pixels), *img.pixels)	 # pack RGBA floats as blob.
    thumb_hash.update(pxblob)
    return thumb_hash.hexdigest()


def filepath_to_framenum(instr):
    nameonly = os.path.split(instr)[-1]
    numstr = "".join([i for i in nameonly if i.isdigit()])
    if numstr:
        return int(numstr)
    else:
        return None   # frame num -1 is still a number... explicit None check seems clearer.


def framenum_to_filepath(frnum, ftemplate=''):
    if not ftemplate:
        ftemplate = bpy.context.scene.render.filepath
        if "#" not in ftemplate:
            ftemplate = os.path.join(ftemplate, "####.png")  # safety: user renderpath.

    numdigits = ftemplate.count('#')
    framenum_str = str(frnum).zfill(numdigits)
    return ftemplate.replace('#'*numdigits, framenum_str)


def render_full(context, doppel_sets, preprocesstime=None):
    # render the first frame of each doppel_set; clone core frames to fill out the sets.
    # print(doppel_sets)
    render_frames = sorted([fnums[0] for fnums in doppel_sets])
    scene = context.scene
    old_fpath = scene.render.filepath
    # scene.render.image_settings.file_format = 'PNG' # safer being explicit...?

    # Ensure there's a numbering pattern on the path; my renderpath was "/tmp/"
    fullrender_pathtemplate = os.path.join(old_fpath, "####.png")

    frame_rts = []    # frame render times, for stats report
    for frame_num in render_frames:
        t0 = time.time()
        scene.frame_set(frame_num)
        scene.render.filepath = framenum_to_filepath(frame_num, fullrender_pathtemplate)
        bpy.ops.render.render(write_still=True)
        tframe = time.time()
        frame_rts.append(tframe-t0)

    tot_frt = sum(frame_rts)
    avg_frt = tot_frt / len(frame_rts)

    scene.render.filepath = old_fpath  # restore to previous

    # Clone all uniques to all their sibling frames.
    # print(doppel_sets)
    clonecount = 0
    clonetimes = []
    # use_symlinks option... Copy method: Copy file | SymLink (toggle buttons)
    do_copy = context.scene.dopplerender_copytype == 'COPY'
    for dopset in doppel_sets:
        corefilenum = dopset[0]
        corefilepath = framenum_to_filepath(corefilenum, fullrender_pathtemplate)
        for clonefilenum in dopset[1:]:
            t0 = time.time()
            clonefilepath = framenum_to_filepath(clonefilenum, fullrender_pathtemplate)
            if do_copy:
                shutil.copy2(corefilepath, clonefilepath)
                # print("copying: %s , %s" % (corefilepath, clonefilepath))
            else:
                os.symlink(os.path.basename(corefilepath), clonefilepath)
                # print("symlinking: %s , %s" % (corefilepath, clonefilepath))

            clonecount += 1
            clonetimes.append(time.time() - t0)

    avg_clonetime = sum(clonetimes) / len(clonetimes)
    cloningtime = clonecount * avg_clonetime
    rendersaved = clonecount * avg_frt
    saving = (rendersaved - cloningtime) - preprocesstime
    print("Avg frame render: %.2f, Avg clone: %.2f. Clones: %d. Timesaving: %.2fs" %
          (avg_frt, avg_clonetime, clonecount, saving))

#####################################


class DoppleRenderPanel(bpy.types.Panel):
    """Creates a Panel in the render context of the properties editor"""
    bl_label = "DoppleRender"
    bl_idname = "RENDER_PT_dopplerender"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"

    def draw(self, context):
        row = self.layout.row()
        # props = row.operator(DoppleRenderOperator.bl_idname, icon="RENDER_ANIMATION", text="Animation")
        row.operator("render.dopplerender", icon="RENDER_ANIMATION", text="Animation")

        row = self.layout.row()
        row.prop(context.scene, "dopplerender_thumbsize")

        row = self.layout.row()
        row.prop(context.scene, "dopplerender_copytype", expand=True)
