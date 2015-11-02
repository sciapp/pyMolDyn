CFLAGS = -O3 
UNAME := $(shell uname -s)
INCLUDES := $(shell ./build-flags --include-flags python numpy)
ifeq ($(PYLIBPATH),)
	LIBS := $(shell ./build-flags --lib-flags python numpy)
else
	LIBS = -L$(PYLIBPATH) -lpython2.7
endif


all: find_index_of_first_element_not_equivalentmodule.so
	

find_index_of_first_element_not_equivalentmodule.so: find_index_of_first_element_not_equivalent.o
	$(CC) -shared -o $@ $^ $(LIBS)

find_index_of_first_element_not_equivalent.o: find_index_of_first_element_not_equivalent.c
	$(CC) -fPIC -c $(CFLAGS) $(INCLUDES) -o $@ $<

clean:
	rm -rf *.o *.so

