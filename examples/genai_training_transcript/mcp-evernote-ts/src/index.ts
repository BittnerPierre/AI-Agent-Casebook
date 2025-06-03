export function startEvernotePluginServer(): void {
  console.log('Starting MCP Evernote plugin server')
}

if (require.main === module) {
  startEvernotePluginServer()
}