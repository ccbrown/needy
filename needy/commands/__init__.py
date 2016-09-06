import importlib


def available_commands():
    commands = [getattr(importlib.import_module(cmd[0], package=__name__), cmd[1])() for cmd in [
        ('.builddir', 'BuildDirCommand'),
        ('.cflags', 'CFlagsCommand'),
        ('.dev', 'DevCommand'),
        ('.exec', 'ExecCommand'),
        ('.generate', 'GenerateCommand'),
        ('.init', 'InitCommand'),
        ('.ldflags', 'LDFlagsCommand'),
        ('.pkg_config_path', 'PkgConfigPathCommand'),
        ('.satisfy', 'SatisfyCommand'),
        ('.sourcedir', 'SourceDirCommand'),
        ('.status', 'StatusCommand'),
    ]]
    return {command.name(): command for command in commands}
