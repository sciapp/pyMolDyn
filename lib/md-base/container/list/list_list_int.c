#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "list_common_types.h"
#define BLOCK_SIZE (32)

#define type list_t_int
#define type_name list_t_int
#define type_default NULL
#include <container/list/list_implementation.tpl>