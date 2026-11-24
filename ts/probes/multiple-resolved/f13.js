new Promise((resolve, reject) => {
    try {
        if (error) {
            reject(error)
        }
    } finally {
        resolve(value)
    }
})