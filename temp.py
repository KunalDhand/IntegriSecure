import tkinter as tk

def select_all(group, var, checkboxes):
    state = var.get()
    for checkbox in checkboxes:
        checkbox_var, checkbox_widget = checkbox
        checkbox_var.set(state)

def create_group(parent, label, options):
    frame = tk.Frame(parent)
    frame.pack(padx=10, pady=5, anchor="w")

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

root = tk.Tk()
root.title("Checkbox Groups with Select All")

# Create three groups of checkboxes
group1 = create_group(root, "Group 1", ["Option 1", "Option 2", "Option 3"])
group2 = create_group(root, "Group 2", ["Option 4", "Option 5", "Option 6"])
group3 = create_group(root, "Group 3", ["Option 7", "Option 8", "Option 9"])

root.mainloop()
