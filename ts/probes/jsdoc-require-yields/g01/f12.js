
                            /**
                             *
                             */
                            function * quux () {
                              try {
                                something();
                              } catch (err) {
                                yield true;
                              }
                              yield;
                            }
                        