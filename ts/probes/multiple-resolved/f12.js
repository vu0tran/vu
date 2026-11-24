new Promise((resolve, reject) => {
    try {
        reject(error)
    } finally {
        resolve(value)
    }
})