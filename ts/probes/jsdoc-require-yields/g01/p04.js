
                              /**
                               *
                               */
                              function quux (bar) {
                                bar.doSomething(function * (baz) {
                                  yield baz.corge();
                                })
                              }
                          