import base64
import mimetypes

def image_to_data_url(filepath):
    # Determine the MIME type based on the file extension
    mime_type, _ = mimetypes.guess_type(filepath)
    if mime_type is None:
        raise ValueError("Unsupported file type")

    # Read the binary content of the image
    with open(filepath, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode()

    # Construct the data URL
    return f"data:{mime_type};base64,{encoded_image}"

# Example usage:
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python image_to_data_url.py <image_path>")
        sys.exit(1)
    filepath = sys.argv[1]
    print(image_to_data_url(filepath))