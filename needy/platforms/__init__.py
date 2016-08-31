import sys

from .generic import GenericPlatform
from .android import AndroidPlatform
from .osx import OSXPlatform
from .ios import iOSPlatform, iOSSimulatorPlatform
from .tvos import tvOSPlatform, tvOSSimulatorPlatform
from .windows import WindowsPlatform


def available_platforms():
    platforms = [GenericPlatform, AndroidPlatform]

    if sys.platform == 'darwin':
        platforms.extend([
            OSXPlatform,
            iOSPlatform,
            iOSSimulatorPlatform,
            tvOSPlatform,
            tvOSSimulatorPlatform,
        ])
    elif sys.platform == 'win32':
        platforms.append(WindowsPlatform)

    ret = {}
    for platform in platforms:
        ret[platform.identifier()] = platform
    return ret


def host_platform():
    if sys.platform == 'darwin':
        return OSXPlatform
    elif sys.platform == 'win32':
        return WindowsPlatform

    return GenericPlatform
