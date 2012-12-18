#ifndef type
#error Need to define type
#endif
#ifndef type_name
#error Need to define type_name
#endif

#include "macros.h"

#include "undefs.h"
#define list_list_ CONCAT3(list_list__,type_name)
#define list_list CONCAT3(list_list,type_name)
#define list_t CONCAT3(list_t_,type_name)
#define list_new CONCAT3(list_new_,type_name)
#define list_free CONCAT3(list_free_,type_name)
#define list_put CONCAT3(list_put_,type_name)
#define list_get CONCAT3(list_get_,type_name)
#define list_append CONCAT3(list_append_,type_name)
#define list_size CONCAT3(list_size_,type_name)
#define list_remove CONCAT3(list_remove_,type_name)
#define list_iterate CONCAT3(list_iterate_,type_name)
typedef struct list_list_ *list_t;

list_t list_new();

void list_free(list_t list);

void list_put(list_t list, int index, type value);

type list_get(list_t list, int index);

void list_append(list_t list, type value);

int list_size(list_t list);

void list_remove(list_t list, int index);

void list_iterate(list_t list, BOOL (*function)(int index, type value));


#undef list_list_
#undef list_list
#undef list_t
#undef list_new
#undef list_free
#undef list_put
#undef list_get
#undef list_append
#undef list_size
#undef list_remove
#undef list_iterate
#include <container/list.h>

#ifndef KEEP_MACROS
#undef type
#undef type_name
#undef type_default
#endif
