#!/bin/bash
docker exec rag_service python /app/ingest_md.py > /home/user/RAG_Project/ingest_md.log 2>&1
