/* Calls the library tests/lib/words.vu exports, through the header vu build --lib wrote, from one
   thread and then from eight at once, checking every answer; built with the sanitizers by
   tests/run_lib.sh. Prints "driver: N checks passed" or the first wrong answer. */
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "words.h"

static long checks;
static int bad(const char *what) { fprintf(stderr, "driver: wrong: %s\n", what); exit(1); }
#define CHECK(c) do { if (!(c)) bad(#c); __atomic_add_fetch(&checks, 1, __ATOMIC_RELAXED); } while (0)

static void once(int k) {
    int64_t n = -1;
    char *err = NULL;
    CHECK(add(40, k) == 40 + k);
    CHECK(half(5.0) == 2.5);
    CHECK(flip(true) == false && flip(false) == true);
    CHECK(next_byte(255) == 0 && next_byte(7) == 8);
    nothing();
    CHECK(count_words("the quick  brown fox", -1) == 4);
    CHECK(count_words("a b c", 3) == 2);            /* the length wins over the NUL */
    CHECK(count_words(NULL, 0) == 0);
    char *s = exclaim("hey", -1, &n);
    CHECK(n == 4 && strcmp(s, "hey!") == 0);
    free(s);
    s = exclaim("a\0b", 3, &n);                       /* zero bytes go through */
    CHECK(n == 4 && memcmp(s, "a\0b!", 5) == 0);
    free(s);
    s = exclaim("", 0, NULL);
    CHECK(strcmp(s, "!") == 0);
    free(s);
    uint8_t bytes[] = {1, 2, 3, 0, 255};
    uint8_t *rb = reverse_bytes(bytes, 5, &n);
    CHECK(n == 5 && rb[0] == 255 && rb[1] == 0 && rb[4] == 1);
    free(rb);
    rb = reverse_bytes(NULL, 0, &n);
    CHECK(n == 0 && rb != NULL);
    free(rb);
    int64_t *sq = squares(10 + k % 5, &n);
    CHECK(n == 10 + k % 5 && sq[3] == 9 && sq[n - 1] == (n - 1) * (n - 1));
    free(sq);
    double xs[] = {1.0, 2.0, 4.5};
    double *sc = scaled(xs, 3, 2.0, &n);
    CHECK(n == 3 && sc[0] == 2.0 && sc[2] == 9.0);
    free(sc);
    int64_t is[] = {5, -2, 8, 1};
    CHECK(total(is, 4) == 12 && total(is, -3) == 0 && total(NULL, 5) == 0);
    CHECK(mean(xs, 3, &err) == 2.5 && err == NULL);
    CHECK(mean(xs, 0, &err) == 0.0 && err && strcmp(err, "mean of no numbers") == 0);
    free(err);
    CHECK(mean(xs, 2, NULL) == 1.5);
    check_name("x", -1, &err);
    CHECK(err == NULL);
    check_name("", 0, &err);
    CHECK(err && strcmp(err, "a name can't be empty") == 0);
    free(err);
    s = greet("Ada", -1, 2, &n, &err);
    CHECK(err == NULL && strcmp(s, "hi Ada. hi Ada.") == 0 && n == 15);
    free(s);
    s = greet("Ada", 3, -3, &n, &err);
    CHECK(s == NULL && n == 0 && err && strcmp(err, "times is negative: -3") == 0);
    free(err);
    int64_t *ev = evens(is, 4, &n, &err);
    CHECK(ev == NULL && n == 0 && strcmp(err, "negative: -2") == 0);
    free(err);
    int64_t ok[] = {4, 7, 10};
    ev = evens(ok, 3, &n, &err);
    CHECK(err == NULL && n == 2 && ev[0] == 4 && ev[1] == 10);
    free(ev);
}

static void *worker(void *arg) {
    int id = (int)(intptr_t)arg;
    for (int i = 0; i < 300; i++) once(id * 1000 + i);
    return NULL;
}

int main(void) {
    once(0);
    CHECK(psum(1000) == 999000);
    pthread_t t[8];
    for (int i = 0; i < 8; i++) pthread_create(&t[i], NULL, worker, (void *)(intptr_t)i);
    for (int i = 0; i < 8; i++) pthread_join(t[i], NULL);
    printf("driver: %ld checks passed\n", checks);
    return 0;
}
