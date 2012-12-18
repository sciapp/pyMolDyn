#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <mdbase.h>
#include <list/list_common_types.h>
#include <list/list_list_int.h>
#include <list/list_list_list_int.h>

int main(void) {
  int i;
  list_t(int) l;
  list_t(list_t(int)) l2;
  list_t(list_t(list_t(int))) l3;
  
  /* Create a list of ints, a list of list of ints (2D) and a list of lists of lists of ints (3D) */
  l = list_new(int)();
  l2 = list_new(list_t(int))();
  l3 = list_new(list_t(list_t(int)))();
  
  /* Append l2 to l3 and l to l2 */
  list_append(list_t(list_t(int)))(l3, l2);
  list_append(list_t(int))(l2, l);
  /* Append 42 to l, so l[0] = 42, l2[0][0] = 42 and l3[0][0][0] = 42 */
  list_append(int)(l, 42);
  /* Print this value by using the normal access method */
  i = list_get(int)(list_get(list_t(int))(l2,0),0);
  printf("%d\n",i);
  /* Print this value by using the 2D and 3D getter macros */
  i = LIST_2D_GET(int,l2,0,0);
  printf("%d\n",i);
  i = LIST_3D_GET(int,l3,0,0,0);
  printf("%d\n",i);
  
  /* Free the lists */
  list_free(int)(l);
  list_free(list_t(int))(l2);
  list_free(list_t(list_t(int)))(l3);
  return 0;
}