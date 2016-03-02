from ..generator import Generator

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

        if 'universal-binaries' in needy.needs:
            for universal_binary in needy.needs['universal-binaries']:
                configuration = needy.needs['universal-binaries'][universal_binary]
                for platform, architectures in configuration.iteritems():
                    target_args[platform] = '-u ' + universal_binary

        contents = """import feature ;
import modules ;
import toolset ;

OS = [ modules.peek : OS ] ;

path-constant NEEDY : {needy} ;
path-constant BASE_DIR : {base_dir} ;
path-constant NEEDS_FILE : {needs_file} ;

feature.feature needyargs : : free ;
toolset.flags $(__name__).satisfy-lib NEEDYARGS <needyargs> ;

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
        target = "$(name) -t android:armv7" ;
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
    local includedir = "$(builddir)/include" ;

    make lib$(name).touch : $(NEEDS_FILE) : @satisfy-lib : $(requirements) <needyargs>$(args) ;
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
""".format(
    needy=os.path.abspath(sys.argv[0]),
    base_dir=needy.path(),
    needs_file=os.path.join(needy.path(), 'needs.json'),
    satisfy_args=needy.parameters().satisfy_args,
    **target_args)

        for library in needy.libraries_to_build():
            contents += """
needlib {0} ;
needlib {0} : : <target-os>iphone <architecture>arm ;
needlib {0} : : <target-os>iphone <architecture>x86 ;
needlib {0} : : <target-os>android ;
needlib {0} : : <target-os>appletv <architecture>arm ;
needlib {0} : : <target-os>appletv <architecture>x86 ;
""".format(library[0])

        with open(path, 'w') as jamfile:
            jamfile.write(contents)
