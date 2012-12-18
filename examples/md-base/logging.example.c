#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <mdbase.h>

int main(void) {
  int i = 0;
  /* Print a debug message (0) to the common channel */
  mdbase_log(0,MD_BASE_LOG_DEBUG,"Test %d\n", i++);
  /* Print a warning (2) to the libmd-base channel */
  mdbase_log(1,MD_BASE_LOG_WARNING,"Test %d\n", i++);
  
  /* Set the channel minimum level to info (1) for the common channel */
  mdbase_log_set_channel_level(0, MD_BASE_LOG_INFO);
  /* Print a debug message to the common channel. This must not be visible, as its level is below the minimum level. */
  mdbase_log(0,MD_BASE_LOG_DEBUG,"Test %d\n", i++);
  /* Print a warning to the common channel. As warnings (2) are above info (1) this message must be visible. */
  mdbase_log(0,MD_BASE_LOG_WARNING,"Test %d\n", i++);
  
  /* Print a message with level -1 (always visible) to the common channel */
  mdbase_log(0,-1,"Test %d\n", i++);
  mdbase_log_set_channel_level(0, 0);
  /* Set the name of the common channel */
  mdbase_log_set_channel_name(0, "test channel");
  /* Print a debug message to the channel "test channel" */
  mdbase_log(0,MD_BASE_LOG_DEBUG,"Test %d\n", i++);
  
  /* Print a more complex message */
  mdbase_log(0,MD_BASE_LOG_DEBUG,"Test %d: %s %0.4f\n", i++, "example", 0.123456789);
  return 0;
}