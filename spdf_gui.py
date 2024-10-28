import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import sys
from PyPDF2 import PdfReader, PdfWriter
import io
from threading import Thread, Event
import queue

"""
    # Main thread (GUI)        <>        # Worker thread (PDF processing)
                              
    button clicked
    └─> start_processing()
            └─> create & start thread ─────> split_pdf() runs
                └─> return to GUI         │
                                          ├─> log_message() queues updates
    GUI remains responsive                │     └─> messages added to queue
    └─> update_output()                   │
            └─> check queue <─────────────┘
                └─> update text widget
"""

class PdfSplitterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Splitter")
        # self.root.iconbitmap(self.resource_path("custom_icon.ico"))
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # create a queue for thread-safe communication
        self.message_queue = queue.Queue()
        
        self.create_widgets() # create the GUI widgets like buttons, labels so on...
        self.update_output()

        self.dialog_response = None
        self.dialog_event = Event()

    def ask_user_from_main_thread(self, msg):
        """
            Ask the user for a response in a separate dialog window.
            This method is called from the main thread and waits for the user to respond.
        """

        def show_dialog():
            self.dialog_response = messagebox.askyesno(
                "Confirm Action",
                msg
            )
            self.dialog_event.set() # notify the main thread that the dialog has been closed

        self.dialog_event.clear() # clear the event flag
        self.root.after(0, show_dialog) # run the dialog in the main thread
        self.dialog_event.wait() # wait for response

        return self.dialog_response

    # get the path to the bundled custom icon file (use flag: --add-data="cropped-zarro-icon.ico;." with PyInstaller)
    def resource_path(self, relative_icon_path):
        if hasattr(sys, '_MEIPASS'):
            # If running from PyInstaller's bundle
            return os.path.join(sys._MEIPASS, relative_icon_path)
        else:
            # If running in a normal Python environment
            return os.path.join(os.path.abspath("."), relative_icon_path)

    def create_widgets(self):
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="10", style="Custom.TFrame")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Input file section with file selector
        ttk.Label(main_frame, text="Selected PDF:", style="Custom.TLabel").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # Frame for file input and button
        file_frame = ttk.Frame(main_frame, style="Custom.TFrame")
        file_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        file_frame.columnconfigure(0, weight=1)
        
        self.input_file = ttk.Entry(file_frame)
        self.input_file.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        select_btn = ttk.Button(file_frame, text="Browse", command=self.select_file, style="Custom.TButton")
        select_btn.grid(row=0, column=1, padx=(5, 0))
        
        # Part size section
        ttk.Label(main_frame, text="Part Size (MB):", style="Custom.TLabel").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.part_size = ttk.Combobox(main_frame, values=[1, 2, 5, 10, 20, 50])
        self.part_size.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        self.part_size.set(5)
        
        # Split PDF button
        self.process_btn = ttk.Button(main_frame, text="Split PDF", command=self.start_processing, style="Custom.TButton")
        self.process_btn.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Output text frame
        output_frame = ttk.LabelFrame(main_frame, text="Logs...", padding="5", style="Custom.TLabelframe")
        output_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.rowconfigure(3, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=15) #
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Waiting for input...")
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, style="Custom.TLabel")
        self.status_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

    def select_file(self):
        """Open file dialog for selecting PDF file"""

        filetypes = (
            ('PDF files', '*.pdf'),
            ('All files', '*.*')
        )
        filename = filedialog.askopenfilename(
            title='Select a PDF file',
            filetypes=filetypes
        )
        if filename:
            self.input_file.delete(0, tk.END)
            self.input_file.insert(0, filename)

    def log_message(self, message):
        self.message_queue.put(message)
    
    def update_output(self):
        """
            At each call, get messages from the queue and update the output text.
            Using this method (producer-comsumer pattern) prevents the GUI from freezing (thread-safe)

        """

        try:
            while True:
                message = self.message_queue.get_nowait()
                self.output_text.insert(tk.END, message + "\n")
                self.output_text.see(tk.END)
                self.output_text.update_idletasks()

        except queue.Empty:
            pass

        finally:
            self.root.after(100, self.update_output) # Schedule the next update. Runs at main thread (consumer)
    
    def start_processing(self):
        """
            Get selected file and part size, then start the PDF splitting process in a separate thread.
        """

        input_file = self.input_file.get()

        try:
            part_size = int(self.part_size.get())
            if part_size <= 0:
                raise ValueError("Invalid part size")

        except ValueError as e:
            messagebox.showerror("Error", e.args[0])
            return
        
        if not os.path.exists(input_file):
            messagebox.showerror("Error", f"File not found: {input_file}")
            return
        
        self.process_btn.state(['disabled'])
        self.status_var.set("Processing...")
        
        # If everything ok, start processing in a separate thread (worker thread)
        Thread(target=self.split_pdf, args=(input_file, "output", part_size), daemon=True).start()

    def get_page_sizes(self, pdf_reader):
        """
            Get the size of each page in the PDF file. 
            Returns a list of page sizes in bytes. 
            Used to check if page will fit in part size.
        """

        page_sizes = []

        for page in pdf_reader.pages:
            temp_writer = PdfWriter()
            temp_writer.add_page(page)

            temp_buffer = io.BytesIO()

            temp_writer.write(temp_buffer) # write to buffer

            page_length = len(temp_buffer.getvalue())
            page_sizes.append(page_length)

        return page_sizes
    
    def split_pdf(self, input_path, output_folder, part_size_mb):
        try:
            # If folder 'output' exists, delete it, if not, create it
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            else:
                for file in os.listdir(output_folder):
                    os.remove(os.path.join(output_folder, file))
            
            # Open the PDF file
            self.log_message(f"Opening PDF: {input_path}")
            pdf_reader = PdfReader(input_path)
            page_sizes = self.get_page_sizes(pdf_reader)
            total_pages = len(pdf_reader.pages)
            self.log_message(f"Original PDF total pages count: {total_pages}")
            
            part_size_bytes = part_size_mb * 1024 * 1024
            current_part = 1
            current_writer = PdfWriter()
            current_page_count = 0
            total_pages_final = 0
            accumulated_size = 0
            
            for page_num in range(total_pages):
                accumulated_size += page_sizes[page_num] # simulate adding page to writer
                
                if accumulated_size >= part_size_bytes:
                    # create new writer without the last page
                    finished_part_length = current_page_count
                    
                    # save current part
                    output_filename = f"{os.path.splitext(os.path.basename(input_path))[0]}_part_{current_part}.pdf"
                    output_path = os.path.join(output_folder, output_filename)
                    with open(output_path, "wb") as output_file:
                        current_writer.write(output_file) # write to file
                    
                    total_pages_final += finished_part_length
                    self.log_message(f"Part #{current_part} has {finished_part_length} pages.")
                    
                    # start new part
                    current_part += 1
                    current_writer = PdfWriter()
                    current_page_count = 0
                    accumulated_size = page_sizes[page_num]

                current_writer.add_page(pdf_reader.pages[page_num]) # add page to writer for real
                current_page_count += 1
            
            # save the last part if not empty
            if current_page_count > 0:
                output_filename = f"{os.path.splitext(os.path.basename(input_path))[0]}_part_{current_part}.pdf"
                output_path = os.path.join(output_folder, output_filename)

                with open(output_path, "wb") as output_file:
                    current_writer.write(output_file)

                self.log_message(f"Part #{current_part} has {current_page_count} pages.")
                total_pages_final += current_page_count
            
            self.log_message(f"PDF splited into {current_part} parts.")
            
            if total_pages_final != total_pages:
                self.log_message(f"WARNING: Total pages in parts ({total_pages_final}) does not match original PDF ({total_pages})")
            else:
                self.log_message(f"Total pages in parts match original PDF: {total_pages_final}")
            
            self.status_var.set("Done!")
            
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
            self.status_var.set("Something went wrong!")

        finally:
            self.root.after(0, lambda: self.process_btn.state(['!disabled']))

def main():
    root = tk.Tk()
    app = PdfSplitterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()