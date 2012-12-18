#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include <shared/shared_common_types.h>
#include <shared.h>

#define BLOCK_SIZE (32)

#define type shared_t(float_p)
#define type_name shared_t(float_p)
#define type_default NULL
#define shared_type_name float_p
#include <container/list/list_implementation.tpl>
