new Promise(async (resolve, reject) => {
    try {
        const r = await foo();
        resolve(r.foo);
    } catch (error) {
        reject(error);
    }
})