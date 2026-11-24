new Promise((resolve, reject) => {
    fn((error, value) => {
        if (error) {
            reject(error)
        }
        if (error) {
            return
        }
        resolve(value)
    })
})