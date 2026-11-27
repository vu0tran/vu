new Promise((resolve, reject) => {
    if (foo) {
        reject(error)
    } else {
        resolve(value)
    }
    if(bar) {
        resolve(value)
    }
})