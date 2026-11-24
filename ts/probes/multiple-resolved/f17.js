new Promise(async (resolve, reject) => {
    let a;
    try {
        const r = await foo();
        resolve();
        import(r);
    } catch (error) {
        reject(error);
    }
})