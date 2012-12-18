#ifndef type
#error Need to define type
#endif
#ifndef type_name
#error Need to define type_name
#endif
#ifndef type_default
#error Need to define type_default value
#endif

#define KEEP_MACROS
#include "list_header.tpl"
#undef KEEP_MACROS

#include "undefs.h"
#define list_list_ CONCAT3(list_list__,type_name)
#define list_list CONCAT3(list_list_,type_name)
#define list_t CONCAT3(list_t_,type_name)
#define list_new CONCAT3(list_new_,type_name)
#define list_free CONCAT3(list_free_,type_name)
#define list_put CONCAT3(list_put_,type_name)
#define list_get CONCAT3(list_get_,type_name)
#define list_append CONCAT3(list_append_,type_name)
#define list_size CONCAT3(list_size_,type_name)
#define list_remove CONCAT3(list_remove_,type_name)
#define list_iterate CONCAT3(list_iterate_,type_name)
#define list_check_index CONCAT3(list_check_index_,type_name)

typedef struct list_list_{
  type *data;
  int capacity;
  int size;
} list_list;

static int list_check_index(list_list *l, int index) {
  if (index < 0) {
    index += l->size;
  }
  if (index < 0 || index >= l->size) {
    fprintf(stderr, "list index out of bounds\n");
    return 0;
  }
  return index;
}

list_t list_new() {
  list_list *l = (list_list *)malloc(sizeof(list_list));
  if(!l) {
    fprintf(stderr, "malloc failed in list_new.\n");
    return NULL;
  }
  l->data = NULL;
  l->size = 0;
  l->capacity = 0;
  return l;
}

void list_free(list_t list) {
  list_list *l = (list_list *)list;
  if (!l) {
    fprintf(stderr, "list_free called with NULL.\n");
    return;
  }
#ifdef shared_type_name
  {
    int i;
    for (i = 0; i < l->size; i++) {
      shared_release(shared_type_name)(l->data[i]);
    }
  }
#endif
  free(l->data);
  free(l);
}

void list_put(list_t list, int index, type value) {
  list_list *l = (list_list *)list;
  if (!l) {
    fprintf(stderr, "list_put called with NULL.\n");
    return;
  }
  index = list_check_index(l,index);
  
#ifdef shared_type_name
  shared_retain(shared_type_name)(value);
  shared_release(shared_type_name)(l->data[index]);
#endif
  l->data[index] = value;
}

type list_get(list_t list, int index) {
  list_list *l = (list_list *)list;
  if (!l) {
    fprintf(stderr, "list_get called with NULL.\n");
    return type_default;
  }
  index = list_check_index(l,index);
  return l->data[index];
}

void list_append(list_t list, type value) {
  list_list *l = (list_list *)list;
  if (!l) {
    fprintf(stderr, "list_append called with NULL.\n");
    return;
  }
  l->size++;
  if (l->size > l->capacity) {
    type *temp;
    l->capacity += BLOCK_SIZE;
    temp = realloc(l->data, l->capacity*sizeof(type));
    if (!temp) {
      fprintf(stderr, "realloc failed in list_append.\n");
      l->capacity -= BLOCK_SIZE;
      l->size--;
      return;
    }
    l->data = temp;
  }
  
#ifdef shared_type_name
  shared_retain(shared_type_name)(value);
#endif
  l->data[l->size-1] = value;
}

int list_size(list_t list) {
  list_list *l = (list_list *)list;
  if (!l) {
    fprintf(stderr, "list_size called with NULL.\n");
    return 0;
  }
  return l->size;
}

void list_remove(list_t list, int index) {
  list_list *l = (list_list *)list;
  if (!l) {
    fprintf(stderr, "list_remove called with NULL.\n");
    return;
  }
  index = list_check_index(l,index);
  
#ifdef shared_type_name
  shared_release(shared_type_name)(l->data[index]);
#endif
  l->size--;
  memmove(l->data+index,l->data+index+1, (l->size-index)*sizeof(type));
  if (l->size < l->capacity-2*BLOCK_SIZE && l->capacity > BLOCK_SIZE) {
    type *temp;
    l->capacity -= BLOCK_SIZE;
    temp = realloc(l->data, l->capacity*sizeof(type));
    if (!temp) {
      fprintf(stderr, "realloc failed in list_remove.\n");
      l->capacity += BLOCK_SIZE;
      return;
    }
    l->data = temp;
  }
}

void list_iterate(list_t list, BOOL (*function)(int index, type value)) {
  BOOL should_continue = TRUE;
  int index;
  list_list *l = (list_list *)list;
  if (!l || !function) {
    fprintf(stderr, "list_iterate called with NULL.\n");
    return;
  }
  for (index = 0; index < l->size && should_continue; index++) {
    should_continue = function(index,l->data[index]);
  }
}

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
#undef list_check_index

#undef type
#undef type_name
#undef type_default
#ifdef shared_type_name
#undef shared_type_name
#endif
