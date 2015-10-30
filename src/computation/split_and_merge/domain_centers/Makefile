CFLAGS = -O3 
UNAME := $(shell uname -s)
INCLUDES := $(shell ./build-flags --include-flags python)
ifeq ($(PYLIBPATH),)
	LIBS := $(shell ./build-flags --lib-flags python)
else
	LIBS = -L$(PYLIBPATH) -lpython2.7
endif


all: calculate_domain_centers.so
	

calculate_domain_centers.so: calculate_domain_centers.o
	$(CC) -shared -o $@ $^ $(LIBS)

calculate_domain_centers.o: calculate_domain_centers.c
	$(CC) -fPIC -c $(CFLAGS) $(INCLUDES) -o $@ $<

clean:
	rm -rf *.o *.so
	rm -f *.pyc *.pyo

