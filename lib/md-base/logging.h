#ifndef MD_BASE_LOGGING_H
#define MD_BASE_LOGGING_H

/* logging levels */
/* debug information (only useful during debugging, probably not useful for the user) */
#define MD_BASE_LOG_DEBUG 0
/* general information (possibly useful for the user) */
#define MD_BASE_LOG_INFO 1
/* warnings (something probably went wrong, so the user should know about it, but the error wasn't critical) */
#define MD_BASE_LOG_WARNING 2
/* errors (something definitly went wrong and it might very well be fatal, so the user must know about it) */
#define MD_BASE_LOG_ERROR 3

/* mdbase_log()
 * works like printf, but if it logs depends on level being greater than or
 * equal to the logging level set with mdbase_log_level() for the channel and
 * prints into the log file set with mdbase_log_file().
 */
void mdbase_log(int channel, int level, const char *format, ...);

/* mdbase_log_stacktrace()
 * logs the current stack trace.
 */
void mdbase_log_stacktrace(int channel, int level);

/* mdbase_log_get_channel_level()
 * returns the current logging level for the given channel. Defaults to 0.
 */
int mdbase_log_get_channel_level(int channel);

/* mdbase_log_get_channel_name()
 * returns the name of the given channel. Defaults to "unknown channel".
 */
const char *mdbase_log_get_channel_name(int channel);

/* mdbase_log_set_channel_name()
 * sets the channel's name used in logging messages. Defaults to "unknown channel".
 */
void mdbase_log_set_channel_name(int channel, const char *name);

/* mdbase_log_level()
 * sets the new logging level and returns the previous one. Defaults to 0.
 */
int mdbase_log_set_channel_level(int channel, int level);

/* mdbase_log_file()
 * sets the new logging file and returns the previous one. Use NULL disable
 * logging completely.
 */
FILE *mdbase_log_file(FILE *file);


#endif
