# Generated projects from what the real apps (knip/test/corpus.txt) showed: config files named on
# command lines with a path that starts like a dependency's name (webpack --config webpack/x.js),
# tools that read them, a folder named like the package.
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cases3 import pkg, mod

CASES = {}

def case(name, files, args=None):
    files = dict(files)
    if args: files["__args__"] = args
    CASES[name] = files

def mods(*names):
    out = {}
    for n in names: out.update(mod(n))
    return out

case("r11_webpack_config_dir", {
    "package.json": pkg(dev=["webpack", "webpack-cli", "babel-loader", "cross-env"], scripts={"build": "cross-env NODE_ENV=production webpack --config webpack/webpack.config.prod.js", "start": "webpack serve --config webpack/webpack.config.dev.js"}), **mods("webpack", "webpack-cli", "babel-loader", "cross-env"),
    "webpack/webpack.config.prod.js": "module.exports = { entry: './src/index.js', module: { rules: [{ test: /\\.js$/, use: 'babel-loader' }] } };\n",
    "webpack/webpack.config.dev.js": "module.exports = require('./webpack.config.prod.js');\n",
    "src/index.js": "",
}, [[], ["--production"]])
case("r11_vite_config_dir", {
    "package.json": pkg(dev=["vite", "vitest"], scripts={"build": "vite build --config vite/vite.config.ts", "test": "vitest --config vitest/vitest.config.ts"}), **mods("vite", "vitest"),
    "vite/vite.config.ts": "export default { build: { lib: { entry: 'src/lib.ts' } } };\n",
    "vitest/vitest.config.ts": "export default { test: { setupFiles: ['./setup.ts'] } };\n",
    "src/lib.ts": "export const a = 1;\n", "setup.ts": "",
})
case("r11_jest_config_dir", {
    "package.json": pkg(dev=["jest", "eslint"], scripts={"test": "jest -c jest/jest.config.js", "lint": "eslint -c eslint/eslint.config.js ."}), **mods("jest", "eslint"),
    "jest/jest.config.js": "module.exports = { setupFiles: ['<rootDir>/../setup.js'] };\n",
    "eslint/eslint.config.js": "module.exports = [];\n",
    "setup.js": "",
})
case("r11_config_dir_not_dep", {
    "package.json": pkg(dev=["webpack-cli"], scripts={"build": "webpack-cli --config webpack/webpack.config.js"}), **mods("webpack-cli"),
    "webpack/webpack.config.js": "module.exports = { entry: './src/index.js' };\n",
    "src/index.js": "",
})
