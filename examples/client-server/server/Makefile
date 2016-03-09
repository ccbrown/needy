all: server

.PHONY: all needs

NEEDY ?= ../../../scripts/needy

needs: needs.json
	$(NEEDY) satisfy
    
server: needs main.cpp
	$(CXX) -std=c++11 main.cpp -o $@ `$(NEEDY) cflags` `$(NEEDY) ldflags` -luv
	
clean:
	rm -f server
	rm -Rf needs