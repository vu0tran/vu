new Promise(async (resolve, reject) => {
    try {
        const r = await foo();
        resolve(import(r));
    } catch (error) {
        reject(error);
    }
})