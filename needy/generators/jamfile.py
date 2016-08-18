from ..generator import Generator
from ..library import Library
from ..platform import available_platforms, host_platform
from ..target import Target

import hashlib
import os
import sys


class JamfileGenerator(Generator):

    @staticmethod
    def identifier():
        return 'jamfile'

    def generate(self, needy):
        path = os.path.join(needy.needs_directory(), 'Jamfile')
        targets = {
            'host': Target(needy.platform('host')),
            'ios': Target(needy.platform('ios')) if 'ios' in available_platforms() else 'unavailable',
            'iossimulator': Target(needy.platform('iossimulator')) if 'iossimulator' in available_platforms() else 'unavailable',
            'android': Target(needy.platform('android')) if 'android' in available_platforms() else 'unavailable',
            'tvos': Target(needy.platform('tvos')) if 'tvos' in available_platforms() else 'unavailable',
            'tvossimulator': Target(needy.platform('tvossimulator')) if 'tvossimulator' in available_platforms() else 'unavailable',
        }

        needs_configuration = needy.needs_configuration()
        if 'universal-binaries' in needs_configuration:
            for name, configuration in needs_configuration['universal-binaries'].items():
                for platform, architectures in configuration.items():
                    targets[platform] = name

        if host_platform().identifier() in targets:
            targets['host'] = targets[host_platform().identifier()]

        contents = """import feature ;
import modules ;
import notfile ;
import toolset ;

OS = [ modules.peek : OS ] ;

path-constant NEEDY : {needy} ;
path-constant BASE_DIR : {base_dir} ;
path-constant NEEDS_FILE : {needs_file} ;

constant PREFIX : [ option.get prefix : "/usr/local" ] ;

feature.feature needy_args_{feature_suffix} : : free ;
toolset.flags satisfy-lib NEEDY_ARGS <needy_args_{feature_suffix}> ;

feature.feature build_dir_{feature_suffix} : : free ;
toolset.flags install-lib BUILD_DIR <build_dir_{feature_suffix}> ;

rule needlib-common ( name : libname )
{{
    local dev-mode-files = [ SPLIT_BY_CHARACTERS [ SHELL "cd $(BASE_DIR) && $(NEEDY) dev-mode $(libname) --query && find `$(NEEDY) sourcedir $(libname)` -type f -not -path '*/\.*' 2> /dev/null" ] : "\\n" ] ;
    alias $(name) : $(dev-mode-files) ;
}}

rule needlib ( name : build-dir : target-args : extra-sources * : requirements * : default-build * : usage-requirements * )
{{
    local args = "$(name) $(target-args) {satisfy_args}" ;
    local includedir = "$(build-dir)/include" ;

    make lib$(name)-{build_compatibility}.touch : $(NEEDS_FILE) $(name)-common : @satisfy-lib : $(requirements) <needy_args_{feature_suffix}>$(args) ;
    actions satisfy-lib {{
        cd $(BASE_DIR) && $(NEEDY) satisfy $(NEEDY_ARGS) && cd - && touch $(<)
    }}

    alias $(name)
        : $(extra-sources)
        : $(requirements)
        : $(default-build)
        : <dependency>lib$(name)-{build_compatibility}.touch
          <include>$(includedir)
          <linkflags>-L$(build-dir)/lib
          $(usage-requirements)
    ;

    notfile install-$(name) : @install-lib : $(name) : $(requirements) <build_dir_{feature_suffix}>$(build-dir) ;
    actions install-lib {{
        mkdir -p $(PREFIX) && cp -pR $(BUILD_DIR)/* $(PREFIX)/ && rm -f $(PREFIX)/needy.status
    }}
    explicit install-$(name) ;
}}
""".format(needy=os.path.abspath(sys.argv[0]),
           base_dir=needy.path(),
           needs_file=needy.needs_file(),
           satisfy_args=needy.parameters().satisfy_args,
           feature_suffix='_'+hashlib.sha1(needy.path() if isinstance(needy.path(), bytes) else needy.path().encode('utf-8')).hexdigest(),
           build_compatibility=Library.build_compatibility()
           )

        libraries_with_common_targets = set()

        contents += "\n" + self.__target_definitions(needy, targets['host'], libraries_with_common_targets)

        if 'ios' in available_platforms():
            contents += "\n" + self.__target_definitions(needy, targets['ios'], libraries_with_common_targets, '<target-os>iphone <architecture>arm')

        if 'iossimulator' in available_platforms():
            contents += "\n" + self.__target_definitions(needy, targets['iossimulator'], libraries_with_common_targets, '<target-os>iphone <architecture>x86')

        if 'android' in available_platforms():
            contents += "\n" + self.__target_definitions(needy, targets['android'], libraries_with_common_targets, '<target-os>android')

        if 'tvos' in available_platforms():
            contents += "\n" + self.__target_definitions(needy, targets['tvos'], libraries_with_common_targets, '<target-os>appletv <architecture>arm')

        if 'tvossimulator' in available_platforms():
            contents += "\n" + self.__target_definitions(needy, targets['tvossimulator'], libraries_with_common_targets, '<target-os>appletv <architecture>x86')

        with open(path, 'w') as jamfile:
            jamfile.write(contents)

    @staticmethod
    def __target_definitions(needy, needy_target_or_universal_binary, libraries_with_common_targets, requirements=''):
        ret = ''
        target_args = ('-t {}' if isinstance(needy_target_or_universal_binary, Target) else '-u {}').format(needy_target_or_universal_binary)
        for name, library in needy.libraries(needy_target_or_universal_binary).items():
            if name not in libraries_with_common_targets:
                ret += "needlib-common {0}-common : {0} ;\n".format(name)
                libraries_with_common_targets.add(name)
            ret += "needlib {} : {} : \"{}\" : : {} ;\n".format(name, needy.build_directory(name, needy_target_or_universal_binary), target_args, requirements)
        return ret
