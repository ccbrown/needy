from ..generator import Generator

import os
import sys


class JamfileGenerator(Generator):
    @staticmethod
    def identifier():
        return 'jamfile'

    def generate(self, needy):
        path = os.path.join(needy.needs_directory(), 'Jamfile')
        contents = """import feature ;
import toolset ;

path-constant NEEDY : %s ;
path-constant BASE_DIR : %s ;
path-constant NEEDS_FILE : %s ;

feature.feature needyargs : : free ;
toolset.flags $(__name__).satisfy-lib NEEDYARGS <needyargs> ;

rule needlib ( name : extra-sources * : requirements * : default-build * : usage-requirements * )
{
    local target = $(name) ;
    
    if <target-os>iphone in $(requirements) {
        if <architecture>arm in $(requirements) {
            target = "$(name) -u iphone" ;
        } else {
            target = "$(name) -u iphonesim" ;
        }
    } else if <target-os>android in $(requirements) {
        target = "$(name) -t android:armv7" ;
    } else if <target-os>appletv in $(requirements) {
        if <architecture>arm in $(requirements) {
            target = "$(name) -t appletv:arm64" ;
        } else {
            target = "$(name) -t appletvsim" ;
        }
    }

    local args = $(target) %s ;
    local builddir = [ SHELL "cd $(BASE_DIR) && $(NEEDY) builddir $(target)" ] ;
    local includedir = "$(builddir)/include" ;
    
    make lib$(name).touch : $(NEEDS_FILE) : @satisfy-lib : $(requirements) <needyargs>$(args) ;
    actions satisfy-lib
    {
        cd $(BASE_DIR) && $(NEEDY) satisfy $(NEEDYARGS) && cd - && touch $(<)
    }

    alias $(name)
        : $(extra-sources) 
        : $(requirements) 
        : $(default-build) 
        : <dependency>lib$(name).touch
          <include>$(includedir)
          <linkflags>-L$(builddir)/lib
          $(usage-requirements)
    ;
}
""" % (os.path.abspath(sys.argv[0]), os.path.dirname(needy.path()), needy.path(), needy.parameters().satisfy_args)

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
