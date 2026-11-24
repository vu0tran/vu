
                            /**
                             *
                             */
                            function * quux () {
                              var a = {};
                              with (a) {
                                yield true;
                              }
                            }
                        