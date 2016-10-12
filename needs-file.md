---
layout: default
title: Needs File
---
{{ page.title }}
==

The needs file is the thing that defines what your needs are. It can be defined as either a JSON or YAML file. YAML is generally preferred as it's less prone to stray comma errors and is much easier to use with <a href="{{ '/jinja-templating' | prepend: site.github.url }}">Jinja templating</a>, but it does require the [pyyaml](http://pyyaml.org/wiki/PyYAML) Python module to be installed. JSON works with no additional Python modules installed, so may be preferable if you have simple needs and don't want to require users to install anything.

The examples here will use YAML, but both JSON and YAML use all of the same configuration parameters.

The most basic of needs files looks something like this:

```yaml
libraries:
    catch:
        repository: git@github.com:philsquared/Catch.git
        commit: v1.3.0
```

This should go into a file named *needs.yaml*. In this example, we're starting off by declaring a dependency on Catch, a unit testing framework. If you invoke `needy satisfy` from the directory with this file, Needy will download and build [Catch](https://github.com/philsquared/Catch).

You can find example configurations for more libraries in the functional tests (look in *tests/functional*).

Using the Output
--

When needy builds a library, it will put the build products into a *needs* directory alongside the needs file. This directory should not be committed to version control (Add it to your *.gitignore* if you're using Git.). The layout of this directory looks something like this:

```
- needs
  - catch
    - build
      - osx
        - x86_64
          + include
          + lib
    + source
  needs.yaml
```

The exact path to the output depends on your target, but the build directory *always* contains *include* and *lib* directories containing the headers you should include and the libraries you might want to link to.

The easiest way to add these *include* and *lib* directories to your path is via the `needy cflags` and `needy ldflags` commands. Passing the output of those commands as compiler and linker arguments will add all of the header and library output to your search paths, and all you'll need to do is add `-l` flags if necessary.

Universal Binaries
--

If you need a universal binary, you can specify it like so:

```yaml
universal-binaries:
    iphoneos:
        ios:
            - armv7
            - arm64
```

Then, you can build it via `needy satisfy -u iphoneos`. Needy will build each library for each target individually, merge the binaries into fat binaries, and create a set of universal headers for you to use.

The output is used in the same way as for individual architectures.

Available Configuration Parameters
--

These are the parameters that can be specified in your needs file.

### Top Level

* `libraries` - A dictionary of library dependencies. The keys of this dictionary are arbitrary names used to identify the libraries. The values are dictionares of library configurations.
* `universal-binaries` - A dictionary of universal binaries to build. The keys of this dictionary are arbitrary names used to identify the universal binaries. The values are dictionaries where the keys are platform identifiers and the values are lists of architectures.

### Library

* `repository` - The repository URI to checkout the library from. Currently only Git repositories are supported.
* `commit` - If a repository is given, you must provide a commit to use. This can be a branch, commit hash, tag, etc.
* `download` - The URI of a zip file or tarball to download the library from.
* `checksum` - If a download is given, you must provide a checksum to verify the download. This can currently be an MD5 or SHA1 hash.
* `directory` - The location on disk to use for the library. This has applications when using dependencies that you're also developing, but should otherwise be avoided.
* `dependencies` - A list of library dependencies. Libraries listed here will always be built before this one.
* `build-directory-suffix` - A suffix to apply to the build directory. For example, if you have debug and release variants, you may wish to build them in differently locations, so both can be present simultaneously.
* `project` - A dictionary of project configuration parameters.

### Project

The project configuration describes how the library is built.

* `type` - The type of project. When omitted, Needy will do its best to determine this based on the project source and the parameters you specify. If you want to force a specific type of project, you can use one of the following values: 'androidmk', 'autotools', 'boostbuild', 'cmake', 'custom', 'make', 'source', 'xcode'.
* `environment` - A dictionary of environment variable overrides. In addition to the formatting parameters listed below, receives a `current` parameter with the current value of the environment variable.
* `root` - The directory to build.
* `post-clean` - A list of commands to execute after cleaning the project directory.
* `configure-steps` - A list of commands used to configure the project. This overrides the default behavior for the project type.
* `pre-build` - A list of commands to execute before building.
* `post-build` - A list of commands to execute after building.

Projects that are header-only or built from source use the following parameters:

* `header-directory` - The directory of header files to be included in builds.
* `source-directory` - The directory of source files to compile into a library.

Projects that are built with Make use the following parameters:

* `make-prefix-arg` - The name of the argument that the makefile uses to determine the output directory (e.g. 'INSTALL_PREFIX').
* `make-targets` - A list of make targets to build.

Projects that are built using Autotools use the following parameters:

* `configure-args` - Additional arguments to be passed to the configure script.
* `make-targets` - A list of make targets to build.

Projects that are built using Boost.Build use the following parameters:

* `bootstrap-args` - Additional arguments to be given to the Boost.Build bootstrap script.
* `b2-args` - Additional arguments to be given to Boost.Build.

Projects that are built using CMake use the following parameters:

* `cmake-options` - Options to be given to CMake.

Projects that are built using MSBuild use the following parameters:

* `msbuild-project` - The Visual Studio project or solution to use.
* `msbuild-properties` - The properties to set or override for the project.
* `header-directory` - If no include directory is created by the project, Needy will copy headers from this directory.

Projects that are built using Xcode use the following parameters:

* `xcode-project` - The Xcode project to use.
* `xcode-scheme` - The Xcode scheme to use.
* `xcode-target` - The Xcode target to use.

Projects that are built using custom steps defined by the needs file use the following parameters:

* `build-steps` - A list of commands used to build the project. The commands should place headers in *{build_directory}/include* and libraries in *{build_directory}/lib*.

String values are formatted with the following parameters:

* `build_directory` - The directory in where build products should go. It is the one that the *include* and *lib* directories are in.
* `platform` - The identifier of the platform being built. For example, 'osx'.
* `architecture` - The architecture being built. For example, 'x86_64'.
* `needs_file_directory` - The directory that contains the needs file.
* `build_concurrency` - The number of parallel processes desired.

This means you may need to escape curly braces in your strings (see [the Python format string documentation](https://docs.python.org/2/library/string.html#formatstrings)).
