import hashlib
import tkinter as tk
from tkinter import filedialog
import os
import json


class FileIntegrityCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Integrity Checker")
                
        # Initialize variables
        self.app_data_path = os.environ['APPDATA']
        self.baseline_file_path = os.path.join(self.app_data_path, "FIC", "baseline_hashes.json")
        
        
        #create baseline_file
        self.create_baseline_file()
        
        #intializing variables depending on baseline_file
        self.baseline_hashes = self.retrieve_data_from_baseline_hashes()
        self.files_to_check = set(self.baseline_hashes.keys())
        self.added_folders = set()
        self.added_files = set()
        self.current_hashes = {}
        
        # Create UI elements
        self.add_file_button = tk.Button(self.root, text="Add File(s)", command= self.add_files)
        self.add_file_button.grid(column = 18, row = 0, pady=10)
        
        self.add_folder_button = tk.Button(self.root, text="Add Folder(s)", command=self.add_folders)
        self.add_folder_button.grid(column = 19, row = 0, pady=10)


        #self.check_button_var = tk.StringVar(value="Check Integrity")
        self.check_button = tk.Button(self.root, text = "Check Integrity", command = self.check_integrity)
        self.check_button.grid(row=0, column=10, pady=10, columnspan= 2, rowspan= 2)

        #show hash button
        self.show_hash_button = tk.Button(self.root, text = "Show Hashes", command = self.show_hashes)
        self.show_hash_button.grid(row=0, column=0, pady=10)
        
        #verify button
        self.show_hash_button = tk.Button(self.root, text = "Verify Changes", command = self.verify_changes)
        self.show_hash_button.grid(row=0, column=1, pady=10)

        
        #result space
        self.result_text = tk.Text(self.root, height=40, width=160)
        self.result_text.grid(row=2, column=0, columnspan=20, rowspan= 10, padx=10, pady=10)
        
        
    def add_files(self):
        
        #tuple of files added till now
        file_paths = filedialog.askopenfilename(parent=self.root, title="Select file(s) to add", multiple=True)
        
        #due to multiple file slection is enabled, tuple is returned by askopenfilename. therefore parsing of each file needs to be done
        if file_paths:
            for file_path in file_paths:
                #normalising file_path
                file_path = self.normalise_file_path(file_path)
                
                #adding file to files_to_check to keep track of what files to check
                self.add_file_to_added_files(file_path)
                
                #creating hash and addding to baseline_hashes file & dict and files_to_check to keep real time tracking
                self.save_baseline(file_path)
                
            self.result_text.insert(tk.END, f"Added {len(file_paths)} file(s).\n")
            
    def add_folders(self):
        folder_path = filedialog.askdirectory(parent=self.root, title = "Select folder(s) to add")
        if folder_path:
            
            #add to folders set to keep real time tracking of selected folders
            self.add_folder_to_added_folders(folder_path)
            
            file_count = 0
            # Iterate through all files in the folder
            for root_dir, _, files in os.walk(folder_path):
                for file_name in files:
                    #joining directory path with file name for creating full file_path
                    file_path = os.path.join(root_dir, file_name)
                    
                    #normalising file_path for having consistency
                    file_path = self.normalise_file_path(file_path)
                    
                    #adding files that are not already added.
                    if file_path not in self.files_to_check:
                        #compute hash and add file to baseline_hashes and files_to_check
                        self.save_baseline(file_path)
                        print(f"{file_path} added\n")
                        #increase file_count for every successful file add
                        file_count += 1
            self.result_text.insert(tk.END, f"Added {file_count} file(s).\n")
                    
    
    def compute_file_hash(self, file_path, hash_algorithm='sha256'):
        """Compute the hash of a file."""
        hash_func = hashlib.new(hash_algorithm)
        try:
            with open(file_path, 'rb') as file:
                while chunk := file.read(8192):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            print(f"Could not read file {file_path}: {e}")
            return None
    
    def check_integrity(self):
        #creating tags for changing forground colors of the file names 
        self.result_text.tag_configure("changed", foreground= "red")
        self.result_text.tag_configure("not_changed", foreground= "green")
        self.result_text.tag_configure("removed", foreground= "grey")
        
        #sorting files according to their integrity
        changed = list()
        removed = list()
        not_changed = list()
        
        #clearing the older outputs
        self.result_text.delete(1.0, tk.END)
        
        if not self.files_to_check:
            tk.messagebox.showwarning("No Files Selected", "Please add files or folders first.")
            return
        
        self.result_text.insert(tk.END, "-"*158 + "\n")
        self.result_text.insert(tk.END, f"{'INTEGRITY CHECK':^{158}}\n")
        self.result_text.insert(tk.END, "-"*158 + "\n")
        
        for file_path in self.files_to_check:
            #checking if file_path in files_to_check is not in os.path, which means file is moved or deleted
            if not os.path.isfile(file_path):
                #self.result_text.insert(tk.END, f"Removed: {file_path}\n", "removed")
                removed.append(file_path)
            
            #if file path is present in OS then checking if hash is same
            else:
                #if hash is not same
                if not self.check_hash(file_path):
                    #self.result_text.insert(tk.END, f"File Changed: {file_path}\n", "changed")
                    changed.append(file_path)
                
                #if hash is same
                else:
                    #self.result_text.insert(tk.END, f"no changes: {file_path}\n", "not_changed")
                    not_changed.append(file_path)
        
        if changed:
            changed.sort()
            self.result_text.insert(tk.END, "CHANGED\n")            
            for file_path in changed:
                self.result_text.insert(tk.END, f"{file_path}\n", "changed")
            self.result_text.insert(tk.END, "\n\n")
        
        if removed:
            removed.sort()
            self.result_text.insert(tk.END, "REMOVED\n")
            for file_path in removed:
                self.result_text.insert(tk.END, f"{file_path}\n", "removed")
            self.result_text.insert(tk.END, "\n\n")
        
        if not_changed:
            not_changed.sort()
            self.result_text.insert(tk.END, "NO CHANGES\n")
            for file_path in not_changed:
                self.result_text.insert(tk.END, f"{file_path}\n", "not_changed")
            self.result_text.insert(tk.END, "\n\n")
                   
        self.result_text.insert(tk.END, "-"*154 + "\n")    
        self.result_text.insert(tk.END, f"{'Integrity Check Completed':^158}\n")
  
        
    #creating checkbox group with select all option
    def create_group(self, parent, label, options):
        frame = tk.Frame(parent)
        frame.pack(padx=10, pady=5, anchor="w")
        
        #adding selct all option
        def select_all(group, var, checkboxes):
            state = var.get()
            for checkbox in checkboxes:
                checkbox_var, checkbox_widget = checkbox
                checkbox_var.set(state)

        var_select_all = tk.IntVar()
        select_all_checkbox = tk.Checkbutton(frame, text="Select All", variable=var_select_all, command=lambda: select_all(frame, var_select_all, checkboxes))
        select_all_checkbox.pack(anchor="w")

        checkboxes = []
        for option in options:
            var = tk.IntVar()
            checkbox = tk.Checkbutton(frame, text=option, variable=var)
            checkbox.pack(anchor="w")
            checkboxes.append((var, checkbox))
        
        return frame
    
    #verify function
    def verify_changes(self, files):
        pass
    
    #compute hash and add file to baseline_hashes
    def save_baseline(self, file_path):
        file_hash = self.compute_file_hash(file_path)
        
        #normalisig file path to have consistency in file path formats
        normalise_file_path = self.normalise_file_path(file_path)
        
        #creating dictionary to add in baseline_hashes file
        data = {normalise_file_path: file_hash}
        self.update_baseline_hashes(data)
        
        #adding to baseline_hashes dictionary for real time consistency
        self.baseline_hashes[normalise_file_path] = file_hash
        
        #adding to files_to_check to keep track of what files to check
        self.files_to_check.add(normalise_file_path)

    def load_baseline(self, file_path):
        # Load from file or database
        self.saved_hash = self.baseline_hashes[file_path]
        return self.saved_hash

    def check_hash(self, file_path):
        saved_hash = self.load_baseline(file_path)
        current_hash = self.compute_file_hash(file_path)
        if current_hash == saved_hash:
            return True
        else:
            return False
        
    def show_hashes(self):
        self.result_text.delete(1.0, tk.END)
        self.result_text.tag_configure("oddRow", background= "white")
        self.result_text.tag_configure("evenRow", background= "lightgrey")
        self.result_text.insert(tk.END, f"{'Files':^{76}} {'Hashes':^{60}}\n")
        self.result_text.insert(tk.END, "-"*154 + "\n")
        row_alternator=0
        for file_path, file_hash in self.baseline_hashes.items():
            if row_alternator == 0:
                self.result_text.insert(tk.END, "{:<76} {:<60}\n".format(file_path, file_hash), "evenRow")
                row_alternator = 1
            else:
                self.result_text.insert(tk.END, "{:<76} {:<60}\n".format(file_path, file_hash), "oddRow")
                row_alternator = 0
        self.result_text.insert(tk.END, "\n\n")
        
    
    #verify_changes function 
    def verify_changes(self):
        #ToDo
        pass
    
        
    def add_folder_to_added_folders(self, folder):
        self.added_folders.add(folder)

    def add_file_to_added_files(self, file):
        self.added_files.add(file)
        
    def normalise_file_path(self, file_path):
        return os.path.normpath(file_path)
         
    def create_baseline_file(self):
        """
        Checks if 'baseline_hashes.txt' exists in the specified directory.
        Creates the file if it doesn't exist.
        """

        #file_path = "C:\Program Files\FIC\baseline\baseline_hashes.txt"
        os.makedirs(os.path.dirname(self.baseline_file_path), exist_ok=True)

        if not os.path.exists(self.baseline_file_path):
            try:
                with open(self.baseline_file_path, 'w') as f:
                    json.dump({}, f)
                print(f"Created empty baseline_hashes.json file at {self.baseline_file_path}")
            except OSError as e:
                print(f"Error creating baseline_hashes.json file: {e}")
        else:
            print(f"baseline_hashes.json file already exists at {self.baseline_file_path}")
            
    
    #update data in baseline_hashes file
    def update_baseline_hashes(self, data):
        """Updates the baseline_hashes file with the given data.

      Args:
          data (dict): The data to update or add to the baseline hashes.
    """
        try:
            with open(self.baseline_file_path, 'r+') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = {}

                existing_data.update(data)
                f.seek(0)
                json.dump(existing_data, f, indent=4)
        except FileNotFoundError:
            print(f"Baseline file not found: {self.baseline_file_path}")
        except OSError as e:
            print(f"Error updating baseline hashes: {e}")


    #function to retrieve data from baseline_hashesh
    def retrieve_data_from_baseline_hashes(self):
        """Retrieves data from the baseline_hashes.json file.

      Args:
          None

      Returns:
          dict: The data from the baseline_hashes.json file.
          """

        try:
            with open(self.baseline_file_path , 'r') as f:
                data = json.load(f)
                return data
        except FileNotFoundError:
            print(f"Baseline file not found: {self.baseline_file_path}")
            return {}
        except json.JSONDecodeError:
            print(f"Error decoding JSON data in {self.baseline_file_path}")
            return {}

    def run(self):
            self.root.mainloop()
# Create the main window
root = tk.Tk()

# Create the application instance
app = FileIntegrityCheckerApp(root)

# Run the application
app.run()
