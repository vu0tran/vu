new Promise(async (resolve, reject) => {
    try {
        const r = await foo();
        resolve(new r());
    } catch (error) {
        reject(error);
    }
})