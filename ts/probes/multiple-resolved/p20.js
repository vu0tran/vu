new Promise(resolve => {
    let frame;
    const finish = () => {
        cancelAnimationFrame(frame);
        resolve();
    };
    frame = requestAnimationFrame(finish);
})