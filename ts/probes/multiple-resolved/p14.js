new Promise((resolve, reject) => {
    fn(async function * () {
        try {
            const r = await foo();
            resolve(yield r);
        } catch (error) {
            reject(error);
        }
    })
})