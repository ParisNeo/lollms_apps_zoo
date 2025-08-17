# SafeStoreGraphRAG

SafeStoreGraphRAG is a comprehensive web interface for the `safe-store` library. It provides a user-friendly platform to build, visualize, and query knowledge graphs from your documents. Leverage the power of Retrieval-Augmented Generation (RAG) to chat with your knowledge base.

## Key Features

- **Document Upload:** Easily upload various document types to build your knowledge base.
- **Automatic Knowledge Graph Construction:** Utilizes a Large Language Model (LLM) to automatically extract entities and relationships from documents and construct a graph.
- **Interactive Graph Visualization:** Explore your knowledge graph with an interactive, physics-based visualization tool.
- **Graph Exploration Tools:** Search for nodes, find paths between entities, and expand node neighborhoods.
- **RAG Chat Interface:** Ask natural language questions and get answers synthesized from the knowledge graph context.
- **Database Management:** Create and manage multiple, isolated knowledge bases.
- **Entity Fusion:** A maintenance tool to identify and merge similar or duplicate entities in the graph.

## Getting Started

### Prerequisites

- Python 3.9+
- An accessible LLM service, such as a running [Ollama](https://ollama.com/) instance.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd SafeStoreGraphRAG
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    The application uses `pipmaster` to automatically install required packages upon first run. Simply running the server will handle this.

### Configuration

1.  Rename `example.config.toml` to `config.toml`.
2.  Open `config.toml` and configure the settings to match your environment.

Here is an overview of the configuration sections:

-   `[lollms]`: Configure your connection to the LLM service.
    -   `binding_name`: The name of the binding (e.g., `ollama`, `openai`).
    -   `host_address`: The URL for the LLM service (e.g., `http://localhost:11434` for Ollama).
    -   `model_name`: The specific model to use (e.g., `mistral-nemo:latest`).

-   `[safestore]`: Settings for document processing and vectorization.
    -   `default_vectorizer`: The sentence-transformer model for embeddings.
    -   `chunk_size` / `chunk_overlap`: Parameters for splitting documents into chunks.

-   `[webui]`: Settings for the web server.
    -   `host` / `port`: The address and port to run the web UI on.
    -   `active_database_name`: The default database to load on startup.

### Running the Application

Once configured, run the server from the project's root directory:

```bash
python server.py
```

The application will be accessible at `http://<your_host>:<your_port>` (e.g., `http://0.0.0.0:8000`).

## Usage

1.  **Upload Documents:** Use the "Upload" button in the sidebar to add documents to your active database. The backend will process them and begin building the graph.
2.  **Explore the Graph:** As the graph is built, nodes and edges will appear in the main view. You can pan, zoom, and click on elements to see details.
3.  **Chat with your Data:** Open the "Chat" modal to ask questions. The system will retrieve relevant information from the graph to provide context-aware answers.
4.  **Manage Databases:** Use the "Databases" button to create new knowledge bases or switch between existing ones.