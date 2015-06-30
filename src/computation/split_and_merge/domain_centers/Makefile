CFLAGS = -O3 
UNAME := $(shell uname -s)

ifeq ($(UNAME), Darwin) 
	INCLUDES = -I/usr/local/include/python2.7 
	LIBS = -L/usr/local/Library/Frameworks/Python.framework/Versions/2.7/lib/ -lpython2.7
else
	INCLUDES = -I/usr/local/include/python2.7
        LIBS = -lpython2.7
endif

all: calculate_domain_centers.so
	

calculate_domain_centers.so: calculate_domain_centers.o
	$(CC) -shared -o $@ $^ $(LIBS)

calculate_domain_centers.o: calculate_domain_centers.c
	$(CC) -fPIC -c $(CFLAGS) $(INCLUDES) -o $@ $<

clean:
	rm -rf *.o *.so
	rm -f *.pyc *.pyo

