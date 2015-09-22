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

rule needlib ( name : extra-sources * : requirements * : default-build * : usage-requirements * )
{
    local builddir = [ SHELL "cd $(BASE_DIR) && $(NEEDY) builddir $(name)" ] ;

    feature.feature needyargs : : free ;
    toolset.flags $(__name__).satisfy-lib NEEDYARGS <needyargs> ;

    make lib$(name).touch : $(NEEDS_FILE) : @satisfy-lib : <needyargs>$(name) ;
    actions satisfy-lib
    {
        cd $(BASE_DIR) && $(NEEDY) satisfy $(NEEDYARGS)
    }

    alias $(name)
        : $(extra-sources) 
        : $(requirements) 
        : $(default-build) 
        : <dependency>lib$(name).touch
          <include>$(builddir)/include
          <linkflags>-L$(builddir)/lib
          $(usage-requirements)
    ;
}

""" % (os.path.abspath(sys.argv[0]), os.path.dirname(needy.path()), needy.path())

        for library in needy.libraries_to_build():
            contents += 'needlib {} ;\n'.format(library[0])

        with open(path, 'w') as jamfile:
            jamfile.write(contents)
