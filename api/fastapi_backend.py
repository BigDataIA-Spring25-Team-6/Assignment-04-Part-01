import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.pdf_extract import process_pdf
from storage.s3_utils import s3_client, S3_BUCKET_NAME 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Run the FastAPI server locally on port 8000
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)