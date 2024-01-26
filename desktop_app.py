import datetime
import os
import re
import tkinter as tk
from tkinter import messagebox, ttk

import mylib

spendings = []
data_folder = 'data/'
os.makedirs(data_folder, exist_ok=True)
data_path = os.path.join(data_folder, 'budget.csv')


def restore_placeholders():
    spending_name_entry_focus_out(event=None)
    spending_source_focus_out(event=None)
    spending_cost_entry_focus_out(event=None)
    spending_day_entry_focus_out(event=None)
    spending_month_entry_focus_out(event=None)
    spending_hour_entry_focus_out(event=None)
    spending_minute_entry_focus_out(event=None)


def validate_name():
    if spending_name_entry.get() == " Enter the name of the purchase.":
        return False
    return True


def validate_source():
    if spending_source_combobox.get() == " Choose the source.":
        return False
    return True


def validate_cost():
    if spending_cost_entry.get() == " Enter the cost.":
        return False
    return True


def get_date_time():
    day_data = spending_day_entry.get()
    month_data = spending_month_entry.get()
    year_data = datetime.datetime.now().year
    hour_data = spending_hour_entry.get()
    minute_data = spending_minute_entry.get()
    if day_data == "DD":
        day_data = datetime.datetime.now().day
    if month_data == "MM":
        month_data = datetime.datetime.now().month
    if hour_data == "hh":
        hour_data = datetime.datetime.now().hour
    if minute_data == "mm":
        minute_data = datetime.datetime.now().minute

    return f'{year_data}-{month_data}-{day_data} {hour_data}:{minute_data}:00'


def clear_data(event=None, confirm=True):
    global spendings
    global added_objects_counter
    if confirm:
        user_response = messagebox.askyesno(
            title="Clear all",
            message="All fields and data will be cleared."
        )
        spendings.clear()
        added_objects_counter = len(spendings)
        add_data_button_text.set("Add Data")
        write_data_button_text.set("Save Data")
        if not user_response:
            return

    spending_name_entry.delete(0, "end")
    spending_source_combobox.delete(0, "end")
    spending_cost_entry.delete(0, "end")
    spending_day_entry.delete(0, "end")
    spending_month_entry.delete(0, "end")
    spending_hour_entry.delete(0, "end")
    spending_minute_entry.delete(0, "end")
    restore_placeholders()
    if confirm:
        clear_data_button.flash()
        clear_data_button.flash()
    root.focus_set()


def add_data(event=None):
    global added_objects_counter
    name = spending_name_entry.get()
    source = spending_source_combobox.get()
    cost = re.sub(r'(\d+),(\d+)', r'\1.\2', spending_cost_entry.get())
    # cost = spending_cost_entry.get()
    if all(
        [
            validate_name(),
            validate_source(),
            validate_cost(),
        ]
    ):
        date_time_string = get_date_time()
        q_list = [name, source, cost]
        try:
            mylib.Spending.validate(q_list)
            spending = mylib.Spending.create_with_date(
                q_list, sp_date=date_time_string)
            spendings.append(spending)
            clear_data(confirm=False)
            added_objects_counter = len(spendings)
            add_data_button_text.set(f"Add Data ({added_objects_counter})")
            write_data_button_text.set(f"Save Data ({added_objects_counter})")
            add_data_button.flash()
            add_data_button.flash()

        except Exception as err:
            messagebox.showerror("Error", err)
    else:
        messagebox.showerror("Error", "Fill in all required fields")


def save_data():
    global added_objects_counter
    message = ""
    if not all(
        [
            validate_name(),
            validate_source(),
            validate_cost(),
        ]
    ):
        if not spendings:
            messagebox.showerror("Error", "No data to save!")
            return
    else:
        add_data()
    try:
        for spending in spendings:
            mylib.CsvDatabase(spending, "Desktop").add_data(data_path)
            message += f"{spending}\n\n"
        messagebox.showinfo("Success", message)
        spendings.clear()
        added_objects_counter = len(spendings)
        add_data_button_text.set("Add Data")
        write_data_button_text.set("Save Data")
    except Exception as err:
        messagebox.showerror("Error", err)


def spending_name_entry_focus_in(event):
    if spending_name_entry.get() == " Enter the name of the purchase.":
        spending_name_entry.delete(0, "end")
        spending_name_entry.configure(fg="black")


def spending_name_entry_focus_out(event):
    if not spending_name_entry.get():
        spending_name_entry.insert(0, " Enter the name of the purchase.")
        # Измените цвет текста на серый
        spending_name_entry.configure(fg="gray")


def spending_source_focus_in(event):
    if spending_source_combobox.get() == " Choose the source.":
        spending_source_combobox.delete(0, "end")
        spending_source_combobox.configure(foreground="black")


