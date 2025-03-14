import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.pdf_extract import process_pdf
from storage.s3_utils import s3_client, S3_BUCKET_NAME,generate_presigned_url
from pydantic import BaseModel
import redis
import requests
import ast
from dotenv import load_dotenv
import os

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT,password=REDIS_PASSWORD, decode_responses=True)

# Redis stream keys
TASK_STREAM = "task_stream"
RESULT_STREAM = "result_stream"

# Request models for summarization and question answering
class SummarizeRequest(BaseModel):
    model_name: str  
    document_url: str

class AskQuestionRequest(BaseModel):
    model_name: str  
    document_url: str
    question: str

@app.get("/select_pdfcontent/")
async def select_pdfcontent():
    """
    Lists all previously processed PDFs stored in S3, along with their Markdown and image files.
    """
    try:
        # Step 1: List objects in the S3 bucket
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME)

        # Step 2: Organize files under their respective PDF groups
        pdf_files = {}

        if "Contents" in response:
            for obj in response["Contents"]:
                object_key = obj["Key"]

                # Extract top-level PDF folder name
                parts = object_key.split("/")
                if len(parts) > 1:
                    pdf_name = parts[0]  # e.g., "example_pdf"

                    # Group all markdown and images under each PDF name
                    if pdf_name not in pdf_files:
                        pdf_files[pdf_name] = {"markdown": None, "images": []}

                    if "markdown" in object_key:
                        pdf_files[pdf_name]["markdown"] = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{object_key}"
                    elif "images" in object_key:
                        pdf_files[pdf_name]["images"].append(f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{object_key}")

        return {"processed_pdfs": pdf_files}

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Handles PDF file upload, processes it, and stores results in S3.
    """
    try:
        # Step 1: Read the uploaded file content
        file_content = await file.read()

        # Step 2: Call process_pdf with original filename for structured S3 storage
        result = process_pdf(file_content, file.filename)

        # Step 3: Return the S3 URLs and other details
        return {
            "message": result["message"],
            "markdown_s3_url": result["markdown_s3_url"],  # Markdown URL
            "image_s3_urls": result["image_s3_urls"],      # List of Image URLs
            "pdf_filename": result["pdf_filename"],        # Filename without extension (used for grouping)
            "status": result["status"]
        }

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
@app.post("/summarize")
async def summarize(request: SummarizeRequest):
    try:
        document_url = request.document_url
        s3_base_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/"
        if document_url.startswith(s3_base_url):
            object_key = document_url.replace(s3_base_url, "")
            signed_url = generate_presigned_url(object_key)
            if not signed_url:
                raise HTTPException(status_code=500, detail="Failed to generate signed URL.")
            document_url = signed_url


        markdown_response = requests.get(document_url)
        if markdown_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch document content.")
        
        markdown_content = markdown_response.text

        # Add summarization task to Redis stream
        task_id = redis_client.xadd(
            TASK_STREAM,
            {
                "task_type": "summarize",
                "model_name": request.model_name,
                "document_content": markdown_content,
            },
        )
        return {"status": "Task added", "task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding summarization task: {str(e)}")

@app.post("/ask_question")
async def ask_question(request: AskQuestionRequest):
    try:
        # Add question answering task to Redis stream
        task_id = redis_client.xadd(
            TASK_STREAM,
            {
                "task_type": "ask_question",
                "model_name": request.model_name,
                "document_content": request.document_url,
                "question": request.question,
            },
        )
        print(task_id)
        return {"status": "Task added", "task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding question answering task: {str(e)}")

@app.get("/get_result/{task_id}")
async def get_result(task_id: str):
    try:
        # Retrieve the result from Redis stream or cache
        result = redis_client.hget(RESULT_STREAM, task_id)
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")

        print(f"Retrieved result for Task ID {task_id}: {result}")
        # Convert Redis string back to dictionary
        result_data = ast.literal_eval(result)

        return {
            "task_id": task_id,
            "result": result_data.get("result", "No result available."),
            "input_tokens": result_data.get("input_tokens", "N/A"),
            "output_tokens": result_data.get("output_tokens", "N/A"),
            "cost": result_data.get("cost", "Cost unavailable.")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving result: {str(e)}")

# Run the FastAPI server locally on port 8000
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)