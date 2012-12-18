#include <stdlib.h>
#include <stdio.h>
#include <stdarg.h>
#include <mdbase.h>
#include <container/list/list_common_types.h>
#include <container/list.h>
#include <container/map/map_int_common_types.h>
#include <container/map.h>

#ifdef MD_BASE_ON_UNIX
#include <execinfo.h>
#endif

static FILE * md_base_log_file;
static map_t(int, char_p) md_base_log_channel_names;
static map_t(int, int) md_base_log_channel_levels;

static BOOL initialized = FALSE;
static void mdbase_log_init(void) {
  if (!initialized) {
    initialized = TRUE;
    md_base_log_file = stderr;
    md_base_log_channel_names = map_new(int, char_p)();
    md_base_log_channel_levels = map_new(int, int)();
    map_put(int, char_p)(md_base_log_channel_names,0,(char *)"common");
    map_put(int, char_p)(md_base_log_channel_names,1,(char *)"libmd-base");
  }
}

void mdbase_log(int channel, int level, const char *format, ...) {
  mdbase_log_init();
  if (md_base_log_file) {
    if (level >= mdbase_log_get_channel_level(channel) || level == -1) {
      va_list args;
      va_start(args, format);
      fprintf(md_base_log_file,"%s (%d): ", mdbase_log_get_channel_name(channel), level);
      vfprintf(md_base_log_file, format, args);
      va_end(args);
    }
  }
}

void mdbase_log_set_channel_name(int channel, const char *name) {
  mdbase_log_init();
  map_put(int, char_p)(md_base_log_channel_names,channel,(char *)name);
}

int mdbase_log_get_channel_level(int channel) {
  mdbase_log_init();
  {
    if (map_contains(int, int)(md_base_log_channel_levels,channel)) {
      return map_get(int, int)(md_base_log_channel_levels,channel);
    } else {
      return 0;
    }
  }
}

const char *mdbase_log_get_channel_name(int channel) {
  mdbase_log_init();
  {
    if (map_contains(int, char_p)(md_base_log_channel_names,channel)) {
      return map_get(int, char_p)(md_base_log_channel_names,channel);
    } else {
      return "unknown channel";
    }
  }
}

int mdbase_log_set_channel_level(int channel, int level) {
  mdbase_log_init();
  {
    int old_level = mdbase_log_get_channel_level(channel);
    map_put(int, int)(md_base_log_channel_levels,channel,level);
    return old_level;
  }
}

FILE *mdbase_log_file(FILE *file) {
  mdbase_log_init(); {
    FILE *tmp = md_base_log_file;
    md_base_log_file = file;
    return tmp;
  }
}

#ifdef MD_BASE_ON_UNIX
void mdbase_log_stacktrace(int channel, int level) {
  {
    void* callstack[128];
    int i, frames = backtrace(callstack, 128);
    char** strs = backtrace_symbols(callstack, frames);
    mdbase_log(channel, level, "current stack trace:\n");
    for (i = frames-1; i >= 0; i--) {
      mdbase_log(channel, level,"%s\n", strs[i]);
    }
    free(strs);
  }
}
#else
void mdbase_log_stacktrace(int channel, int level) {
  mdbase_log(channel, level, "current stack trace:\n");
  mdbase_log(channel, level, "Unable to provide a stack trace (Windows).\n");
}
#endif

void mdbase_crash() {
  mdbase_log_stacktrace(0, MD_BASE_LOG_ERROR);
  mdbase_log(0, MD_BASE_LOG_ERROR, "crashing...\n");
  abort();
}
