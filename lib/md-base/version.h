#ifndef MD_BASE_VERSION_H
#define MD_BASE_VERSION_H
#include "macros.h"

#ifdef __APPLE__
#define MD_BASE_ON_MAC
#define MD_BASE_ON_UNIX
#else
#ifdef __linux__
#define MD_BASE_ON_LINUX
#define MD_BASE_ON_UNIX
#else
#ifdef __WIN32
#define MD_BASE_ON_WINDOWS
#else
#error "Unknown operating system"
#endif
#endif
#endif

/* version constants
 * versions are in the format of major.minor.patch and an additional comment
 * these constants can be used to get the library version of the header, for the
 * library version in use, see the functions:
 * mdbase_get_version() and mdbase_get_version_comment()
 */
#define MD_BASE_VERSION_MAJOR 0
#define MD_BASE_VERSION_MINOR 0
#define MD_BASE_VERSION_PATCH 0
#define MD_BASE_VERSION_COMMENT "just started development"
#define MD_BASE_VERSION STR2(MD_BASE_VERSION_MAJOR)"."STR2(MD_BASE_VERSION_MINOR)"."STR2(MD_BASE_VERSION_PATCH)" ("MD_BASE_VERSION_COMMENT")"

/* mdbase_get_version()
 * returns the compile time version string and sets the pointer contents (if
 * not NULL) to the compile time version values.
 */
const char * mdbase_get_version(unsigned int *major, unsigned int *minor, unsigned int *patch);

/* mdbase_get_version_comment()
 * returns the compile time version comment.
 */
const char * mdbase_get_version_comment();



#endif
