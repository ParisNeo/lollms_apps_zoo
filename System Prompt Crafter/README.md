# System Prompt Crafter

An AI-powered application that iteratively crafts, tests, and refines system prompts based on a user's idea.

## Features

- **Initial Crafting**: Provide an idea, and the "Craftor AI" will generate a first draft of a system prompt and a set of test cases.
- **Automated Testing**: The "Tester AI" runs through the generated test cases using the current system prompt.
- **Iterative Refinement**: The "Craftor AI" analyzes the test results for adherence to the prompt's instructions and refines the prompt if necessary.
- **Model Selection**: Choose different models for the crafting/analysis and testing roles.
- **Clear UI**: See the entire process unfold, from the initial prompt to the final, validated version.

## Setup

1.  **Clone the application folder.**

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables:**
    -   Copy the `.env.example` file to a new file named `.env`.
    -   Edit the `.env` file to set your `LOLLMS_HOST`.
    -   (Optional) You can specify different models for the `CRAFTOR_MODEL_NAME` and `TESTER_MODEL_NAME`. If left blank, the default model from your Lollms service will be used.

4.  **Run the application:**
    ```bash
    uvicorn server:app --reload
    ```

5.  **Open your browser** and navigate to `http://127.0.0.1:8000`.
