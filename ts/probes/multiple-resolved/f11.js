new Promise((resolve, reject) => {
    do {
        if (error) {
            resolve()
        }
    } while (error)
    reject()
})