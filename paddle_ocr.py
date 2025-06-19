import os
import json
from paddleocr import PaddleOCR
from pdf2image import convert_from_path
from datetime import datetime
from PIL import Image
import traceback


    


class PaddleOCRProcessor:
    def __init__(self, output_dir=r"OUTPUT\Processed Purchases_2"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # Initialize PaddleOCR with error handling
        try:
            self.ocr = PaddleOCR(lang='en')
            print("PaddleOCR initialized successfully")
        except Exception as e:
            print(f"Error initializing PaddleOCR: {str(e)}")
            raise

    def resize_image(self, image_path, max_size=4000):
        """Resize the image if it exceeds the maximum size limit."""
        with Image.open(image_path) as img:
            width, height = img.size
            if max(width, height) > max_size:
                ratio = max_size / max(width, height)
                new_size = (int(width * ratio), int(height * ratio))
                resample_filter = Image.Resampling.LANCZOS
                img = img.resize(new_size, resample_filter)

                resized_image_path = "resized_" + os.path.basename(image_path)
                img.save(resized_image_path)
                return resized_image_path
            else:
                return image_path

    def process_image(self, image_path):
        """Process a single image file"""
        try:
            print(f"Processing image: {image_path}")

            # Resize the image if necessary
            resized_image_path = self.resize_image(image_path)
            image_path_str = str(resized_image_path)

            # Run OCR
            result = self.ocr.predict(image_path_str)
            print(f"OCR completed, result type: {type(result)}")

            # Extract all text with confidence scores
            text_blocks = []
            full_text_parts = []

            if result is not None:
                for page_idx, page_result in enumerate(result):
                    if page_result is not None:
                        for idx, block in enumerate(page_result):
                            try:
                                text = block[1][0] if len(block) > 1 and len(block[1]) > 0 else ""
                                confidence = float(block[1][1]) if len(block) > 1 and len(block[1]) > 1 else 0.0
                                coordinates = block[0] if len(block) > 0 else []

                                text_blocks.append({
                                    "block_id": idx,
                                    "text": text,
                                    "confidence": confidence,
                                    "coordinates": coordinates
                                })

                                if text.strip():
                                    full_text_parts.append(text)

                            except (IndexError, ValueError, TypeError) as e:
                                print(f"Warning: Error parsing block {idx}: {e}")
                                continue

            # Remove the resized image if it was created
            if resized_image_path != image_path:
                try:
                    os.remove(resized_image_path)
                except OSError:
                    pass

            return {
                "filename": os.path.basename(image_path),
                "filetype": "image",
                "text_blocks": text_blocks,
                "full_text": "\n".join(full_text_parts),
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "image_size": list(Image.open(image_path).size),
                    "image_mode": Image.open(image_path).mode,
                    "ocr_engine": "PaddleOCR",
                    "total_blocks": len(text_blocks)
                }
            }

        except Exception as e:
            print(f"Error processing {image_path}: {str(e)}")
            traceback.print_exc()
            return None

    def process_pdf(self, pdf_path):
        """Process a PDF file"""
        try:
            print(f"Processing PDF: {pdf_path}")

            try:
                images = convert_from_path(pdf_path, dpi=200)
                print(f"PDF converted to {len(images)} images")
            except Exception as e:
                print(f"Error converting PDF to images: {e}")
                return None

            results = []

            for i, img in enumerate(images):
                try:
                    print(f"Processing page {i+1}/{len(images)}")

                    temp_img_path = f"temp_page_{i+1}_{os.getpid()}.jpg"
                    img.save(temp_img_path, 'JPEG', quality=95)

                    page_result = self.process_image(temp_img_path)
                    if page_result:
                        page_result["page_number"] = i + 1
                        page_result["filetype"] = "pdf_page"
                        results.append(page_result)

                    try:
                        os.remove(temp_img_path)
                    except OSError:
                        pass

                except Exception as e:
                    print(f"Error processing page {i+1}: {e}")
                    continue

            return results

        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {str(e)}")
            traceback.print_exc()
            return None

    def save_results(self, data, input_filename):
        """Save results as JSON with same name as input"""
        if not data:
            print("No data to save")
            return False

        try:
            base_name = os.path.splitext(os.path.basename(input_filename))[0]
            output_path = os.path.join(self.output_dir, f"{base_name}.json")

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"Results saved to: {output_path}")
            return True

        except Exception as e:
            print(f"Error saving results: {str(e)}")
            traceback.print_exc()
            return False

    def process_file(self, file_path):
        """Process either image or PDF"""
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False

        ext = os.path.splitext(file_path)[1].lower()
        print(f"Processing file: {file_path} (type: {ext})")

        if ext in ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'):
            result = self.process_image(file_path)
        elif ext == '.pdf':
            result = self.process_pdf(file_path)
        else:
            print(f"Unsupported file type: {ext}")
            return False

        if result:
            return self.save_results(result, file_path)
        else:
            print("No results to save")
            return False

def main():
    print("=== PaddleOCR Processor ===")
    print("Processes images/PDFs and saves text as JSON\n")

    input_path = r"DATA\Processed Purchases"

    if not os.path.exists(input_path):
        print(f"Input directory does not exist: {input_path}")
        print("Please create the directory or update the path")
        return

    try:
        processor = PaddleOCRProcessor()

        if os.path.isdir(input_path):
            files_processed = 0
            files_failed = 0

            print(f"Scanning directory: {input_path}")

            for filename in os.listdir(input_path):
                file_path = os.path.join(input_path, filename)

                if os.path.isfile(file_path):
                    print(f"\n--- Processing: {filename} ---")

                    if processor.process_file(file_path):
                        files_processed += 1
                        print(f"✓ Successfully processed: {filename}")
                    else:
                        files_failed += 1
                        print(f"✗ Failed to process: {filename}")

            print(f"\n=== Summary ===")
            print(f"Files processed successfully: {files_processed}")
            print(f"Files failed: {files_failed}")
            print(f"Total files attempted: {files_processed + files_failed}")

        elif os.path.isfile(input_path):
            print(f"Processing single file: {input_path}")
            processor.process_file(input_path)
        else:
            print(f"Invalid path: {input_path}")

    except Exception as e:
        print(f"Fatal error: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
