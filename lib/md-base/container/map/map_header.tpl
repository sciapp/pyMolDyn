#ifndef keytype
#error Need to define keytype
#endif
#ifndef keytype_name
#error Need to define keytype_name
#endif
#ifndef valuetype
#error Need to define valuetype
#endif
#ifndef valuetype_name
#error Need to define valuetype_name
#endif

#include "macros.h"

#include "undefs.h"
#define map_map_ CONCAT3(CONCAT2(CONCAT3(map_map_,keytype_name),_),valuetype_name)
#define map_t CONCAT3(CONCAT2(CONCAT3(map_t_,keytype_name),_),valuetype_name)
#define map_new CONCAT3(CONCAT2(CONCAT3(map_new_,keytype_name),_),valuetype_name)
#define map_free CONCAT3(CONCAT2(CONCAT3(map_free_,keytype_name),_),valuetype_name)
#define map_put CONCAT3(CONCAT2(CONCAT3(map_put_,keytype_name),_),valuetype_name)
#define map_get CONCAT3(CONCAT2(CONCAT3(map_get_,keytype_name),_),valuetype_name)
#define map_contains CONCAT3(CONCAT2(CONCAT3(map_contains_,keytype_name),_),valuetype_name)
#define map_size CONCAT3(CONCAT2(CONCAT3(map_size_,keytype_name),_),valuetype_name)
#define map_remove CONCAT3(CONCAT2(CONCAT3(map_remove_,keytype_name),_),valuetype_name)
#define map_iterate CONCAT3(CONCAT2(CONCAT3(map_iterate_,keytype_name),_),valuetype_name)
#define map_getkeys CONCAT3(CONCAT2(CONCAT3(map_getkeys_,keytype_name),_),valuetype_name)
typedef struct map_map_ *map_t;

map_t map_new();

void map_free(map_t map);

void map_put(map_t map, keytype key, valuetype value);

BOOL map_contains(map_t map, keytype key);

valuetype map_get(map_t map, keytype key);

void map_remove(map_t map, keytype key);

void map_iterate(map_t map, BOOL (*function)(keytype key, valuetype value));

list_t(keytype_name) map_getkeys(map_t map);


#undef map_map_
#undef map_t
#undef map_new
#undef map_free
#undef map_put
#undef map_get
#undef map_contains
#undef map_size
#undef map_remove
#undef map_iterate
#undef map_getkeys

#include <container/map.h>

#ifndef KEEP_MACROS
#undef keytype
#undef keytype_name
#undef valuetype
#undef valuetype_name
#undef valuetype_default
#endif
