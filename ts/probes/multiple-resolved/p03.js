new Promise((resolve, reject) => {
    fn((error, value) => {
        if (error) {
            reject(error)
            return
        }
        resolve(value)
    })
})