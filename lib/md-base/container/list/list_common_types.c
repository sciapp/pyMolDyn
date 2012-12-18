#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include <shared/shared_common_types.h>
#include <shared.h>

#define BLOCK_SIZE (32)

#define type char
#define type_name char
#define type_default 0
#include <container/list/list_implementation.tpl>

#define type unsigned char
#define type_name uchar
#define type_default 0
#include <container/list/list_implementation.tpl>

#define type int
#define type_name int
#define type_default 0
#include <container/list/list_implementation.tpl>

#define type unsigned int
#define type_name uint
#define type_default 0
#include <container/list/list_implementation.tpl>

#define type float
#define type_name float
#define type_default 0.0f
#include <container/list/list_implementation.tpl>

#define type double
#define type_name double
#define type_default 0.0
#include <container/list/list_implementation.tpl>

#define type shared_t_char_p
#define type_name shared_t_char_p
#define type_default NULL
#define shared_type_name char_p
#include <container/list/list_implementation.tpl>

#define type char *
#define type_name char_p
#define type_default NULL
#include <container/list/list_implementation.tpl>

#define type void *
#define type_name void_p
#define type_default NULL
#include <container/list/list_implementation.tpl>
