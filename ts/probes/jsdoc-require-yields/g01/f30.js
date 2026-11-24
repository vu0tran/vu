
                            /**
                             *
                             */
                            function * quux () {
                              +(yield);
                              [...yield];
                              [...+(yield true)];
                            }
                        