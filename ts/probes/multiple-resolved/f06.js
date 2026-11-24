new Promise((resolve, reject) => {
    fn((error, value) => {
        if (error) {
            reject(error)
        } else {
            return
        }

        resolve(value)
    })
})