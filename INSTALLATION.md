## Installation

### 1. Clone the Repository

```
git clone https://github.com/ShashwatAwate/medical_agent.git
cd medical-agent
```

### 2. Create a Virtual Environment (Recommended)

**On macOS/Linux:**
```
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```
python -m venv venv
venv\Scripts\activate
```

### 3. Update Dependencies in pyproject.toml

Before installing, make sure your \`pyproject.toml\` includes all required dependencies:

```
[project]
name = "medial-agent"
version = "0.1.0"
description = "Hospital Resource Allocation System"
authors = [{name = "Shashwat"}]
dependencies = [
    "streamlit",
    "numpy",
    "pandas",
    "langgraph",
    "google-genai",
    "python-dotenv",
    "sentence-transformers",
    "faiss-cpu",
    "scikit-learn"
]

[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"
```

### 4. Install Dependencies

```
pip install -e .
```

Or, if you prefer installing with pip directly:

```
pip install streamlit numpy pandas langgraph google-generativeai python-dotenv sentence-transformers faiss-cpu scikit-learn
```

## Configuration

### Set Up Environment Variables

Create a \`.env\` file in the project root directory:

```
touch .env
```

Add the following environment variables to \`.env\`:

```env
GEMINI_API_KEY=your_google_generative_ai_api_key_here
```

**How to get a Google API Key:**
1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Click "Create API Key"
3. Copy the key and paste it into your \`.env\` file

**Note:** The environment variable must be named \`GEMINI_API_KEY\`, not \`GOOGLE_API_KEY\`.

## Running the Application

### Start the Streamlit App

```
streamlit run main.py
```

The application will launch at \`http://localhost:8501\` in your default web browser.

### Verify Startup

You should see:
```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

