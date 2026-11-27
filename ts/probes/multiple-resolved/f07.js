new Promise((resolve, reject) => {
    if(foo) {
        if (error) {
            reject(error)
        } else {
            return
        }
        resolve(value)
    }

    resolve(value)
})