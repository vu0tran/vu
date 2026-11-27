
                        /**
                         * @param {array} a
                         */
                        async function * foo(a) {
                          yield Promise.all(a);
                        }
                        