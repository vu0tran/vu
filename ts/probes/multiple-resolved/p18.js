const abortableDelay = (ms, signal) =>
    new Promise(resolve => {
        let timer;
        const finish = () => {
            clearTimeout(timer);
            signal?.removeEventListener('abort', finish);
            resolve();
        };
        timer = setTimeout(finish, ms);
        if (signal?.aborted) {
            finish();
            return;
        }
        signal?.addEventListener('abort', finish);
    })