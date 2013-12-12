CFLAGS = -O3 
UNAME := $(shell uname -s)

ifeq ($(UNAME), Darwin) 
	INCLUDES = -I/usr/local/include/python2.7 -I/usr/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/numpy/core/include 
	LIBS = -L/usr/local/Library/Frameworks/Python.framework/Versions/2.7/lib/ -lpython2.7
else
	INCLUDES = -I/usr/include/python2.7
        LIBS = -lpython2.7
endif

all: find_index_of_first_element_not_equivalentmodule.so
	

find_index_of_first_element_not_equivalentmodule.so: find_index_of_first_element_not_equivalent.o
	$(CC) -shared -o $@ $^ $(LIBS)

find_index_of_first_element_not_equivalent.o: find_index_of_first_element_not_equivalent.c
	$(CC) -fPIC -c $(CFLAGS) $(INCLUDES) -o $@ $<

clean:
	rm -rf *.o *.so

