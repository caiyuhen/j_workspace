#!/bin/bash
nohup python /app/ingest_md.py > /app/ingest_md_full.log 2>&1 &
