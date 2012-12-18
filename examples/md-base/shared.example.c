#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <mdbase.h>
#include <shared/shared_common_types.h>
#include <list/list_shared_float_p.h>

int main(void) {
  float *f_ = malloc(sizeof(float));
  shared_t(float_p) f;
  list_t(shared_t(float_p)) l;
  
  /* Create a shared float pointer f (with 1 element) */
  f = shared_new(float_p)(f_);
  /* Retain f (reference counter += 1) */
  shared_retain(float_p)(f);
  /* Set the value of the first element to 0.0 */
  shared_get(float_p)(f)[0] = 0;
  /* Set the value of the first element to 42.0 */
  *shared_get(float_p)(f) = 42;
  /* Print the value of the first element */
  printf("f=%f\n",*shared_get(float_p)(f));
  
  /* Create a list of shared float pointers l */
  l = list_new(shared_t(float_p))();
  /* Append f to this list (ownership is SHARED, so: reference counter += 1) */
  list_append(shared_t(float_p))(l,f);
  
  /* Release f (reference counter -= 1) */
  shared_release(float_p)(f);
  
  /* Get f back from the list. l still owns f, so we should... */
  f = list_get(shared_t(float_p))(l,0);
  /* Retain f (reference counter += 1) */
  shared_retain(float_p)(f);
  
  /* Free l and therefore free all elements of l (this means f is released by l, so: reference counter -= 1) */
  list_free(shared_t(float_p))(l);
  
  /* Print the value of the first element */
  printf("f=%f\n",*shared_get(float_p)(f));
  
  /* Release f (reference counter -= 1) */
  shared_release(float_p)(f);
  /* The reference counter has now reached 0, so the memory f owned is now freed. */
  return 0;
}