new Promise((resolve, reject) => {
    if (error) {
        reject(error)
    } else {
        resolve(value)
    }
})