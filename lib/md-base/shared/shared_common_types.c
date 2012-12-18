#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define type char *
#define type_name char_p
#define type_free free
#include <shared/shared_implementation.tpl>

#define type unsigned char *
#define type_name uchar_p
#define type_free free
#include <shared/shared_implementation.tpl>

#define type int *
#define type_name int_p
#define type_free free
#include <shared/shared_implementation.tpl>

#define type unsigned int *
#define type_name uint_p
#define type_free free
#include <shared/shared_implementation.tpl>

#define type float *
#define type_name float_p
#define type_free free
#include <shared/shared_implementation.tpl>

#define type double *
#define type_name double_p
#define type_free free
#include <shared/shared_implementation.tpl>

#define type void *
#define type_name void_p
#define type_free free
#include <shared/shared_implementation.tpl>
