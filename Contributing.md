# Contributing Guidelines

## Prerequisites 📋

1. Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

2. Configure your repository to use [ParisNeo's pre-commit hooks](https://github.com/ParisNeo/parisneo-precommit-hooks)

## File Requirements 📝

### description.yaml
```yaml
name: "Your App Name"
version: "1.0.0"
description: "Brief description of your app"
author: "Your Name"
license: "Apache-2.0"
requires_backend: true/false
dependencies:
  python: 
    - "required_package1"
    - "required_package2"
  js:
    - "required_library1"
    - "required_library2"
```

### index.html
- Must be valid HTML5
- Should include responsive design
- Must properly integrate with LoLLMs WebUI

### server.py (if needed)
- Must follow PEP 8 guidelines
- Must include proper error handling
- Must pass ParisNeo's linting requirements

## Code Quality Standards ⭐

All code must pass ParisNeo's pre-commit hooks, which include:
- Code formatting
- Linting
- Security checks
- Import sorting
- Code complexity checks

## Documentation Requirements 📚

1. Clear inline code comments
2. Function/method documentation
3. README.md (if included) should contain:
   - Installation instructions
   - Usage guide
   - API documentation (if applicable)
   - Screenshots/demos

## Security Guidelines 🔒

1. No hardcoded credentials
2. Proper input validation
3. Secure data handling
4. No sensitive data exposure

## Submission Process 🚀

1. Ensure your code passes all pre-commit hooks
2. Join our [Discord Channel](https://discord.com/channels/1092918764925882418)
3. Submit your application with:
   - GitHub repository link
   - Brief description
   - Demo/screenshots
4. Wait for review and feedback

## Review Process 🔍

Applications will be reviewed for:
1. Adherence to file structure requirements
2. Code quality (must pass pre-commit hooks)
3. Security
4. Documentation quality
5. User experience

## Maintenance 🛠️

Contributors should:
1. Monitor issues and bug reports
2. Maintain compatibility with LoLLMs updates
3. Respond to user feedback

## Need Help? 💡

- Join our [Discord community](https://discord.com/channels/1092918764925882418)
- Check existing documentation
- Review sample applications