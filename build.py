#!/usr/bin/env python
# -*- coding: utf-8 -*-


from bincrafters import build_template_default
import platform
import copy

if __name__ == "__main__":

    builder = build_template_default.get_builder()

    items = []
    for item in builder.items:
        # skip mingw cross-builds
        if not (platform.system() == "Windows" and item.settings["compiler"] == "gcc" and
                item.settings["arch"] == "x86"):
            items.append(item)
        # add full-options build for selected platforms
        if platform.system() != "Windows" and item.settings["arch"] == "x86_64" and \
                item.settings["build_type"] == "Release":
            new_options = copy.copy(item.options)
            new_options["leptonica:with_webp"] = True
            new_options["leptonica:with_openjpeg"] = True
            items.append([item.settings, new_options, item.env_vars,
                item.build_requires, item.reference])

    builder.items = items

    builder.run()
