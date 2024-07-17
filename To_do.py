from tkinter import *
from tkinter import ttk
from tkinter import messagebox

class ToDoList:
    def __init__(self, root):
        self.root = root
        self.root.title("To-Do-List")
        self.tasks = []
        self.label = Label(self.root, text= 'To-Do-List-App',
                            font='ariel, 25 bold', width= 10, bd=5, bg='blue', fg= 'yellow')
        self.label.pack(side='top', fill="both")

        self.frame_tasks = Frame(self.root)
        self.frame_tasks.pack(fill="both", expand=True)

        self.frame_add_task = Frame(self.root)
        self.frame_add_task.pack(fill="x")

        self.task_list = Listbox(self.frame_tasks, width=50)
        self.task_list.pack(fill="both", expand=True)

        self.task_entry = Entry(self.frame_add_task, width=30)
        self.task_entry.pack(side="left")

        self.priority_label = Label(self.frame_add_task, text="Priority:")
        self.priority_label.pack(side="left")
        self.priority_entry = Entry(self.frame_add_task, width=5)
        self.priority_entry.pack(side="left")

        self.due_date_label =Label(self.frame_add_task, text="Due Date:")
        self.due_date_label.pack(side="left")
        self.due_date_entry =Entry(self.frame_add_task, width=10)
        self.due_date_entry.pack(side="left")

        self.add_task_button = Button(self.frame_add_task, text="Add Task", command=self.add_task)
        self.add_task_button.pack(side="left")

        self.remove_task_button = Button(self.frame_add_task, text="Remove Task", command=self.remove_task)
        self.remove_task_button.pack(side="left")

        self.mark_as_done_button =Button(self.frame_add_task, text="Mark as Done", command=self.mark_as_done)
        self.mark_as_done_button.pack(side="left")

    def add_task(self):
        task = self.task_entry.get()
        priority = self.priority_entry.get()
        due_date = self.due_date_entry.get()
        if task:
            self.tasks.append({"task": task, "priority": priority, "due_date": due_date, "done": False})
            self.task_list.insert("end", task)
            self.task_entry.delete(0, "end")
            self.priority_entry.delete(0, "end")
            self.due_date_entry.delete(0, "end")

    def remove_task(self):
        try:
            task_index = self.task_list.curselection()[0]
            self.task_list.delete(task_index)
            self.tasks.pop(task_index)
        except:
            messagebox.showerror("Error", "Select a valid task to remove !")

    def mark_as_done(self):
        try:
            task_index = self.task_list.curselection()[0]
            self.tasks[task_index]["done"] = True
            self.task_list.delete(task_index)
            self.task_list.insert(task_index, self.tasks[task_index]["task"] + " (Done)")
        except:
            messagebox.showerror("Error", "Select a proper task to be marked as done !")

if __name__ == "__main__":
    root = Tk()
    app = ToDoList(root)
    root.mainloop()