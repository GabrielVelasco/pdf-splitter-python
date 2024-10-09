# PDF Splitter

A simple GUI application that splits PDF files into smaller parts based on file size. Built with Python and Tkinter.

## For Users

### Quick Start

1. Download `spdf_gui.exe'.
2. Double-click to run the application
3. Select your PDF file using the "Browse" button
4. Choose the desired part size (in MB) from the dropdown
5. Click "Split PDF" to start the process
6. Find the split PDF parts in the "output" folder (created in the same directory as the executable)

### Notes

- When a page is larger than the specified part size, you'll be prompted to either:
  - Include it as a single part
  - Skip it entirely
- The application will create (or clear) an "output" folder for the split PDF files
- Each part will be named as `original_filename_part_X.pdf` where X is the part number

## For Developers

### Prerequisites

- Python 3.12.7
- Required packages:
  ```
  pip install tkinter
  pip install PyPDF2
  pip install pyinstaller  # Only needed for creating executable
  ```

### Running from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pdf-splitter.git
   cd pdf-splitter
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python spdf_gui.py
   ```

### Creating the Executable

To create a standalone executable:

```bash
pyinstaller --onefile --windowed spdf_gui.py
```

The executable will be created in the `dist` directory.

#### Build Options Explained:
- `--onefile`: Creates a single executable file
- `--windowed`: Prevents console window from appearing when running the executable

### Project Structure

```
pdf-splitter/
├── spdf_gui.py          # Main application source
├── spdf_gui.exe         # Compiled executable
```

## How It Works

Explained throughout the code...