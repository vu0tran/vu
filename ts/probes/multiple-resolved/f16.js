new Promise(async (resolve, reject) => {
    let a;
    try {
        const r = await foo();
        resolve();
        a = new r();
    } catch (error) {
        reject(error);
    }
})