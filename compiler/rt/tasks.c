/* Tasks (spawn): lightweight threads, run on one thread per core. New tasks go to the threads in
   turn (an idle thread may take one that hasn't started from a busy thread); once a task has run,
   it stays on that thread. It runs until it waits for the network, a channel or a timer; then a
   task that is ready on that thread runs. Each task has its own stack
   (VU_TASK_STACK of address space, used as it grows) and its own call stack for backtraces.
   Values move into a task and through channels, and Vu has no globals, so tasks share nothing but
   channels, which are locked. */
#include <sys/mman.h>
#include <sched.h>
#include <signal.h>
#include <fcntl.h>
#include <sys/socket.h>
#ifdef __APPLE__
/* macOS: kqueue stands in for the parts of epoll used here (read and write interest, edge-triggered
   or not), a pipe for an eventfd, and fcntl for the flags Linux sets when a socket is made. */
#include <sys/event.h>
#define EPOLLIN 0x001u
#define EPOLLOUT 0x004u
#define EPOLLERR 0x008u
#define EPOLLHUP 0x010u
#define EPOLLRDHUP 0x2000u
#define EPOLLET (1u << 31)
#define EPOLL_CTL_ADD 1
#define EPOLL_CTL_DEL 2
#define EPOLL_CLOEXEC 0
#define SOCK_NONBLOCK 0
#define SOCK_CLOEXEC 0
#define MSG_NOSIGNAL 0
#define EFD_NONBLOCK 0
#define EFD_CLOEXEC 0
typedef union { void *ptr; int fd; uint64_t u64; } epoll_data_t;
struct epoll_event { uint32_t events; epoll_data_t data; };
static int epoll_create1(int flags) { (void)flags; int k = kqueue(); if (k >= 0) fcntl(k, F_SETFD, FD_CLOEXEC); return k; }
static int epoll_ctl(int ep, int op, int fd, struct epoll_event *ev) {
    struct kevent k[2];
    if (op == EPOLL_CTL_DEL) {
        EV_SET(&k[0], fd, EVFILT_READ, EV_DELETE, 0, 0, NULL);
        kevent(ep, k, 1, NULL, 0, NULL);
        EV_SET(&k[0], fd, EVFILT_WRITE, EV_DELETE, 0, 0, NULL);
        kevent(ep, k, 1, NULL, 0, NULL);   /* (deleting a filter that wasn't added fails: fine) */
        return 0;
    }
    int n = 0;
    unsigned short fl = EV_ADD | ((ev->events & EPOLLET) ? EV_CLEAR : 0);
    if (ev->events & EPOLLIN) { EV_SET(&k[n], fd, EVFILT_READ, fl, 0, 0, ev->data.ptr); n++; }
    if (ev->events & EPOLLOUT) { EV_SET(&k[n], fd, EVFILT_WRITE, fl, 0, 0, ev->data.ptr); n++; }
    return kevent(ep, k, n, NULL, 0, NULL) < 0 ? -1 : 0;
}
static int epoll_wait(int ep, struct epoll_event *out, int max, int timeout_ms) {
    struct kevent k[256];
    if (max > 256) max = 256;
    struct timespec ts, *tp = NULL;
    if (timeout_ms >= 0) { ts.tv_sec = timeout_ms / 1000; ts.tv_nsec = (long)(timeout_ms % 1000) * 1000000; tp = &ts; }
    int n = kevent(ep, NULL, 0, k, max, tp);
    for (int i = 0; i < n; i++) {
        uint32_t e = k[i].filter == EVFILT_READ ? EPOLLIN : EPOLLOUT;
        if (k[i].flags & EV_EOF) e |= k[i].filter == EVFILT_READ ? EPOLLRDHUP : EPOLLHUP;
        if (k[i].flags & EV_ERROR) e |= EPOLLERR;
        out[i].events = e;
        out[i].data.ptr = k[i].udata;
    }
    return n;
}
static int vu_efd_w[65536];   /* an eventfd's stand-in: the write end of the pipe whose read end it is */
static void vu_fd_flags(int fd) {
    fcntl(fd, F_SETFL, fcntl(fd, F_GETFL) | O_NONBLOCK);
    fcntl(fd, F_SETFD, FD_CLOEXEC);
}
static int eventfd(unsigned v, int flags) {
    (void)v; (void)flags;
    int p[2];
    if (pipe(p) != 0) return -1;
    if (p[0] >= 65536) { close(p[0]); close(p[1]); errno = EMFILE; return -1; }
    vu_fd_flags(p[0]);
    vu_fd_flags(p[1]);
    vu_efd_w[p[0]] = p[1];
    return p[0];
}
static void vu_efd_signal(int efd) { uint8_t one = 1; if (write(vu_efd_w[efd], &one, 1) < 0) { /* full: already signalled */ } }
static void vu_efd_drain(int efd) { uint8_t b[64]; while (read(efd, b, sizeof b) > 0) {} }
static void vu_efd_close(int efd) { close(vu_efd_w[efd]); close(efd); }
static void vu_sock_flags(int fd) { vu_fd_flags(fd); int one = 1; setsockopt(fd, SOL_SOCKET, SO_NOSIGPIPE, &one, sizeof one); }
static int accept4(int fd, struct sockaddr *a, socklen_t *n, int flags) { (void)flags; int c = accept(fd, a, n); if (c >= 0) vu_sock_flags(c); return c; }
static int vu_pipe2(int p[2], int flags) { (void)flags; if (pipe(p) != 0) return -1; fcntl(p[0], F_SETFD, FD_CLOEXEC); fcntl(p[1], F_SETFD, FD_CLOEXEC); return 0; }
#define pipe2 vu_pipe2   /* (newer SDKs declare a pipe2 of their own) */
#ifndef MAP_NORESERVE
#define MAP_NORESERVE 0
#endif
#ifndef MAP_STACK
#define MAP_STACK 0
#endif
#else
#include <sys/epoll.h>
#include <sys/eventfd.h>
static void vu_efd_signal(int efd) { uint64_t one = 1; if (write(efd, &one, 8) < 0) { /* already signalled */ } }
static void vu_efd_drain(int efd) { uint64_t x; if (read(efd, &x, 8) < 0) { /* nothing to read */ } }
static void vu_efd_close(int efd) { close(efd); }
static void vu_sock_flags(int fd) { (void)fd; }
#endif
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <limits.h>
#if defined(__SANITIZE_ADDRESS__)
#define VU_ASAN_FIBERS 1
#elif defined(__has_feature)
#if __has_feature(address_sanitizer)
#define VU_ASAN_FIBERS 1
#endif
#endif
#if defined(__SANITIZE_THREAD__)
#define VU_TSAN_FIBERS 1
#elif defined(__has_feature)
#if __has_feature(thread_sanitizer)
#define VU_TSAN_FIBERS 1
#endif
#endif
#ifdef VU_ASAN_FIBERS
#include <sanitizer/common_interface_defs.h>
#include <sanitizer/lsan_interface.h>
/* A switched-out task's locals can sit in AddressSanitizer's "fake stack" (used to catch returns of
   pointers to locals, which Vu code can't make), and LeakSanitizer doesn't look there: it would
   report what a waiting task holds as leaked. */
const char *__asan_default_options(void) { return "detect_stack_use_after_return=0"; }
#endif
#ifdef VU_TSAN_FIBERS
#include <sanitizer/tsan_interface.h>
#endif
#if defined(__x86_64__) || defined(__aarch64__)
#define VU_ASM_SWITCH 1   /* a hand-written switch (below); ucontext elsewhere */
#else
#include <ucontext.h>
#endif
/* Inside a par loop? Only programs with par loops are built with OpenMP (VU_PAR is defined then;
   without an OpenMP compiler, as Apple's clang without libomp, par loops run on one thread). */
#if defined(VU_PAR) && defined(_OPENMP)
#include <omp.h>
#define vu_in_par() omp_in_parallel()
#else
#define vu_in_par() 0
#endif
#define VU_TASK_STACK ((size_t)8 << 20)
#define VU_TASK_GUARD ((size_t)64 << 10)
#define VU_MAX_LOOPS 256
enum { VU_W_NONE, VU_W_FD, VU_W_CHAN, VU_W_SLEEP, VU_W_SEL };
typedef struct vu_task vu_task;
typedef struct vu_loop vu_loop;
struct vu_task {
    void *sp;                     /* saved stack pointer while switched out (x86-64, ARM64) */
#ifndef VU_ASM_SWITCH
    ucontext_t uc;
#endif
    char *mem;                    /* the mapping: guard, then the stack; NULL for a thread's own context */
    void (*entry)(void *);
    void *arg;
    vu_task *next;                /* in a ready queue or a channel's wait list */
    vu_loop *loop;                /* the thread it runs on, for its whole life */
    vu_frame *top;                /* its call stack, for backtraces */
    uintptr_t lo, hi;             /* its stack, for stack-overflow reports */
    int64_t deadline;             /* when a timed wait ends (ns) */
    int64_t heap_at;              /* its place in its thread's timer heap, or -1 */
    int line;                     /* where it was spawned */
    int wait_kind, wait_line;
    void *wait_obj;               /* the socket, or the channel wait list, it waits on */
    void *wait_chan;              /* the channel it waits on */
    bool timed_out, writing;
    bool started;                 /* has run: then it stays on its thread (see vu_steal); read by other
                                     threads, so only through vu_has_started */
    bool uncounted;               /* waiting on a channel with no deadline: not counted in vu_nactive */
    int sel_state;                /* a select waiting on channels only: 1 while waiting, 2 once woken */
    void *fake_stack;             /* AddressSanitizer's per-fiber state */
    void *tsan_fiber;
};
/* A socket. It is watched by the poller of the thread whose task last waited on it (loop), and
   reader/writer/rpend/wpend are shared with pollers, so they are only touched atomically. */
typedef struct vu_sock {
    int fd;
    vu_task *reader, *writer;
    void *ssl, *tls_ctx;
    bool hs, moved;               /* moved: was watched by another thread's poller before */
    int rpend, wpend;             /* readiness that arrived while no task was waiting */
    vu_loop *loop;
} vu_sock;
/* A scheduler: one per thread that runs tasks. A task runs on its loop's thread; a thread with
   nothing to do takes new tasks from another's queue (see vu_steal), so one task that never waits
   can't hold up the new tasks queued behind it. Only tasks that haven't started move, and never a
   thread's own context (main's). */
struct vu_loop {
    int ep, efd;                  /* the poller, and an eventfd that wakes it */
    pthread_mutex_t lock;
    vu_task *rhead, *rtail;       /* made ready by other threads */
    int sleeping;                 /* in epoll_wait, so a remote wake must signal efd */
    int64_t epoch;                /* batches of events handled (see vu_retire) */
    pthread_mutex_t qlock;        /* the ready queue, which other threads may steal from */
    vu_task *qhead, *qtail;
    int64_t nready;
};
static int vu_nsleeping;          /* loops asleep in epoll_wait (that could take work)*/
static vu_loop vu_loops[VU_MAX_LOOPS];
static int vu_nloops;             /* 1 + the worker threads, once tasks are in use */
static bool vu_workers_started;
static uint32_t vu_next_loop;
static int64_t vu_nactive;        /* tasks that can still run: every task not waiting forever on a channel */
static int vu_last_wait_line;
static __thread vu_loop *vu_my;
static __thread vu_task vu_base_task;   /* the thread's own context */
static __thread vu_task *vu_cur_task, *vu_dead;
static __thread vu_task **vu_heap;
static __thread int64_t vu_nheap, vu_capheap, vu_polls;
static __thread char *vu_stack_pool[16];
static __thread int vu_nstack_pool;
static __thread uint8_t vu_iobuf[65536];

