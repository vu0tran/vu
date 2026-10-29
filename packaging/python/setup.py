"""Builds the Vu library with `vu build --lib` (vu on PATH, or $VU) into the package, so the wheel
holds libfuzzy.so next to __init__.py. The wheel is for this platform only."""
import os
import shutil
import subprocess
import sys
from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.dist import Distribution


class BuildVu(build_py):
    def run(self):
        super().run()
        vu = os.environ.get("VU") or shutil.which("vu")
        if not vu:
            sys.exit("building fuzzy needs Vu's compiler: put vu on PATH or set VU")
        here = os.path.dirname(os.path.abspath(__file__))
        out = os.path.join(self.build_lib, "fuzzy", "libfuzzy.so")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        subprocess.run([vu, "build", "--lib", os.path.join(here, "src", "fuzzy", "fuzzy.vu"), "-o", out], check=True)


class PlatformDist(Distribution):
    def has_ext_modules(self):   # (a wheel for this platform, not "any")
        return True


setup(cmdclass={"build_py": BuildVu}, distclass=PlatformDist)
