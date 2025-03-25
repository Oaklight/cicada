# Contributing Guide

Welcome to the CICADA project! We are thrilled that you’re interested in contributing. Your efforts help make CICADA better for everyone. This guide will walk you through the process of contributing to the project.

---

## Getting Started

### 1. **Set Up Your Development Environment**

Follow the [Installation Steps (For Developers)](./usage.md#installation-steps-for-developers) to set up the CICADA environment.

### 2. **Fork the Repository**

1. Go to the [CICADA GitHub repository](https://github.com/Oaklight/cicada).
2. Click the **Fork** button in the top-right corner to create a copy of the repository under your GitHub account.

### 3. **Clone Your Fork**

Clone your forked repository to your local machine:

```bash
git clone https://github.com/YOUR_USERNAME/cicada.git
cd cicada
```

### 4. **Set Up Upstream Remote**

Add the original CICADA repository as an upstream remote to sync with the latest changes:

```bash
git remote add upstream https://github.com/Oaklight/cicada.git
```

### 5. **Create a New Branch**

Always create a new branch for your changes. Use a descriptive name for the branch:

```bash
git checkout -b feature/your-feature-name
```

---

## Making Changes

### 1. **Follow the Code Style**

- Use **PEP 8** for Python code formatting.
- Add comments where necessary to explain complex logic.
- Ensure all functions and classes are documented with docstrings.

### 2. **Test Your Changes**

- Ensure your changes do not break existing functionality.
- Write unit tests for new features or bug fixes.

### 3. **Commit Your Changes**

- Write clear and concise commit messages.
- Use the present tense (e.g., "Add feature X" instead of "Added feature X").
- Reference related issues or pull requests in your commit messages (e.g., "Fix #123").

```bash
git add .
git commit -m "Add feature X"
```

---

## Submitting a Pull Request

### 1. **Push Your Changes**

Push your branch to your forked repository:

```bash
git push origin feature/your-feature-name
```

### 2. **Create a Pull Request**

1. Go to the [CICADA GitHub repository](https://github.com/Oaklight/cicada).
2. Click **Compare & pull request**.
3. Provide a clear title and description for your changes, including:
   - The purpose of the changes.
   - Any related issues or pull requests.
   - Steps to test the changes.

### 3. **Review and Feedback**

- Your pull request will be reviewed by the maintainers.
- Address any feedback or requested changes promptly.
- Once approved, your changes will be merged into the main repository.

---

## Reporting Issues

If you encounter a bug or have a feature request, please [open an issue](https://github.com/Oaklight/cicada/issues) on GitHub. Include the following details:

- A clear and descriptive title.
- Steps to reproduce the issue.
- Expected vs. actual behavior.
- Screenshots, logs, or error messages (if applicable).

---

## Thank You!

Your contributions are invaluable to the CICADA project. We appreciate your time and effort in making CICADA better for everyone!

---

**CICADA** — Revolutionizing CAD Design with Intelligent Automation. 🚀
