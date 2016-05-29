Needy [![Build Status](https://travis-ci.org/ccbrown/needy.svg?branch=master)](https://travis-ci.org/ccbrown/needy) [![Documentation](https://img.shields.io/badge/docs-available-brightgreen.svg)](https://ccbrown.github.com/needy) [![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](https://raw.githubusercontent.com/ccbrown/needy/master/LICENSE)
==

Needy is tool that aims to make C++ library dependencies as magical as possible. Dependencies are declared in a file called known as the "needs file", usually by simply adding a source URI. Then Needy will download and build those dependencies for you.

For example, by creating a *needs.yaml* file in your project that looks like this:

```yaml
libraries:
    catch:
        repository: git@github.com:philsquared/Catch.git
        commit: v1.3.0
```

You can then use a simple command invocation (`needy satisfy`) to download and build [Catch](https://github.com/philsquared/Catch) for your target platforms. Once integrated with your build system, adding, updating, or modifying dependencies in any way becomes a trivial matter.

Needy is extremely capable, so be sure to check out the examples directory or [the documentation](https://ccbrown.github.com/needy) to see some more things you can do.
