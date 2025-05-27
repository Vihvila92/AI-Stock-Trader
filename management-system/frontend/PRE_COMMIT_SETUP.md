# Pre-commit Hooks Setup - Frontend

This document describes the pre-commit hooks setup for the React/Next.js frontend project.

## Overview

The pre-commit hooks are configured to run automatic code quality checks before each commit to ensure consistent code style and catch issues early.

## Tools Configured

### 1. Prettier

- **Purpose**: Code formatting
- **Configuration**: `prettier.config.js`
- **Ignore file**: `.prettierignore`
- **Commands**:
  - `npm run format` - Format all files
  - `npm run format:check` - Check formatting without changing files

### 2. ESLint

- **Purpose**: Code linting and static analysis
- **Configuration**: `.eslintrc.json`
- **Commands**:
  - `npm run lint` - Run ESLint checks
  - `npm run lint:fix` - Run ESLint and auto-fix issues

### 3. TypeScript Compiler

- **Purpose**: Type checking
- **Configuration**: `tsconfig.json`
- **Commands**:
  - `npm run type-check` - Check TypeScript types without emitting files

### 4. Jest

- **Purpose**: Running tests
- **Configuration**: `jest.config.js`, `jest.setup.js`
- **Commands**:
  - `npm test` - Run all tests
  - `npm run test:watch` - Run tests in watch mode
  - `npm run test:coverage` - Run tests with coverage

## Pre-commit Hook Configuration

### Husky

- **Hook file**: `/.husky/pre-commit` (at repository root)
- **Triggers**: lint-staged for frontend files

### lint-staged

- **Configuration**: `.lintstagedrc`
- **Behavior**:
  - Runs Prettier on staged `.js`, `.jsx`, `.ts`, `.tsx` files
  - Runs Prettier on staged `.json`, `.css`, `.md` files

## File Structure

```
frontend/
├── .eslintrc.json          # ESLint configuration
├── .lintstagedrc           # lint-staged configuration
├── .prettierignore         # Files to ignore in Prettier
├── prettier.config.js      # Prettier configuration
├── jest.config.js          # Jest configuration
├── jest.setup.js           # Jest setup file
├── tsconfig.json           # TypeScript configuration
└── types/
    └── jest-dom.d.ts       # Custom Jest DOM type declarations
```

## How It Works

1. **On git commit**: The pre-commit hook is triggered
2. **Husky**: Executes the pre-commit script
3. **lint-staged**: Processes only staged files
4. **Tools run**: Prettier formats the staged files
5. **Auto-fix**: Modified files are automatically staged
6. **Commit proceeds**: If all checks pass, commit continues

## Manual Commands

You can run these tools manually at any time:

```bash
# Format all files
npm run format

# Check code style
npm run format:check

# Lint code
npm run lint

# Fix lint issues
npm run lint:fix

# Check TypeScript types
npm run type-check

# Run tests
npm test

# Run lint-staged manually
npx lint-staged
```

## Configuration Details

### Prettier Configuration

- Single quotes for strings
- No semicolons
- Tab width: 2 spaces
- Tailwind CSS class sorting enabled

### ESLint Configuration

- Extends Next.js core web vitals
- Custom rules for code quality
- Warnings for image optimization and React hooks

### TypeScript Configuration

- Strict mode enabled
- JSX preserve mode
- Incremental compilation
- Custom type declarations included

## Troubleshooting

### If pre-commit hook fails:

1. Run `npm run lint` to see specific ESLint errors
2. Run `npm run format` to fix formatting issues
3. Run `npm run type-check` to see TypeScript errors
4. Fix any issues and try committing again

### If lint-staged doesn't run:

1. Check that files are properly staged: `git status`
2. Run manually: `npx lint-staged`
3. Check Husky installation: `ls -la .husky/`

## Dependencies

The following dev dependencies are required:

- `husky` - Git hooks management
- `lint-staged` - Run tools on staged files
- `prettier` - Code formatting
- `prettier-plugin-tailwindcss` - Tailwind CSS class sorting
- `eslint` - Code linting
- `eslint-config-next` - Next.js ESLint configuration
- `eslint-config-prettier` - Disable ESLint formatting rules
- `@typescript-eslint/*` - TypeScript ESLint support
- `jest` - Testing framework
- `@testing-library/*` - Testing utilities