static int64_t vu_now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (int64_t)ts.tv_sec * 1000000000 + ts.tv_nsec;
}
static void vu_loop_init(vu_loop *L) {
    L->ep = epoll_create1(EPOLL_CLOEXEC);
    L->efd = eventfd(0, EFD_NONBLOCK | EFD_CLOEXEC);
    struct epoll_event ev = {.events = EPOLLIN, .data = {.ptr = NULL}};
    if (L->ep < 0 || L->efd < 0 || epoll_ctl(L->ep, EPOLL_CTL_ADD, L->efd, &ev) < 0) {
        static const char m[] = "can't start the task scheduler: out of file descriptors";
        vu_panic(0, m, sizeof m - 1);
    }
    pthread_mutex_init(&L->lock, NULL);
    pthread_mutex_init(&L->qlock, NULL);
}
/* This thread runs loop L's tasks, starting from its own context. */
static void vu_thread_tasks(vu_loop *L) {
    vu_thread_guard();
    vu_my = L;
    vu_base_task.heap_at = -1;
    vu_base_task.loop = L;
    vu_base_task.lo = vu_t_lo;
    vu_base_task.hi = vu_t_hi;
#ifdef VU_TSAN_FIBERS
    vu_base_task.tsan_fiber = __tsan_get_current_fiber();
#endif
    vu_cur_task = &vu_base_task;
}
static void vu_tasks_init(void) {
    if (vu_cur_task) return;
    /* the first task operation, on the main thread: main is the first task */
    vu_loop_init(&vu_loops[0]);
    __atomic_store_n(&vu_nloops, 1, __ATOMIC_RELEASE);
    __atomic_store_n(&vu_nactive, 1, __ATOMIC_SEQ_CST);
    vu_thread_tasks(&vu_loops[0]);
}
/* Every task operation: tasks run on the task threads, so par loop threads can't use them. */
static void vu_task_here(const char *what, int line) {
    if (vu_in_par()) {
        char m[200];
        int n = snprintf(m, sizeof m, "%s can't be used inside a par loop", what);
        vu_panic(line, m, n);
    }
    vu_tasks_init();
}
/* -- the timer heap: this thread's tasks waiting with a deadline, earliest first */
static void vu_heap_swap(int64_t i, int64_t j) {
    vu_task *t = vu_heap[i];
    vu_heap[i] = vu_heap[j];
    vu_heap[j] = t;
    vu_heap[i]->heap_at = i;
    vu_heap[j]->heap_at = j;
}
static void vu_heap_up(int64_t i) {
    while (i > 0 && vu_heap[(i - 1) / 2]->deadline > vu_heap[i]->deadline) { vu_heap_swap(i, (i - 1) / 2); i = (i - 1) / 2; }
}
static void vu_heap_down(int64_t i) {
    for (;;) {
        int64_t l = 2 * i + 1, r = l + 1, m = i;
        if (l < vu_nheap && vu_heap[l]->deadline < vu_heap[m]->deadline) m = l;
        if (r < vu_nheap && vu_heap[r]->deadline < vu_heap[m]->deadline) m = r;
        if (m == i) return;
        vu_heap_swap(i, m);
        i = m;
    }
}
static void vu_heap_add(vu_task *t) {
    if (vu_nheap == vu_capheap) {
        vu_capheap = vu_capheap ? vu_capheap * 2 : 64;
        vu_heap = (vu_task **)realloc(vu_heap, (size_t)vu_capheap * sizeof *vu_heap);
        if (!vu_heap) vu_oom();
    }
    t->heap_at = vu_nheap;
    vu_heap[vu_nheap++] = t;
    vu_heap_up(t->heap_at);
}
static void vu_heap_remove(vu_task *t) {
    int64_t i = t->heap_at;
    if (i < 0) return;
    t->heap_at = -1;
    vu_nheap--;
    if (i == vu_nheap) return;
    vu_heap[i] = vu_heap[vu_nheap];
    vu_heap[i]->heap_at = i;
    vu_heap_down(i);
    vu_heap_up(i);
}
/* -- ready queues */
static inline bool vu_has_started(vu_task *t) { return __atomic_load_n(&t->started, __ATOMIC_RELAXED); }
/* Wakes one sleeping thread other than busy, so it can take new tasks queued on busy (vu_steal). */
static void vu_wake_idle(vu_loop *busy) {
    if (__atomic_load_n(&vu_nsleeping, __ATOMIC_RELAXED) <= 0) return;
    int nl = __atomic_load_n(&vu_nloops, __ATOMIC_ACQUIRE);
    for (int i = 0; i < nl; i++)
        if (&vu_loops[i] != busy && __atomic_load_n(&vu_loops[i].sleeping, __ATOMIC_RELAXED)) {
            vu_efd_signal(vu_loops[i].efd);
            return;
        }
}
static void vu_ready(vu_task *t) {
    vu_loop *L = vu_my;
    /* (read before t is queued: once it is, another thread may take it, run it and free it) */
    bool fresh = t->mem && !vu_has_started(t);
    t->next = NULL;
    pthread_mutex_lock(&L->qlock);
    if (L->qtail) __atomic_store_n(&L->qtail->next, t, __ATOMIC_RELAXED);
    else __atomic_store_n(&L->qhead, t, __ATOMIC_RELAXED);   /* (other threads peek at qhead without the lock) */
    L->qtail = t;
    int64_t n = ++L->nready;
    pthread_mutex_unlock(&L->qlock);
    /* new work is queuing up here while another thread sleeps: wake one to take some */
    __atomic_thread_fence(__ATOMIC_SEQ_CST);
    if (n >= 2 && fresh) vu_wake_idle(L);
}
static vu_task *vu_ready_pop(void) {
    vu_loop *L = vu_my;
    if (!__atomic_load_n(&L->qhead, __ATOMIC_RELAXED)) return NULL;
    pthread_mutex_lock(&L->qlock);
    vu_task *t = L->qhead;
    if (t) {
        __atomic_store_n(&L->qhead, t->next, __ATOMIC_RELAXED);
        if (!t->next) L->qtail = NULL;
        L->nready--;
        t->next = NULL;
    }
    pthread_mutex_unlock(&L->qlock);
    return t;
}
/* Takes a ready task from another thread's queue, to run here (it moves here for good). Only a task
   that hasn't started moves: C compilers may keep the address of a thread-local variable (the
   allocator's free lists, the call stack for backtraces) in a register across a call, so a task that
   stopped partway through a function must resume on the thread it stopped on. */
static bool vu_steal(void) {
    vu_loop *me = vu_my;
    int nl = __atomic_load_n(&vu_nloops, __ATOMIC_ACQUIRE);
    if (nl < 2) return false;
    int start = (int)(me - vu_loops);
    for (int k = 1; k < nl; k++) {
        vu_loop *V = &vu_loops[(start + k) % nl];
        vu_task *t = NULL;
        if (__atomic_load_n(&V->qhead, __ATOMIC_RELAXED)) {
            pthread_mutex_lock(&V->qlock);
            /* the first task that may move (a thread's own context stays) */
            vu_task **q = &V->qhead, *prev = NULL;
            while (*q) {
                if ((*q)->mem && !vu_has_started(*q)) { t = *q; __atomic_store_n(q, t->next, __ATOMIC_RELAXED); if (V->qtail == t) V->qtail = prev; V->nready--; break; }
                prev = *q;
                q = &(*q)->next;
            }
            pthread_mutex_unlock(&V->qlock);
        }
        /* or one sent to V from another thread (spawned there) that V, busy, hasn't taken in yet */
        if (!t && __atomic_load_n(&V->rhead, __ATOMIC_RELAXED)) {
            pthread_mutex_lock(&V->lock);
            vu_task **r = &V->rhead, *rprev = NULL;
            while (*r) {
                if ((*r)->mem && !vu_has_started(*r)) {
                    t = *r;
                    __atomic_store_n(r, t->next, __ATOMIC_RELAXED);
                    if (V->rtail == t) V->rtail = rprev;
                    break;
                }
                rprev = *r;
                r = &(*r)->next;
            }
            pthread_mutex_unlock(&V->lock);
        }
        if (t) {
            t->next = NULL;
            t->loop = me;
            t->wait_kind = VU_W_NONE;
            vu_ready(t);
            return true;
        }
    }
    return false;
}
/* Makes t ready to run on its own thread: here directly, or through its thread's remote queue. */
static void vu_wake(vu_task *t) {
    vu_loop *L = t->loop;
    if (L == vu_my) {
        vu_heap_remove(t);
        t->wait_kind = VU_W_NONE;
        vu_ready(t);
        return;
    }
    bool fresh = t->mem && !vu_has_started(t);   /* (before L can take t, run it and free it) */
    pthread_mutex_lock(&L->lock);
    t->next = NULL;
    if (L->rtail) L->rtail->next = t;
    else __atomic_store_n(&L->rhead, t, __ATOMIC_RELAXED);   /* (read without the lock by vu_drain) */
    L->rtail = t;
    int sleeping = __atomic_load_n(&L->sleeping, __ATOMIC_RELAXED);
    pthread_mutex_unlock(&L->lock);
    if (sleeping) vu_efd_signal(L->efd);
    else if (fresh) {
        /* L is busy: a sleeping thread may take this new task instead */
        __atomic_thread_fence(__ATOMIC_SEQ_CST);
        vu_wake_idle(L);
    }
}
/* Takes the tasks other threads made ready. */
static void vu_drain(void) {
    vu_loop *L = vu_my;
    if (!__atomic_load_n(&L->rhead, __ATOMIC_RELAXED)) return;
    pthread_mutex_lock(&L->lock);
    vu_task *t = L->rhead;
    __atomic_store_n(&L->rhead, NULL, __ATOMIC_RELAXED);
    L->rtail = NULL;
    pthread_mutex_unlock(&L->lock);
    while (t) {
        vu_task *n = t->next;
        vu_heap_remove(t);
        t->wait_kind = VU_W_NONE;
        vu_ready(t);
        t = n;
    }
}
/* -- switching */
#ifdef __x86_64__
/* Saves the callee-saved registers and the floating-point control words on the current stack,
   stores the stack pointer in *from, and continues on the stack to. */
__attribute__((naked, noinline)) static void vu_ctx_switch(void **from, void *to) {
    __asm__ volatile(
        "pushq %rbp\n\tpushq %rbx\n\tpushq %r12\n\tpushq %r13\n\tpushq %r14\n\tpushq %r15\n\t"
        "subq $8, %rsp\n\tstmxcsr (%rsp)\n\tfnstcw 4(%rsp)\n\t"
        "movq %rsp, (%rdi)\n\tmovq %rsi, %rsp\n\t"
        "ldmxcsr (%rsp)\n\tfldcw 4(%rsp)\n\taddq $8, %rsp\n\t"
        "popq %r15\n\tpopq %r14\n\tpopq %r13\n\tpopq %r12\n\tpopq %rbx\n\tpopq %rbp\n\tret\n\t");
}
#elif defined(__aarch64__)
/* The same on ARM64: x19-x30 (x29 the frame pointer, x30 the return address), d8-d15 and FPCR in a
   176-byte frame on the current stack; then sp moves to the other task's frame, which is unpacked.
   A top-level asm function, since GCC ignores the naked attribute on ARM64. */
#ifdef __APPLE__
#define VU_SW_SYM "_vu_ctx_switch_a64"
#define VU_SW_HEAD ".private_extern " VU_SW_SYM "\n"
#else
#define VU_SW_SYM "vu_ctx_switch_a64"
#define VU_SW_HEAD ".hidden " VU_SW_SYM "\n.type " VU_SW_SYM ", %function\n"
#endif
void vu_ctx_switch_a64(void **from, void *to);
__asm__(
    ".text\n.p2align 4\n.globl " VU_SW_SYM "\n" VU_SW_HEAD VU_SW_SYM ":\n"
    "sub sp, sp, #176\n"
    "stp x19, x20, [sp, #0]\nstp x21, x22, [sp, #16]\nstp x23, x24, [sp, #32]\n"
    "stp x25, x26, [sp, #48]\nstp x27, x28, [sp, #64]\nstp x29, x30, [sp, #80]\n"
    "stp d8, d9, [sp, #96]\nstp d10, d11, [sp, #112]\nstp d12, d13, [sp, #128]\nstp d14, d15, [sp, #144]\n"
    "mrs x9, fpcr\nstr x9, [sp, #160]\n"
    "mov x9, sp\nstr x9, [x0]\nmov sp, x1\n"
    "ldr x9, [sp, #160]\nmsr fpcr, x9\n"
    "ldp x19, x20, [sp, #0]\nldp x21, x22, [sp, #16]\nldp x23, x24, [sp, #32]\n"
    "ldp x25, x26, [sp, #48]\nldp x27, x28, [sp, #64]\nldp x29, x30, [sp, #80]\n"
    "ldp d8, d9, [sp, #96]\nldp d10, d11, [sp, #112]\nldp d12, d13, [sp, #128]\nldp d14, d15, [sp, #144]\n"
    "add sp, sp, #176\nret\n");
