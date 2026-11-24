
                              /**
                               * @yields {Array}
                               */
                              function * quux (bar) {
                                yield bar.doSomething(function * (baz) {
                                  yield baz.corge();
                                })
                              }
                          