def spending_source_focus_out(event):
    source = spending_source_combobox.get()
    if source not in spending_sources:
        spending_source_combobox.delete(0, "end")
    if not spending_source_combobox.get():
        spending_source_combobox.insert(0, " Choose the source.")
        spending_source_combobox.configure(foreground="gray")


def spending_source_select(event):
    selected_source = spending_source_combobox.get()
    # Обновляем строку или переменную, куда будет сохранен выбранный источник
    selected_source_variable.set(selected_source)


def spending_cost_entry_focus_in(event):
    if spending_cost_entry.get() == " Enter the cost.":
        spending_cost_entry.delete(0, "end")
        spending_cost_entry.configure(fg="black")


def spending_cost_entry_focus_out(event):
    pattern = r"^[0-9.,]+$"
    text = spending_cost_entry.get()
    if not re.match(pattern, text):
        spending_cost_entry.delete(0, "end")
    if not spending_cost_entry.get():
        spending_cost_entry.insert(0, " Enter the cost.")
        spending_cost_entry.configure(fg="gray")


def spending_day_entry_focus_in(event):
    if spending_day_entry.get() == "DD":
        spending_day_entry.delete(0, "end")
        spending_day_entry.configure(fg="black")


def spending_day_entry_focus_out(event):
    day = spending_day_entry.get()
    pattern = r"^[0-9]{1,2}$"
    if not re.match(pattern, day):
        spending_day_entry.delete(0, "end")
    elif int(day) < 1 or int(day) > 31:
        spending_day_entry.delete(0, "end")
    if not spending_day_entry.get():
        spending_day_entry.insert(0, "DD")
        spending_day_entry.configure(fg="gray")


def spending_month_entry_focus_in(event):
    if spending_month_entry.get() == "MM":
        spending_month_entry.delete(0, "end")
        spending_month_entry.configure(fg="black")


def spending_month_entry_focus_out(event):
    month = spending_month_entry.get()
    pattern = r"^[0-9]{1,2}$"
    if not re.match(pattern, month):
        spending_month_entry.delete(0, "end")
    elif int(month) < 1 or int(month) > 12:
        spending_month_entry.delete(0, "end")
    if not spending_month_entry.get():
        spending_month_entry.insert(0, "MM")
        spending_month_entry.configure(fg="gray")


def spending_hour_entry_focus_in(event):
    if spending_hour_entry.get() == "hh":
        spending_hour_entry.delete(0, "end")
        spending_hour_entry.configure(fg="black")


def spending_hour_entry_focus_out(event):
    hour = spending_hour_entry.get()
    pattern = r"^[0-9]{1,2}$"
    if not re.match(pattern, hour):
        spending_hour_entry.delete(0, "end")
    elif int(hour) < 0 or int(hour) > 23:
        spending_hour_entry.delete(0, "end")
    if not spending_hour_entry.get():
        spending_hour_entry.insert(0, "hh")
        spending_hour_entry.configure(fg="gray")


def spending_minute_entry_focus_in(event):
    if spending_minute_entry.get() == "mm":
        spending_minute_entry.delete(0, "end")
        spending_minute_entry.configure(fg="black")


def spending_minute_entry_focus_out(event):
    minute = spending_minute_entry.get()
    pattern = r"^[0-9]{1,2}$"
    if not re.match(pattern, minute):
        spending_minute_entry.delete(0, "end")
    elif int(minute) < 0 or int(minute) > 59:
        spending_minute_entry.delete(0, "end")
    if not spending_minute_entry.get():
        spending_minute_entry.insert(0, "mm")
        spending_minute_entry.configure(fg="gray")


def mouseover(event):
    if event.widget == clear_data_button:
        clear_data_button['bg'] = '#f2f5f5'
        clear_data_button['fg'] = '#7a1c10'
    elif event.widget == add_data_button:
        add_data_button['bg'] = '#f2f5f5'
        add_data_button['fg'] = '#f59c0c'
    elif event.widget == write_data_button:
        write_data_button['bg'] = '#f2f5f5'
        write_data_button['fg'] = '#14591d'


def mouseout(event):
    if event.widget == clear_data_button:
        clear_data_button['bg'] = '#757474'
        clear_data_button['fg'] = '#ffffff'
    elif event.widget == add_data_button:
        add_data_button['bg'] = '#757474'
        add_data_button['fg'] = '#ffffff'
    elif event.widget == write_data_button:
        write_data_button['bg'] = '#757474'
        write_data_button['fg'] = '#ffffff'


def quit_app(event=None):
    if messagebox.askyesno("", "Are you sure you want to quit the App?"):
        root.destroy()


def help_window():
    messagebox.showinfo("Help", "Home budgeting app\nMy simple budget. V.1")


def about_app():
    messagebox.showinfo("App", "Home budgeting app\nMy simple budget. V.1")


