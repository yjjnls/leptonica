#!/usr/bin/env python
# -*- coding: utf-8 -*-


from bincrafters import build_template_default
import platform
import copy
import os

os.environ['CONAN_USERNAME'] = os.environ.get('CONAN_USERNAME','conanos')

if __name__ == "__main__":

    builder = build_template_default.get_builder()
	
    if os.environ.get('EMSCRIPTEN_VERSIONS'):
        for version in os.environ['EMSCRIPTEN_VERSIONS'].split(','):
            for build_type in os.environ.get('CONAN_BUILD_TYPES','Debug').split(','):
                builder.add(settings={
                    "compiler": "emcc",
                    "compiler.libcxx":'libcxxabi',
                    "build_type": build_type, 
                    "compiler.version": version
                    })

        items = []
        for item in builder.items:
            if not os.environ.get('CONAN_GCC_VERSIONS') and item.settings['compiler'] == 'gcc':
                continue  
            if not os.environ.get('CONAN_CLANG_VERSIONS') and item.settings['compiler'] == 'clang':
                continue 
            items.append(item)

        builder.items = items
        builder.run()
        
        os._exit(0)
    
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
