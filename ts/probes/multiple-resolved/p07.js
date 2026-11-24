new Promise((resolve, reject) => {
    fn((error, value) => {
        if (error) {
            reject(error)
            return
        }
        if (!error) {
            // process
        } else {
            // process
        }

        resolve(value)
    })
})