# Creating the main window
root = tk.Tk()
root.title("My simple budget. V.1")
root.geometry("700x485")
root.resizable(width=False, height=False)
# root.minsize(width=700, height=485)
# root.maxsize(width=700, height=485)
root.protocol("WM_DELETE_WINDOW", quit_app)

# Creating menu bar
main_menu = tk.Menu(root)
root.config(menu=main_menu)
sub_menu_file = tk.Menu(main_menu, tearoff=0)
main_menu.add_cascade(label="File", menu=sub_menu_file, underline=0)
sub_menu_file.add_separator()
sub_menu_file.add_command(
    label="Quit", accelerator="Ctrl-Q", underline=0, command=quit_app)
main_menu.add_command(label="Help", command=help_window, underline=0)
main_menu.add_command(label="About...", command=about_app, underline=0)


# Spending Name Frame
spending_name_frame = tk.Frame(
    root, relief=tk.GROOVE, borderwidth=3)
spending_name_frame.place(x=2, y=5, width=697, height=120)

# Spending Name Label
spending_name_label = tk.Label(
    spending_name_frame,
    text="Spending Name: *",
    font=("Arial", "12", "bold"),
    anchor="w"
)
spending_name_label.place(x=5, y=5)

# Spending Name Entry
spending_name_entry = tk.Entry(spending_name_frame, fg="gray")
spending_name_entry.insert(0, " Enter the name of the purchase.")
spending_name_entry.bind("<FocusIn>", spending_name_entry_focus_in)
spending_name_entry.bind("<FocusOut>", spending_name_entry_focus_out)
spending_name_entry.place(x=180, y=5, width=502, height=25)

# Separator
separator = ttk.Separator(spending_name_frame, orient="horizontal")
separator.place(x=5, y=35, width=677, height=2)

# Spending Name Description Label
spending_name_description_label = tk.Label(
    spending_name_frame,
    text="""Enter the name of the purchase.
Example: milk.
If purchase contains several items, do not use a comma.
Example: milk bread fruit""",
    font=("Arial", "10", "italic")
)
spending_name_description_label.place(x=5, y=40)
spending_name_description_label.config(justify="left")

# Spending Source Frame
spending_source_frame = tk.Frame(
    root, relief=tk.GROOVE, borderwidth=3)
spending_source_frame.place(x=2, y=125, width=697, height=90)

# Spending Source Label
spending_source_label = tk.Label(
    spending_source_frame,
    text="Spending Source: *",
    font=("Arial", "12", "bold"),
    anchor="w"
)
spending_source_label.place(x=5, y=5)

# Spending Source Combobox
spending_sources = ["Card", "Cash", "Check"]
selected_source_variable = tk.StringVar()
spending_source_combobox = ttk.Combobox(
    spending_source_frame,
    values=spending_sources,
    foreground="gray"
)
spending_source_combobox.insert(0, " Choose the source.")
spending_source_combobox.bind(
    "<<ComboboxSelected>>", spending_source_select)
spending_source_combobox.bind(
    "<FocusIn>", spending_source_focus_in)
spending_source_combobox.bind(
    "<FocusOut>", spending_source_focus_out)
spending_source_combobox.place(x=180, y=5, width=502, height=25)

# Separator
separator = ttk.Separator(spending_source_frame, orient="horizontal")
separator.place(x=5, y=35, width=677, height=2)

# Spending Source Description Label
spending_source_description_lable = tk.Label(
    spending_source_frame,
    text="Select an appropriate source of funds from the dropdown list.",
    font=("Arial", "10", "italic")
)
spending_source_description_lable.place(x=5, y=40)
spending_source_description_lable.config(justify="left")

# Spending Cost Frame
spending_cost_frame = tk.Frame(
    root, relief=tk.GROOVE, borderwidth=3)
spending_cost_frame.place(x=2, y=215, width=697, height=90)

# Spending Cost Label
spending_cost_label = tk.Label(
    spending_cost_frame,
    text="Spending Cost: *",
    font=("Arial", "12", "bold"),
    anchor="w"
)
spending_cost_label.place(x=5, y=5)

# Spending Cost Entry
spending_cost_entry = tk.Entry(spending_cost_frame, fg="gray")
spending_cost_entry.insert(0, " Enter the cost.")
spending_cost_entry.bind("<FocusIn>", spending_cost_entry_focus_in)
spending_cost_entry.bind("<FocusOut>", spending_cost_entry_focus_out)
spending_cost_entry.place(x=180, y=5, width=502, height=25)

# Separator
separator = ttk.Separator(spending_cost_frame, orient="horizontal")
separator.place(x=5, y=35, width=677, height=2)

