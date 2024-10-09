from setuptools import Extension, setup
import numpy as np


setup(
    ext_modules=[
        Extension(
            name='src.computation.split_and_merge.util.numpy_extension.find_index_of_first_element_not_equivalent',
            sources=['src/computation/split_and_merge/util/numpy_extension/find_index_of_first_element_not_equivalent.c'],
            include_dirs=[np.get_include()],
        ),
        Extension(
            name='src.computation.split_and_merge.domain_centers.calculate_domain_centers',
            sources=['src/computation/split_and_merge/domain_centers/calculate_domain_centers.c'],
            include_dirs=[np.get_include()],
        ),
        Extension(
            name='src.core.calculation.extension.algorithm',
            sources=['src/core/calculation/extension/algorithm.c'],
            include_dirs=['/Users/moll/local/gr/include'],
            library_dirs=['/Users/moll/local/gr/lib'],
            libraries=['gr3', 'gr']
        )
    ]
)
