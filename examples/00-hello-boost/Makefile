NEEDY = $(realpath $(shell dirname $(lastword $(MAKEFILE_LIST)))/../../scripts/needy)

.PHONY: all host iphone clean

all: host
host: build/host/hello-boost
iphone: build/iphone/hello-boost

build/host/hello-boost: needs.json hello-boost.cpp
	$(NEEDY) satisfy
	mkdir -p $(shell dirname $@)
	$(CXX) hello-boost.cpp -o $@ `$(NEEDY) cflags` `$(NEEDY) ldflags` -lboost_program_options

NEEDY_IPHONE_FLAGS = -t ios:arm64
build/iphone/hello-boost: needs.json hello-boost.cpp
	$(NEEDY) satisfy $(NEEDY_IPHONE_FLAGS)
	mkdir -p $(shell dirname $@)
	xcrun -sdk iphoneos clang++ -arch arm64 -stdlib=libstdc++ hello-boost.cpp -o $@ `$(NEEDY) cflags $(NEEDY_IPHONE_FLAGS)` `$(NEEDY) ldflags $(NEEDY_IPHONE_FLAGS)` -lboost_program_options

clean:
	rm -rf build
	rm -rf needs
