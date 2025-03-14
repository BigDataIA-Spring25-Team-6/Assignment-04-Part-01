# Streamlit Application with LLM Integration

## Team Members
- **Aditi Ashutosh Deodhar**  002279575  
- **Lenin Kumar Gorle**       002803806  
- **Poorvika Girish Babu**    002801388  

## Project Overview
### Problem Statement
This assignment enhances the existing project by developing a Streamlit web application that programmatically invokes Large Language Models (LLMs) using FastAPI as an intermediary and LiteLLM for API management. The application processes PDF documents to provide summarization and Q&A functionalities while efficiently managing API calls and pricing.

### Methodology
Refer to the codelabs document for a detailed explanation of the QuickStart.

### Scope
The project aims to build an interactive Streamlit web application with backend API support via FastAPI. The application will:
- Allow users to select previously parsed PDF content or upload new PDF files.
- Utilize LLMs such as GPT-4o through LiteLLM to generate document summaries and answer user-submitted questions.
- Implement API integrations using LiteLLM to manage interactions with different LLM providers.
- Use Redis Streams for efficient communication between FastAPI and other services.
- Deploy all components using Docker Compose for scalable cloud deployment.

## Technologies Used
- Python  
- Streamlit  
- FastAPI  
- LiteLLM  
- Redis Streams  
- Docker  
- AWS  

## Architecture Diagram
![image](https://github.com/user-attachments/assets/e741cbdb-a217-4bfc-ab2e-9b8d22fd9df5)


## Codelabs Documentation
(https://codelabs-preview.appspot.com/?file_id=15u3ISoyIAyo5sf330sx46cRe1uK48j4NtYSDqzU8v3Q#0)

## Hosted Applications links 
- Frontend : https://frontend-541167511413.us-central1.run.app
- Backend : https://backend-541167511413.us-central1.run.app

## Prerequisites
- Python 3.9+  
- AWS Account  
- LiteLLM API Key  
- Redis Server  

## Set Up the Environment
```sh
# Clone the repository
git clone https://github.com/BigDataIA-Spring25-Team-6/Assignment-04.git
cd DAMG7245-Assignment-04

# Add all the environmental variables in .env file
# Configure secrets for FastAPI, LiteLLM, and Redis in GitHub Secrets
# Enable GitHub Actions for CI/CD pipeline

# Install required dependencies
pip install -r requirements.txt

# Set up a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate     # On Windows
pip install -r requirements.txt

# Configure Redis Server
# If running locally, start Redis server:
redis-server
# Or configure an external Redis service (AWS ElastiCache, Redis Cloud, etc.)

# Run FastAPI backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Run Streamlit frontend
streamlit run frontend/app.py

# Docker Setup (optional, for deployment)
docker-compose up --build
```

## Project Structure

```

ASSIGNMENT-04-PART-01/

├── .venv/

├── api/               # fastapi code

├── backend/           # backend code for pdf extraction

├── frontend/          # streamlit code

├── llm_integration/   # redis code 

├── storage/           # s3 code

├── .dockerignore

├── .gitignore

├── docker-compose.yml

└── requirements.txt

```
 





