# Copyright (c) 2019 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
import os
import sys
import nuke

from tank_vendor import six

HookBaseClass = sgtk.get_hook_baseclass()


class RenderMedia(HookBaseClass):
    """
    RenderMedia hook implementation for the tk-nuke engine.
    """

    def __init__(self, *args, **kwargs):
        super(RenderMedia, self).__init__(*args, **kwargs)

        self.__app = self.parent

        self._burnin_nk = os.path.join(
            self.__app.disk_location, "resources", "burnin.nk"
        )
        self._font = os.path.join(
            self.__app.disk_location, "resources", "liberationsans_regular.ttf"
        )

        # If the slate_logo supplied was an empty string, the result of getting
        # the setting will be the config folder which is invalid so catch that
        # and make our logo path an empty string which Nuke won't have issues with.
        self._logo = None
        if os.path.isfile(self.__app.get_setting("slate_logo", "")):
            self._logo = self.__app.get_setting("slate_logo", "")
        else:
            self._logo = ""

        # now transform paths to be forward slashes, otherwise it wont work on windows.
        if sgtk.util.is_windows():
            self._font = self._font.replace(os.sep, "/")
            self._logo = self._logo.replace(os.sep, "/")
            self._burnin_nk = self._burnin_nk.replace(os.sep, "/")

    def render(
        self,
        input_path,
        output_path,
        width,
        height,
        first_frame,
        last_frame,
        version,
        name,
        color_space,
    ):
        """
        Use Nuke to render a movie.

        :param str input_path:      Path to the input frames for the movie
        :param str output_path:     Path to the output movie that will be rendered
        :param int width:           Width of the output movie
        :param int height:          Height of the output movie
        :param int first_frame:     The first frame of the sequence of frames.
        :param int last_frame:      The last frame of the sequence of frames.
        :param str version:         Version number to use for the output movie slate and burn-in
        :param str name:            Name to use in the slate for the output movie
        :param str color_space:     Colorspace of the input frames

        :returns:               Location of the rendered media
        :rtype:                 str
        """
        output_node = None
        ctx = self.__app.context

        # create group where everything happens
        group = nuke.nodes.Group()

        # now operate inside this group
        group.begin()
        try:
            # create read node
            read = nuke.nodes.Read(name="source", file=input_path.replace(os.sep, "/"))
            read["on_error"].setValue("black")
            read["first"].setValue(first_frame)
            read["last"].setValue(last_frame)
            if color_space:
                read["colorspace"].setValue(color_space)

            # now create the slate/burnin node
    

            # create a scale node
            scale = self.__create_scale_node(width, height)
            scale.setInput(0, read)

            # Create the output node
            output_node = self.__create_output_node(output_path)
            output_node.setInput(0, scale)
        finally:
            group.end()

        if output_node:
            # Make sure the output folder exists
            output_folder = os.path.dirname(output_path)
            self.__app.ensure_folder_exists(output_folder)

            # Render the outputs, first view only
            nuke.executeMultiple(
                [output_node], ([first_frame - 1, last_frame, 1],), [nuke.views()[0]]
            )

        # Cleanup after ourselves
        nuke.delete(group)

        return output_path

    def __create_scale_node(self, width, height):
        """
        Create the Nuke scale node to resize the content.

        :param int width:           Width of the output movie
        :param int height:          Height of the output movie

        :returns:               Pre-configured Reformat node
        :rtype:                 Nuke node
        """
        scale = nuke.nodes.Reformat()
        scale["type"].setValue("to box")
        scale["box_width"].setValue(2640)
        scale["box_height"].setValue(1486)
        scale["resize"].setValue("width")
        scale["box_fixed"].setValue(True)
        scale["center"].setValue(True)
        scale["black_outside"].setValue(True)
        return scale
    def __create_output_node(self, path):
        """
        Create the Nuke output node for the movie.

        :param str path:           Path of the output movie

        :returns:               Pre-configured Write node
        :rtype:                 Nuke node
        """
        # get the Write node settings we'll use for generating the Quicktime
        wn_settings = self.__get_quicktime_settings()

        node = nuke.nodes.Write(file_type=wn_settings.get("file_type"))

        # apply any additional knob settings provided by the hook. Now that the knob has been
        # created, we can be sure specific file_type settings will be valid.
        for knob_name, knob_value in six.iteritems(wn_settings):
            if knob_name != "file_type":
                node.knob(knob_name).setValue(knob_value)

        # Don't fail if we're in proxy mode. The default Nuke publish will fail if
        # you try and publish while in proxy mode. But in earlier versions of
        # tk-multi-publish (< v0.6.9) if there is no proxy template set, it falls
        # back on the full-res version and will succeed. This handles that case
        # and any custom cases where you may want to send your proxy render to
        # screening room.
        root_node = nuke.root()
        is_proxy = root_node["proxy"].value()
        if is_proxy:
            self.__app.log_info("Proxy mode is ON. Rendering proxy.")
            node["proxy"].setValue(path.replace(os.sep, "/"))
        else:
            node["file"].setValue(path.replace(os.sep, "/"))

        return node

    def __get_quicktime_settings(self, **kwargs):
        """
        Allows modifying default codec settings for Quicktime generation.
        Returns a dictionary of settings to be used for the Write Node that generates
        the Quicktime in Nuke.

        :returns:               Codec settings
        :rtype:                 dict
        """
        settings = {}
        if sgtk.util.is_windows() or sgtk.util.is_macos():
            settings['colorspace'] = "Output - Rec.709"
            if nuke.NUKE_VERSION_MAJOR >= 12:
                # Nuke 9.0v1 changed the codec knob name to meta_codec and added an encoder knob
                # (which defaults to the new mov64 encoder/decoder).
                settings["file_type"] = "mov64"
                settings["mov64_codec"] = "appr"
                settings['mov_prores_codec_profile'] = 'ProRes 4:2:2 HQ 10-bit'

            else:
                settings["file_type"] = "mov64"
                settings["meta_codec"] = "AVdn"
                settings['mov64_dnxhd_codec_profile'] = 'DNxHD 444 10-bit 440Mbit'

        elif sgtk.util.is_linux():
            if nuke.NUKE_VERSION_MAJOR >= 12:
                # Nuke 9.0v1 removed ffmpeg and replaced it with the mov64 writer
                # http://help.thefoundry.co.uk/nuke/9.0/#appendices/appendixc/supported_file_formats.html
                ettings["file_type"] = "ffmpeg"
                settings["format"] = "MOV format (mov)"
            else:
                # the 'codec' knob name was changed to 'format' in Nuke 7.0
                settings["file_type"] = "ffmpeg"
                settings["format"] = "MOV format (mov)"

        return settings

