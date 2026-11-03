/* vknip's terminal and file-watching glue: isatty, the terminal's width, and inotify (Linux) for
   --watch. Elsewhere vk_watch_open returns -1 and vknip polls. */
#include <unistd.h>
#include <sys/ioctl.h>
#include <poll.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#ifdef __linux__
#include <sys/inotify.h>
#endif

bool vk_isatty(int64_t fd) { return isatty((int)fd) == 1; }

int64_t vk_columns(int64_t fd) {
    struct winsize w;
    if (ioctl((int)fd, TIOCGWINSZ, &w) == 0 && w.ws_col > 0) return w.ws_col;
    return 0;
}

int64_t vk_watch_open(void) {
#ifdef __linux__
    return inotify_init1(IN_CLOEXEC);
#else
    return -1;
#endif
}

int64_t vk_watch_add(int64_t fd, const vu_str *path) {
#ifdef __linux__
    char buf[4096];
    if (path->len >= (int64_t)sizeof buf) return -1;
    memcpy(buf, path->data, path->len);
    buf[path->len] = 0;
    return inotify_add_watch((int)fd, buf, IN_CREATE | IN_DELETE | IN_MODIFY | IN_MOVED_FROM | IN_MOVED_TO | IN_CLOSE_WRITE | IN_DELETE_SELF | IN_ONLYDIR);
#else
    (void)fd; (void)path;
    return -1;
#endif
}

/* Waits up to timeout_ms for events; returns them as lines "wd \t kind \t name \n" (kind: c created,
   d deleted, m modified, D a created folder, X a deleted folder), "" when none came. */
vu_str vk_watch_read(int64_t fd, int64_t timeout_ms) {
#ifdef __linux__
    struct pollfd p = { (int)fd, POLLIN, 0 };
    if (poll(&p, 1, (int)timeout_ms) <= 0) return vu_str_from("", 0);
    char buf[65536] __attribute__((aligned(__alignof__(struct inotify_event))));
    ssize_t n = read((int)fd, buf, sizeof buf);
    if (n <= 0) return vu_str_from("", 0);
    size_t cap = 1024, len = 0;
    char *out = malloc(cap);
    for (char *q = buf; q < buf + n;) {
        struct inotify_event *e = (struct inotify_event *)q;
        char kind = 'm';
        bool dir = (e->mask & IN_ISDIR) != 0;
        if (e->mask & (IN_CREATE | IN_MOVED_TO)) kind = dir ? 'D' : 'c';
        else if (e->mask & (IN_DELETE | IN_MOVED_FROM)) kind = dir ? 'X' : 'd';
        else if (e->mask & IN_DELETE_SELF) kind = 'X';
        size_t nl = e->len ? strlen(e->name) : 0;
        size_t need = len + nl + 48;
        if (need > cap) { while (need > cap) cap *= 2; out = realloc(out, cap); }
        len += (size_t)snprintf(out + len, cap - len, "%d\t%c\t", e->wd, kind);
        memcpy(out + len, e->name, nl);
        len += nl;
        out[len++] = '\n';
        q += sizeof(struct inotify_event) + e->len;
    }
    vu_str r = vu_str_from(out, (int64_t)len);
    free(out);
    return r;
#else
    (void)fd;
    usleep((useconds_t)(timeout_ms * 1000));
    return vu_str_from("", 0);
#endif
}
