from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_community.document_loaders import TextLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.text_splitter import CharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
from routes import emailSend

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables from .env file
load_dotenv()

# Include the email sending router
app.include_router(emailSend.router, tags=["email"])

# Pydantic model for request body
class QuestionRequest(BaseModel):
    question: str

# Initialize the Google Generative AI
llm = GoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# Load text file and create index
try:
    loader = TextLoader("Data.txt")
except Exception as e:
    raise RuntimeError(f"Error loading data: {e}")

# Create embedding
embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# Create text splitter
text_splitter = CharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
)

# Create vector store index
index_creator = VectorstoreIndexCreator(
    embedding=embedding,
    text_splitter=text_splitter,
)

# Initialize index
try:
    index = index_creator.from_loaders([loader])
except Exception as e:
    raise RuntimeError(f"Error creating index: {e}")

# --- MEMORY for storing last 5 questions ---
memory: List[str] = []

# POST endpoint to handle questions
@app.post("/ask/")
async def ask_question(request: QuestionRequest):
    try:
        # Save the question into memory
        memory.append(request.question)
        if len(memory) > 5:
            memory.pop(0)  # Keep only last 5 questions
        
        # You could also include memory in the prompt if needed
        memory_context = "\n".join(memory)
        full_prompt = f"Previous questions:\n{memory_context}\n\nCurrent question: {request.question}"

        # Query the index with the modified prompt
        response = index.query(full_prompt, llm=llm)
        
        return {
            "response": response,
            "memory": memory  # Optional: return memory so frontend can display it if needed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")
