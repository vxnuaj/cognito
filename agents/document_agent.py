import os
from utils.arxiv_utils import PaperMetadata
from utils.shared_types import ExtractedContent
from orgo import Computer

class DocumentAgent:
    def run(self, paper_metadata: PaperMetadata) -> ExtractedContent:
        print(f"DocumentAgent: Processing {paper_metadata.title} within Orgo VM...")
        computer = None
        raw_text = ""
        image_data = []

        try:
            computer = Computer()
            pdf_filename = f"{paper_metadata.arxiv_id}.pdf"
            pdf_path_in_vm = f"/tmp/{pdf_filename}" # Orgo VM typically has /tmp writable

            # 1. Download PDF within the VM using computer.prompt
            print(f"DocumentAgent: Instructing VM to download PDF from {paper_metadata.pdf_url}")
            download_prompt = (
                f"Download the PDF from the URL {paper_metadata.pdf_url} "
                f"and save it to {pdf_path_in_vm}. Confirm successful download."
            )
            download_response_messages = computer.prompt(download_prompt)
            # TODO: Parse download_response_messages to confirm success. For now, assume it works.
            print("DocumentAgent: VM instructed to download PDF.")

            # 2. Extract text from PDF within the VM
            print("DocumentAgent: Instructing VM to extract text from PDF...")
            text_extract_prompt = (
                f"Open the PDF file at {pdf_path_in_vm}. "
                f"Extract all the text content from it. "
                f"Return the raw text content as a single string in your response."
            )
            text_extract_response_messages = computer.prompt(text_extract_prompt)
            # Parse the response to get the raw text
            for message in text_extract_response_messages:
                if message.role == "assistant":
                    for block in message.content:
                        if block.type == "text":
                            raw_text += block.text
            print("DocumentAgent: VM instructed to extract text and returned content.")

            # 3. Screenshotting within the VM
            # Instruct the VM to open the PDF for screenshotting
            print("DocumentAgent: Instructing VM to open PDF for screenshot...")
            open_pdf_prompt = f"Open the PDF file at {pdf_path_in_vm}."
            computer.prompt(open_pdf_prompt) # No need to capture response, just execute

            # Now that the PDF is presumably open in the VM, take a screenshot directly
            try:
                print("DocumentAgent: Capturing screenshot via Computer.screenshot_base64()...")
                base64_image = computer.screenshot_base64()
                image_data.append(base64_image)
                print("DocumentAgent: Screenshot captured.")
            except Exception as e:
                print(f"DocumentAgent: Could not capture screenshot: {e}")

            return ExtractedContent(raw_text=raw_text, image_data=image_data)

        except Exception as e:
            print(f"DocumentAgent Error processing {paper_metadata.title}: {e}")
            return ExtractedContent(raw_text="", image_data=[])
        finally:
            if computer:
                computer.destroy()
                print("DocumentAgent: Orgo Computer instance destroyed.")
