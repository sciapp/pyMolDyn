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
#ifndef valuetype_default
#error Need to define valuetype_default value
#endif
#ifdef MAP_H
#error Include all map type headers before including the map header.
#endif

#define KEEP_MACROS
#include "map_header.tpl"
#undef KEEP_MACROS

#include "undefs.h"
#define map_map_ CONCAT3(CONCAT2(CONCAT3(map_map_,keytype_name),_),valuetype_name)
#define map_map CONCAT3(CONCAT2(CONCAT3(map_map_t_,keytype_name),_),valuetype_name)
#define map_t CONCAT3(CONCAT2(CONCAT3(map_t_,keytype_name),_),valuetype_name)
#define map_new CONCAT3(CONCAT2(CONCAT3(map_new_,keytype_name),_),valuetype_name)
#define map_free CONCAT3(CONCAT2(CONCAT3(map_free_,keytype_name),_),valuetype_name)
#define map_put CONCAT3(CONCAT2(CONCAT3(map_put_,keytype_name),_),valuetype_name)
#define map_contains CONCAT3(CONCAT2(CONCAT3(map_contains_,keytype_name),_),valuetype_name)
#define map_get CONCAT3(CONCAT2(CONCAT3(map_get_,keytype_name),_),valuetype_name)
#define map_size CONCAT3(CONCAT2(CONCAT3(map_size_,keytype_name),_),valuetype_name)
#define map_remove CONCAT3(CONCAT2(CONCAT3(map_remove_,keytype_name),_),valuetype_name)
#define map_iterate CONCAT3(CONCAT2(CONCAT3(map_iterate_,keytype_name),_),valuetype_name)
#define map_getkeys CONCAT3(CONCAT2(CONCAT3(map_getkeys_,keytype_name),_),valuetype_name)


typedef struct map_map_{
  list_t(keytype_name) keys;
  list_t(valuetype_name) values;
} map_map;

map_t map_new() {
  map_map *m = (map_map *)malloc(sizeof(map_map));
  if(!m) {
    fprintf(stderr, "malloc failed in map_new.\n");
    return NULL;
  }
  m->keys = list_new(keytype_name)();
  if (!m->keys) {
    free(m);
    fprintf(stderr, "list_new failed in map_new.\n");
    return NULL;
  }
  m->values = list_new(valuetype_name)();
  if (!m->values) {
    free(m);
    list_free(keytype_name)(m->keys);
    fprintf(stderr, "list_new failed in map_new.\n");
    return NULL;
  }
  return m;
}

void map_free(map_t map) {
  map_map *m = (map_map *)map;
  if (!m) {
    fprintf(stderr, "map_free called with NULL.\n");
    return;
  }
  list_free(keytype_name)(m->keys);
  list_free(valuetype_name)(m->values);
  free(m);
}

void map_put(map_t map, keytype key, valuetype value) {
  BOOL found = FALSE;
  int index;
  int num_keys;
  map_map *m = (map_map *)map;
  if (!m) {
    fprintf(stderr, "map_put called with NULL.\n");
    return;
  }
  num_keys = list_size(keytype_name)(m->keys);
  for(index = 0; index < num_keys; index++) {
    keytype ckey = list_get(keytype_name)(m->keys,index);
    if (map_keys_are_equal(key,ckey)) {
      found = TRUE;
      list_put(keytype_name)(m->keys,index,key);
      list_put(valuetype_name)(m->values,index,value);
      break;
    }
  }
  if (!found) {
    list_append(keytype_name)(m->keys,key);
    list_append(valuetype_name)(m->values,value);
  }
}

BOOL map_contains(map_t map, keytype key) {
  int index;
  int num_keys;
  map_map *m = (map_map *)map;
  if (!m) {
    fprintf(stderr, "map_contains called with NULL.\n");
    return FALSE;
  }
  num_keys = list_size(keytype_name)(m->keys);
  for(index = 0; index < num_keys; index++) {
    keytype ckey = list_get(keytype_name)(m->keys,index);
    if (map_keys_are_equal(key,ckey)) {
      return TRUE;
    }
  }
  return FALSE;
}

valuetype map_get(map_t map, keytype key) {
  int index;
  int num_keys;
  map_map *m = (map_map *)map;
  if (!m) {
    fprintf(stderr, "map_get called with NULL.\n");
    return valuetype_default;
  }
  num_keys = list_size(keytype_name)(m->keys);
  for(index = 0; index < num_keys; index++) {
    keytype ckey = list_get(keytype_name)(m->keys,index);
    if (map_keys_are_equal(key,ckey)) {
      return list_get(valuetype_name)(m->values,index);
    }
  }
  fprintf(stderr, "key not in map.\n");
  return valuetype_default;
}

void map_remove(map_t map, keytype key) {
  int index;
  int num_keys;
  map_map *m = (map_map *)map;
  if (!m) {
    fprintf(stderr, "map_remove called with NULL.\n");
    return;
  }
  num_keys = list_size(keytype_name)(m->keys);
  for(index = 0; index < num_keys; index++) {
    keytype ckey = list_get(keytype_name)(m->keys,index);
    if (map_keys_are_equal(key,ckey)) {
      list_remove(keytype_name)(m->keys,index);
      list_remove(valuetype_name)(m->values,index);
      return;
    }
  }
}

void map_iterate(map_t map, BOOL (*function)(keytype key, valuetype value)) {
  BOOL should_continue = TRUE;
  int index;
  int num_keys;
  map_map *m = (map_map *)map;
  if (!m || !function) {
    fprintf(stderr, "map_iterate called with NULL.\n");
    return;
  }
  num_keys = list_size(keytype_name)(m->keys);
  for(index = 0; index < num_keys && should_continue; index++) {
    keytype ckey = list_get(keytype_name)(m->keys,index);
    valuetype cvalue = list_get(valuetype_name)(m->values,index);
    should_continue = function(ckey,cvalue);
  }
}

list_t(keytype_name) map_getkeys(map_t map) {
  map_map *m = (map_map *)map;
  if (!m) {
    fprintf(stderr, "map_getkeys called with NULL.\n");
    return NULL;
  }
  return m->keys;
}

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


#undef keytype
#undef keytype_name
#undef valuetype
#undef valuetype_name
#undef valuetype_default