#define vu_ctx_switch vu_ctx_switch_a64
#endif
static void vu_task_boot(void);
static void vu_reap(void) {
    vu_task *d = vu_dead;
    if (!d) return;
    vu_dead = NULL;
#ifdef VU_TSAN_FIBERS
    __tsan_destroy_fiber(d->tsan_fiber);
#endif
    if (vu_nstack_pool < 16) vu_stack_pool[vu_nstack_pool++] = d->mem;
    else {
#ifdef VU_ASAN_FIBERS
        __lsan_unregister_root_region(d->mem + VU_TASK_GUARD, VU_TASK_STACK);
#endif
        munmap(d->mem, VU_TASK_GUARD + VU_TASK_STACK);
    }
    free(d);
}
static void vu_switch_to(vu_task *t) {
    vu_task *from = vu_cur_task;
    if (t == from) return;
    if (!vu_has_started(t)) __atomic_store_n(&t->started, true, __ATOMIC_RELAXED);
    bool dying = from == vu_dead;
    from->top = vu_top;
    vu_top = t->top;
    vu_t_lo = t->lo;
    vu_t_hi = t->hi;
    vu_cur_task = t;
#ifdef VU_ASAN_FIBERS
    __sanitizer_start_switch_fiber(dying ? NULL : &from->fake_stack, (const void *)t->lo, t->hi - t->lo);
#endif
#ifdef VU_TSAN_FIBERS
    __tsan_switch_to_fiber(t->tsan_fiber, 0);
#endif
#ifdef VU_ASM_SWITCH
    vu_ctx_switch(&from->sp, t->sp);
#else
    swapcontext(&from->uc, &t->uc);
#endif
    (void)dying;
    /* back in from, which was woken */
#ifdef VU_ASAN_FIBERS
    __sanitizer_finish_switch_fiber(from->fake_stack, NULL, NULL);
#endif
    vu_reap();
}
static __attribute__((noreturn, cold)) void vu_deadlock(int line) {
    static const char m[] = "deadlock: every task is waiting on a channel, and none can be woken";
    vu_panic(line, m, sizeof m - 1);
}
/* -- sockets freed while another thread's poller may still hold an event for them: freed once every
   poller has finished the batch it was handling (each counts its batches in epoch). */
typedef struct vu_retired { struct vu_retired *next; void *p; int n; int64_t epochs[]; } vu_retired;
static pthread_mutex_t vu_retire_lock = PTHREAD_MUTEX_INITIALIZER;
static vu_retired *vu_retired_list;
static int64_t vu_nretired;
static void vu_retire(void *p) {
    int n = __atomic_load_n(&vu_nloops, __ATOMIC_ACQUIRE);
    vu_retired *r = (vu_retired *)vu_malloc(sizeof *r + (size_t)n * sizeof(int64_t));
    r->p = p;
    r->n = n;
    for (int i = 0; i < n; i++) r->epochs[i] = __atomic_load_n(&vu_loops[i].epoch, __ATOMIC_ACQUIRE);
    pthread_mutex_lock(&vu_retire_lock);
    r->next = vu_retired_list;
    vu_retired_list = r;
    __atomic_add_fetch(&vu_nretired, 1, __ATOMIC_RELAXED);
    pthread_mutex_unlock(&vu_retire_lock);
    for (int i = 0; i < n; i++)   /* a sleeping poller finishes a batch when woken */
        if (&vu_loops[i] != vu_my && __atomic_load_n(&vu_loops[i].sleeping, __ATOMIC_RELAXED)) vu_efd_signal(vu_loops[i].efd);
}
static void vu_reclaim(void) {
    if (!__atomic_load_n(&vu_nretired, __ATOMIC_RELAXED)) return;
    pthread_mutex_lock(&vu_retire_lock);
    vu_retired **q = &vu_retired_list;
    while (*q) {
        vu_retired *r = *q;
        bool done = true;
        for (int i = 0; i < r->n && done; i++)
            if (__atomic_load_n(&vu_loops[i].epoch, __ATOMIC_ACQUIRE) == r->epochs[i]) done = false;
        if (done) {
            *q = r->next;
            free(r->p);
            free(r);
            __atomic_sub_fetch(&vu_nretired, 1, __ATOMIC_RELAXED);
        } else q = &r->next;
    }
    pthread_mutex_unlock(&vu_retire_lock);
}
/* A socket became ready: wake the task waiting on it, or remember it for the next one. */
static void vu_fd_ready(vu_task **slot, int *pend) {
    vu_task *t = __atomic_exchange_n(slot, NULL, __ATOMIC_SEQ_CST);
    if (t) vu_wake(t);
    else __atomic_store_n(pend, 1, __ATOMIC_SEQ_CST);
}
/* Waits for sockets, timers and other threads, and makes the tasks they wake ready. */
static void vu_poll(void) {
    vu_loop *L = vu_my;
    vu_drain();
    vu_reclaim();
    if (__atomic_load_n(&L->qhead, __ATOMIC_RELAXED)) return;
    if (vu_steal()) return;
#ifndef VU_MALLOC
    /* values made on one thread and freed on another would pile up on the freeing thread's free lists */
    if ((++vu_polls & 255) == 0 && __atomic_load_n(&vu_nloops, __ATOMIC_RELAXED) > 1) vu_share_free();
#endif
    int timeout = -1;
    if (vu_nheap) {
        int64_t d = vu_heap[0]->deadline - vu_now_ns();
        timeout = d <= 0 ? 0 : (d / 1000000 + 1 > INT_MAX ? INT_MAX : (int)(d / 1000000 + 1));
    }
    pthread_mutex_lock(&L->lock);
    bool queued = L->rhead != NULL;
    if (!queued) __atomic_store_n(&L->sleeping, 1, __ATOMIC_SEQ_CST);
    pthread_mutex_unlock(&L->lock);
    if (queued) { vu_drain(); return; }
    __atomic_add_fetch(&vu_nsleeping, 1, __ATOMIC_SEQ_CST);
    __atomic_thread_fence(__ATOMIC_SEQ_CST);
    /* (a task queued elsewhere just before we went to sleep: take it instead) */
    if (vu_steal()) {
        __atomic_sub_fetch(&vu_nsleeping, 1, __ATOMIC_SEQ_CST);
        __atomic_store_n(&L->sleeping, 0, __ATOMIC_SEQ_CST);
        return;
    }
    struct epoll_event ev[256];
    int n = epoll_wait(L->ep, ev, 256, timeout);
    __atomic_sub_fetch(&vu_nsleeping, 1, __ATOMIC_SEQ_CST);
    __atomic_store_n(&L->sleeping, 0, __ATOMIC_RELAXED);
    for (int i = 0; i < n; i++) {
        vu_sock *s = (vu_sock *)ev[i].data.ptr;
        uint32_t e = ev[i].events;
        if (!s) {
            vu_efd_drain(L->efd);
            continue;
        }
        if (e & (EPOLLIN | EPOLLERR | EPOLLHUP | EPOLLRDHUP)) vu_fd_ready(&s->reader, &s->rpend);
        if (e & (EPOLLOUT | EPOLLERR | EPOLLHUP)) vu_fd_ready(&s->writer, &s->wpend);
    }
    __atomic_add_fetch(&L->epoch, 1, __ATOMIC_RELEASE);
    int64_t now = vu_now_ns();
    while (vu_nheap && vu_heap[0]->deadline <= now) {
        vu_task *t = vu_heap[0];
        vu_heap_remove(t);
        if (t->wait_kind == VU_W_FD) {
            vu_sock *s = (vu_sock *)t->wait_obj;
            vu_task *expected = t;
            /* if a poller took it first, its wake is on the way */
            if (!__atomic_compare_exchange_n(t->writing ? &s->writer : &s->reader, &expected, NULL, false,
                                             __ATOMIC_SEQ_CST, __ATOMIC_SEQ_CST)) continue;
        } else if (t->wait_kind == VU_W_CHAN) {
            pthread_mutex_t *cl = (pthread_mutex_t *)t->wait_chan;
            pthread_mutex_lock(cl);
            vu_task **q = (vu_task **)t->wait_obj;
            while (*q && *q != t) q = &(*q)->next;
            bool found = *q != NULL;
            if (found) *q = t->next;
            pthread_mutex_unlock(cl);
            if (!found) continue;   /* a sender or receiver woke it meanwhile */
        } else if (t->wait_kind == VU_W_SEL) {
            int one = 1;
            if (!__atomic_compare_exchange_n(&t->sel_state, &one, 2, false, __ATOMIC_SEQ_CST, __ATOMIC_SEQ_CST)) continue;
        }
        t->timed_out = true;
        t->wait_kind = VU_W_NONE;
        vu_ready(t);
    }
    vu_drain();
}
/* The current task has put itself on a wait list (or is finished): run others until it is woken. */
static void vu_block(void) {
    for (;;) {
        vu_task *t = vu_ready_pop();
        if (t) {
            vu_switch_to(t);
            return;
        }
        vu_poll();
    }
}
static int64_t vu_deadline(double seconds, bool has, int line) {
    if (!has) return -1;
    if (!(seconds >= 0)) vu_fail(line, "a timeout is 0 or more seconds, not %g", seconds);
    if (seconds > 1e9) seconds = 1e9;
    return vu_now_ns() + (int64_t)(seconds * 1e9);
}
static void vu_wait_until(int64_t deadline) {
    vu_task *t = vu_cur_task;
    t->timed_out = false;
    if (deadline >= 0) {
        t->deadline = deadline;
        vu_heap_add(t);
    }
}
/* This thread's poller watches s (it moves from another thread's poller when a task there used it). */
static void vu_sock_watch(vu_sock *s, int line) {
    vu_loop *L = vu_my;
    if (s->loop == L) return;
    if (s->loop) {
        epoll_ctl(s->loop->ep, EPOLL_CTL_DEL, s->fd, NULL);
        s->moved = true;
    }
    struct epoll_event ev = {.events = EPOLLIN | EPOLLOUT | EPOLLRDHUP | EPOLLET, .data = {.ptr = s}};
    if (epoll_ctl(L->ep, EPOLL_CTL_ADD, s->fd, &ev) < 0) vu_fail(line, "can't watch a socket: %s", strerror(errno));
    s->loop = L;
}
/* Waits until socket s is readable (or writable); false if the deadline passed first. */
static bool vu_wait_fd(vu_sock *s, bool write, int64_t deadline, int line) {
    vu_task *t = vu_cur_task;
    vu_sock_watch(s, line);
    vu_task **slot = write ? &s->writer : &s->reader;
    int *pend = write ? &s->wpend : &s->rpend;
    t->wait_kind = VU_W_FD;
    t->wait_obj = s;
    t->writing = write;
    t->wait_line = line;
    t->timed_out = false;
    __atomic_store_n(slot, t, __ATOMIC_SEQ_CST);
    if (__atomic_exchange_n(pend, 0, __ATOMIC_SEQ_CST)) {
        /* it became ready meanwhile: try again now, unless a poller is already waking this task */
        vu_task *expected = t;
        if (__atomic_compare_exchange_n(slot, &expected, NULL, false, __ATOMIC_SEQ_CST, __ATOMIC_SEQ_CST)) {
            t->wait_kind = VU_W_NONE;
            return true;
        }
    }
    vu_wait_until(deadline);
    vu_block();
    return !t->timed_out;
}
/* -- spawning */
static void vu_task_exit(void) {
    vu_dead = vu_cur_task;
    if (__atomic_sub_fetch(&vu_nactive, 1, __ATOMIC_SEQ_CST) == 0)
        vu_deadlock(__atomic_load_n(&vu_last_wait_line, __ATOMIC_RELAXED));
    vu_block();   /* never returns: the next task to run on this thread frees this one */
    __builtin_unreachable();
}
static void vu_task_boot(void) {
#ifdef VU_ASAN_FIBERS
    __sanitizer_finish_switch_fiber(NULL, NULL, NULL);
#endif
    vu_reap();
    vu_task *t = vu_cur_task;
#ifdef VU_TRACE
    vu_frame base = {"spawn", t->line, NULL};
    vu_top = &base;
#endif
    t->entry(t->arg);
    vu_task_exit();
}
static void *vu_worker(void *p) {
    vu_thread_tasks((vu_loop *)p);
    vu_base_task.wait_kind = VU_W_SLEEP;   /* never woken: this thread's own context only waits */
    vu_block();
    return NULL;
}
/* The first spawn starts the other task threads: one per core it may run on (VU_THREADS sets how many
   in all). */
