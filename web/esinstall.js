const { install, printStats } = require("esinstall")

install(
  [{
    specifier: "htm/preact",
    all: false,
    default: false,
    namespace: false,
    named: ["html", "render", "Component"],
  }],
  {
    dest: "./lib",
    sourceMap: false,
    treeshake: true,
    verbose: true,
  }
).then(data => {
  const oldPrefix = "web_modules/"
  const newPrefix = "lib/"
  const spaces = " ".repeat(oldPrefix.length - newPrefix.length)
  console.log("Installation complete")
  console.log(printStats(data.stats).replace(oldPrefix, newPrefix + spaces))
})
