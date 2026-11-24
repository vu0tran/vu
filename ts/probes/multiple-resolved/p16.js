new Promise((resolve, reject) => {
    try {
        try {
            resolve(value);
        } catch (error) {
            reject(error);
        }
    } catch (error) {
        reject(error);
    }
})