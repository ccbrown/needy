from .androidmk import AndroidMkProject
from .autotools import AutotoolsProject
from .boostbuild import BoostBuildProject
from .cmake import CMakeProject
from .custom import CustomProject
from .make import MakeProject
from .source import SourceProject
from .xcode import XcodeProject

project_types = [AndroidMkProject, AutotoolsProject, CMakeProject, BoostBuildProject, MakeProject, XcodeProject, SourceProject, CustomProject]
