#ifndef LIST_H
#define LIST_H

#include "macros.h"

#define list_t(typename) CONCAT3(list_t_,typename)
#define list_new(typename) CONCAT3(list_new_,typename)
#define list_free(typename) CONCAT3(list_free_,typename)
#define list_put(typename) CONCAT3(list_put_,typename)
#define list_get(typename) CONCAT3(list_get_,typename)
#define list_append(typename) CONCAT3(list_append_,typename)
#define list_size(typename) CONCAT3(list_size_,typename)
#define list_remove(typename) CONCAT3(list_remove_,typename)
#define list_iterate(typename) CONCAT3(list_iterate_,typename)

/* function-like macros for multi-dimensional list access */
#define LIST_2D_GET(type,l,i,j) list_get(type)(list_get(list_t(type))(l,i),j)
#define LIST_3D_GET(type,l,i,j,k) list_get(type)(list_get(list_t(type))(list_get(list_t(list_t(type)))(l,i),j),k)
#endif
