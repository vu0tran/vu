declare namespace N { interface AsyncIt<T, TReturn = undefined, TNext = any> { next(): [T, TReturn, TNext] } }
