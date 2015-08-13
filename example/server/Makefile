all: server

NEEDY ?= ../../scripts/needy

needs: needs.json
	$(NEEDY) satisfy
    
server: needs main.cpp
	$(CXX) main.cpp -o server `$(NEEDY) cflags` `$(NEEDY) ldflags` -luv