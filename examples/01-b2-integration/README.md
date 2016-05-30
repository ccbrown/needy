B2 Integration
==

Though not widely used outside of the Boost suite of libraries, [Boost.Build](http://www.boost.org/build/) is actually an extremely powerful build system. This example uses the Boost.Build build system and Needy's Jamfile generation to integrate a third-party dependency into a trivial, yet full-featured project structure.

This example requires `b2` to be installed, which you can find [here](https://github.com/boostorg/build/releases).

The Needs File
--

The needs file defines our dependency on cppformat:

```json
{
    "libraries": {
        "cppformat": {
            "repository": "git@github.com:fmtlib/fmt.git",
            "commit": "8650c57ccd6146971d1ee8a68ca8d8f881cfafef"
        }
    }
}
```

Building and Running
--

This project has a two-phase build.

First, run `./configure`. This is a one-line shell script that simply invokes `needy generate jamfile`.

Once you've done that, simply run `b2`. This is another one-liner that defines our executable.

The result is an executable named "b2-integration":

```
cbrown@MacBook-Pro-3:~/Development/needy/examples/b2-integration% ./bin/darwin-4.2.1/debug/b2-ingegration
It worked!```
