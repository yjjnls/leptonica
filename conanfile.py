#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools
import os
import shutil
from conanos.build import config_scheme
try:
    import conanos.conan.hacks.cmake
except:
    if os.environ.get('EMSCRIPTEN_VERSIONS'):
        raise Exception('Please use pip install conanos to patch conan for emscripten binding !')

class LeptonicaConan(ConanFile):
    name = "leptonica"
    version = "1.76.0"
    url = "https://github.com/bincrafters/conan-leptonica"
    homepage = "http://leptonica.org"
    description = "Library containing software that is broadly useful for image processing and image analysis applications."
    license = "BSD 2-Clause"

    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"

    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False],
               "with_gif": [True, False],
               "with_jpeg": [True, False],
               "with_png": [True, False],
               "with_tiff": [True, False],
               "with_openjpeg": [True, False],
               "with_webp": [True, False],
               "fPIC": [True, False]
              }
    default_options = ("shared=False",
                       "with_gif=False",
                       "with_jpeg=True",
                       "with_png=True",
                       "with_tiff=True",
                       "with_openjpeg=False",
                       "with_webp=False",
                       "fPIC=True")

    source_subfolder = "source_subfolder"

    def is_emscripten(self):
        try:
            return self.settings.compiler == 'emcc'
        except:
            return False

    def configure(self):
        del self.settings.compiler.libcxx

        if self.is_emscripten():
            del self.settings.os
            del self.settings.arch
            self.options.remove("fPIC")
            self.options.remove("shared")
            

        ## use shared zlib for dynamic lib
        #if not self.is_emscripten():
        #    if self.options.shared:
        #        self.options['zlib'].shared = True
        #        if self.options.with_jpeg:
        #            self.options['libjpeg-turbo'].shared = True
        #        if self.options.with_png:
        #            self.options['libpng'].shared = True

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.remove("fPIC")

    def requirements(self):
        self.requires.add("zlib/1.2.11@conanos/stable")
        if self.options.with_jpeg:
            self.requires.add("libjpeg-turbo/1.5.2@conanos/stable")
        if self.options.with_png:
            self.requires.add("libpng/1.6.34@conanos/stable")

        if self.options.with_gif:
            self.requires.add("giflib/5.1.4@bincrafters/stable")
        if self.options.with_tiff:
            self.requires.add("libtiff/4.0.9@conanos/stable")
        if self.options.with_openjpeg:
            self.requires.add("openjpeg/2.3.0@bincrafters/stable")
        if self.options.with_webp:
            self.requires.add("libwebp/1.0.0@bincrafters/stable")
            
        config_scheme(self)

    def source(self):
        source_url = "https://github.com/DanBloomberg/leptonica"
        tools.get("{0}/archive/{1}.tar.gz".format(source_url, self.version))
        extracted_dir = self.name + "-" + self.version

        os.rename(extracted_dir, self.source_subfolder)
        os.rename(os.path.join(self.source_subfolder, "CMakeLists.txt"),
                  os.path.join(self.source_subfolder, "CMakeListsOriginal.txt"))
        shutil.copy("CMakeLists.txt",
                    os.path.join(self.source_subfolder, "CMakeLists.txt"))

    def build(self):
        emcc = self.is_emscripten()
        if self.options.with_openjpeg:
            # patch prefix for openjpeg pc file.
            # note the difference between pc name and package name
            shutil.copy(os.path.join(self.deps_cpp_info['openjpeg'].rootpath, 'lib', 'pkgconfig', 'libopenjp2.pc'), 'libopenjp2.pc')
            tools.replace_prefix_in_pc_file("libopenjp2.pc", self.deps_cpp_info['openjpeg'].rootpath)
            # leptonica finds openjpeg.h in a wrong directory. just patch a pc file
            tools.replace_in_file("libopenjp2.pc",
                                  'includedir=${prefix}/include/openjpeg-2.3',
                                  'includedir=${prefix}/include')

        with tools.environment_append({'PKG_CONFIG_PATH': self.build_folder}):
            cmake = CMake(self)
            cmake.definitions['STATIC'] = False if emcc else not self.options.shared
            cmake.definitions['BUILD_PROG'] = False
            # avoid finding system libs
            cmake.definitions['CMAKE_DISABLE_FIND_PACKAGE_GIF']  = not self.options.with_gif
            cmake.definitions['CMAKE_DISABLE_FIND_PACKAGE_PNG']  = not self.options.with_png
            cmake.definitions['CMAKE_DISABLE_FIND_PACKAGE_TIFF'] = not self.options.with_tiff
            cmake.definitions['CMAKE_DISABLE_FIND_PACKAGE_JPEG'] = not self.options.with_jpeg

            # avoid finding system libs by pkg-config by removing finders because they have no off switch
            if self.options.with_openjpeg:
                # check_include_files need to know where openjp2k resides
                tools.replace_in_file(os.path.join(self.source_subfolder, "CMakeListsOriginal.txt"),
                                      "pkg_check_modules(JP2K libopenjp2)",
                                      'pkg_check_modules(JP2K libopenjp2)\n'
                                      'list(APPEND CMAKE_REQUIRED_INCLUDES "${JP2K_INCLUDE_DIRS}")')
            else:
                tools.replace_in_file(os.path.join(self.source_subfolder, "CMakeListsOriginal.txt"),
                                      "pkg_check_modules(JP2K libopenjp2)",
                                      "")
            # webp does not provide .pc file but provide cmake configs. so use find_package instead
            if self.options.with_webp:
                tools.replace_in_file(os.path.join(self.source_subfolder, "CMakeListsOriginal.txt"),
                                      "pkg_check_modules(WEBP libwebp)",
                                      "find_package(WEBP REQUIRED NAMES WEBP WebP NO_SYSTEM_ENVIRONMENT_PATH)")
            else:
                tools.replace_in_file(os.path.join(self.source_subfolder, "CMakeListsOriginal.txt"),
                                      "pkg_check_modules(WEBP libwebp)",
                                      "")

            cmake.configure(source_folder=self.source_subfolder)
            cmake.build()
            cmake.install()

        self._fix_absolute_paths()

    def _fix_absolute_paths(self):
        # Fix pc file: cmake does not fill libs.private
        if self.is_emscripten() or self.settings.os != 'Windows':
            libs_private = []
            for dep in self.deps_cpp_info.deps:
                libs_private.extend(['-L'+path for path in self.deps_cpp_info[dep].lib_paths])
                libs_private.extend(['-l'+lib for lib in self.deps_cpp_info[dep].libs])
            path = os.path.join(self.package_folder, 'lib', 'pkgconfig', 'lept.pc')
            tools.replace_in_file(path,
                                 'Libs.private:',
                                 'Libs.private: ' + ' '.join(libs_private))

        # Fix cmake config file with absolute path
        path = os.path.join(self.package_folder, 'cmake', 'LeptonicaConfig.cmake')
        tools.replace_in_file(path,
                "# Provide the include directories to the caller",
                'get_filename_component(PACKAGE_PREFIX "${CMAKE_CURRENT_LIST_FILE}" PATH)\n'
                'get_filename_component(PACKAGE_PREFIX "${PACKAGE_PREFIX}" PATH)')
        if not self.is_emscripten() and self.settings.os == 'Windows':
            from_str = self.package_folder.replace('\\', '/')
        else:
            from_str = self.package_folder
        tools.replace_in_file(path, from_str, '${PACKAGE_PREFIX}')

    def package(self):
        self.copy(pattern="leptonica-license.txt", dst="licenses", src=self.source_subfolder)
        #self.copy(pattern="*.dll", dst="bin", keep_path=False)
        #self.copy(pattern="*.lib", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
