import os
from pyfakefs import fake_filesystem_unittest

from needy.platform import host_platform
from needy.project import Project, ProjectDefinition
from needy.target import Target


class ProjectTest(fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_pre_build_creating_output_directories(self):
        project = Project(ProjectDefinition(Target(host_platform()()), '.'), None)
        project.pre_build(os.path.join('build', 'out'))
        self.assertTrue(os.path.isdir(os.path.join('build', 'out', 'include')))
        self.assertTrue(os.path.isdir(os.path.join('build', 'out', 'lib')))
