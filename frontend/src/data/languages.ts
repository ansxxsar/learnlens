import type { LanguageOption, ProgrammingLanguage } from "../types";

export const languageOptions: LanguageOption[] = [
  { id: "python", label: "Python" },
  { id: "java", label: "Java" },
  { id: "cpp", label: "C++" },
  { id: "javascript", label: "JavaScript" },
  { id: "html", label: "HTML" },
  { id: "css", label: "CSS" },
];

export const defaultLanguage: ProgrammingLanguage = "python";

export const starterCode: Record<ProgrammingLanguage, string> = {
  python: `# Write your solution here
`,
  java: `public class Main {
    public static void main(String[] args) {
        // Write your solution here
    }
}
`,
  cpp: `#include <iostream>

int main() {
    // Write your solution here
    return 0;
}
`,
  javascript: `// Write your solution here
`,
  html: `<!DOCTYPE html>
<html lang="en">
  <head>
    <title>My page</title>
  </head>
  <body>
    <!-- Write your page here -->
  </body>
</html>
`,
  css: `/* Write your styles here */
`,
};
