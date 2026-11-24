new Promise(async (resolve, reject) => {
    let a;
    try {
        const r = await foo();
        resolve();
        a = r.foo;
    } catch (error) {
        reject(error);
    }
})