/** @type {import('eslint').Linter.FlatConfig[]} */
const { FlatCompat } = require("@eslint/eslintrc");
const compat = new FlatCompat();

module.exports = [
  ...compat.extends("next/core-web-vitals", "prettier"),
  {
    files: ["**/*.{js,jsx,ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    rules: {
      // Basic rules
      "prefer-const": "error",
      "no-var": "error",
      "no-console": "warn",

      // React/Next.js rules
      "@next/next/no-img-element": "warn",
      "react-hooks/exhaustive-deps": "warn",
    },
  },
];
