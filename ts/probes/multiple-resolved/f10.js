new Promise((resolve, reject) => {
    for (let i = 0; i < 10; i++) {
        if (error) {
            resolve(error)
        }
    }
    resolve(value)
})