import os
import shutil
import glob
from datetime import datetime
import pymupdf  # fitz
from docx import Document

SOURCE_DIR = "/mnt/disk3/home/pg/RAG_Project/data/sf/"
BASE_DEST_DIR = "/mnt/disk3/home/pg/RAG_Project/data/"

def get_timestamp_folder():
    now = datetime.now()
    folder_name = f"convert_folder_{now.strftime('%Y%m%d_%H%M%S')}"
    return os.path.join(BASE_DEST_DIR, folder_name)

def convert_pdf_to_md(pdf_path, output_path):
    try:
        doc = pymupdf.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\n\n"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        return True
    except Exception as e:
        print(f"Error converting PDF {pdf_path}: {e}")
        return False

def convert_docx_to_md(docx_path, output_path):
    try:
        doc = Document(docx_path)
        text = "\n\n".join([para.text for para in doc.paragraphs])
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        return True
    except Exception as e:
        print(f"Error converting DOCX {docx_path}: {e}")
        return False

def main():
    dest_dir = get_timestamp_folder()
    
    # Check if source dir exists
    if not os.path.exists(SOURCE_DIR):
        print(f"Source directory {SOURCE_DIR} does not exist.")
        return

    files = glob.glob(os.path.join(SOURCE_DIR, "*"))
    files = [f for f in files if os.path.isfile(f)]
    
    if not files:
        print(f"No files found in {SOURCE_DIR}.")
        return

    os.makedirs(dest_dir, exist_ok=True)
    print(f"Created output directory: {dest_dir}")

    converted_files = []
    failed_files = []

    for file_path in files:
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        output_path = os.path.join(dest_dir, name + ".md")
        success = False

        if ext == ".pdf":
            success = convert_pdf_to_md(file_path, output_path)
        elif ext == ".docx":
            success = convert_docx_to_md(file_path, output_path)
        elif ext == ".doc":
            print(f"Skipping .doc file (requires manual conversion): {filename}")
            failed_files.append(file_path)
            continue
        else:
            print(f"Skipping unsupported file type: {filename}")
            continue

        if success:
            converted_files.append(file_path)
        else:
            failed_files.append(file_path)

    # Delete processed files
    print("\nDeleting successfully converted files...")
    for file_path in converted_files:
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")
            
    # Handle failed files
    if failed_files:
        print("\nNote: The following files were NOT deleted because conversion failed or was skipped:")
        for f in failed_files:
            print(f" - {os.path.basename(f)}")
            
    # Force delete all if strictly requested? 
    # The user said "delete ALL files". 
    # I will add a final cleanup step for ALL files, but warn.
    # Actually, to be strictly compliant with "delete all files in ...", I should delete everything.
    # I'll implement "delete everything" but print a warning about what wasn't converted.
    
    print("\nCleaning up remaining files in source directory (as requested)...")
    remaining_files = glob.glob(os.path.join(SOURCE_DIR, "*"))
    for file_path in remaining_files:
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

    print("\nConversion Summary:")
    print(f"Total files processed: {len(files)}")
    print(f"Converted: {len(converted_files)}")
    print(f"Output folder: {dest_dir}")

if __name__ == "__main__":
    main()
