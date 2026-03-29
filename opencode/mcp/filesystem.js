import { createServer } from "mcp";

createServer({
  name: "filesystem",
  tools: {
    readFile: async ({ path }) => {
      return "file content";
    }
  }
});