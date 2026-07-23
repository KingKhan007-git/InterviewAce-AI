import os

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a given PDF file path using pypdf or PyPDF2.
    Returns clean text string or raises ValueError if invalid file/empty text.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at path: {pdf_path}")
        
    extracted_text = ""
    
    # Try pypdf first
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
    except ImportError:
        # Fallback to PyPDF2 if pypdf is not available
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text + "\n"
        except Exception as e:
            raise RuntimeError(f"Error parsing PDF with PyPDF2: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error parsing PDF with pypdf: {str(e)}")

    clean_text = extracted_text.strip()
    if not clean_text:
        raise ValueError("Could not extract any readable text from the uploaded PDF document. Please ensure it contains selectable text, not scanned images.")

    return clean_text
