/** @type {import('prettier').Config} */
module.exports = {
  // Core formatting
  semi: true,
  singleQuote: true,
  tabWidth: 2,
  useTabs: false,
  trailingComma: "es5",
  printWidth: 80,

  // JavaScript/TypeScript specific
  arrowParens: "always",
  bracketSpacing: true,
  bracketSameLine: false,
  quoteProps: "as-needed",

  // JSX specific
  jsxSingleQuote: true,

  // Tailwind CSS plugin
  plugins: ["prettier-plugin-tailwindcss"],

  // File type overrides
  overrides: [
    {
      files: "*.json",
      options: {
        tabWidth: 2,
      },
    },
    {
      files: "*.md",
      options: {
        proseWrap: "always",
        tabWidth: 2,
      },
    },
    {
      files: "*.yaml",
      options: {
        tabWidth: 2,
      },
    },
  ],
};
