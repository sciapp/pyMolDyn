#ifndef type
#error Need to define type
#endif
#ifndef type_name
#error Need to define type_name
#endif

#include "macros.h"
#include "undefs.h"
#define shared_shared_ CONCAT3(shared_shared__,type_name)
#define shared_t CONCAT3(shared_t_,type_name)
#define shared_new CONCAT3(shared_new_,type_name)
#define shared_free CONCAT3(shared_free_,type_name)
#define shared_get CONCAT3(shared_get_,type_name)
#define shared_retain CONCAT3(shared_retain_,type_name)
#define shared_release CONCAT3(shared_release_,type_name)
#define shared_getcount CONCAT3(shared_getcount_,type_name)
typedef struct shared_shared_ *shared_t;

shared_t shared_new(type object);

void shared_free(shared_t shared);

type shared_get(shared_t shared);

void shared_retain(shared_t shared);

void shared_release(shared_t shared);

int shared_getcount(shared_t shared);


#undef shared_shared_
#undef shared_t
#undef shared_new
#undef shared_free
#undef shared_get
#undef shared_retain
#undef shared_release
#undef shared_getcount
#include <shared.h>

#ifndef KEEP_MACROS
#undef type
#undef type_name
#endif
