#include <stdio.h>
#include "version.h"

static const unsigned int md_base_version_major = MD_BASE_VERSION_MAJOR;
static const unsigned int md_base_version_minor = MD_BASE_VERSION_MINOR;
static const unsigned int md_base_version_patch = MD_BASE_VERSION_PATCH;
static const char * const md_base_version_comment = MD_BASE_VERSION_COMMENT;
static const char * const md_base_version = MD_BASE_VERSION;

const char * mdbase_get_version(unsigned int *major, unsigned int *minor, unsigned int *patch) {
  if (major) *major = md_base_version_major;
  if (minor) *minor = md_base_version_minor;
  if (patch) *patch = md_base_version_patch;
  return md_base_version;
}

const char * mdbase_get_version_comment() {
  return md_base_version_comment;
}

