#ifndef LIST_COMMON_TYPES_H
#define LIST_COMMON_TYPES_H

#include <shared/shared_common_types.h>
#include <shared.h>

#define type char
#define type_name char
#include <container/list/list_header.tpl>

#define type unsigned char
#define type_name uchar
#include <container/list/list_header.tpl>

#define type int
#define type_name int
#include <container/list/list_header.tpl>

#define type unsigned int
#define type_name uint
#include <container/list/list_header.tpl>

#define type float
#define type_name float
#include <container/list/list_header.tpl>

#define type double
#define type_name double
#include <container/list/list_header.tpl>

#define type shared_t_char_p
#define type_name shared_t_char_p
#include <container/list/list_header.tpl>

#define type char *
#define type_name char_p
#include <container/list/list_header.tpl>

#define type void *
#define type_name void_p
#include <container/list/list_header.tpl>

#endif
