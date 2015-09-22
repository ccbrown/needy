`needy` is tool that aims to make library dependencies as magical as possible. Dependencies are declared in a file called "needs.json", usually by simply adding a download URL and checksum. Then `needy` will download and build those dependencies for you, for iOS, Android, or your host system.

To run without installing, you can use `scripts/needy`. To install, you can run `sudo setup.py install`. After installing, you can invoke needy via simply `needy`. To uninstall, you can use `sudo pip uninstall needy`.

It's in pretty early stages though, so expect bugs and incomplete features. It also isn't yet versioned and is constantly breaking backwards compatibility, so if you use it, it's recommended that you include it with your distribution.
