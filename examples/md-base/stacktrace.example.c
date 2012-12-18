#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <mdbase.h>

int main(void) {
  mdbase_log_stacktrace(0, MD_BASE_LOG_INFO);
  return 0;
}