static void vu_start_workers(void) {
    vu_workers_started = true;
    const char *e = getenv("VU_THREADS");
    long n = e ? strtol(e, NULL, 10) : 0;
#ifdef __linux__
    cpu_set_t cs;
    if (n <= 0 && sched_getaffinity(0, sizeof cs, &cs) == 0) n = CPU_COUNT(&cs);   /* the cores it may use (taskset) */
#endif
    if (n <= 0) n = sysconf(_SC_NPROCESSORS_ONLN);
    if (n < 1) n = 1;
    if (n > VU_MAX_LOOPS) n = VU_MAX_LOOPS;
    for (int i = 1; i < n; i++) {
        vu_loop_init(&vu_loops[i]);
        pthread_t th;
        pthread_attr_t at;
        pthread_attr_init(&at);
        pthread_attr_setdetachstate(&at, PTHREAD_CREATE_DETACHED);
        int rc = pthread_create(&th, &at, vu_worker, &vu_loops[i]);
        pthread_attr_destroy(&at);
        if (rc != 0) { close(vu_loops[i].ep); vu_efd_close(vu_loops[i].efd); break; }
        __atomic_store_n(&vu_nloops, i + 1, __ATOMIC_RELEASE);
    }
}
static void vu_task_spawn(void (*entry)(void *), void *arg, int line) {
    vu_task_here("spawn", line);
    if (!vu_workers_started) vu_start_workers();
    vu_task *t = (vu_task *)calloc(1, sizeof *t);
    if (!t) vu_oom();
    char *mem = vu_nstack_pool ? vu_stack_pool[--vu_nstack_pool] : NULL;
    if (!mem) {
        mem = (char *)mmap(NULL, VU_TASK_GUARD + VU_TASK_STACK, PROT_READ | PROT_WRITE,
                           MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE | MAP_STACK, -1, 0);
        if (mem == MAP_FAILED) vu_fail(line, "can't start a task: out of memory for its stack");
        mprotect(mem, VU_TASK_GUARD, PROT_NONE);
#ifdef VU_ASAN_FIBERS
        /* LeakSanitizer looks for pointers on thread stacks; a task's stack is memory of its own */
        __lsan_register_root_region(mem + VU_TASK_GUARD, VU_TASK_STACK);
#endif
    }
    t->mem = mem;
    t->entry = entry;
    t->arg = arg;
    t->line = line;
    t->heap_at = -1;
    t->lo = (uintptr_t)(mem + VU_TASK_GUARD);
    t->hi = (uintptr_t)(mem + VU_TASK_GUARD + VU_TASK_STACK);
#ifdef VU_TSAN_FIBERS
    t->tsan_fiber = __tsan_create_fiber(0);
#endif
#ifdef __x86_64__
    /* The first switch "returns" into vu_task_boot, with the stack as a call would leave it. */
    uintptr_t *sp = (uintptr_t *)t->hi;
    *--sp = 0;                          /* vu_task_boot's (never used) return address */
    *--sp = (uintptr_t)vu_task_boot;
    for (int i = 0; i < 6; i++) *--sp = 0;   /* rbp rbx r12 r13 r14 r15 */
    uint32_t cw[2] = {0x1F80, 0x037F};  /* the default MXCSR and x87 control word */
    sp--;
    memcpy(sp, cw, 8);
    t->sp = sp;
#elif defined(__aarch64__)
    /* a frame as vu_ctx_switch leaves it, with x30 (where ret goes) = vu_task_boot */
    uintptr_t *sp = (uintptr_t *)(t->hi - 176);
    memset(sp, 0, 176);
    sp[11] = (uintptr_t)vu_task_boot;
    t->sp = sp;
#else
    getcontext(&t->uc);
    t->uc.uc_stack.ss_sp = (void *)t->lo;
    t->uc.uc_stack.ss_size = VU_TASK_STACK;
    t->uc.uc_link = NULL;
    makecontext(&t->uc, vu_task_boot, 0);
#endif
    /* new tasks go to the threads in turn */
    int n = __atomic_load_n(&vu_nloops, __ATOMIC_ACQUIRE);
    t->loop = &vu_loops[__atomic_fetch_add(&vu_next_loop, 1, __ATOMIC_RELAXED) % (uint32_t)n];
    __atomic_add_fetch(&vu_nactive, 1, __ATOMIC_SEQ_CST);
    vu_wake(t);
}
/* os.sleep(seconds): lets other tasks run meanwhile. */
static void vu_task_sleep(vu_cap os, double seconds, int line) {
    (void)os;
    vu_task_here("os.sleep()", line);
    int64_t d = vu_deadline(seconds, true, line);
    vu_task *t = vu_cur_task;
    t->wait_kind = VU_W_SLEEP;
    t->wait_line = line;
    vu_wait_until(d);
    vu_block();
}
/* -- channels: a queue of up to cap values, shared by the tasks holding it (counted references).
   Tasks on any thread use it, under its lock. */
typedef struct vu_chan {
    pthread_mutex_t lock;         /* first: a waiting task's wait_chan points here */
    int64_t refs, cap, len, head;
    size_t esz;
    char *buf;
    bool closed;
    vu_task *rq, *sq;             /* tasks waiting to receive / to send */
    struct vu_watch *watch;       /* selects waiting for it to change */
    void (*drop)(void *);         /* frees a value left in the channel */
} vu_chan;
/* A select waiting on a channel: woken when anything changes there (a value in or out, a close). With a
   socket among its arms it waits on that socket's reader slot (sock), and is woken by taking it from the
   slot, as the timer and the poller do; otherwise through sel_state. */
typedef struct vu_watch { vu_task *t; vu_sock *sock; struct vu_watch *next; } vu_watch;
/* With c locked */
static void vu_chan_notify(vu_chan *c) {
    for (vu_watch *w = c->watch; w; w = w->next) {
        vu_task *t = w->t;
        if (w->sock) {
            vu_task *expected = t;
            if (__atomic_compare_exchange_n(&w->sock->reader, &expected, NULL, false, __ATOMIC_SEQ_CST, __ATOMIC_SEQ_CST)) vu_wake(t);
        } else {
            int one = 1;
            if (__atomic_compare_exchange_n(&t->sel_state, &one, 2, false, __ATOMIC_SEQ_CST, __ATOMIC_SEQ_CST)) vu_wake(t);
        }
    }
}
static vu_chan *vu_chan_new(int64_t cap, size_t esz, void (*drop)(void *), int line) {
    if (cap < 1 || cap > ((int64_t)1 << 40) / (int64_t)(esz ? esz : 1))
        vu_fail(line, "chan(%lld): a channel holds 1 or more values", (long long)cap);
    vu_chan *c = (vu_chan *)calloc(1, sizeof *c);
    if (!c) vu_oom();
    pthread_mutex_init(&c->lock, NULL);
    c->refs = 1;
    c->cap = cap;
    c->esz = esz;
    c->drop = drop;
    c->buf = (char *)vu_malloc((size_t)cap * esz + 1);
    return c;
}
static vu_chan *vu_chan_share(vu_chan *c) { __atomic_add_fetch(&c->refs, 1, __ATOMIC_RELAXED); return c; }
static void vu_chan_release(vu_chan **p) {
    vu_chan *c = *p;
    if (!c) return;
    *p = NULL;
    if (__atomic_sub_fetch(&c->refs, 1, __ATOMIC_ACQ_REL) > 0) return;
    if (c->drop)
        for (int64_t i = 0; i < c->len; i++) c->drop(c->buf + (size_t)((c->head + i) % c->cap) * c->esz);
    pthread_mutex_destroy(&c->lock);
    free(c->buf);
    free(c);
}
static vu_chan *vu_sig_chan;   /* os.signals(): a signal, not a task, can wake its receivers */
/* With c locked: waits on the list at head until woken (or the deadline passes); c is locked again after. */
static void vu_chan_wait(vu_chan *c, vu_task **head, int64_t deadline, int line) {
    vu_task *t = vu_cur_task;
    t->next = NULL;
    vu_task **q = head;
    while (*q) q = &(*q)->next;
    *q = t;
    t->wait_kind = VU_W_CHAN;
    t->wait_obj = (void *)head;   /* the list's head: a timeout removes t from wherever it is then */
    t->wait_chan = &c->lock;
    t->wait_line = line;
    vu_wait_until(deadline);
    if (deadline < 0 && c != __atomic_load_n(&vu_sig_chan, __ATOMIC_ACQUIRE)) {
        /* only another task can wake it: when no task is left that can, that's a deadlock */
        t->uncounted = true;
        __atomic_store_n(&vu_last_wait_line, line, __ATOMIC_RELAXED);
        if (__atomic_sub_fetch(&vu_nactive, 1, __ATOMIC_SEQ_CST) == 0) vu_deadlock(line);
    }
    pthread_mutex_unlock(&c->lock);
    vu_block();
    pthread_mutex_lock(&c->lock);
}
/* With c locked: wakes the first task on list q. */
static void vu_chan_wake(vu_task **q) {
    vu_task *t = *q;
    if (!t) return;
    *q = t->next;
    if (t->uncounted) {
        t->uncounted = false;
        __atomic_add_fetch(&vu_nactive, 1, __ATOMIC_SEQ_CST);
    }
    vu_wake(t);
}
static void vu_chan_send(vu_chan *c, const void *v, int line) {
    vu_task_here("send() on a channel", line);
    pthread_mutex_lock(&c->lock);
    while (!c->closed && c->len == c->cap) vu_chan_wait(c, &c->sq, -1, line);
    if (c->closed) { pthread_mutex_unlock(&c->lock); vu_fail(line, "send() on a closed channel"); }
    memcpy(c->buf + (size_t)((c->head + c->len) % c->cap) * c->esz, v, c->esz);
    c->len++;
    vu_chan_wake(&c->rq);
    vu_chan_notify(c);
    pthread_mutex_unlock(&c->lock);
}
/* ch.send(v, timeout: s): fails if the channel stays full that long, or is closed (v is then freed). */
static bool vu_chan_send_t(vu_chan *c, void *v, double timeout, bool has, vu_str *err, int line) {
    vu_task_here("send() on a channel", line);
    int64_t deadline = vu_deadline(timeout, has, line);
    pthread_mutex_lock(&c->lock);
    while (!c->closed && c->len == c->cap) {
        if (deadline >= 0 && vu_now_ns() >= deadline) break;
        vu_chan_wait(c, &c->sq, deadline, line);
    }
    if (c->closed || c->len == c->cap) {
        bool closed = c->closed;
        pthread_mutex_unlock(&c->lock);
        if (c->drop) c->drop(v);
        *err = vu_errf(closed ? "the channel is closed" : "timed out");
        return false;
    }
    memcpy(c->buf + (size_t)((c->head + c->len) % c->cap) * c->esz, v, c->esz);
    c->len++;
    vu_chan_wake(&c->rq);
    vu_chan_notify(c);
    pthread_mutex_unlock(&c->lock);
    return true;
}
static bool vu_chan_recv(vu_chan *c, void *out, double timeout, bool has, vu_str *err, int line) {
    vu_task_here("recv() on a channel", line);
    int64_t deadline = vu_deadline(timeout, has, line);
    pthread_mutex_lock(&c->lock);
    while (c->len == 0) {
        if (c->closed) { pthread_mutex_unlock(&c->lock); *err = vu_errf("the channel is closed"); return false; }
        if (deadline >= 0 && vu_now_ns() >= deadline) { pthread_mutex_unlock(&c->lock); *err = vu_errf("timed out"); return false; }
        vu_chan_wait(c, &c->rq, deadline, line);
    }
    memcpy(out, c->buf + (size_t)c->head * c->esz, c->esz);
    c->head = (c->head + 1) % c->cap;
    c->len--;
    vu_chan_wake(&c->sq);
    if (c->len > 0) vu_chan_wake(&c->rq);   /* another receiver can take the next value */
    vu_chan_notify(c);
    pthread_mutex_unlock(&c->lock);
    return true;
}
static void vu_chan_close(vu_chan *c, int line) {
    vu_task_here("close() on a channel", line);
    pthread_mutex_lock(&c->lock);
    c->closed = true;
    while (c->rq) vu_chan_wake(&c->rq);
    while (c->sq) vu_chan_wake(&c->sq);
    vu_chan_notify(c);
    pthread_mutex_unlock(&c->lock);
}
/* ch.closed(): whether close() was called (a closed channel is how one task tells many to stop) */
static bool vu_chan_closed(vu_chan *c) {
    pthread_mutex_lock(&c->lock);
    bool r = c->closed;
    pthread_mutex_unlock(&c->lock);
    return r;
}
/* Puts v on c without waiting, from a thread that isn't running a task; a value that doesn't fit is dropped. */
static void vu_chan_offer(vu_chan *c, const void *v) {
    pthread_mutex_lock(&c->lock);
    if (!c->closed && c->len < c->cap) {
        memcpy(c->buf + (size_t)((c->head + c->len) % c->cap) * c->esz, v, c->esz);
        c->len++;
        vu_chan_wake(&c->rq);
        vu_chan_notify(c);
    }
    pthread_mutex_unlock(&c->lock);
}
/* -- os.signals(): SIGTERM, SIGINT and SIGHUP arrive on a channel, as "TERM", "INT" and "HUP", instead of
   ending the program, so that a server can finish what it's doing and stop. The handler only writes
   the signal's number to a pipe; a thread of its own reads it and puts the name on the channel. */
