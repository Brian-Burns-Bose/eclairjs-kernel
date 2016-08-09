import sys
import os
import json

from setuptools import setup
from distutils import log
from distutils.command.install import install

kernel_json = {
    "name": "eclair",
    "display_name": "Spark 2.0 (EclairJS Kernel)",
    "language": "javascript",
    "argv": [
        sys.executable,
        "-m", "eclairjskernel",
        "-f",
        "{connection_file}"
    ],
    "env": {
        "ECLAIRJS_NASHORN_JAR": os.environ['ECLAIRJS_NASHORN_JAR'],
        "SPARK_HOME": os.environ['SPARK_HOME']
    }
}

svem_flag = '--single-version-externally-managed'
if svem_flag in sys.argv:
    # Die, setuptools, die.
    sys.argv.remove(svem_flag)
            
class install_with_kernelspec(install):

    def run(self):
        install.run(self)
        user = '--user' in sys.argv
        try:
            from ipykernel.kerspec import install_kernel_spec
        except ImportError:
            from IPython.kernel.kernelspec import install_kernel_spec
        from IPython.utils.tempdir import TemporaryDirectory
        with TemporaryDirectory() as td:
            os.chmod(td, 0o755)  # Starts off as 700, not user readable
            with open(os.path.join(td, 'kernel.json'), 'w') as f:
                json.dump(kernel_json, f, sort_keys=True)
            log.info('Installing kernel spec')
            kernel_name = kernel_json['name']
            try:
                install_kernel_spec(td, kernel_name, user=user,
                                    replace=True)
            except:
                install_kernel_spec(td, kernel_name, user=not user,
                                    replace=True)


setup(name='eclairjs-kernel',
      version='0.1',
      description='jupyter kernel for eclairjs',
      url='https://github.com/bpburns/eclairjs-kernel',
      author='Brian Burns',
      author_email='brian.p.burns@gmail.com',
      license='Apache 2',
      install_requires=["IPython >= 4.0", "ipykernel", "metakernel", "py4j"],
      cmdclass={'install': install_with_kernelspec},
      packages=['eclairjskernel']
)
