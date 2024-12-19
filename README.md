# LoLLMs Apps Zoo 🎪

Welcome to the LoLLMs Apps Zoo - A centralized repository for applications built for the LoLLMs WebUI ecosystem.

## Overview 🌟

LoLLMs Apps Zoo is a curated collection of web applications that extend the functionality of LoLLMs WebUI. These applications can leverage LoLLMs' powerful services while providing specialized features through custom implementations.

## Required Files Structure 📁

```
your_app_name/
├── description.yaml     # Required: App metadata and configuration
├── index.html          # Required: Main app interface
├── icon.png           # Required: App icon (recommended size: 128x128px)
├── README.md          # Optional: Detailed documentation
├── server.py         # Optional: Backend server implementation
└── assets/           # Optional: Additional resources
    ├── css/
    ├── js/
    └── images/
```

## File Path Convention 🔗

When referencing additional files in your HTML, use the following path format:
```html
<!-- Example path structure -->
<img src="/apps/your_app_name/assets/images/example.png">
<link rel="stylesheet" href="/apps/your_app_name/assets/css/style.css">
<script src="/apps/your_app_name/assets/js/script.js"></script>
```

## Types of Applications 📱

Applications in this repository can be:
- Frontend-only apps using LoLLMs WebUI backend
- Full-stack applications with custom Python backends
- Apps utilizing LoLLMs core services:
  - Text Generation
  - Image Generation
  - Speech Generation
  - Text Data Vectorization

## Required Files Details 📋

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
  js:
    - "required_library1"
```

### icon.png
- Mandatory app icon
- Recommended size: 128x128 pixels
- Format: PNG with transparency support
- Should be visually representative of the app's function

## Contributing 🤝

1. Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

2. Configure your repository to use [ParisNeo's pre-commit hooks](https://github.com/ParisNeo/parisneo-precommit-hooks)
3. Join our [Discord Channel](https://discord.com/channels/1092918764925882418)

## Code Quality ⭐

All code must pass ParisNeo's pre-commit hooks, which include:
- Code formatting
- Linting
- Security checks
- Import sorting
- Code complexity checks

## License 📄

This repository is licensed under the Apache License 2.0.

## Author ✍️

Created and maintained by ParisNeo

## Contact 📞

- Discord: [Join our community](https://discord.com/channels/1092918764925882418)

---

For detailed contribution guidelines, security requirements, and best practices, please refer to our [CONTRIBUTING.md](CONTRIBUTING.md) file.

Happy coding! 🚀

