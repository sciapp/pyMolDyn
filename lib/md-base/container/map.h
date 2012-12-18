#ifndef MAP_H
#define MAP_H

#include "macros.h"

#define map_t(keytypename,valuetypename) CONCAT3(CONCAT2(CONCAT3(map_t_,keytypename),_),valuetypename)
#define map_new(keytypename,valuetypename) CONCAT3(CONCAT2(CONCAT3(map_new_,keytypename),_),valuetypename)
#define map_free(keytypename,valuetypename) CONCAT3(CONCAT2(CONCAT3(map_free_,keytypename),_),valuetypename)
#define map_put(keytypename,valuetypename) CONCAT3(CONCAT2(CONCAT3(map_put_,keytypename),_),valuetypename)
#define map_get(keytypename,valuetypename) CONCAT3(CONCAT2(CONCAT3(map_get_,keytypename),_),valuetypename)
#define map_contains(keytypename,valuetypename) CONCAT3(CONCAT2(CONCAT3(map_contains_,keytypename),_),valuetypename)
#define map_size(keytypename,valuetypename) CONCAT3(CONCAT2(CONCAT3(map_size_,keytypename),_),valuetypename)
#define map_remove(keytypename,valuetypename) CONCAT3(CONCAT2(CONCAT3(map_remove_,keytypename),_),valuetypename)
#define map_iterate(keytypename,valuetypename) CONCAT3(CONCAT2(CONCAT3(map_iterate_,keytypename),_),valuetypename)
#define map_getkeys(keytypename,valuetypename) CONCAT3(CONCAT2(CONCAT3(map_getkeys_,keytypename),_),valuetypename)

#endif
