
			          /**
			           * @class
			           * @property {Error} error Exit code
			           * @property {number} [code = 1] Exit code
			           */
			          function quux (code = 1) {
			            this.error = new Error('oops');
			            this.code = code;
			          }
			      