# Spending Cost Description Label
spending_cost_description_lable = tk.Label(
    spending_cost_frame,
    text="""Enter the cost of the purchase.
Evalable input: digits and decimal points.""",
    font=("Arial", "10", "italic")
)
spending_cost_description_lable.place(x=5, y=40)
spending_cost_description_lable.config(justify="left")


# Date and time frame
date_time_frame = tk.Frame(
    root, relief=tk.GROOVE, borderwidth=3)
date_time_frame.place(x=2, y=305, width=697, height=85)

# Date label
date_label = tk.Label(
    date_time_frame,
    text="Spending Date:  ",
    font=("Arial", "12", "bold"),
    anchor="w")
date_label.place(x=5, y=5)

# Date entries
spending_day_entry = tk.Entry(date_time_frame, fg="gray")
spending_day_entry.insert(0, "DD")
spending_day_entry.bind("<FocusIn>", spending_day_entry_focus_in)
spending_day_entry.bind("<FocusOut>", spending_day_entry_focus_out)

spending_month_entry = tk.Entry(date_time_frame, fg="gray")
spending_month_entry.insert(0, "MM")
spending_month_entry.bind("<FocusIn>", spending_month_entry_focus_in)
spending_month_entry.bind("<FocusOut>", spending_month_entry_focus_out)

spending_day_entry.place(x=180, y=5, width=25, height=25)
tk.Label(date_time_frame, text='/').place(x=210, y=5, width=5, height=25)
spending_month_entry.place(x=220, y=5, width=25, height=25)

# Time label
time_label = tk.Label(
    date_time_frame,
    text="Spending Time: ",
    font=("Arial", "12", "bold"),
    anchor="w")
time_label.place(x=5, y=45)

# Time entries
spending_hour_entry = tk.Entry(date_time_frame, fg="gray")
spending_hour_entry.insert(0, "hh")
spending_hour_entry.bind("<FocusIn>", spending_hour_entry_focus_in)
spending_hour_entry.bind("<FocusOut>", spending_hour_entry_focus_out)

spending_minute_entry = tk.Entry(date_time_frame, fg="gray")
spending_minute_entry.insert(0, "mm")
spending_minute_entry.bind("<FocusIn>", spending_minute_entry_focus_in)
spending_minute_entry.bind("<FocusOut>", spending_minute_entry_focus_out)

spending_hour_entry.place(x=180, y=45, width=25, height=25)
tk.Label(date_time_frame, text=':').place(x=210, y=45, width=5, height=25)
spending_minute_entry.place(x=220, y=45, width=25, height=25)

# Separator
separator = ttk.Separator(date_time_frame, orient="vertical")
separator.place(x=300, y=5, width=2, height=75)

# Date and time description label
date_time_description_label = tk.Label(
    date_time_frame,
    text="""In the case that any field related to date and time is left
empty or partially filled, it will be automatically populated
with the current month, day, hour, or minute, respectively.""",
    font=("Arial",
          "10", "italic")
)
date_time_description_label.place(x=310, y=10)
date_time_description_label.config(justify="left")

# Buttons frame
buttons_frame = tk.Frame(
    root, relief=tk.GROOVE, borderwidth=3)
buttons_frame.place(x=2, y=420, width=697, height=52)

# Buttons
clear_data_button = tk.Button(
    buttons_frame,
    text="Clear All",
    font=("Arial", "12", "bold"),
    bg='#757474',
    activebackground='#7a1c10',
    fg='#ffffff',
    activeforeground='#ffffff',
    command=clear_data)
clear_data_button.place(x=5, y=5, width=222, height=35)
clear_data_button.bind("<Enter>", mouseover)
clear_data_button.bind("<Leave>", mouseout)


added_objects_counter = len(spendings)
add_data_button_text = tk.StringVar()
add_data_button_text.set("Add Data")
add_data_button = tk.Button(
    buttons_frame,
    textvariable=add_data_button_text,
    font=("Arial", "12", "bold"),
    bg='#757474',
    activebackground='#f59c0c',
    fg='#ffffff',
    activeforeground='#ffffff',
    command=add_data)
add_data_button.place(x=234, y=5, width=222, height=35)
add_data_button.bind("<Enter>", mouseover)
add_data_button.bind("<Leave>", mouseout)

write_data_button_text = tk.StringVar()
write_data_button_text.set("Save Data")
write_data_button = tk.Button(
    buttons_frame,
    textvariable=write_data_button_text,
    font=("Arial", "12", "bold"),
    bg='#757474',
    activebackground='#14591d',
    fg='#ffffff',
    activeforeground='#ffffff',
    command=save_data)
write_data_button.place(x=464, y=5, width=222, height=35)
write_data_button.bind("<Enter>", mouseover)
write_data_button.bind("<Leave>", mouseout)

root.bind_all("<Control-q>", quit_app)
root.mainloop()
