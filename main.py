import os
import json
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from datetime import datetime

class OCRProcessor:
    def __init__(self, output_dir="OUTPUT\Processed Purchases"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def process_image(self, image_path):
        """Process a single image file and return OCR results"""
        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            
            return {
                "filename": os.path.basename(image_path),
                "filetype": "image",
                "text": text,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "image_size": img.size,
                    "image_mode": img.mode,
                    "ocr_engine": "Tesseract " + pytesseract.get_tesseract_version()
                }
            }
        except Exception as e:
            print(f"Error processing image {image_path}: {str(e)}")
            return None
    
    def process_pdf(self, pdf_path):
        """Process a PDF file and return OCR results for each page"""
        try:
            images = convert_from_path(pdf_path)
            results = []
            
            for i, img in enumerate(images):
                text = pytesseract.image_to_string(img)
                
                results.append({
                    "filename": os.path.basename(pdf_path),
                    "filetype": "pdf",
                    "page_number": i + 1,
                    "text": text,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {
                        "image_size": img.size,
                        "image_mode": img.mode,
                        "ocr_engine": "Tesseract " + pytesseract.get_tesseract_version()
                    }
                })
            
            return results
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {str(e)}")
            return None
    
    def save_results(self, data, input_filename):
        """Save OCR results to JSON file with same name as input"""
        if not data:
            return False
            
        try:
            # Create output filename (same as input but with .json extension)
            base_name = os.path.splitext(os.path.basename(input_filename))[0]
            output_filename = f"{base_name}.json"
            output_path = os.path.join(self.output_dir, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"OCR results saved to: {output_path}")
            return True
        except Exception as e:
            print(f"Error saving results: {str(e)}")
            return False
    
    def process_single_file(self, file_path):
        """Process a single file (image or PDF)"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif'):
            return self.process_image(file_path)
        elif file_ext == '.pdf':
            return self.process_pdf(file_path)
        else:
            print(f"Skipping unsupported file type: {file_path}")
            return None
    
    def process_directory(self, dir_path):
        """Process all supported files in a directory"""
        processed_files = 0
        skipped_files = 0
        
        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            
            if os.path.isfile(file_path):
                result = self.process_single_file(file_path)
                
                if result is not None:
                    if self.save_results(result, file_path):
                        processed_files += 1
                    else:
                        skipped_files += 1
                else:
                    skipped_files += 1
        
        print(f"\nProcessing complete!")
        print(f"Files processed: {processed_files}")
        print(f"Files skipped: {skipped_files}")
        return processed_files > 0

def main():
    # Configure Tesseract path if not in system PATH
    # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    print("=== OCR File Processor ===")
    print("Processes image/PDF files and saves text as JSON\n")
    
    while True:
        input_path = "DATA\Processed Purchases"
        
        if input_path.lower() == 'quit':
            break
            
        if not os.path.exists(input_path):
            print("Error: The specified path does not exist\n")
            continue
            
        processor = OCRProcessor()
        
        if os.path.isfile(input_path):
            result = processor.process_single_file(input_path)
            if result:
                processor.save_results(result, input_path)
            else:
                print("Failed to process the file\n")
        elif os.path.isdir(input_path):
            processor.process_directory(input_path)
            print()
        else:
            print("Error: Invalid input path\n")

if __name__ == "__main__":
    main()