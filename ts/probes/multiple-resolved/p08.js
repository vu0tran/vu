new Promise(async (resolve, reject) => {
    try {
        await foo();
        resolve();
    } catch (error) {
        reject(error);
    }
})