static int vu_sig_pipe[2] = {-1, -1};
static pthread_mutex_t vu_sig_lock = PTHREAD_MUTEX_INITIALIZER;
static void vu_sig_handler(int sig) {
    int e = errno;
    unsigned char b = (unsigned char)sig;
    if (write(vu_sig_pipe[1], &b, 1) < 0) { /* the pipe is full: signals are already waiting */ }
    errno = e;
}
static void *vu_sig_thread(void *p) {
    (void)p;
    for (;;) {
        unsigned char b;
        ssize_t n = read(vu_sig_pipe[0], &b, 1);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) return NULL;
        const char *name = b == SIGTERM ? "TERM" : b == SIGINT ? "INT" : "HUP";
        vu_str s = vu_str_lit(name, (int64_t)strlen(name));
        vu_chan_offer(vu_sig_chan, &s);
    }
}
static vu_chan *vu_os_signals(vu_cap os, int line) {
    (void)os;
    vu_task_here("os.signals()", line);
    pthread_mutex_lock(&vu_sig_lock);
    if (!vu_sig_chan) {
        if (pipe2(vu_sig_pipe, O_CLOEXEC) != 0) {
            pthread_mutex_unlock(&vu_sig_lock);
            vu_fail(line, "can't watch for signals: %s", strerror(errno));
        }
        __atomic_store_n(&vu_sig_chan, vu_chan_new(16, sizeof(vu_str), NULL, line), __ATOMIC_RELEASE);
        pthread_t th;
        pthread_attr_t at;
        pthread_attr_init(&at);
        pthread_attr_setdetachstate(&at, PTHREAD_CREATE_DETACHED);
        if (pthread_create(&th, &at, vu_sig_thread, NULL) != 0) {
            pthread_mutex_unlock(&vu_sig_lock);
            vu_fail(line, "can't watch for signals: no thread available");
        }
        pthread_attr_destroy(&at);
        struct sigaction sa;
        memset(&sa, 0, sizeof sa);
        sa.sa_handler = vu_sig_handler;
        sa.sa_flags = SA_RESTART;
        sigemptyset(&sa.sa_mask);
        sigaction(SIGTERM, &sa, NULL);
        sigaction(SIGINT, &sa, NULL);
        sigaction(SIGHUP, &sa, NULL);
    }
    vu_chan *c = vu_chan_share(vu_sig_chan);
    pthread_mutex_unlock(&vu_sig_lock);
    return c;
}
/* -- the network: Listener and Conn are sockets, edge-triggered, watched by the poller of the thread
   whose task waits on them */
static void vu_tls_free(vu_sock *s);
static void vu_sock_drop(void *p) {
    vu_sock *s = (vu_sock *)p;
    if (s->ssl || s->tls_ctx) vu_tls_free(s);
    if (s->loop) epoll_ctl(s->loop->ep, EPOLL_CTL_DEL, s->fd, NULL);   /* (an fd that was dup'ed stays watched otherwise) */
    close(s->fd);
    /* another thread's poller may hold an event for it that it hasn't handled yet */
    if (s->loop && (s->loop != vu_my || s->moved)) vu_retire(s);
    else free(s);
}
static vu_sock *vu_sock_new(int fd, vu_str *err) {
    (void)err;
    vu_sock *s = (vu_sock *)calloc(1, sizeof *s);
    if (!s) vu_oom();
    s->fd = fd;
    return s;
}
static bool vu_tls_accepted(vu_sock *l, vu_sock *s, vu_str *err);
static bool vu_tls_recv(vu_sock *c, int64_t deadline, vu_str *out, vu_str *err, int line);
static bool vu_tls_send(vu_sock *c, const uint8_t *data, int64_t len, int64_t deadline, vu_str *err, int line);
static bool vu_net_listen(vu_cap net, int64_t port, void **out, vu_str *err, int line) {
    (void)net;
    vu_task_here("net.listen()", line);
    if (port < 0 || port > 65535) { *err = vu_errf("port %lld is not in 0..65535", (long long)port); return false; }
    int fd = socket(AF_INET, SOCK_STREAM | SOCK_NONBLOCK | SOCK_CLOEXEC, 0);
    if (fd < 0) { *err = vu_errf("can't listen on port %lld: %s", (long long)port, strerror(errno)); return false; }
    vu_sock_flags(fd);
    int one = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof one);
    struct sockaddr_in a;
    memset(&a, 0, sizeof a);
    a.sin_family = AF_INET;
    a.sin_addr.s_addr = htonl(INADDR_ANY);
    a.sin_port = htons((uint16_t)port);
    if (bind(fd, (struct sockaddr *)&a, sizeof a) < 0 || listen(fd, SOMAXCONN) < 0) {
        int e = errno;
        close(fd);
        *err = vu_errf("can't listen on port %lld: %s", (long long)port, strerror(e));
        return false;
    }
    vu_sock *s = vu_sock_new(fd, err);
    if (!s) return false;
    *out = s;
    return true;
}
/* The port a listener is on (useful after listening on port 0, which picks a free one). */
static int64_t vu_net_port(vu_cap net, void *l) {
    (void)net;
    struct sockaddr_in a;
    socklen_t n = sizeof a;
    if (getsockname(((vu_sock *)l)->fd, (struct sockaddr *)&a, &n) < 0) return 0;
    return ntohs(a.sin_port);
}
static bool vu_net_accept(vu_cap net, void *lp, double timeout, bool has, void **out, vu_str *err, int line) {
    (void)net;
    vu_task_here("net.accept()", line);
    vu_sock *l = (vu_sock *)lp;
    int64_t deadline = vu_deadline(timeout, has, line);
    for (;;) {
        int c = accept4(l->fd, NULL, NULL, SOCK_NONBLOCK | SOCK_CLOEXEC);
        if (c >= 0) {
            int one = 1;
            setsockopt(c, IPPROTO_TCP, TCP_NODELAY, &one, sizeof one);
            vu_sock *s = vu_sock_new(c, err);
            if (!s) return false;
            if (l->tls_ctx && !vu_tls_accepted(l, s, err)) { vu_sock_drop(s); return false; }
            *out = s;
            return true;
        }
        if (errno == EINTR || errno == ECONNABORTED) continue;
        if (errno == EMFILE || errno == ENFILE || errno == ENOBUFS || errno == ENOMEM) {
            /* out of file descriptors: try again shortly (closing connections frees some) */
            vu_task *t = vu_cur_task;
            t->wait_kind = VU_W_SLEEP;
            t->wait_line = line;
            int64_t soon = vu_now_ns() + 10000000;
            vu_wait_until(deadline >= 0 && deadline < soon ? deadline : soon);
            vu_block();
            if (deadline >= 0 && vu_now_ns() >= deadline) { *err = vu_errf("timed out"); return false; }
            continue;
        }
        if (errno != EAGAIN && errno != EWOULDBLOCK) { *err = vu_errf("accept failed: %s", strerror(errno)); return false; }
        if (deadline >= 0 && vu_now_ns() >= deadline) { *err = vu_errf("timed out"); return false; }
        if (!vu_wait_fd(l, false, deadline, line)) { *err = vu_errf("timed out"); return false; }
    }
}
/* The bytes that have arrived (at least one, at most about 1 MB), or "" once the other side has
   closed the connection. */
