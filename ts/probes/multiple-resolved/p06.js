new Promise((resolve, reject) => {
    fn((error, value) => {
        if (error) {
            reject(error)
        }
        if (!error) {
            // process
        } else {
            // process
        }
        if(!error) {
            resolve(value)
        }
    })
})