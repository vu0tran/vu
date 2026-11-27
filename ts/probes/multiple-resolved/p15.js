new Promise(async (resolve, reject) => {
    let a;
    try {
        const r = await foo();
        resolve();
        if(r) return;
    } catch (error) {
        reject(error);
    }
})