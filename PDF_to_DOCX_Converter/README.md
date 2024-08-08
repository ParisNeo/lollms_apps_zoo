# PDF to DOCX Converter

This application allows users to convert PDF files to DOCX format easily. It consists of a FastAPI backend that handles the file conversion and a simple HTML frontend for user interaction.

## Table of Contents

- [PDF to DOCX Converter](#pdf-to-docx-converter)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Technologies Used](#technologies-used)
  - [Installation](#installation)
  - [Usage](#usage)
  - [File Structure](#file-structure)
  - [License](#license)

## Features

- Upload PDF files through a user-friendly interface.
- Convert PDF files to DOCX format.
- Download the converted DOCX files.

## Technologies Used

- **FastAPI**: A modern web framework for building APIs with Python.
- **pdf2docx**: A library for converting PDF files to DOCX format.
- **HTML/CSS**: For the frontend user interface.
- **Tailwind CSS**: A utility-first CSS framework for styling.

## Installation

1. Install the application from lollms apps zoo
2. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the FastAPI server:

   ```bash
   uvicorn server:app --reload
   ```

   The server will run at `http://127.0.0.1:8000`.

2. Open your App from the lollms apps zoo.

3. Use the interface to upload a PDF file and click the "Convert to DOCX" button.

4. After conversion, a link will appear to download the converted DOCX file.

## File Structure

```plaintext
pdf-to-docx-converter/
│
├── server.py         # FastAPI backend for handling file conversion
└── index.html        # HTML frontend for user interaction
```

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details