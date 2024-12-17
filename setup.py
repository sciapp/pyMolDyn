import os
import platform

import gr
import numpy as np
from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext as build_ext_orig


# Modified version of <https://stackoverflow.com/a/34830639/5958465>
class build_ext(build_ext_orig):
    def get_export_symbols(self, ext):
        # For CTypes extensions, do not require to export a `PyInit_` function
        if isinstance(ext, CTypes):
            return ext.export_symbols
        return super().get_export_symbols(ext)

    def get_ext_filename(self, fullname):
        # For CTypes extensions, force to use the default system prefix and extension for shared libraries.
        # This avoids file extensions like `.cpython-312-x86_64-linux-gnu.so`.
        if isinstance(self.ext_map[fullname], CTypes):
            shared_lib_prefix = {
                "Windows": "",
            }.get(platform.system(), "lib")
            shared_lib_ext = {
                "Darwin": ".dylib",
                "Windows": ".dll",
            }.get(platform.system(), ".so")
            fullname_components = fullname.split(".")
            ext_fullname = "".join(
                (
                    (
                        os.path.join(*fullname_components[:-1]),
                        os.path.sep,
                    )
                    if len(fullname_components) > 1
                    else tuple()
                )
                + (
                    shared_lib_prefix,
                    fullname_components[-1],
                    shared_lib_ext,
                )
            )
            return ext_fullname
        return super().get_ext_filename(fullname)


class CTypes(Extension):
    pass


gr_dir = os.path.dirname(os.path.dirname(gr.__gr._name))

setup(
    cmdclass={"build_ext": build_ext},
    ext_modules=[
        Extension(
            name="pymoldyn.computation.split_and_merge.util.numpy_extension.find_index_of_first_element_not_equivalent",
            sources=[
                "pymoldyn/computation/split_and_merge/util/numpy_extension/find_index_of_first_element_not_equivalent.c"
            ],
            include_dirs=[np.get_include()],
        ),
        Extension(
            name="pymoldyn.computation.split_and_merge.domain_centers.calculate_domain_centers",
            sources=["pymoldyn/computation/split_and_merge/domain_centers/calculate_domain_centers.c"],
            include_dirs=[np.get_include()],
        ),
        CTypes(
            name="pymoldyn.core.calculation.extension.algorithm",
            sources=["pymoldyn/core/calculation/extension/algorithm.c"],
            include_dirs=[os.path.join(gr_dir, "include")],
            library_dirs=[os.path.join(gr_dir, "lib")],
            libraries=["libGR3" if platform.system() == "Windows" else "GR3"],
        ),
    ],
)
