#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "macros.h"
#include <container/list/list_common_types.h>
#include <container/list.h>

static BOOL map_keys_are_equal(int key1, int key2) {
  return key1 == key2;
}

#define keytype int
#define keytype_name int
#define valuetype float
#define valuetype_name float
#define valuetype_default 0
#include <container/map/map_implementation.tpl>

#define keytype int
#define keytype_name int
#define valuetype int
#define valuetype_name int
#define valuetype_default 0
#include <container/map/map_implementation.tpl>

#define keytype int
#define keytype_name int
#define valuetype char *
#define valuetype_name char_p
#define valuetype_default NULL
#include <container/map/map_implementation.tpl>
