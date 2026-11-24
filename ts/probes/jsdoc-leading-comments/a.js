/** @bogus */
foo();
foo(); /** @bogus */
bar();
foo(); /** @bogus */ bar();
let x = foo() /** @bogus */ + 1;
let y = /** @bogus */ 2;
foo(/** @bogus */ 1);
/** @bogus */ /** @bogus */
let z;
/*** @property */
foo();
/** @license
 * @property */
foo();
/*****/
foo(); /** @bogus */ // tail
bar();
foo() /** @bogus */ // c
foo = /** @bogus */ // c
1;
foo(/** @bogus */ // c
1);
a ? /** @bogus */ b : c;
x = a /** @bogus */ ? b : c;
x = a /** @bogus */ ?? b;
x = a /** @bogus */ in b;
x = a /** @bogus */ instanceof b;
x = a /** @bogus */ === b;
x = a /** @bogus */++;
x = a++ /** @bogus */ + b;
x = a /** @bogus */ => b;
x = `t` /** @bogus */ + 1;
x = /re/ /** @bogus */ + 1;
