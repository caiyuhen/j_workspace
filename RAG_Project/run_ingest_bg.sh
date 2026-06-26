#!/bin/bash
nohup python /app/ingest_md.py > /app/ingest.log 2>&1 &
