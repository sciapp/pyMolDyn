#ifndef type
#error Need to define type
#endif
#ifndef type_name
#error Need to define type_name
#endif

#define KEEP_MACROS
#include "shared_header.tpl"
#undef KEEP_MACROS

#include "undefs.h"
#define shared_shared_ CONCAT3(shared_shared__,type_name)
#define shared_shared CONCAT3(shared_shared_,type_name)
#define shared_t CONCAT3(shared_t_,type_name)
#define shared_new CONCAT3(shared_new_,type_name)
#define shared_free CONCAT3(shared_free_,type_name)
#define shared_get CONCAT3(shared_get_,type_name)
#define shared_retain CONCAT3(shared_retain_,type_name)
#define shared_release CONCAT3(shared_release_,type_name)
#define shared_getcount CONCAT3(shared_getcount_,type_name)

typedef struct shared_shared_ {
  type object;
  int refcount;
} shared_shared;

shared_t shared_new(type object) {
  shared_t s = (shared_t)malloc(sizeof(shared_shared));
  if (!s) {
    fprintf(stderr, "malloc failed in shared_new.\n");
    return NULL;
  }
  s->object = object;
  s->refcount = 0;
  return s;
}

type shared_get(shared_t shared) {
  shared_shared *s = (shared_shared *)shared;
  if (!s) {
    fprintf(stderr, "shared_get called with NULL.\n");
    return NULL;
  }
  if (s->refcount <= 0) {
    fprintf(stderr, "shared_get called with refcount <= 0.\n");
  }
  return s->object;
}

void shared_retain(shared_t shared) {
  shared_shared *s = (shared_shared *)shared;
  if (!s) {
    fprintf(stderr, "shared_retain called with NULL.\n");
    return;
  }
  s->refcount++;
}

void shared_release(shared_t shared) {
  shared_shared *s = (shared_shared *)shared;
  if (!s) {
    fprintf(stderr, "shared_release called with NULL.\n");
    return;
  }
  s->refcount--;
  if (s->refcount < 0) {
    fprintf(stderr, "shared_release called with refcount <= 0.\n");
  }
  if (s->refcount <= 0) {
    type_free(s->object);
    free(s);
  }
}

void shared_free(shared_t shared) {
  shared_shared *s = (shared_shared *)shared;
  if (!s) {
    fprintf(stderr, "shared_free called with NULL.\n");
    return;
  }
  free(s);
}

int shared_getcount(shared_t shared) {
  shared_shared *s = (shared_shared *)shared;
  if (!s) {
    fprintf(stderr, "shared_free called with NULL.\n");
    return 0;
  }
  return s->refcount;
}


#undef shared_shared_
#undef shared_t
#undef shared_new
#undef shared_free
#undef shared_get
#undef shared_retain
#undef shared_release
#undef shared_getcount

#undef type
#undef type_name
#undef type_free
