new Promise((resolve, reject) => {
    fn((error, value) => {
        if (error) {
            if (foo) {
                if (bar) reject(error)
            }
        }

        resolve(value)
    })
})