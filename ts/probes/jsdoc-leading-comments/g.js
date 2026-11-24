#!/usr/bin/env node /** @bogus */
foo(); /*! legal */ /** @bogus */
bar();
foo(); /* @license x */ /** @bogus */
bar();
foo(); /** @bogus */ /* plain */
bar();
foo() /* x */ /** @bogus */
+ 1;
