import type { ProgrammingLanguage } from "../types";

// Mock assessment only: these checks pattern-match the source text and never
// execute it. Real grading must run in the isolated backend workers.

// HTML and CSS are not programming languages, so they get their own checks.
type CodeLanguage = Exclude<ProgrammingLanguage, "html" | "css">;

export interface CodeCheck {
  passed: boolean;
  success: string;
  improvement: string;
}

interface LanguageSyntax {
  variable: RegExp;
  conversion: RegExp;
  output: RegExp;
  comment: RegExp;
  ifStatement: RegExp;
  alternativeBranch: RegExp;
  // Each pattern must be global and capture the parameter list in group 1.
  functionDefinitions: RegExp[];
  hints: {
    conversion: string;
    output: string;
    comment: string;
    alternativeBranch: string;
    functionDefinition: string;
  };
}

const cStyleComment = /\/\/|\/\*/;
const cStyleIf = /\bif\s*\(/;
const cStyleElse = /\belse\b/;

const syntax: Record<CodeLanguage, LanguageSyntax> = {
  python: {
    variable: /[a-z_]\w*\s*=(?!=)/i,
    conversion: /\b(int|float|str|bool)\s*\(/,
    output: /\bprint\s*\(/,
    comment: /#/,
    ifStatement: /\bif\b/,
    alternativeBranch: /\b(elif|else)\b/,
    functionDefinitions: [/\bdef\s+[a-z_]\w*\s*\(([^)]*)\)/gi],
    hints: {
      conversion: "int(), float(), str(), or bool()",
      output: "print()",
      comment: "#",
      alternativeBranch: "elif or else",
      functionDefinition: "the def keyword",
    },
  },
  java: {
    variable:
      /\b(int|long|double|float|boolean|char|String|var)\s+[a-z_]\w*\s*=(?!=)/i,
    conversion:
      /\b(Integer\.parseInt|Integer\.valueOf|Integer\.toString|Double\.parseDouble|Double\.valueOf|Double\.toString|String\.valueOf)\s*\(|\(\s*(int|long|double|float|char)\s*\)/,
    output: /\bSystem\.out\.print(ln|f)?\s*\(/,
    comment: cStyleComment,
    ifStatement: cStyleIf,
    alternativeBranch: cStyleElse,
    // The starter's main method does not count as the student's own method.
    functionDefinitions: [
      /\b(?:void|int|long|double|float|boolean|char|String)\s+(?!main\b)[a-z_]\w*\s*\(([^)]*)\)\s*\{/gi,
    ],
    hints: {
      conversion: "Integer.parseInt(), Double.parseDouble(), String.valueOf(), or a cast",
      output: "System.out.println()",
      comment: "//",
      alternativeBranch: "else if or else",
      functionDefinition: "a static method",
    },
  },
  cpp: {
    variable:
      /\b(int|long|double|float|bool|char|auto|string|std::string)\s+[a-z_]\w*\s*=(?!=)/i,
    conversion:
      /\b(std::)?(stoi|stol|stod|stof|to_string)\s*\(|\bstatic_cast\s*<|\(\s*(int|long|double|float|char)\s*\)/,
    output: /\b(std::)?cout\s*<<|\bprintf\s*\(/,
    comment: cStyleComment,
    ifStatement: cStyleIf,
    alternativeBranch: cStyleElse,
    // The starter's main function does not count as the student's own function.
    functionDefinitions: [
      /\b(?:void|int|long|double|float|bool|char|auto|string|std::string)\s+(?!main\b)[a-z_]\w*\s*\(([^)]*)\)\s*\{/gi,
    ],
    hints: {
      conversion: "std::stoi(), std::to_string(), or static_cast<>",
      output: "std::cout",
      comment: "//",
      alternativeBranch: "else if or else",
      functionDefinition: "a function with a return type",
    },
  },
  javascript: {
    variable: /\b(let|const|var)\s+[a-z_$][\w$]*\s*=(?!=)/i,
    conversion: /\b(Number|parseInt|parseFloat|String|Boolean)\s*\(|\.toString\s*\(/,
    output: /\bconsole\.log\s*\(/,
    comment: cStyleComment,
    ifStatement: cStyleIf,
    alternativeBranch: cStyleElse,
    functionDefinitions: [
      /\bfunction\s+[a-z_$][\w$]*\s*\(([^)]*)\)/gi,
      /\b(?:const|let|var)\s+[a-z_$][\w$]*\s*=\s*\(([^)]*)\)\s*=>/gi,
    ],
    hints: {
      conversion: "Number(), parseInt(), or String()",
      output: "console.log()",
      comment: "//",
      alternativeBranch: "else if or else",
      functionDefinition: "the function keyword or an arrow function",
    },
  },
};

// Keywords followed by "(" and the starter main() header are not function calls.
const nonCallParentheses = /\b(if|for|while|switch|catch|return|main)\s*\(/g;

// The C++ starter ends with "return 0;", which must not count as a returned value.
const returnValue = /\breturn\b(?!\s*0\s*;)/;

// Tokens that contain < or > but are not comparisons (includes, streams, arrows, casts).
const nonComparisonTokens = /#include\s*<[^>]*>|<<|>>|=>|->|static_cast\s*<[^>]*>/g;
const anyCall = /\b[a-z_$][\w$.]*\s*\([^)]*\)/i;

const findFunctionParameters = (
  language: LanguageSyntax,
  code: string,
): string[] =>
  language.functionDefinitions.flatMap((pattern) =>
    Array.from(code.matchAll(pattern), (match) => match[1].trim()),
  );

const removeFunctionDefinitions = (
  language: LanguageSyntax,
  code: string,
): string =>
  language.functionDefinitions.reduce(
    (remaining, pattern) => remaining.replace(pattern, ""),
    code,
  );

const evaluateProgram = (
  assignmentId: number,
  language: LanguageSyntax,
  code: string,
): CodeCheck[] => {
  const { hints } = language;

  if (assignmentId === 1) {
    return [
      {
        passed: language.variable.test(code),
        success: "You created and assigned a variable.",
        improvement: "Declare at least one variable and assign it a value.",
      },
      {
        passed: language.conversion.test(code),
        success: "You used explicit type conversion.",
        improvement: `Use ${hints.conversion} for type conversion.`,
      },
      {
        passed: language.output.test(code),
        success: "You displayed the result.",
        improvement: `Use ${hints.output} to display the converted value.`,
      },
      {
        passed: language.comment.test(code),
        success: "You documented part of your solution.",
        improvement: `Add a short ${hints.comment} comment explaining the conversion.`,
      },
    ];
  }

  if (assignmentId === 2) {
    return [
      {
        passed: language.ifStatement.test(code),
        success: "You used an if statement.",
        improvement: "Add an if statement for the main condition.",
      },
      {
        passed: language.alternativeBranch.test(code),
        success: "You handled an alternative condition.",
        improvement: `Handle another case using ${hints.alternativeBranch}.`,
      },
      {
        passed: /(==|!=|>=|<=|>|<)/.test(code.replace(nonComparisonTokens, "")),
        success: "You used a comparison operator.",
        improvement: "Compare the score with an appropriate boundary value.",
      },
      {
        passed: language.output.test(code) || returnValue.test(code),
        success: "Your solution produces an output.",
        improvement: `Return or display the calculated grade with ${hints.output}.`,
      },
    ];
  }

  const parameters = findFunctionParameters(language, code);
  const codeOutsideDefinitions = removeFunctionDefinitions(
    language,
    code,
  ).replace(nonCallParentheses, "");

  return [
    {
      passed: parameters.length > 0,
      success: "You defined a function.",
      improvement: `Define a function using ${hints.functionDefinition}.`,
    },
    {
      passed: parameters.some((parameterList) => parameterList.length > 0),
      success: "Your function accepts a parameter.",
      improvement: "Add at least one parameter to the function.",
    },
    {
      passed: returnValue.test(code),
      success: "Your function returns a value.",
      improvement: "Use return to send a result back from the function.",
    },
    {
      passed: anyCall.test(codeOutsideDefinitions),
      success: "You called the function.",
      improvement: "Call the function with a sample argument.",
    },
  ];
};

// Comments are removed first so commented-out tags or rules do not pass checks.
const evaluateHtml = (code: string): CodeCheck[] => {
  const markup = code.replace(/<!--[\s\S]*?-->/g, "");

  return [
    {
      passed: /<h[1-6][\s>]/i.test(markup),
      success: "You added a heading.",
      improvement: "Add a heading such as <h1> for the page title.",
    },
    {
      passed: /<p[\s>]/i.test(markup),
      success: "You added a paragraph.",
      improvement: "Add a <p> paragraph that introduces the profile.",
    },
    {
      passed: /<(ul|ol)[\s>][\s\S]*?<li[\s>]/i.test(markup),
      success: "You built a list with list items.",
      improvement: "Add a <ul> or <ol> list containing <li> items.",
    },
    {
      passed: /<a\s[^>]*href\s*=/i.test(markup),
      success: "You added a link.",
      improvement: 'Add a link using <a href="...">.',
    },
  ];
};

const evaluateCss = (code: string): CodeCheck[] => {
  const styles = code.replace(/\/\*[\s\S]*?\*\//g, "");

  return [
    {
      passed: /[^{}\s][^{}]*\{[^}]*:[^}]*\}/.test(styles),
      success: "You wrote a CSS rule with a selector.",
      improvement: "Write a rule such as .card { ... } with at least one property.",
    },
    {
      passed: /(^|[{;\s])(color|background(-color)?)\s*:/i.test(styles),
      success: "You set a color.",
      improvement: "Set color or background-color on the card.",
    },
    {
      passed: /(^|[{;\s])(margin|padding)(-[a-z]+)?\s*:/i.test(styles),
      success: "You added spacing.",
      improvement: "Use margin or padding to add space around the content.",
    },
    {
      passed: /(^|[{;\s])display\s*:\s*(inline-)?(flex|grid)\b/i.test(styles),
      success: "You used a flex or grid layout.",
      improvement: "Use display: flex or display: grid to arrange the content.",
    },
  ];
};

export const evaluateAssignment = (
  assignmentId: number,
  languageId: ProgrammingLanguage,
  code: string,
): CodeCheck[] => {
  if (languageId === "html") {
    return evaluateHtml(code);
  }

  if (languageId === "css") {
    return evaluateCss(code);
  }

  return evaluateProgram(assignmentId, syntax[languageId], code);
};
