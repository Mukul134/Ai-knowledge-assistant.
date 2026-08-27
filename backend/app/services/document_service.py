import os
import uuid
from typing import List, Dict, Any
from fastapi import UploadFile, HTTPException, status, BackgroundTasks
from supabase import Client
from app.database.supabase import get_supabase_client, get_supabase_user_client
from app.core.security import CurrentUser
from app.rag.parser import PDFParser
from app.rag.chunker import TokenChunker
from app.llm.openai_client import openai_helper

class DocumentService:
    @staticmethod
    def _ensure_bucket_exists(supabase_client: Client):
        """Ensure the 'documents' private bucket exists in Supabase Storage."""
        try:
            supabase_client.storage.get_bucket("documents")
        except Exception:
            try:
                supabase_client.storage.create_bucket("documents", options={"public": False})
            except Exception as e:
                print(f"Ensuring documents bucket existed raised exception: {str(e)}")

    @staticmethod
    async def upload_document(
        file: UploadFile, 
        current_user: CurrentUser, 
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """
        Validate PDF file, upload raw binary payload to Supabase Storage,
        register document metadata record, and schedule background ingestion task.
        """
        # 1. Validation
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format. Only PDF files are supported."
            )
        
        file_content = await file.read()
        file_size = len(file_content)
        
        # Enforce 10MB limit
        MAX_SIZE = 10 * 1024 * 1024
        if file_size > MAX_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of 10MB. Current: {file_size / (1024*1024):.2f}MB"
            )

        # 2. Storage Setup
        admin_supabase = get_supabase_client()
        DocumentService._ensure_bucket_exists(admin_supabase)
        
        document_id = str(uuid.uuid4())
        storage_path = f"{current_user.id}/{document_id}.pdf"
        
        try:
            admin_supabase.storage.from_("documents").upload(
                path=storage_path,
                file=file_content,
                file_options={"content-type": "application/pdf"}
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload document to Supabase Storage: {str(e)}"
            )

        # 3. Database Sync & Background Worker Queue
        try:
            document_data = {
                "id": document_id,
                "user_id": str(current_user.id),
                "file_name": file.filename,
                "file_path": storage_path,
                "file_size": file_size,
                "status": "uploaded"
            }
            
            response = admin_supabase.table("documents").insert(document_data).execute()
            if not response.data:
                raise Exception("Failed to insert record into database table")
                
            doc_record = response.data[0]
            
            # Enqueue the parser, embedding, and pgvector upload task asynchronously
            background_tasks.add_task(
                DocumentService.process_document_background,
                document_id,
                storage_path,
                file.filename,
                str(current_user.id)
            )
            
            return doc_record
            
        except Exception as e:
            try:
                admin_supabase.storage.from_("documents").remove([storage_path])
            except Exception:
                pass
                
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to register document in database: {str(e)}"
            )

    @staticmethod
    async def process_document_background(
        document_id: str,
        storage_path: str,
        file_name: str,
        user_id: str
    ):
        """
        Background task to download PDF from storage, parse text per page,
        split text into chunks, generate OpenAI embeddings, and bulk insert to Supabase.
        """
        admin_supabase = get_supabase_client()
        
        try:
            # 1. Update status to 'processing'
            admin_supabase.table("documents").update({
                "status": "processing"
            }).eq("id", document_id).execute()

            # 2. Download raw PDF payload from Storage
            file_bytes = admin_supabase.storage.from_("documents").download(storage_path)

            # 3. Parse PDF page-by-page
            pages = PDFParser.extract_text_by_page(file_bytes)
            
            # 4. Generate metadata-rich token chunks
            chunker = TokenChunker()
            all_chunks = []
            
            for page in pages:
                page_chunks = chunker.chunk_page(
                    page_text=page["text"],
                    page_number=page["page_number"],
                    file_name=file_name,
                    document_id=document_id,
                    user_id=user_id
                )
                all_chunks.extend(page_chunks)

            # Check if text extraction worked but produced no chunk segments
            if not all_chunks:
                raise ValueError("PDF parsing succeeded but no semantic text chunks were created.")

            # 5. Call OpenAI Embeddings in Batch
            chunk_contents = [c["content"] for c in all_chunks]
            embeddings = await openai_helper.get_embeddings(chunk_contents)

            # 6. Merge vector embeddings into chunk data
            for chunk_obj, embedding_vector in zip(all_chunks, embeddings):
                chunk_obj["embedding"] = embedding_vector

            # 7. Bulk Insert chunks to database (runs in background under admin privileges)
            # Split bulk writes into sub-batches of 100 to prevent transaction payload limits
            BATCH_SIZE = 100
            for i in range(0, len(all_chunks), BATCH_SIZE):
                batch = all_chunks[i : i + BATCH_SIZE]
                admin_supabase.table("document_chunks").insert(batch).execute()

            # 8. Update status to 'completed' with correct page counts
            admin_supabase.table("documents").update({
                "status": "completed",
                "page_count": len(pages),
                "error_message": None
            }).eq("id", document_id).execute()

            print(f"Background ingestion success: Document {document_id} completely processed ({len(all_chunks)} chunks).")

        except Exception as e:
            # Catch all extraction failures, flag status to 'failed', and write error details
            error_msg = str(e)
            print(f"Background ingestion failure on document {document_id}: {error_msg}")
            try:
                admin_supabase.table("documents").update({
                    "status": "failed",
                    "error_message": error_msg
                }).eq("id", document_id).execute()
            except Exception as db_err:
                print(f"Failed to write failure status to DB: {str(db_err)}")

    @staticmethod
    def list_documents(current_user: CurrentUser, jwt_token: str) -> List[Dict[str, Any]]:
        """List all documents uploaded by the authenticated user."""
        user_supabase = get_supabase_user_client(jwt_token)
        response = user_supabase.table("documents").select("*").order("created_at", descending=True).execute()
        return response.data

    @staticmethod
    def get_document(document_id: str, current_user: CurrentUser, jwt_token: str) -> Dict[str, Any]:
        """Get metadata for a specific document."""
        user_supabase = get_supabase_user_client(jwt_token)
        response = user_supabase.table("documents").select("*").eq("id", document_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or access denied."
            )
        return response.data[0]

    @staticmethod
    def delete_document(document_id: str, current_user: CurrentUser, jwt_token: str) -> Dict[str, Any]:
        """Delete document metadata from PostgreSQL and binary payload from Supabase Storage."""
        user_supabase = get_supabase_user_client(jwt_token)
        admin_supabase = get_supabase_client()
        
        doc = DocumentService.get_document(document_id, current_user, jwt_token)
        storage_path = doc["file_path"]

        try:
            user_supabase.table("documents").delete().eq("id", document_id).execute()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete document metadata: {str(e)}"
            )

        try:
            admin_supabase.storage.from_("documents").remove([storage_path])
        except Exception as e:
            print(f"Warning: Failed to delete raw file from Supabase Storage: {str(e)}")

        return {"message": "Document and associated chunks deleted successfully.", "id": document_id}
