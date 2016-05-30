from ..generator import Generator
from ..platform import available_platforms
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
        target_args = {
            'ios': '-t ios',
            'iossimulator': '-t iossimulator',
            'tvos': '-t tvos',
            'tvossimulator': '-t tvossimulator',
            'osx': '-t osx',
        }

        needs_configuration = needy.needs_configuration()
        if 'universal-binaries' in needs_configuration:
            for name, configuration in needs_configuration['universal-binaries'].items():
                for platform, architectures in configuration.items():
                    target_args[platform] = '-u ' + name

        contents = """import feature ;
import modules ;
import toolset ;

OS = [ modules.peek : OS ] ;

path-constant NEEDY : {needy} ;
path-constant BASE_DIR : {base_dir} ;
path-constant NEEDS_FILE : {needs_file} ;

feature.feature {needy_args_feature} : : free ;
toolset.flags satisfy-lib NEEDYARGS <{needy_args_feature}> ;

rule needlib ( name : extra-sources * : requirements * : default-build * : usage-requirements * )
{{
    local target = $(name) ;
    if <target-os>iphone in $(requirements) {{
        if <architecture>arm in $(requirements) {{
            target = "$(name) {ios}" ;
        }} else {{
            target = "$(name) {iossimulator}" ;
        }}
    }} else if <target-os>android in $(requirements) {{
        target = "$(name) -t android" ;
    }} else if <target-os>appletv in $(requirements) {{
        if <architecture>arm in $(requirements) {{
            target = "$(name) {tvos}" ;
        }} else {{
            target = "$(name) {tvossimulator}" ;
        }}
    }} else if $(OS) = MACOSX {{
        target = "$(name) {osx}" ;
    }}

    local args = $(target) {satisfy_args} ;
    local builddir = [ SHELL "cd $(BASE_DIR) && $(NEEDY) builddir $(target)" ] ;
    local sourcedir = [ SHELL "cd $(BASE_DIR) && $(NEEDY) sourcedir $(name)" ] ;
    local includedir = "$(builddir)/include" ;
    local files = [ SPLIT_BY_CHARACTERS [ SHELL "find $(sourcedir) -type f -not -path '*/\\.*' 2> /dev/null" ] : "\\n" ] ;

    make lib$(name).touch : $(NEEDS_FILE) $(files) : @satisfy-lib : $(requirements) <{needy_args_feature}>$(args) ;
    actions satisfy-lib
    {{
        cd $(BASE_DIR) && $(NEEDY) satisfy $(NEEDYARGS) && cd - && touch $(<)
    }}

    alias $(name)
        : $(extra-sources)
        : $(requirements)
        : $(default-build)
        : <dependency>lib$(name).touch
          <include>$(includedir)
          <linkflags>-L$(builddir)/lib
          $(usage-requirements)
    ;
}}
""".format(needy=os.path.abspath(sys.argv[0]),
           base_dir=needy.path(),
           needs_file=needy.needs_file(),
           satisfy_args=needy.parameters().satisfy_args,
           needy_args_feature='needyargs_'+hashlib.sha1(needy.path() if isinstance(needy.path(), bytes) else needy.path().encode('utf-8')).hexdigest(),
           **target_args)

        contents += "\n"
        for library in needy.libraries_to_build(Target(needy.platform('host'))):
            contents += "needlib {0} ;\n".format(library[0])

        if 'ios' in available_platforms():
            contents += "\n"
            for library in needy.libraries_to_build(Target(needy.platform('ios'))):
                contents += "needlib {0} : : <target-os>iphone <architecture>arm ;\n".format(library[0])

        if 'iossimulator' in available_platforms():
            contents += "\n"
            for library in needy.libraries_to_build(Target(needy.platform('iossimulator'))):
                contents += "needlib {0} : : <target-os>iphone <architecture>x86 ;\n".format(library[0])

        if 'android' in available_platforms():
            contents += "\n"
            for library in needy.libraries_to_build(Target(needy.platform('android'))):
                contents += "needlib {0} : : <target-os>android ;\n".format(library[0])

        if 'tvos' in available_platforms():
            contents += "\n"
            for library in needy.libraries_to_build(Target(needy.platform('tvos'))):
                contents += "needlib {0} : : <target-os>appletv <architecture>arm ;\n".format(library[0])

        if 'tvossimulator' in available_platforms():
            contents += "\n"
            for library in needy.libraries_to_build(Target(needy.platform('tvossimulator'))):
                contents += "needlib {0} : : <target-os>appletv <architecture>x86 ;\n".format(library[0])

        with open(path, 'w') as jamfile:
            jamfile.write(contents)
