# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import nuke

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class FrameOperation(HookBaseClass):
    """
    Hook called to perform a frame operation with the
    current scene
    """

    def get_frame_range(self, **kwargs):
        """
        get_frame_range will return a tuple of (in_frame, out_frame)

        :returns: Returns the frame range in the form (in_frame, out_frame)
        :rtype: tuple[int, int]
        """
        current_in = int(nuke.root()["first_frame"].value())
        current_out = int(nuke.root()["last_frame"].value())
        return (current_in, current_out)

    def set_frame_range(self, in_frame=None, out_frame=None, **kwargs):
        """
        set_frame_range will set the frame range using `in_frame` and `out_frame`

        :param int in_frame: in_frame for the current context
            (e.g. the current shot, current asset etc)

        :param int out_frame: out_frame for the current context
            (e.g. the current shot, current asset etc)

        """

        # unlock
        locked = nuke.root()["lock_range"].value()
        if locked:
            nuke.root()["lock_range"].setValue(False)

        # and lock again
        if locked:
            nuke.root()["lock_range"].setValue(True)

        nuke.root()["colorManagement"].setValue("OCIO")
        nuke.root()["OCIO_config"].setValue("aces_1.0.3")
        #nuke.root()["floatLUT"].setValue("ACES - ACES2065-1")

        nuke.root()["fps"].setValue(25)
        format = '1920 1080 1 DEMO'
        nuke.addFormat(format)
        nuke.root()["format"].setValue('DEMO')
        nuke.root()["lock_range"].setValue(True)

        # Add custom paths
       #shotnkPath = str(sgtk.platform.current_engine().context.filesystem_locations).replace(']', '').replace('[', '').replace("'", "")
       #scenesPath = ('%s/scenes/nuke') % shotnkPath
       #nukePrecompPath = ('%s/scenes/nuke/_elements') % shotnkPath
       #elementsPath = ('%s/elements') % shotnkPath

       #nuke.addFavoriteDir('Current Shot', shotNkPath, nuke.SCRIPT | nuke.IMAGE, icon='slate_icon.png')
       #nuke.addFavoriteDir('Elements', elementsPath, nuke.SCRIPT | nuke.IMAGE, icon='slate_icon.png')
       #nuke.addFavoriteDir('Prerrender (_elements)', nukePrecompPath, nuke.SCRIPT | nuke.IMAGE, icon='slate_icon.png')
       #nuke.addFavoriteDir('Nuke Scenes', scenesPath, nuke.SCRIPT | nuke.IMAGE, icon='slate_icon.png')
        # set values
        nuke.root()["first_frame"].setValue(in_frame)
        nuke.root()["last_frame"].setValue(out_frame)