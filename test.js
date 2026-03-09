import mermaid from 'mermaid';
const graph = `
graph LR
  Terminal -->|uses| ConsoleHost
  ConsoleHost -->|shares| SharedComponents
  Terminal -->|includes| ColorTool
  Terminal -->|includes| SampleProjects
  ConsoleHost -->|partof| WindowsConsole
  Terminal -->|alternative| TerminalPreview
  Terminal -->|docs| Documentation
  Documentation -->|source| DocsRepo
  Terminal -->|builds| BuildSystem
  BuildSystem -->|uses| PowerShell
  BuildSystem -->|uses| Cmd
`;
console.log("OK");
