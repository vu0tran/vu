new Promise(async (resolve, reject) => {
    try {
        const r = await foo();
        resolve(r);
    } catch (error) {
        reject(error);
    }
})