static bool vu_net_recv(vu_cap net, void *cp, double timeout, bool has, vu_str *out, vu_str *err, int line) {
    (void)net;
    vu_task_here("net.recv()", line);
    vu_sock *c = (vu_sock *)cp;
    int64_t deadline = vu_deadline(timeout, has, line);
    if (c->ssl) return vu_tls_recv(c, deadline, out, err, line);
    vu_str s = {0};
    for (;;) {
        ssize_t n = read(c->fd, vu_iobuf, sizeof vu_iobuf);
        if (n > 0) {
            vu_str_cat_bytes(&s, vu_iobuf, (int64_t)n);
            if ((size_t)n < sizeof vu_iobuf || s.len >= (1 << 20)) break;
            continue;
        }
        if (n == 0) break;
        if (errno == EINTR) continue;
        if (errno == EAGAIN || errno == EWOULDBLOCK) {
            if (s.len) break;
            if (deadline >= 0 && vu_now_ns() >= deadline) { *err = vu_errf("timed out"); return false; }
            if (!vu_wait_fd(c, false, deadline, line)) { *err = vu_errf("timed out"); return false; }
            continue;
        }
        if (s.len) break;   /* report the error on the next call */
        if (errno == ECONNRESET) break;   /* the other side is gone: like a close */
        *err = vu_errf("recv failed: %s", strerror(errno));
        return false;
    }
    *out = s;
    return true;
}
/* Sends all of data; other tasks run while the connection is full. */
static bool vu_net_send(vu_cap net, void *cp, const uint8_t *data, int64_t len, double timeout, bool has,
                        vu_str *err, int line) {
    (void)net;
    vu_task_here("net.send()", line);
    vu_sock *c = (vu_sock *)cp;
    int64_t deadline = vu_deadline(timeout, has, line);
    if (c->ssl) return vu_tls_send(c, data, len, deadline, err, line);
    while (len > 0) {
        ssize_t n = send(c->fd, data, (size_t)len, MSG_NOSIGNAL);
        if (n > 0) { data += n; len -= n; continue; }
        if (n < 0 && errno == EINTR) continue;
        if (n < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
            if (deadline >= 0 && vu_now_ns() >= deadline) { *err = vu_errf("timed out"); return false; }
            if (!vu_wait_fd(c, true, deadline, line)) { *err = vu_errf("timed out"); return false; }
            continue;
        }
        *err = errno == EPIPE || errno == ECONNRESET ? vu_errf("the connection is closed")
                                                     : vu_errf("send failed: %s", strerror(errno));
        return false;
    }
    return true;
}
/* -- connecting out. Names are looked up on a helper thread, so other tasks keep running. */
typedef struct vu_dns {
    char *host;
    char port[8];
    struct addrinfo *res;
    int rc, efd;
    int done;    /* the lookup finished (rc and res are set) */
    int refs;    /* the task and the thread: whichever lets go last frees it */
} vu_dns;
static void vu_dns_free(vu_dns *d) {
    if (d->res) freeaddrinfo(d->res);
    vu_efd_close(d->efd);
    free(d->host);
    free(d);
}
static void *vu_dns_thread(void *p) {
    vu_dns *d = (vu_dns *)p;
    struct addrinfo hints;
    memset(&hints, 0, sizeof hints);
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    d->rc = getaddrinfo(d->host, d->port, &hints, &d->res);
    __atomic_store_n(&d->done, 1, __ATOMIC_RELEASE);
    uint64_t one = 1;
    (void)one;
    vu_efd_signal(d->efd);
    if (__atomic_sub_fetch(&d->refs, 1, __ATOMIC_ACQ_REL) == 0) vu_dns_free(d);   /* the task gave up */
    return NULL;
}
static bool vu_resolve(const char *host, int64_t port, int64_t deadline, struct addrinfo **res, vu_str *err, int line) {
    struct addrinfo hints;
    memset(&hints, 0, sizeof hints);
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags = AI_NUMERICHOST;
    char ps[8];
    snprintf(ps, sizeof ps, "%lld", (long long)port);
    if (getaddrinfo(host, ps, &hints, res) == 0) return true;   /* an address, no lookup needed */
    vu_dns *d = (vu_dns *)calloc(1, sizeof *d);
    if (!d) vu_oom();
    d->host = strdup(host);
    memcpy(d->port, ps, sizeof ps);
    d->efd = eventfd(0, EFD_NONBLOCK | EFD_CLOEXEC);
    d->refs = 2;
    if (d->efd < 0 || !d->host) { *err = vu_errf("can't look up '%.200s': %s", host, strerror(errno)); free(d->host); free(d); return false; }
    vu_str e2 = {0};
    vu_sock *w = vu_sock_new(dup(d->efd), &e2);
    if (!w) { *err = e2; vu_dns_free(d); return false; }
    pthread_t th;
    pthread_attr_t at;
    pthread_attr_init(&at);
    pthread_attr_setdetachstate(&at, PTHREAD_CREATE_DETACHED);
    if (pthread_create(&th, &at, vu_dns_thread, d) != 0) {
        pthread_attr_destroy(&at);
        vu_sock_drop(w);
        vu_dns_free(d);
        *err = vu_errf("can't look up '%.200s': no thread available", host);
        return false;
    }
    pthread_attr_destroy(&at);
    while (!__atomic_load_n(&d->done, __ATOMIC_ACQUIRE)) {
        if ((deadline >= 0 && vu_now_ns() >= deadline) || !vu_wait_fd(w, false, deadline, line)) {
            if (__atomic_sub_fetch(&d->refs, 1, __ATOMIC_ACQ_REL) == 0) vu_dns_free(d);   /* finished just now */
            vu_sock_drop(w);
            *err = vu_errf("timed out looking up '%.200s'", host);
            return false;
        }
        /* read the count, so that a wake before the lookup finished leaves the next write a new edge */
        uint64_t x;
        if (read(w->fd, &x, 8) < 0) { /* not written yet */ }
    }
    vu_sock_drop(w);
    int rc = d->rc;
    struct addrinfo *got = d->res;
    d->res = NULL;
    /* the thread may still be finishing its write: whichever of the two lets go last frees d */
    if (__atomic_sub_fetch(&d->refs, 1, __ATOMIC_ACQ_REL) == 0) vu_dns_free(d);
    if (rc != 0) {
        if (got) freeaddrinfo(got);
        *err = vu_errf("can't look up '%.200s': %s", host, gai_strerror(rc));
        return false;
    }
    *res = got;
    return true;
}
/* Connects to h:port (h a C string the caller frees) by the deadline. */
static bool vu_connect_to(const char *h, int64_t port, int64_t deadline, void **out, vu_str *err, int line) {
    struct addrinfo *res = NULL;
    if (!vu_resolve(h, port, deadline, &res, err, line)) return false;
    int last = ECONNREFUSED;
    for (struct addrinfo *a = res; a; a = a->ai_next) {
        int fd = socket(a->ai_family, SOCK_STREAM | SOCK_NONBLOCK | SOCK_CLOEXEC, 0);
        if (fd < 0) { last = errno; continue; }
        vu_sock_flags(fd);
        vu_str e2 = {0};
        if (connect(fd, a->ai_addr, a->ai_addrlen) < 0 && errno != EINPROGRESS) { last = errno; close(fd); continue; }
        vu_sock *s = vu_sock_new(fd, &e2);
        if (!s) { drop_Str(&e2); last = errno; continue; }
        for (;;) {
            int soerr = 0;
            socklen_t sl = sizeof soerr;
            getsockopt(fd, SOL_SOCKET, SO_ERROR, &soerr, &sl);
            if (soerr == 0) {
                struct sockaddr_storage peer;
                socklen_t pl = sizeof peer;
                if (getpeername(fd, (struct sockaddr *)&peer, &pl) == 0) {
                    int one = 1;
                    setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &one, sizeof one);
                    freeaddrinfo(res);
                    *out = s;
                    return true;
                }
                if (errno != ENOTCONN) { soerr = errno; }
            }
            if (soerr != 0) { last = soerr; break; }
            if ((deadline >= 0 && vu_now_ns() >= deadline) || !vu_wait_fd(s, true, deadline, line)) {
                vu_sock_drop(s);
                freeaddrinfo(res);
                *err = vu_errf("timed out connecting to %.200s:%lld", h, (long long)port);
                return false;
            }
        }
        vu_sock_drop(s);
    }
    freeaddrinfo(res);
    *err = vu_errf("can't connect to %.200s:%lld: %s", h, (long long)port, strerror(last));
    return false;
}
static bool vu_net_connect(vu_cap net, const vu_str *host, int64_t port, double timeout, bool has, void **out,
                           vu_str *err, int line) {
    (void)net;
    vu_task_here("net.connect()", line);
    if (port < 1 || port > 65535) { *err = vu_errf("port %lld is not in 1..65535", (long long)port); return false; }
    char *h = vu_cpath(host, err);
    if (!h) { drop_Str(err); *err = vu_errf("a host name can't contain a zero byte"); return false; }
    int64_t deadline = vu_deadline(timeout, has, line);
    bool ok = vu_connect_to(h, port, deadline, out, err, line);
    free(h);
    return ok;
}
/* net.resolve(host): the addresses a name stands for, as text ("93.184.215.14", "2606:2800::1"), in the
   order connect would try them, each once. An address resolves to itself. */
static bool vu_net_resolve(vu_cap net, const vu_str *host, double timeout, bool has, vu_str **out, int64_t *count,
                           vu_str *err, int line) {
    (void)net;
    vu_task_here("net.resolve()", line);
    char *h = vu_cpath(host, err);
    if (!h) { drop_Str(err); *err = vu_errf("a host name can't contain a zero byte"); return false; }
    if (!*h) { free(h); *err = vu_errf("can't look up an empty host name"); return false; }
    int64_t deadline = vu_deadline(timeout, has, line);
    struct addrinfo *res = NULL;
    bool ok = vu_resolve(h, 80, deadline, &res, err, line);
    free(h);
    if (!ok) return false;
    int64_t n = 0, cap = 4;
    vu_str *items = (vu_str *)vu_malloc((size_t)cap * sizeof(vu_str));
    for (struct addrinfo *a = res; a; a = a->ai_next) {
        char buf[INET6_ADDRSTRLEN + 1];
        const void *src = NULL;
        if (a->ai_family == AF_INET) src = &((struct sockaddr_in *)a->ai_addr)->sin_addr;
        else if (a->ai_family == AF_INET6) src = &((struct sockaddr_in6 *)a->ai_addr)->sin6_addr;
        if (!src || !inet_ntop(a->ai_family, src, buf, sizeof buf)) continue;
        bool seen = false;
        for (int64_t i = 0; i < n && !seen; i++)
            seen = items[i].len == (int64_t)strlen(buf) && memcmp(items[i].data, buf, (size_t)items[i].len) == 0;
        if (seen) continue;
        if (n == cap) { cap *= 2; vu_str *m = (vu_str *)vu_malloc((size_t)cap * sizeof(vu_str)); memcpy(m, items, (size_t)n * sizeof(vu_str)); free(items); items = m; }
        items[n++] = vu_str_from_c(buf);
    }
    freeaddrinfo(res);
    *out = items;
    *count = n;
    return true;
}
#ifndef VU_TLS
static int vu_tls_pending(vu_sock *s) { (void)s; return 0; }
static void vu_tls_free(vu_sock *s) { (void)s; }
static bool vu_tls_accepted(vu_sock *l, vu_sock *s, vu_str *err) { (void)l; (void)s; (void)err; return true; }
static bool vu_tls_recv(vu_sock *c, int64_t deadline, vu_str *out, vu_str *err, int line) {
    (void)c; (void)deadline; (void)out; (void)err; (void)line; return false;
}
static bool vu_tls_send(vu_sock *c, const uint8_t *data, int64_t len, int64_t deadline, vu_str *err, int line) {
    (void)c; (void)data; (void)len; (void)deadline; (void)err; (void)line; return false;
}
#else
/* -- TLS (OpenSSL), compiled in when a program calls net.tls_connect or net.tls_listen. A TLS Conn is a
   plain one with an SSL object on top: recv and send go through it, and wait for the socket the same
   way. OpenSSL's error queue is per thread and other tasks on the same thread run in between, so each
   call clears it. */
#include <openssl/ssl.h>
#include <openssl/err.h>
#include <openssl/x509v3.h>
#include <arpa/inet.h>
static int vu_tls_pending(vu_sock *s) { return s->ssl ? SSL_pending((SSL *)s->ssl) : 0; }
/* A socket BIO that sends with MSG_NOSIGNAL: a write to a closed connection is an error, never SIGPIPE. */
static int vu_bio_write(BIO *b, const char *d, int n) {
    BIO_clear_retry_flags(b);
    ssize_t r = send((int)(intptr_t)BIO_get_data(b), d, (size_t)n, MSG_NOSIGNAL);
    if (r < 0 && (errno == EAGAIN || errno == EWOULDBLOCK || errno == EINTR)) BIO_set_retry_write(b);
    return (int)r;
}
static int vu_bio_read(BIO *b, char *d, int n) {
    BIO_clear_retry_flags(b);
    ssize_t r = recv((int)(intptr_t)BIO_get_data(b), d, (size_t)n, 0);
    if (r < 0 && (errno == EAGAIN || errno == EWOULDBLOCK || errno == EINTR)) BIO_set_retry_read(b);
    return (int)r;
}
static long vu_bio_ctrl(BIO *b, int cmd, long num, void *ptr) {
    (void)b; (void)num; (void)ptr;
    return cmd == BIO_CTRL_FLUSH ? 1 : 0;
}
static int vu_bio_create(BIO *b) { BIO_set_init(b, 1); return 1; }
static BIO_METHOD *vu_bio_method;
static SSL_CTX *vu_tls_system;   /* clients that trust the system's certificates share one context */
static pthread_once_t vu_tls_once = PTHREAD_ONCE_INIT;
static int vu_alpn_index = -1;   /* a context's ALPN list (ex_data), freed with the context */
static void vu_alpn_free(void *parent, void *ptr, CRYPTO_EX_DATA *ad, int idx, long argl, void *argp) {
    (void)parent; (void)ad; (void)idx; (void)argl; (void)argp;
    free(ptr);
}
static pthread_mutex_t vu_tls_lock = PTHREAD_MUTEX_INITIALIZER;
static void vu_tls_init(void) {
    /* no cleanup at exit: other task threads may still be using TLS when main returns */
    OPENSSL_init_ssl(OPENSSL_INIT_NO_ATEXIT, NULL);
    vu_bio_method = BIO_meth_new(BIO_get_new_index() | BIO_TYPE_SOURCE_SINK, "vu socket");
    BIO_meth_set_write(vu_bio_method, vu_bio_write);
    BIO_meth_set_read(vu_bio_method, vu_bio_read);
    BIO_meth_set_ctrl(vu_bio_method, vu_bio_ctrl);
    BIO_meth_set_create(vu_bio_method, vu_bio_create);
    vu_alpn_index = SSL_CTX_get_ex_new_index(0, NULL, NULL, NULL, vu_alpn_free);
}
static bool vu_tls_attach(vu_sock *s, SSL_CTX *ctx, vu_str *err) {
    pthread_once(&vu_tls_once, vu_tls_init);
    SSL *ssl = SSL_new(ctx);
    BIO *b = ssl ? BIO_new(vu_bio_method) : NULL;
    if (!b) {
        if (ssl) SSL_free(ssl);
        ERR_clear_error();
        *err = vu_errf("can't start TLS: out of memory");
        return false;
    }
    BIO_set_data(b, (void *)(intptr_t)s->fd);
    SSL_set_bio(ssl, b, b);
    s->ssl = ssl;
    return true;
}
static void vu_tls_free(vu_sock *s) {
    if (s->ssl) {
        ERR_clear_error();
        if (s->hs) SSL_shutdown((SSL *)s->ssl);   /* one try at close_notify; the socket closes either way */
        SSL_free((SSL *)s->ssl);
    }
    if (s->tls_ctx) SSL_CTX_free((SSL_CTX *)s->tls_ctx);
    ERR_clear_error();
}
static SSL_CTX *vu_tls_ctx(bool server) {
    pthread_once(&vu_tls_once, vu_tls_init);
    SSL_CTX *ctx = SSL_CTX_new(server ? TLS_server_method() : TLS_client_method());
    if (!ctx) vu_oom();
    SSL_CTX_set_min_proto_version(ctx, TLS1_2_VERSION);
    /* A peer that closes without close_notify reads as a close, as with plain TCP. Idle connections
       give their buffers back (RELEASE_BUFFERS): 26 KB each instead of 37, at no measured cost. */
    SSL_CTX_set_options(ctx, SSL_OP_IGNORE_UNEXPECTED_EOF);
    SSL_CTX_set_mode(ctx, SSL_MODE_ENABLE_PARTIAL_WRITE | SSL_MODE_ACCEPT_MOVING_WRITE_BUFFER | SSL_MODE_RELEASE_BUFFERS);
    if (!server) SSL_CTX_set_verify(ctx, SSL_VERIFY_PEER, NULL);
    return ctx;
}
static int vu_no_password(char *b, int n, int rw, void *u) { (void)b; (void)n; (void)rw; (void)u; return 0; }
static BIO *vu_pem_bio(const vu_str *pem) {
    return BIO_new_mem_buf(pem->data ? (const void *)pem->data : (const void *)"", (int)pem->len);
}
/* What OpenSSL says went wrong, as words ("certificate verify failed"), or fallback. */
static const char *vu_tls_reason(const char *fallback) {
    unsigned long e = ERR_peek_last_error();
    const char *r = e ? ERR_reason_error_string(e) : NULL;
    return r ? r : fallback;
}
/* After an SSL call returned r <= 0: 1 when it should be tried again (it waited for the socket),
   -1 when the deadline passed, 0 on an error (*kind is SSL_get_error's answer). */
