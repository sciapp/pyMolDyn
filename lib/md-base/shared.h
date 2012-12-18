#ifndef SHARED_H
#define SHARED_H

#include "macros.h"

#define shared_t(typename) CONCAT3(shared_t_,typename)
#define shared_new(typename) CONCAT3(shared_new_,typename)
#define shared_free(typename) CONCAT3(shared_free_,typename)
#define shared_get(typename) CONCAT3(shared_get_,typename)
#define shared_retain(typename) CONCAT3(shared_retain_,typename)
#define shared_release(typename) CONCAT3(shared_release_,typename)
#define shared_getcount(typename) CONCAT3(shared_getcount_,typename)

#endif
