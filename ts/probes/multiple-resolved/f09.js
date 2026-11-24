new Promise((resolve, reject) => {
    while (error) {
        reject(error)
    }
    resolve(value)
})