static int vu_tls_again(vu_sock *s, int r, int64_t deadline, int line, int *kind) {
    int k = SSL_get_error((SSL *)s->ssl, r);
    *kind = k;
    if (k != SSL_ERROR_WANT_READ && k != SSL_ERROR_WANT_WRITE) return 0;
    if (deadline >= 0 && vu_now_ns() >= deadline) return -1;
    if (!vu_wait_fd(s, k == SSL_ERROR_WANT_WRITE, deadline, line)) return -1;
    return 1;
}
/* Runs the handshake if it hasn't happened yet (a server's connections do it on first use). */
static bool vu_tls_handshake(vu_sock *s, int64_t deadline, vu_str *err, int line) {
    while (!s->hs) {
        ERR_clear_error();
        int r = SSL_do_handshake((SSL *)s->ssl);
        if (r == 1) { s->hs = true; break; }
        int k, a = vu_tls_again(s, r, deadline, line, &k);
        if (a > 0) continue;
        if (a < 0) { *err = vu_errf("timed out"); return false; }
        long v = SSL_get_verify_result((SSL *)s->ssl);
        if (v != X509_V_OK && !SSL_is_server((SSL *)s->ssl))
            *err = vu_errf("can't verify the server's certificate: %s", X509_verify_cert_error_string(v));
        else if (k == SSL_ERROR_SYSCALL || k == SSL_ERROR_ZERO_RETURN)
            *err = vu_errf("the TLS handshake failed: the connection closed");
        else
            *err = vu_errf("the TLS handshake failed: %s", vu_tls_reason("unknown error"));
        ERR_clear_error();
        return false;
    }
    return true;
}
static bool vu_tls_accepted(vu_sock *l, vu_sock *s, vu_str *err) {
    if (!vu_tls_attach(s, (SSL_CTX *)l->tls_ctx, err)) return false;
    SSL_set_accept_state((SSL *)s->ssl);
    return true;
}
static bool vu_tls_recv(vu_sock *c, int64_t deadline, vu_str *out, vu_str *err, int line) {
    if (!vu_tls_handshake(c, deadline, err, line)) return false;
    vu_str s = {0};
    for (;;) {
        ERR_clear_error();
        int n = SSL_read((SSL *)c->ssl, vu_iobuf, (int)sizeof vu_iobuf);
        if (n > 0) {
            vu_str_cat_bytes(&s, vu_iobuf, (int64_t)n);
            /* Stop after a short record with nothing left decrypted: reading on would only find the
               socket empty (one wasted syscall per request). Full records usually have more behind them. */
            if (s.len >= (1 << 20) || (n < 16384 && SSL_pending((SSL *)c->ssl) == 0)) break;
            continue;
        }
        int k = SSL_get_error((SSL *)c->ssl, n);
        if (k == SSL_ERROR_ZERO_RETURN) break;   /* closed */
        if (k == SSL_ERROR_WANT_READ || k == SSL_ERROR_WANT_WRITE) {
            if (s.len) break;
            if ((deadline >= 0 && vu_now_ns() >= deadline) || !vu_wait_fd(c, k == SSL_ERROR_WANT_WRITE, deadline, line)) {
                *err = vu_errf("timed out");
                return false;
            }
            continue;
        }
        if (s.len) break;   /* report the error on the next call */
        if (k == SSL_ERROR_SYSCALL && (errno == 0 || errno == ECONNRESET)) break;   /* the other side is gone */
        *err = vu_errf("recv failed: %s", vu_tls_reason(k == SSL_ERROR_SYSCALL ? strerror(errno) : "TLS error"));
        ERR_clear_error();
        return false;
    }
    ERR_clear_error();
    *out = s;
    return true;
}
static bool vu_tls_send(vu_sock *c, const uint8_t *data, int64_t len, int64_t deadline, vu_str *err, int line) {
    if (!vu_tls_handshake(c, deadline, err, line)) return false;
    while (len > 0) {
        ERR_clear_error();
        int n = SSL_write((SSL *)c->ssl, data, len > (1 << 30) ? (1 << 30) : (int)len);
        if (n > 0) { data += n; len -= n; continue; }
        int k, a = vu_tls_again(c, n, deadline, line, &k);
        if (a > 0) continue;
        if (a < 0) { *err = vu_errf("timed out"); return false; }
        if (k == SSL_ERROR_ZERO_RETURN || (k == SSL_ERROR_SYSCALL && (errno == EPIPE || errno == ECONNRESET || errno == 0)))
            *err = vu_errf("the connection is closed");
        else
            *err = vu_errf("send failed: %s", vu_tls_reason("TLS error"));
        ERR_clear_error();
        return false;
    }
    return true;
}
/* net.tls_listen(port, cert: pem, key: pem): the certificate (then any intermediate certificates) and
   its private key, as PEM text. */
/* "h2,http/1.1" -> a length byte, then the wire form: 2 h2 8 http/1.1 (NULL and *err if it's malformed) */
static unsigned char *vu_alpn_wire(const vu_str *alpn, vu_str *err) {
    unsigned char *wire = (unsigned char *)vu_malloc((size_t)alpn->len + 3);
    size_t w = 1, start = 0;
    for (size_t i = 0; i <= (size_t)alpn->len; i++) {
        if (i < (size_t)alpn->len && alpn->data[i] != ',') continue;
        size_t n = i - start;
        if (n == 0 || n > 255) { free(wire); *err = vu_errf("alpn: a comma-separated list of protocol names, like \"h2,http/1.1\""); return NULL; }
        wire[w++] = (unsigned char)n;
        memcpy(wire + w, alpn->data + start, n);
        w += n;
        start = i + 1;
    }
    if (w - 1 > 255) { free(wire); *err = vu_errf("alpn: the list is too long"); return NULL; }
    wire[0] = (unsigned char)(w - 1);
    return wire;
}
/* ALPN: the server picks the first of its protocols (alpn: "h2,http/1.1") that the client offers. */
static int vu_alpn_pick(SSL *ssl, const unsigned char **out, unsigned char *outlen, const unsigned char *in, unsigned inlen, void *arg) {
    (void)ssl;
    const unsigned char *ours = (const unsigned char *)arg;
    unsigned char *o;
    if (SSL_select_next_proto(&o, outlen, ours + 1, ours[0], in, inlen) != OPENSSL_NPN_NEGOTIATED) return SSL_TLSEXT_ERR_NOACK;
    *out = o;
    return SSL_TLSEXT_ERR_OK;
}
static bool vu_net_tls_listen_alpn(vu_cap net, int64_t port, const vu_str *cert, const vu_str *key, const vu_str *alpn,
                                   void **out, vu_str *err, int line);
static bool vu_net_tls_listen(vu_cap net, int64_t port, const vu_str *cert, const vu_str *key, void **out, vu_str *err,
                              int line) {
    return vu_net_tls_listen_alpn(net, port, cert, key, NULL, out, err, line);
}
static bool vu_net_tls_listen_alpn(vu_cap net, int64_t port, const vu_str *cert, const vu_str *key, const vu_str *alpn,
                                   void **out, vu_str *err, int line) {
    vu_task_here("net.tls_listen()", line);
    unsigned char *wire = NULL;
    if (alpn && !(wire = vu_alpn_wire(alpn, err))) return false;
    if (cert->len > (1 << 24) || key->len > (1 << 24)) { *err = vu_errf("the certificate or key is too long"); return false; }
    ERR_clear_error();
    SSL_CTX *ctx = vu_tls_ctx(true);
    /* the ALPN list lives as long as the context (connections accepted from this listener hold it
       too), and is freed with it on every path */
    if (wire) SSL_CTX_set_ex_data(ctx, vu_alpn_index, wire);
    BIO *b = vu_pem_bio(cert);
    X509 *x = b ? PEM_read_bio_X509(b, NULL, vu_no_password, NULL) : NULL;
    if (!x || SSL_CTX_use_certificate(ctx, x) != 1) {
        if (x) X509_free(x);
        if (b) BIO_free(b);
        SSL_CTX_free(ctx);
        ERR_clear_error();
        *err = vu_errf("cert: no certificate found in the PEM text");
        return false;
    }
    X509_free(x);
    while ((x = PEM_read_bio_X509(b, NULL, vu_no_password, NULL)))
        if (SSL_CTX_add_extra_chain_cert(ctx, x) != 1) X509_free(x);   /* on success the context owns it */
    BIO_free(b);
    ERR_clear_error();
    b = vu_pem_bio(key);
    EVP_PKEY *k = b ? PEM_read_bio_PrivateKey(b, NULL, vu_no_password, NULL) : NULL;
    if (b) BIO_free(b);
    if (!k) {
        SSL_CTX_free(ctx);
        ERR_clear_error();
        *err = vu_errf("key: no private key found in the PEM text (keys protected by a password aren't supported)");
        return false;
    }
    int used = SSL_CTX_use_PrivateKey(ctx, k);
    EVP_PKEY_free(k);
    if (used != 1 || SSL_CTX_check_private_key(ctx) != 1) {
        SSL_CTX_free(ctx);
        ERR_clear_error();
        *err = vu_errf("key: the private key doesn't match the certificate");
        return false;
    }
    if (!vu_net_listen(net, port, out, err, line)) { SSL_CTX_free(ctx); return false; }
    if (wire) SSL_CTX_set_alpn_select_cb(ctx, vu_alpn_pick, wire);
    ((vu_sock *)*out)->tls_ctx = ctx;
    return true;
}
/* net.tls_connect(host, port, ca: pem, timeout: s): checks the server's certificate against the system's
   certificates (or only the ones in ca) and that it is for host. */
