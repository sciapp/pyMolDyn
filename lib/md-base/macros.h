#ifndef MD_BASE_MACROS_H
#define MD_BASE_MACROS_H

/* boolean values */
#define TRUE (1)
#define FALSE (0)
#define BOOL int

/* stringify token */
#define STR(tok) #tok
/* stringify token (expand once) */
#define STR2(tok) STR(tok)

/* concat tokens */
#define CONCAT(tok1,tok2) tok1 ## tok2
/* concat tokens (expand once) */
#define CONCAT2(tok1,tok2) CONCAT(tok1,tok2)
/* concat tokens (expand twice) */
#define CONCAT3(tok1,tok2) CONCAT2(tok1,tok2)

#define UNUSED (void)

#endif
