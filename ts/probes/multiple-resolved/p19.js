new Promise(resolve => {
    let timer;
    const finish = () => {
        clearInterval(timer);
        resolve();
    };
    timer = setInterval(finish, ms);
})