static bool vu_net_tls_connect(vu_cap net, const vu_str *host, int64_t port, const vu_str *ca, const vu_str *alpn, double timeout,
                               bool has, void **out, vu_str *err, int line) {
    (void)net;
    vu_task_here("net.tls_connect()", line);
    if (port < 1 || port > 65535) { *err = vu_errf("port %lld is not in 1..65535", (long long)port); return false; }
    unsigned char *wire = NULL;
    if (alpn && !(wire = vu_alpn_wire(alpn, err))) return false;
    char *h = vu_cpath(host, err);
    if (!h) { free(wire); drop_Str(err); *err = vu_errf("a host name can't contain a zero byte"); return false; }
    int64_t deadline = vu_deadline(timeout, has, line);
    ERR_clear_error();
    SSL_CTX *ctx;
    if (ca) {
        if (ca->len > (1 << 24)) { free(wire); free(h); *err = vu_errf("ca: the PEM text is too long"); return false; }
        ctx = vu_tls_ctx(false);
        X509_STORE *st = SSL_CTX_get_cert_store(ctx);
        BIO *b = vu_pem_bio(ca);
        int n = 0;
        X509 *x;
        while (b && (x = PEM_read_bio_X509(b, NULL, vu_no_password, NULL))) { X509_STORE_add_cert(st, x); X509_free(x); n++; }
        if (b) BIO_free(b);
        ERR_clear_error();
        if (!n) { free(wire); SSL_CTX_free(ctx); free(h); *err = vu_errf("ca: no certificate found in the PEM text"); return false; }
    } else {
        pthread_mutex_lock(&vu_tls_lock);
        if (!vu_tls_system) {
            SSL_CTX *sys = vu_tls_ctx(false);
            SSL_CTX_set_default_verify_paths(sys);
            ERR_clear_error();
            vu_tls_system = sys;
        }
        ctx = vu_tls_system;
        SSL_CTX_up_ref(ctx);
        pthread_mutex_unlock(&vu_tls_lock);
    }
    void *sp = NULL;
    if (!vu_connect_to(h, port, deadline, &sp, err, line)) { free(wire); SSL_CTX_free(ctx); free(h); return false; }
    vu_sock *s = (vu_sock *)sp;
    bool ok = vu_tls_attach(s, ctx, err);
    SSL_CTX_free(ctx);   /* the SSL object keeps its own reference */
    if (ok) {
        SSL *ssl = (SSL *)s->ssl;
        unsigned char ip[16];
        bool is_ip = inet_pton(AF_INET, h, ip) == 1 || inet_pton(AF_INET6, h, ip) == 1;
        if (is_ip) X509_VERIFY_PARAM_set1_ip_asc(SSL_get0_param(ssl), h);
        else { SSL_set_tlsext_host_name(ssl, h); SSL_set1_host(ssl, h); }
        if (wire) SSL_set_alpn_protos(ssl, wire + 1, wire[0]);
        SSL_set_connect_state(ssl);
        ok = vu_tls_handshake(s, deadline, err, line);
        if (!ok) {
            vu_str e = *err;
            *err = vu_errf("%.200s:%lld: %.*s", h, (long long)port, (int)e.len, (const char *)e.data);
            drop_Str(&e);
        }
    }
    free(h);
    free(wire);
    if (!ok) { vu_sock_drop(s); return false; }
    *out = s;
    return true;
}
/* net.start_tls(&conn, host, ca:, timeout:): TLS on a connection that's already open (STARTTLS, as
   PostgreSQL and SMTP do it), with the same checks as tls_connect. */
static bool vu_net_start_tls(vu_cap net, void **conn, const vu_str *host, const vu_str *ca, double timeout, bool has,
                             vu_str *err, int line) {
    (void)net;
    vu_task_here("net.start_tls()", line);
    vu_sock *s = (vu_sock *)*conn;
    if (!s) { *err = vu_errf("net.start_tls(): the connection is closed"); return false; }
    if (s->ssl) { *err = vu_errf("net.start_tls(): the connection already uses TLS"); return false; }
    char *h = vu_cpath(host, err);
    if (!h) { drop_Str(err); *err = vu_errf("a host name can't contain a zero byte"); return false; }
    int64_t deadline = vu_deadline(timeout, has, line);
    ERR_clear_error();
    SSL_CTX *ctx;
    if (ca) {
        if (ca->len > (1 << 24)) { free(h); *err = vu_errf("ca: the PEM text is too long"); return false; }
        ctx = vu_tls_ctx(false);
        X509_STORE *st = SSL_CTX_get_cert_store(ctx);
        BIO *b = vu_pem_bio(ca);
        int n = 0;
        X509 *x;
        while (b && (x = PEM_read_bio_X509(b, NULL, vu_no_password, NULL))) { X509_STORE_add_cert(st, x); X509_free(x); n++; }
        if (b) BIO_free(b);
        ERR_clear_error();
        if (!n) { SSL_CTX_free(ctx); free(h); *err = vu_errf("ca: no certificate found in the PEM text"); return false; }
    } else {
        pthread_mutex_lock(&vu_tls_lock);
        if (!vu_tls_system) {
            SSL_CTX *sys = vu_tls_ctx(false);
            SSL_CTX_set_default_verify_paths(sys);
            ERR_clear_error();
            vu_tls_system = sys;
        }
        ctx = vu_tls_system;
        SSL_CTX_up_ref(ctx);
        pthread_mutex_unlock(&vu_tls_lock);
    }
    bool ok = vu_tls_attach(s, ctx, err);
    SSL_CTX_free(ctx);
    if (ok) {
        SSL *ssl = (SSL *)s->ssl;
        unsigned char ip[16];
        bool is_ip = inet_pton(AF_INET, h, ip) == 1 || inet_pton(AF_INET6, h, ip) == 1;
        if (is_ip) X509_VERIFY_PARAM_set1_ip_asc(SSL_get0_param(ssl), h);
        else { SSL_set_tlsext_host_name(ssl, h); SSL_set1_host(ssl, h); }
        SSL_set_connect_state(ssl);
        ok = vu_tls_handshake(s, deadline, err, line);
        if (!ok) {
            vu_str e = *err;
            *err = vu_errf("%.200s: %.*s", h, (int)e.len, (const char *)e.data);
            drop_Str(&e);
        }
    }
    free(h);
    if (!ok) { vu_sock_drop(s); *conn = NULL; return false; }
    return true;
}
/* net.protocol(conn): the protocol chosen by ALPN on a TLS connection ("h2"), else "" */
static vu_str vu_net_protocol(vu_cap net, void *c) {
    (void)net;
    vu_sock *s = (vu_sock *)c;
    const unsigned char *p = NULL;
    unsigned n = 0;
    if (s && s->ssl) SSL_get0_alpn_selected((SSL *)s->ssl, &p, &n);
    vu_str r = {0};
    if (n) vu_str_cat_bytes(&r, p, (int64_t)n);
    return r;
}
#endif
/* -- select: waits until one of its arms can go ahead, then does it. Arms: take a value from a channel
   (or see it closed), put one in, see a channel closed, see data on a connection (or its end). */
#include <poll.h>
enum { VU_SEL_RECV, VU_SEL_SEND, VU_SEL_CLOSED, VU_SEL_READABLE, VU_SEL_OFF };
static __thread uint64_t vu_sel_rng;
static uint64_t vu_rand_u64(void) {
    uint64_t x = vu_sel_rng ? vu_sel_rng : (uint64_t)(uintptr_t)&vu_sel_rng ^ (uint64_t)vu_now_ns();
    x ^= x << 13; x ^= x >> 7; x ^= x << 17;
    vu_sel_rng = x;
    return x;
}
typedef struct { int kind; vu_chan *ch; void *buf; vu_sock *sock; } vu_sel;
/* Whether arm a can go ahead now; a recv or send arm does its part if so. */
static bool vu_sel_try(vu_sel *a) {
    if (a->kind == VU_SEL_OFF) return false;
    if (a->kind == VU_SEL_READABLE) {
        if (vu_tls_pending(a->sock) > 0) return true;
        struct pollfd p = {.fd = a->sock->fd, .events = POLLIN};
        return poll(&p, 1, 0) > 0;
    }
    vu_chan *c = a->ch;
    bool ok = false;
    pthread_mutex_lock(&c->lock);
    if (a->kind == VU_SEL_CLOSED) ok = c->closed && c->len == 0;   /* (closed, and nothing left to take) */
    else if (a->kind == VU_SEL_RECV && c->len > 0) {
        memcpy(a->buf, c->buf + (size_t)c->head * c->esz, c->esz);
        c->head = (c->head + 1) % c->cap;
        c->len--;
        vu_chan_wake(&c->sq);
        if (c->len > 0) vu_chan_wake(&c->rq);
        vu_chan_notify(c);
        ok = true;
    } else if (a->kind == VU_SEL_SEND && !c->closed && c->len < c->cap) {
        memcpy(c->buf + (size_t)((c->head + c->len) % c->cap) * c->esz, a->buf, c->esz);
        c->len++;
        vu_chan_wake(&c->rq);
        vu_chan_notify(c);
        ok = true;
    }
    pthread_mutex_unlock(&c->lock);
    return ok;
}
static void vu_watch_drop(vu_chan *c, vu_watch *w) {
    pthread_mutex_lock(&c->lock);
    vu_watch **q = &c->watch;
    while (*q && *q != w) q = &(*q)->next;
    if (*q) *q = w->next;
    pthread_mutex_unlock(&c->lock);
}
/* The arm that went ahead (its index), or n when the deadline came first. Arms are tried from a
   random one on, so a busy one can't keep the others waiting forever. */
static int vu_select(vu_sel *a, int n, double timeout, bool has, int line) {
    vu_task_here("select", line);
    int64_t deadline = vu_deadline(timeout, has, line);
    vu_task *t = vu_cur_task;
    vu_sock *sock = NULL;
    int live = 0;
    for (int i = 0; i < n; i++) {
        if (a[i].kind == VU_SEL_READABLE) sock = a[i].sock;
        if (a[i].kind != VU_SEL_OFF) live++;
    }
    if (!live && !has) vu_fail(line, "select: every arm's condition is false, and there's no timeout: it would wait forever");
    vu_watch ws[64];
    if (n > 64) vu_fail(line, "a select has at most 64 arms");
    int start = n ? (int)(vu_rand_u64() % (uint64_t)n) : 0;
    for (;;) {
        for (int k = 0; k < n; k++) {
            int i = (start + k) % n;
            if (vu_sel_try(&a[i])) return i;
        }
        if (deadline >= 0 && vu_now_ns() >= deadline) return n;
        /* wait: watch every channel, then look once more (what changed meanwhile has woken this task) */
        if (sock) vu_sock_watch(sock, line);
        else __atomic_store_n(&t->sel_state, 1, __ATOMIC_SEQ_CST);
        t->wait_kind = sock ? VU_W_FD : VU_W_SEL;
        t->wait_obj = sock;
        t->writing = false;
        t->wait_line = line;
        t->timed_out = false;
        if (sock) __atomic_store_n(&sock->reader, t, __ATOMIC_SEQ_CST);
        for (int i = 0; i < n; i++) {
            ws[i].t = t;
            ws[i].sock = sock;
            ws[i].next = NULL;
            if (a[i].kind == VU_SEL_READABLE || a[i].kind == VU_SEL_OFF) continue;
            pthread_mutex_lock(&a[i].ch->lock);
            ws[i].next = a[i].ch->watch;
            a[i].ch->watch = &ws[i];
            pthread_mutex_unlock(&a[i].ch->lock);
        }
        int got = -1;
        for (int k = 0; k < n && got < 0; k++) {
            int i = (start + k) % n;
            if (vu_sel_try(&a[i])) got = i;
        }
        bool woken = false;   /* someone has woken (or is waking) this task: that wake must be taken */
        if (got >= 0 || (sock && __atomic_exchange_n(&sock->rpend, 0, __ATOMIC_SEQ_CST))) {
            if (sock) {
                vu_task *expected = t;
                woken = !__atomic_compare_exchange_n(&sock->reader, &expected, NULL, false, __ATOMIC_SEQ_CST, __ATOMIC_SEQ_CST);
            } else {
                int one = 1;
                woken = !__atomic_compare_exchange_n(&t->sel_state, &one, 0, false, __ATOMIC_SEQ_CST, __ATOMIC_SEQ_CST);
            }
            if (woken) vu_block();
        } else {
            vu_wait_until(deadline);
            vu_block();
        }
        vu_heap_remove(t);
        t->wait_kind = VU_W_NONE;
        __atomic_store_n(&t->sel_state, 0, __ATOMIC_SEQ_CST);
        for (int i = 0; i < n; i++) if (a[i].kind != VU_SEL_READABLE && a[i].kind != VU_SEL_OFF) vu_watch_drop(a[i].ch, &ws[i]);
        if (got >= 0) return got;
        start = (start + 1) % (n ? n : 1);
    }
}
static void drop_X_Conn(void **p) { if (*p) { vu_sock_drop(*p); *p = NULL; } }
static void drop_X_Listener(void **p) { if (*p) { vu_sock_drop(*p); *p = NULL; } }