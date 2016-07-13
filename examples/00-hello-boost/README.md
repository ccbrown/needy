Hello, Boost!
==

It can be a real pain to integrate Boost into some projects. This example introduces you to Needy by building an executable that uses Boost and compiles for multiple platforms.

This example requires `make` to be installed, and some patience as Boost is not a small library.

The Needs File
--

The needs file contains a simple structure that defines our dependency on Boost:

```json
{
    "libraries": {
        "boost": {
            "download": "http://downloads.sourceforge.net/project/boost/boost/1.59.0/boost_1_59_0.tar.bz2",
            "checksum": "b94de47108b2cdb0f931833a7a9834c2dd3ca46e",
            "project": {
                "b2-args": ["--with-program_options", "link=static"]
            }
        }
    }
}
```

The `download` and `checksum` parameters define the source that we get Boost from.

The `project` structure defines the method for building Boost. In many cases, this isn't necessary, but we want to specify some b2 arguments to optimize the build.

Building and Running
--

To compile for the host platform, simply run `make`.

The result is an executable named "hello-boost":

```
cbrown@MacBook-Pro-3:~/Development/needy/examples/hello-boost% ./build/host/hello-boost
the option '--name' is required but missing
cbrown@MacBook-Pro-3:~/Development/needy/examples/hello-boost% ./build/host/hello-boost --name Chris
Hello, Chris!
```

To demonstrate compilation for other platforms, you can use `make iphone` to compile for iPhone. Running an executable on an iPhone is up for you to figure out, but you can at least verify that everything was built for the correct architecture via `lipo -i build/iphone/hello-boost`.

To compile for Apple TV or Android, you can pretty trivially add them to the Makefile as well.
