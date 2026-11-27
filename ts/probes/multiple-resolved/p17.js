new Promise(resolve => {
    let timer;
    const finish = () => {
        clearTimeout(timer);
        resolve();
    };
    timer = setTimeout(finish, ms);
})