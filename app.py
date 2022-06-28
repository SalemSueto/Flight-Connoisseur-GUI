from tkinter import Tk, Frame, Entry, DISABLED, NORMAL, Text, Scrollbar, RIGHT, BOTH, filedialog, INSERT, END
from tkmacosx import Button
from tkinter.messagebox import showinfo, showerror
from search import Search

class App(Tk):
    def __init__(self):
        super().__init__()
        self.width, self.height = 700, 330
        self.entry_api = Entry()
        self.btn_search = Button()
        self.btn_input_data = Button()
        self.text_result = Text()
        self.placeholder = "Insert Tequila API Key..."
        self.tequila_api = ""
        self.input_data_path = ""
        self.create_gui()

    def create_gui(self):
        # --- GUI --- #
        self.geometry('{}x{}'.format(self.width, self.height))
        self.resizable(False, False)
        self.title('Flight Connoisseur')

        # -- Frame Input -- #
        frame_input = Frame(self, highlightthickness=0, pady=10)
        frame_input.pack()

        self.entry_api = Entry(frame_input, width=30, bd=5, justify='center')
        self.entry_api.insert(0, self.placeholder)
        self.entry_api.bind('<FocusIn>', self.erase)
        self.entry_api.bind('<FocusOut>', self.add)

        self.btn_input_data = Button(frame_input, text='Input File', width=200, command=self.select_file)
        self.btn_search = Button(frame_input, text='Search', width=100, command=self.search_flight)

        self.entry_api.grid(row=0, column=0, padx=3)
        self.btn_input_data.grid(row=0, column=1, padx=3)
        self.btn_search.grid(row=0, column=2, padx=3)

        # -- Frame Result -- #
        frame_result = Frame(self, width=self.width-100, height=250, highlightthickness=0)
        frame_result.pack_propagate(False)
        frame_result.pack()

        self.text_result = Text(frame_result, width=1, height=1, bg="white", fg="black", state=DISABLED,
                           highlightthickness=0, insertbackground="black")
        self.text_result.pack(fill="both", expand=True, padx=0, pady=0)
        self.text_result.configure(font=('Arial', 14, 'normal'))

        sb = Scrollbar(self.text_result)
        self.text_result.config(yscrollcommand=sb.set)
        sb.configure(command=self.text_result.yview)
        sb.pack(side=RIGHT, fill=BOTH)

    def erase(self, event=None):
        if self.entry_api.get() == self.placeholder:
            self.entry_api.delete(0, 'end')

    def add(self, event=None):
        if self.entry_api.get() == '':
            self.entry_api.insert(0, self.placeholder)

    def select_file(self):
        filetypes = (('text files', '*.txt'), ('CSV files', '*.csv'))
        self.input_data_path = filedialog.askopenfilename(title='Open a file', initialdir='/', filetypes=filetypes)
        if len(self.input_data_path) > 0:
            self.btn_input_data["bg"] = "green"
            self.btn_input_data['text'] = self.input_data_path.rsplit('/', 1)[1]
        else:
            self.btn_input_data["bg"] = "white"
            self.btn_input_data['text'] = 'Input File'

    def search_flight(self):
        self.tequila_api = self.entry_api.get()

        # Check Inputs
        error_message = ""
        if self.tequila_api is self.placeholder:
            error_message = f"{error_message}\nPlease insert the Tequila-API data."
        if len(self.tequila_api) == 0:
            error_message = f"{error_message}\nThe Tequila-API entry is missing."
        if len(self.input_data_path) == 0:
            error_message = f"{error_message}\nThe Input File is missing."

        if len(error_message) > 0:
            showerror(title='Error', message=error_message)
        else:
            new_search = Search(self.tequila_api, self.input_data_path)
            self.text_result.delete(0, 'end')
            self.text_result.configure(state=NORMAL)
            self.text_result.insert(INSERT, "*** Tequila Flight Search Summary ***\n\n")
            self.text_result.insert(END, f"{new_search.result_message}")
            self.text_result.configure(state=DISABLED)

