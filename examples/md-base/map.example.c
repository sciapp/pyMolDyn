#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <mdbase.h>
#include <list/list_common_types.h>
#include <map/map_int_common_types.h>

static BOOL helpfunc(int key, float value);

int main(void) {
  map_t(int,float) m;
  
  /* Create an int->float map m */
  m = map_new(int,float)();
  /* Set a values */
  map_put(int,float)(m,1,-1);
  /* Overwrite the value */
  map_put(int,float)(m,1,3.14);
  /* Print the value */
  printf("%f\n",map_get(int,float)(m,1));
  
  /* Set a different value and print it */
  map_put(int,float)(m,-1337,9000);
  printf("%f\n",map_get(int,float)(m,-1337));
  
  /* Print the map keys and values in a iteration function (similar to map(helpfunc,keys(m),m) in python) */
  map_iterate(int,float)(m,helpfunc);
  
  /* Do the same by using a loop */
  {
    int index;
    int num_keys;
    list_t(int) keys;
    keys = map_getkeys(int,float)(m);
    num_keys = list_size(int)(keys);
    for (index = 0; index < num_keys; index++) {
      printf("key %d: %d\n",index,list_get(int)(keys,index));
    }
  }
  
  /* Remove an item from m */
  map_remove(int,float)(m,1);
  /* Try to print it (this will print a warning and the default float 0.0) */
  printf("%f\n",map_get(int,float)(m,1));
  
  /* Free the map */
  map_free(int,float)(m);
  return 0;
}

static BOOL helpfunc(int key, float value) {
  printf("called with %d => %f\n",key,value);
  return TRUE;
}