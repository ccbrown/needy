Needy [![Build Status](https://travis-ci.org/ccbrown/needy.svg?branch=master)](https://travis-ci.org/ccbrown/needy)
==

Needy is tool that aims to make C++ library dependencies as magical as possible. Dependencies are declared in a file called "needs.json", usually by simply adding a download URL and checksum. Then Needy will download and build those dependencies for you, for iOS, TvOS, Android, your host system, or anything possible.

To run without installing, you can use `scripts/needy`. To install, you can run `sudo setup.py install`. After installing, you can invoke needy via simply `needy`. To uninstall, you can use `sudo pip uninstall needy`.

It's in pretty early stages though, so expect bugs and incomplete features. It also isn't yet versioned and is constantly breaking backwards compatibility, so if you use it, it's recommended that you include it with your distribution.

Getting Started
--

The first thing you'll need to do to get started is define your dependencies. This is done via a JSON or YAML file. The specs and capabilities are the same, but you'll probably find YAML easier to work with:

```yaml
libraries:
    catch:
        repository: git@github.com:philsquared/Catch.git
        commit: v1.3.0
```

This should go into a file named *needs.yaml* (or *needs.json* if you use JSON). In this example, we're starting off by declaring a dependency on Catch, a unit testing framework. If you invoke `needy satisfy` from the directory with this file, Needy will download and build [Catch](https://github.com/philsquared/Catch).

From there, you'll need to integrate with your build system. The most flexible way is via the `needy cflags` and `needy ldflags`. Passing the output of those commands as compiler and linker arguments will add all of the header and library output to your search paths, and all you'll need to do is add `-l` flags if necessary.

If you use [Boost.Build](http://www.boost.org/build/), you have another option: `needy generate jamfile` will create a jamfile in the *needs* subdirectory with targets that you can add as dependencies.

Dealing With Libraries That Don't Just Work
--

Sometimes libraries don't work out of the box and need a little coercing. Needy provides ample tools to make any dependency build.

A very common use-case is header-only libraries. Many header-only libraries come with build systems for tests and other optional components. If you're not interested in that stuff, you can provide a little hint to Needy and it'll just copy your headers:

```yaml
libraries:
    gsl:
        repository: git@github.com:Microsoft/GSL.git
        commit: a9f865900d28b854de5ead971aadb82e5ef9ed40
        project:
            header-directory: include
```

There are several other tools available that I'll document later, but if it comes down to it, you can just specify all the build steps yourself:

```yaml
libraries:
    smaz:
        repository: git@github.com:antirez/smaz.git
        commit: 2f625846a775501fb69456567409a8b12f10ea25
        project:
            build-steps:
                - mkdir -p {build_directory}/include {build_directory}/lib
                - c++ -c smaz.c -o smaz.o
                - ar -rc {build_directory}/lib/libsmaz.a smaz.o
                - cp smaz.h {build_directory}/include/smaz.h
```

Universal Binaries
--

One of Needy's strengths is its ability to create universal binaries for libraries that don't officially support them. If you need a universal binary, you can specify them like so:

```yaml
universal-binaries:
    iphoneos:
        ios:
            - armv7
            - arm64
```

Then, you can build for them via `needy satisfy -u iphoneos`. Needy will build each library for each target individually, merge the binaries into fat binaries, and create a set of universal headers for you to use.

Jinja Templating
--

If you have the [Jinja2](http://jinja.pocoo.org/) Python module installed, you can use Jinja templating in your needs files to give them super powers.

This is most frequently used for platform-specific configuration:

```yaml
libraries:
    libjpeg-turbo:
        download: http://downloads.sourceforge.net/project/libjpeg-turbo/1.4.90%20%281.5%20beta1%29/libjpeg-turbo-1.4.90.tar.gz
        checksum: 62af89207d08252a1d8c4997ae50e11f4195ed74
        project:
            {% if platform == 'osx' %}
            configure-args: NASM=nasm
            {% elif platform == 'ios' or platform == 'tvos' %}
            configure-args: CCAS=nasm
            {% elif platform == 'iossimulator' and architecture == 'i386' %}
            configure-args: --host=i686-apple-darwin
            {% elif platform == 'android' %}
            configure-args: CCAS=arm-linux-androideabi-as
            {% endif %}
```
