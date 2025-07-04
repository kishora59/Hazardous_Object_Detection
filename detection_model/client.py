import socket
import pickle
import pyttsx3
import threading
import customtkinter as ctk

tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)
tts_engine.setProperty('volume', 1)

def speak_instruction(instruction):
    tts_engine.say(instruction)
    tts_engine.runAndWait()

server_ip = '127.0.0.1' 
server_port = 12345

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((server_ip, server_port))

ctk.set_appearance_mode("light")  
ctk.set_default_color_theme("blue")  

app = ctk.CTk()
app.geometry("600x700")
app.title("Obstacle Detection Client")

instruction_frame = ctk.CTkFrame(app, fg_color="#ffffff")
instruction_frame.pack(pady=20, padx=20, fill="both", expand=True)

instruction_label = ctk.CTkLabel(
    instruction_frame, 
    text="Recent Instructions", 
    font=("Arial", 24, "bold"),
    text_color="#000000"
)
instruction_label.pack(pady=15)

instruction_listbox = ctk.CTkTextbox(
    instruction_frame, 
    height=350, 
    state="disabled", 
    font=("Arial", 18),
    text_color="#000000", 
    fg_color="#f0f0f0"
)
instruction_listbox.pack(pady=10, padx=10, fill="both", expand=True)

status_label = ctk.CTkLabel(
    app, 
    text="SAFE", 
    font=("Arial", 28, "bold"), 
    text_color="green"
)
status_label.pack(pady=20)

recent_instructions = []
last_instruction = ""

def update_ui(instruction):
    recent_instructions.append(instruction)
    if len(recent_instructions) > 10:
        recent_instructions.pop(0)
    instruction_listbox.configure(state="normal")
    instruction_listbox.delete("1.0", "end")
    for ins in recent_instructions:
        instruction_listbox.insert("end", ins.center(50) + "\n")  
    instruction_listbox.configure(state="disabled")

    harmful_objects = ["knife", "scissors"]
    if any(obj in instruction.lower() for obj in harmful_objects):
        status_label.configure(text="UNSAFE", text_color="red")
    else:
        status_label.configure(text="SAFE", text_color="green")

def receive_data():
    global last_instruction
    while True:
        try:
            data = client_socket.recv(4096)
            if not data:
                break
            try:
                instruction = pickle.loads(data)
            except:
                continue
            if instruction != last_instruction:
                speak_instruction(instruction)
                app.after(0, update_ui, instruction)
                last_instruction = instruction
        except:
            break
    client_socket.close()

threading.Thread(target=receive_data, daemon=True).start()
app.mainloop()
