import hashlib
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import os
import json


class FileIntegrityCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IntegriSecure")
                
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
        self.check_button.grid(row=0, column=9, pady=10, columnspan= 2, rowspan= 2)

        #show hash button
        self.show_hash_button = tk.Button(self.root, text = "Show Hashes", command = self.show_hashes)
        self.show_hash_button.grid(row=0, column=0, pady=10, padx=0)
        
        #verify button
        self.show_hash_button = tk.Button(self.root, text = "Verify Changes", command = self.verify_changes)
        self.show_hash_button.grid(row=0, column=1, pady=10)

        
        #result space
        self.result_text = tk.Text(self.root, height=40, width=160)
        self.result_text.grid(row=2, column=0, columnspan=20, rowspan= 10, padx=10, pady=10)
        self.result_text.insert(tk.END, "-"*160 + "\n")
        self.result_text.insert(tk.END, f"{'IntegriSecure':^{162}}\n")
        self.result_text.insert(tk.END, "-"*160 + "\n")
    
    def get_files_to_check(self):
        return self.files_to_check
        
        
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
        self.result_text.tag_configure("removed", foreground= "grey")
        self.result_text.tag_configure("renamed", foreground= "yellow")
        self.result_text.tag_configure("not_changed", foreground= "green")
        
        #sorting files according to their integrity
        changed = list()
        removed = list()
        renamed = list()
        not_changed = list()
        
        #clearing the older outputs
        self.result_text.delete(1.0, tk.END)
        
        if not self.files_to_check:
            tk.messagebox.showwarning("No Files Selected", "Please add files or folders first.")
            return
        
        self.result_text.insert(tk.END, "-"*160 + "\n")
        self.result_text.insert(tk.END, f"{'INTEGRITY CHECK':^{162}}\n")
        self.result_text.insert(tk.END, "-"*160 + "\n")
        
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
                   
        self.result_text.insert(tk.END, "-"*158 + "\n")    
        self.result_text.insert(tk.END, f"{'Integrity Check Completed':^162}\n")
  
    def select_items_from_lists(self, titles_and_elements):
        selected_items = []

        def submit():
            selected_items.clear()
            for i, (title, check_vars) in enumerate(check_vars_list):
                selected_list = []
                for j, var in enumerate(check_vars):
                    if var.get():
                        selected_list.append(titles_and_elements[i][1][j])  # Append selected items from the list
                selected_items.append((title, selected_list))  # Append the title and the selected items
            #messagebox.showinfo("Selected Items", f"Selected items: {selected_items}")
            
            #updating baseline hash
            for title, items in selected_items:
                if title == "changed":
                    for item in items:
                        new_hash = self.compute_file_hash(item)
                        self.update_baseline_hashes('change', item, new_hash=new_hash)
                elif title == "removed":
                    for item in items:
                        self.update_baseline_hashes('remove', item)
            
            self.display_selected_items(selected_items)  # Display selected items
            selection_window.destroy()  # Close the selection window

        def toggle_select_all(check_vars, select_all_var):
            """Toggle all checkboxes when 'Select All' is checked or unchecked."""
            select_all_checked = select_all_var.get()
            for var in check_vars:
                var.set(select_all_checked)

        # Create a new window for selection
        selection_window = tk.Toplevel(self.root)
        selection_window.title("Select Items")

        # List to store check_vars for each list of elements
        check_vars_list = []

        # Loop through each title and its corresponding list of elements
        for title, elements in titles_and_elements:
            # Title Label for each list
            tk.Label(selection_window, text=title, font=("Arial", 14)).pack(pady=10)

            # Frame for each set of checkboxes
            frame = tk.Frame(selection_window)
            frame.pack(padx=20, pady=10)

            # Create a list to hold IntVar objects for each checkbox
            check_vars = []

            # Add a "Select All" checkbox for each list
            select_all_var = tk.IntVar()
            select_all_checkbox = tk.Checkbutton(frame, text="Select All", variable=select_all_var, 
                                                 command=lambda v=check_vars, sv=select_all_var: toggle_select_all(v, sv))
            select_all_checkbox.pack(anchor="w")

            # Dynamically create a checkbox for each element in the list
            for element in elements:
                var = tk.IntVar()
                checkbox = tk.Checkbutton(frame, text=element, variable=var)
                checkbox.pack(anchor="w")
                check_vars.append(var)

            # Append check_vars for the current list to the main check_vars_list
            check_vars_list.append((title, check_vars))

        # Submit button
        submit_button = tk.Button(selection_window, text="Submit", command=submit)
        submit_button.pack(pady=10)
        
    def display_selected_items(self, selected_items):
        """Display the selected items in the result text area."""
        self.result_text.delete(1.0, tk.END)  # Clear previous results
        self.result_text.insert(tk.END, "-" * 160 + "\n")
        self.result_text.insert(tk.END, f"{'Selected Items':^{162}}\n")
        self.result_text.insert(tk.END, "-" * 160 + "\n")

        for title, items in selected_items:
            self.result_text.insert(tk.END, f"{title}: {', '.join(items)}\n")
            self.result_text.insert(tk.END, "-" * 160 + "\n")
    

    def verify_changes(self):
        """Method to handle the Verify Changes button click."""
        
        #sorting files according to their integrity
        changed = list()
        removed = list()
        not_changed = list()
        
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
                            
        # Example data for verification (can be replaced with actual logic)
        titles_and_elements = list()
        if changed:
            titles_and_elements.append(('changed', changed))
        if removed:
            titles_and_elements.append(('removed', removed))
        
        if titles_and_elements:
            self.select_items_from_lists(titles_and_elements)
        else:
            messagebox.showinfo("Nothing to Verify", "There is no file change to verify.")
        
    #compute hash and add file to baseline_hashes
    def save_baseline(self, file_path):
        file_hash = self.compute_file_hash(file_path)
        
        #normalisig file path to have consistency in file path formats
        normalise_file_path = self.normalise_file_path(file_path)
        
        #creating dictionary to add in baseline_hashes file
        data = {normalise_file_path: file_hash}
        self.append_to_baseline_hashes(data)
                
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
    def append_to_baseline_hashes(self, data):
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

    def update_baseline_hashes(self, operation, file_name, new_name=None, new_hash=None):
        """
        Update the baseline_hashes.json file.
    
        Args:
            operation (str): The operation to perform ('remove', 'rename', 'change').
            file_name (str): The name of the file to update.
            new_name (str, optional): The new name for the file if renaming.
            new_hash (str, optional): The new hash value for the file if changing the hash.
    
        Raises:
            ValueError: If an invalid operation is provided.
        """
        try:
            with open(self.baseline_file_path, 'r+') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = {}
    
                if operation == 'remove':
                    if file_name in existing_data:
                        del existing_data[file_name]
                        
                        #remove file name from files_to_check list
                        self.files_to_check.remove(file_name)
                        print(f"Deleted {file_name} from baseline hashes.")
                    else:
                        print(f"{file_name} not found in baseline hashes.")
                
                elif operation == 'rename':
                    if file_name in existing_data:
                        if new_name is not None:
                            existing_data[new_name] = existing_data.pop(file_name)
                            print(f"Renamed {file_name} to {new_name}.")
                        else:
                            print("New name must be provided for renaming.")
                    else:
                        print(f"{file_name} not found in baseline hashes.")
                
                elif operation == 'change':
                    if file_name in existing_data:
                        if new_hash is not None:
                            existing_data[file_name] = new_hash
                            
                            #update baseline_hash list too
                            self.baseline_hashes[file_name] = new_hash
                            print(f"Changed hash for {file_name}.")
                        else:
                            print("New hash value must be provided for changing hash.")
                    else:
                        print(f"{file_name} not found in baseline hashes.")
                
                else:
                    raise ValueError("Invalid operation. Use 'delete', 'rename', or 'change'.")
    
                f.seek(0)
                json.dump(existing_data, f, indent=4)
                f.truncate()  # Ensure the file size is updated
    
        except FileNotFoundError:
            print(f"Baseline file not found: {self.baseline_file_path}")
        except OSError as e:
            print(f"Error updating baseline hashes: {e}")


    def run(self):
            self.root.mainloop()
# Create the main window
root = tk.Tk()

# Create the application instance
app = FileIntegrityCheckerApp(root)

# Run the application
app.run()
