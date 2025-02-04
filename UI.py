from tkinter import *
from PIL import ImageTk, Image
    
def present_login_screen():
    root = Tk()
    root.title("Login")
    #setting tkinter window size
    root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}")
    
    # Load the image 
    image = ImageTk.PhotoImage(Image.open("nExchange_logo.png"))

    # Create a label to display the image
    image_label = Label(root, image=image, width=450, height=450)
    image_label.image = image  # Keep a reference to avoid garbage collection
    image_label.pack(pady=20)  # Add some padding to the top

    username_label = Label(root, text="Username:")
    username_label.pack()
    
    username_entry = Entry(root, width=100)
    username_entry.pack()
    
    password_label = Label(root, text="Password:")
    password_label.pack()
    
    password_entry = Entry(root, width=100, show="*")
    password_entry.pack()
    
    login_button = Button(root, text="Login")
    login_button.pack()
    
    root.mainloop()

present_login_screen()
