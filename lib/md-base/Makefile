INCLUDES=$(shell find . -type d | sed "s/^/-I/" | sed "s/$$/\//")
SRCS=$(shell find . -type f ! -iname ".*" | grep "\.c$$")
OBJS=$(shell find . -type f ! -iname ".*" | grep "\.c$$" | sed "s/\.c$$/.o/")
TARGET=libmd-base.a
CC=gcc
CFLAGS=-O0 -Wall -Wextra -pedantic-errors -std=c89 -DDEBUG -g -fopenmp -DMD_BASE_USE_OMP

all: ${TARGET} cleanup

-include dependencies.mk

.c.o:
	${CC} $< -c ${INCLUDES} ${CFLAGS} -o $@
	
${TARGET}: ${OBJS}
	ar rcs ${TARGET} ${OBJS}

dependencies.mk:
	${CC} -MM ${SRCS} ${INCLUDES} ${CFLAGS} > dependencies.mk

cleanup:
	rm -f dependencies.mk

clean:
	rm -f dependencies.mk
	find . -name "*.o" -print0 | xargs -0 rm -f
	rm -f $(TARGET)
