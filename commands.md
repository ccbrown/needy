---
layout: default
title: Commands
---
{{ page.title }}
==

This is an overview of the commands available. You should also see the authoritative source for more: `need --help`.

satisfy
--

Satisfies your needs. This builds the specified libraries for the specified targets.

Example:

<pre class="highlight"><code>cbrown@mbp:~/example% <span class="green">./needy/scripts/needy</span> satisfy smaz
Satisfying needs in /Users/cbrown/example
<span class="cyan">[OUT-OF-DATE]</span> smaz
Building for osx x86_64
mkdir -p /Users/cbrown/example/needs/smaz/build/osx/x86_64/include /Users/cbrown/example/needs/smaz/build/osx/x86_64/lib
c++ -c smaz.c -o smaz.o
ar -rc /Users/cbrown/example/needs/smaz/build/osx/x86_64/lib/libsmaz.a smaz.o
cp smaz.h /Users/cbrown/example/needs/smaz/build/osx/x86_64/include/smaz.h
<span class="green">[SUCCESS]</span> smaz</code></pre>

cflags
--

Provides the flags necessary to add the header paths to your compilation.

Example:

<pre class="highlight"><code>cbrown@mbp:~/example% <span class="green">./needy/scripts/needy</span> cflags
-I/Users/cbrown/example/needs/smaz/build/osx/x86_64/include</code></pre>

ldflags
--

Provides the flags necessary to add the library paths to your linking.

Example:

<pre class="highlight"><code>cbrown@mbp:~/example% <span class="green">./needy/scripts/needy</span> ldflags
-L/Users/cbrown/example/needs/smaz/build/osx/x86_64/lib</code></pre>

builddir
--

Provides the build directory for the given library.

Example:

<pre class="highlight"><code>cbrown@mbp:~/example% <span class="green">./needy/scripts/needy</span> builddir smaz
/Users/cbrown/example/needs/smaz/build/osx/x86_64</code></pre>

generate
--

Generates helpful files.

Example:

<pre class="highlight"><code>cbrown@mbp:~/example% <span class="green">./needy/scripts/needy</span> generate jamfile</code></pre>

This example places a Jamfile in the needs directory with targets that can be used to integrate with Boost.Build systems.
