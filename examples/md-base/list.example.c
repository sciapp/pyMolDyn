#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <mdbase.h>
#include <list/list_common_types.h>

static BOOL helpfunc(int index, int value);

int main(void) {
  int i;
  list_t(int) l;
  
  /* Create a list of ints l */
  l = list_new(int)();
  
  /* Append 1 */
  list_append(int)(l, 1);
  /* Print the first element: 1 */
  printf("%d\n",list_get(int)(l,0));
  /* Set the first element to 15 */
  list_put(int)(l,0,15);
  /* Print the last element (equal to the first element): 15 */
  printf("%d\n",list_get(int)(l,-1));
  /* Print the list size: 1 */
  printf("%d\n",list_size(int)(l));
  /* Remove the first element */
  list_remove(int)(l,0);
  /* Print the list size: 0 */
  printf("%d\n",list_size(int)(l));
  
  /* Fill the list with 0,1,4,9,...,81 */
  for (i = 0; i < 10; i++) {
    list_append(int)(l, i*i);
  }
  /* Print the list items in a loop */
  for (i = 0; i < list_size(int)(l); i++) {
    printf("%d: %d\n",i,list_get(int)(l,i));
  }
  /* Print the list items in a iteration function (similar to map(helpfunc,range(len(l)),l) in python) */
  list_iterate(int)(l,helpfunc);
  /* Remove the list items one by one */
  for (i = 0; i < 10; i++) {
    list_remove(int)(l, 0);
  }
  
  /* Free the list */
  list_free(int)(l);
  return 0;
}

static BOOL helpfunc(int index, int value) {
  printf("called with %d for index %d\n", value, index);
  return value < 100*100;
}