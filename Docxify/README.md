# Docxify

Docxify is a lightweight **FastAPI-based web service** that converts Markdown (`.md`) documents into professional Word (`.docx`) files.  
It comes with a clean **TailwindCSS-powered UI**, allowing users to either upload a Markdown file or type/paste Markdown directly into a text box, then download the generated `.docx`.

---

## ✨ Features
- Convert Markdown to `.docx` with full formatting:
  - Headings, lists, tables, blockquotes
  - Code blocks & inline code
  - Images and hyperlinks
- Upload `.md` files or type Markdown directly
- Stylish, responsive UI built with **TailwindCSS**
- Download the generated `.docx` instantly
- Configurable host & port

---

## 🚀 Installation

### Prerequisites
- Python **3.9+**
- `pip` (Python package manager)

### Clone the repository
```bash
git clone https://github.com/ParisNeo/Docxify.git
cd Docxify
````

### Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Usage

### Run the FastAPI service

```bash
python docxify.py --host 0.0.0.0 --port 8000
```

### Access the UI

Open your browser at:
👉 `http://localhost:8000`

---

## 📦 API Endpoints

### `POST /convert`

Convert Markdown text or uploaded file into `.docx`.

* **Form Data:**

  * `markdown_text` *(optional)*: Raw Markdown string
  * `file` *(optional)*: Markdown file (`.md`)

* **Response:**
  Returns a `.docx` file.

---

## 🖼️ Screenshots

*(Add screenshots of the UI here once available)*

---

## ⚖️ License

This project is licensed under the **MIT License**.

---

## 👤 Author

Developed by **ParisNeo**

* GitHub: [ParisNeo](https://github.com/ParisNeo)
* Twitter: [@ParisNeo](https://twitter.com/ParisNeo)

---

## 📝 Roadmap

* [ ] Add support for custom styling templates
* [ ] Add PDF export option
* [ ] Support collaborative editing

