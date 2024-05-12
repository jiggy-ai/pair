import io

def main():
    # Create a bytes-like object in memory
    bytes_data = b"Hello, this is a demo of io.BytesIO!"

    # Use io.BytesIO to create a file-like object from bytes data
    file_like_object = io.BytesIO(bytes_data)

    # Now you can read from this "file"
    # To read content from it like a file:
    content = file_like_object.read()
    print(content)  # This would print the bytes data that was initially stored

    # When you are done, you can close the stream
    file_like_object.close()

if __name__ == "__main__":
    main()