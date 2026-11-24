new Promise((resolve, reject) => {
    if (error) {
        reject(error)
    }

    resolve(value)
})