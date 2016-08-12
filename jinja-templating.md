---
layout: default
title: Jinja Templating
---
{{ page.title }}
==

If you have the [Jinja2](http://jinja.pocoo.org) Python module installed, you can use Jinja templating in your needs files to give them super powers.

This is most frequently used for platform-specific configuration:

{% raw %}
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
{% endraw %}

Variables
--

* `platform` - The identifier of the platform being built. For example, 'osx'.
* `architecture` - The architecture being built.
* `host_platform` - The identifier of the host platform.
* `needs_file` - The path of the needs file.
* `env` - A map of environment variables.

### User-Defined Variables

You can also define your own variables via the command line:

* `needy satisfy -Dmyvariable=something`

Functions
--

* `build_directory` - Takes a library name as a parameter and returns the library's build directory.

Filters
--

* `dirname` - Gives the parent directory of the given path.

Render Passes
--

### Satisfy

When needs are satisfied, the needs file is rendered before each build with all of the above variables.

### Universal Binaries

When univeral binaries are used, the needs file is rendered before anything else is done in order to get the universal binary configuration. Therefore the needs file must *always* render with a complete `universal-binaries` dictionary.

The `platform` and `architecture` variables are not available for this render pass.
