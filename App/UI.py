from tkinter import *
from tkinter import messagebox
import customtkinter as ctk
import textwrap
from datetime import datetime
import requests
import json
import threading
import subprocess
import sys
import pyperclip
from PIL import Image
import ctypes

scaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100

Messages: list[ctk.CTkFrame] = []
DefaultHeight = 50
ErrorLabel = None

def LoadSettings() -> dict:
    with open(".\\App\\Application Data\\Settings\\settings.json", "r", encoding='utf-8') as SettingsF:
        return json.load(SettingsF)

GlobalSettings = LoadSettings()
Settings = GlobalSettings.get("Settings")

UserTheme = Settings.get("Theme")

Theme = Settings.get("ThemeList").get(UserTheme)

FirstColor   = Theme.get("First")
SecondColor  = Theme.get("Second")

BorderColor  = Theme.get("Border")
LoadingColor = Theme.get("Loading")

UsersColors = Theme.get("User")

UserMsgColor = UsersColors.get("Msg")
UserTextColor = UsersColors.get("TextColor")

AIColors = Theme.get("AI")

AIMsgColor = AIColors.get("Msg")
AITextColor = AIColors.get("TextColor")

ButtonColors = Theme.get("Button")

ButtonColor = ButtonColors.get("Color")
ButtonHover = ButtonColors.get("Hover")

WindowTheme = Theme.get("Mode")

ctk.set_appearance_mode(WindowTheme)

def Restart() -> None:
    subprocess.Popen(".\\App\\Restart.bat", creationflags=subprocess.CREATE_NO_WINDOW)
    sys.exit()

def LoadImg(Path: str, Size: tuple[int, int]) -> ctk.CTkImage:
    return ctk.CTkImage(Image.open(Path), size=Size)

def ClearConv() -> None:    
    global Messages

    if len(Messages) > 0:
        if messagebox.askyesno("Supression de la conversation", "Êtes(vous sûr de vouloir suprimmer la conversation ? Cette action est définitive et videras également la mémoire de l'IA."):
            with open(".\\App\\Application Data\\Messages\\messages.json", "w", encoding='utf-8') as ConvJSON:
                ConvJSON.write("[]")

            DeletingFrame = ctk.CTkFrame(Window, height=600, width=1000, fg_color=FirstColor, corner_radius=1)
            DeletingFrame.place(y=0, x=0)

            DeletingLabel = ctk.CTkLabel(DeletingFrame, text="Supression de la conversation", font=("Arial", 35, "bold"))
            DeletingLabel.place(y=200 / scaleFactor, relx=0.5, anchor='center')

            Deleted = ctk.DoubleVar(value=0.0)
            Total = len(Messages)
            DeletedCount = 0

            DeletedProgress = ctk.CTkProgressBar(DeletingFrame, width=450, height=5, fg_color="#545454", progress_color=LoadingColor, variable=Deleted)
            DeletedProgress.place(y=280 / scaleFactor, relx=0.5, anchor='center')

            DeletedCountLabel = ctk.CTkLabel(DeletingFrame, text=f"{DeletedCount}/{Total}", font=("Arial", 15))
            DeletedCountLabel.place(y=305 / scaleFactor)

            for MsgFrame in Messages:
                MsgFrame.destroy()
                Deleted.set(Deleted.get() + 1 / Total)
                DeletedCount += 1
                DeletedCountLabel.configure(text=f"{DeletedCount}/{Total}")
                DeletedCountLabel.place(y=305 / scaleFactor, relx=0.5, anchor='center')

            Window.after(1000, Restart)
    else:
        messagebox.showinfo("Supresssion de la conversation", "Vous n'avez aucun message dans la conversation")

def UpdateSettings() -> None:
    global GlobalSettings

    with open(".\\App\\Application Data\\Settings\\settings.json", "w", encoding='utf-8') as F:
        json.dump(GlobalSettings, F, indent=2, ensure_ascii=False)
    
    Restart()

def GetTime() -> str:
    return datetime.now().strftime("Le %d/%m/%Y à %H:%M")

def SaveMsg(Text: str, _from: str, Date: str) -> None:
    with open(".\\App\\Application Data\\Messages\\messages.json", "r", encoding='utf-8') as CurrentConvJSON:
        CompleteConv = json.load(CurrentConvJSON)
        CompleteConv.append({
            "text": Text,
            "from": _from,
            "date": Date
        })

    with open(".\\App\\Application Data\\Messages\\messages.json", "w", encoding='utf-8') as UpdatedConvJSON:
        json.dump(CompleteConv, UpdatedConvJSON, ensure_ascii=False, indent=2)

def GetResponse(Payload: dict) -> str:
    response = requests.post("https://api.deepinfra.com/v1/openai/chat/completions", json=Payload, stream=True)

    full_text = ""
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode("utf-8")
            if decoded_line.startswith("data: "):
                data_str = decoded_line[len("data: "):]
                if data_str == "[DONE]":
                    break
                chunk = json.loads(data_str)

                delta = chunk["choices"][0]["delta"]
                if "content" in delta:
                    full_text += delta["content"]
    PlaceMessage(None, "AI", full_text)

    AskEntry.configure(state="normal")
    SendButton.configure(state="normal")


def PlaceMessage(event=None, _from: str = "User", Text: str = "", PlaceOnly: bool = False, Date: str = None, FromLoading: bool = False) -> None:
    global ErrorLabel

    Time = GetTime()

    if _from == "User":
        Anchor = "e"
        Color = UserMsgColor
        TextColor = UserTextColor

        if not PlaceOnly:
            Message = AskEntry.get()

            Payload = {
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-Turbo",
            "messages": [
                { "role": "system", "content": f"Be a helpful assistant. Always answer in french excpet if it is precised by the author. Do not use markdown in your answers (like *, **, -, `, ```...), even for the programs/codes. Use a friendly language and sum up your answers. To respond, you will always assume that the context of your discussion is this json of messages  (directly connects with the following part, usethe dates precised if you need to, and if the json is empty, then answer like if it was the first time you talks to the author, no context): {LoadMessages()}" },
                { "role": "user", "content": Message }
            ],
            "stream": True,
            "stream_options": { "include_usage": True, "continuous_usage_stats": True }
            }

            if not Message.strip():
                AskEntry.configure(border_color="red")
                return
            elif len(Message) > 1000:
                AskEntry.configure(border_color="red")
                error_label = ctk.CTkLabel(Window, text=f"Le message ne doit pas dépasser 1000 caractères ({len(Message) - 1000} en trop)", text_color="red", font=("Arial", 12))
                error_label.place(y=570 / scaleFactor, x=12.5 / scaleFactor)
                ErrorLabel = error_label
                return
            
            if not FromLoading:
                SaveMsg(Message, _from, Time)

        else:
            Message = Text
            Time = Date
    else:
        Message = Text.replace("```", "\n").replace("`", "").replace("**", "").replace("##", "")

        if not Message:
            Message = "<error>Une erreur est survenue. Si cette erreur se reproduis fréquemment, c'est que votre ip a été black listée par l'api car à l'origine elle est payantes ! L'utilisation d'un VPN tel que ProtonVPN ou UrbanVPN (Gratuis) peut régler ce problème."

        if not FromLoading:
            SaveMsg(Message, _from, Time)    

        Anchor = "w"
        Color = AIMsgColor
        TextColor = AITextColor
    
    AskEntry.delete(0, END)

    wrapped_lines = []

    for line in Message.splitlines():
        wrapped_lines.extend(textwrap.wrap(line, width=100, break_long_words=True) or [""])  

    height = len(wrapped_lines) * 20 + DefaultHeight

    MessageFrame = ctk.CTkFrame(MainFrame, height=height, fg_color=Color if not "\n".join(wrapped_lines).startswith("<error>") else "red", corner_radius=3, width=800)
    MessageFrame.pack(pady=5, padx=10, anchor=Anchor) 

    if _from != "User":
        Copy = ctk.CTkButton(MessageFrame, height=18, width=18, fg_color=AIMsgColor, hover_color=SecondColor,text="", image=LoadImg(".\\App\\Application Data\\Img\\copy.png", (12,12)), command=lambda: pyperclip.copy(Message))
        Copy.pack(side="bottom", anchor="e", padx=5, pady=(0,5))

    label = ctk.CTkLabel(MessageFrame, text_color_disabled=TextColor, text="\n".join(wrapped_lines) if not "\n".join(wrapped_lines).startswith("<error>") else "\n".join(wrapped_lines).replace("<error>", ""), font=('Arial', 15),wraplength=700, justify="left", text_color=TextColor if not "\n".join(wrapped_lines).startswith("<error>") else "white")
    label.pack(padx=10, pady=(10, 2), anchor=Anchor)

    time_label = ctk.CTkLabel(MessageFrame, text=Time, font=("Arial", 10), text_color="lightgray")
    time_label.pack(padx=10, pady=(0, 5), anchor=Anchor)

    Messages.append(MessageFrame)

    Window.after(10, lambda: MainFrame._parent_canvas.yview_moveto(1.0))

    print("ok")
    if _from == "User" and not PlaceOnly:
        AskEntry.configure(state="disabled")
        SendButton.configure(state="disabled")
        threading.Thread(target=GetResponse, args=(Payload,), daemon=True).start()

def ResetEntryAppareance(event) -> None:
    global ErrorLabel

    if ErrorLabel != None:
        ErrorLabel.destroy()
        ErrorLabel = None
    AskEntry.configure(border_color=BorderColor)

def LoadMessages() -> dict:
    with open(".\\App\\Application Data\\Messages\\messages.json", "r", encoding='utf-8') as ConvF:
        return json.load(ConvF)

def ChangeTheme(Theme: str) -> None:
    with open(".\\App\\Application Data\\Settings\\settings.json", "r", encoding='utf-8') as BaseJSON:
        OldSettings = json.load(BaseJSON)
    
    OldSettings.get("Settings")["Theme"] = Theme 

    with open(".\\App\\Application Data\\Settings\\settings.json", "w", encoding='utf-8') as NewJSON:
        json.dump(OldSettings, NewJSON)

    Restart()

def PlaceConv() -> None:
    LoadingFrame = ctk.CTkFrame(Window, fg_color=FirstColor, corner_radius=1, height=600, width=1000)
    LoadingFrame.place(y=0, x=0)

    LoadingLabel = ctk.CTkLabel(LoadingFrame, text="Chargement de la conversation", font=("Arial", 35, "bold"), text_color="white")
    LoadingLabel.place(y=200 / scaleFactor, relx=0.5, anchor='center')

    Conv = LoadMessages()

    Total = len(Conv)

    Progress = ctk.DoubleVar(value=0.0)
    LoadinProgress = ctk.CTkProgressBar(LoadingFrame, fg_color="#545454", height=5, width=450, progress_color=LoadingColor, variable=Progress)
    LoadinProgress.place(y=280 / scaleFactor, relx=0.5, anchor='center')

    MsgCount = 0
    MsgCountLabel = ctk.CTkLabel(LoadingFrame, text=f"{MsgCount}/{Total}", font=("Arial", 15), text_color="white")
    MsgCountLabel.place(y=305 / scaleFactor, relx=0.5, anchor='center')

    for Msg in Conv:
        if isinstance(Msg, dict) and "from" in Msg and "text" in Msg:
            PlaceMessage(None, _from=Msg["from"], Text=Msg["text"], PlaceOnly=True, Date=Msg["date"], FromLoading=True)
            Progress.set(Progress.get() + 1 / Total)
            MsgCount += 1
            MsgCountLabel.configure(text=f"{MsgCount}/{Total}")
            MsgCountLabel.place(y=305 / scaleFactor, relx=0.5, anchor='center')

    Window.after(1000, LoadingFrame.destroy)

ChoosenTheme = (None, None)
CurrentH = 50
CurrentW = 65

def ConfigTheme() -> None:
    def AddTheme(FirstColor: str, SecondColor: str, Name: str) -> None:
        global ChoosenTheme, CurrentH, CurrentW

        def ChooseTheme(event, Frame: ctk.CTkFrame, Name: str) -> None:
            global ChoosenTheme, CurrentH, CurrentW

            if ChoosenTheme[0] != None:
                ChoosenTheme[1].configure(border_width=0)

            ChoosenTheme = (Name, Frame)
            Frame.configure(border_width=5, border_color=LoadingColor)
            print("ok")

        if CurrentW >= 554 / scaleFactor:
            CurrentH += 100 / scaleFactor
            CurrentW = 65

        GlobalFrame = ctk.CTkFrame(ThemeWindow, fg_color=FirstColor, corner_radius=6, height=76, width=146)
        GlobalFrame.place(y=CurrentH / scaleFactor, x=CurrentW / scaleFactor)

        FirstFrame = ctk.CTkFrame(GlobalFrame, height=70, width=70, fg_color=FirstColor, corner_radius=1)
        FirstFrame.place(y=3 / scaleFactor, x=3 / scaleFactor)

        SecondFrame = ctk.CTkFrame(GlobalFrame, height=70, width=70, fg_color=SecondColor, corner_radius=1)
        SecondFrame.place(y=3 / scaleFactor, x=73 / scaleFactor)    

        FirstFrame.bind("<Button-1>",lambda e: ChooseTheme(e, GlobalFrame, Name))
        SecondFrame.bind("<Button-1>",lambda e: ChooseTheme(e, GlobalFrame, Name))
        print(CurrentW)
        CurrentW += 163 / scaleFactor

    def CloseThemeWindow() -> None:
        global ChoosenTheme, CurrentH, CurrentW

        CurrentW = 62
        CurrentH = 50
        ChoosenTheme = (None, None)

        ThemeWindow.quit()

    def ChangeTheme() -> None:
        global ChoosenTheme, GlobalSettings

        if ChoosenTheme[0] != None:
            GlobalSettings["Settings"]["Theme"] = ChoosenTheme[0]
            UpdateSettings()
        else:
            CloseThemeWindow()

    ThemeWindow = ctk.CTkToplevel(fg_color=FirstColor)
    ThemeWindow.geometry('600x400')
    ThemeWindow.maxsize(600, 400)
    ThemeWindow.title("Personalisation de l'interface")
    ThemeWindow.attributes("-topmost", True)
    ThemeWindow.protocol("WM_DELETE_WINDOW", CloseThemeWindow)
    ThemeWindow.after(200, lambda: ThemeWindow.iconbitmap(".\\App\\Application Data\\Img\\picon.ico"))

    AddTheme("#000000", "#ff811a", "ph")
    AddTheme("#18587d", "#ffcc00", "python")
    AddTheme("#0a0a0a", "#00ff00", "hacker")
    AddTheme("#0f2c3f", "#143f56", "ocean")
    AddTheme("#2c1b12", "#402218", "sunset")
    AddTheme("#1e2d1e", "#2b3d2b", "forest")
    AddTheme("#1a0000", "#330000", "infrared")
    AddTheme("#0f0f1a", "#290033", "cyberpunk")
    AddTheme("#171717", "#1b1b1b", "default")

    SaveThemeButton = ctk.CTkButton(ThemeWindow, command=ChangeTheme, text="Appliquer", height=30, font=("Arial", 16, "bold"), fg_color="#545454", hover_color="#464647", corner_radius=3, width=470)
    SaveThemeButton.place(y=350 / scaleFactor, x=65 / scaleFactor)

    ThemeWindow.mainloop()

Window = ctk.CTk(fg_color=FirstColor)
Window.title("AI ChatBot UI by Noone")
Window.geometry("1000x600")
Window.maxsize(1000, 600)
Window.attributes("-topmost", True)
Window.after(250, lambda: Window.attributes("-topmost", False))
Window.iconbitmap(".\\App\\Application Data\\Img\\wicon.ico")

MainFrame = ctk.CTkScrollableFrame(Window, height=470, width=950, fg_color=SecondColor, border_color=BorderColor, border_width=1)
MainFrame.place(x=12.5 / scaleFactor, y=42.5 / scaleFactor)

ToolBar = ctk.CTkFrame(Window, height=25, width=1000, fg_color=FirstColor, corner_radius=1)
ToolBar.place(y=0, x=0)

ThemeOptionsButton = ctk.CTkButton(ToolBar, command=ConfigTheme, height=25, width=100, fg_color=FirstColor, text='Thèmes', corner_radius=1, font=("Arial", 12), hover_color=SecondColor)
ThemeOptionsButton.place(y=0, x=0)

DelConvButton = ctk.CTkButton(ToolBar, command=ClearConv, text="Suprimer la conversation", fg_color=FirstColor, corner_radius=1, hover_color="red", height=25, width=100, font=("Arial", 12))
DelConvButton.place(y=0, x=100 / scaleFactor)

AskEntry = ctk.CTkEntry(Window, placeholder_text='Tapez une question ici...', height=35, width=825, fg_color=SecondColor, corner_radius=3, border_color=BorderColor, border_width=1)
AskEntry.place(y=535 / scaleFactor, x=12.5 / scaleFactor)

AskEntry.bind("<Key>", ResetEntryAppareance)
AskEntry.bind("<Return>", PlaceMessage)

SendButton = ctk.CTkButton(Window, command=PlaceMessage, height=34, width=140, fg_color=ButtonColor, hover_color=ButtonHover, corner_radius=3, text="Envoyer", font=("Arial", 16, "bold"))
SendButton.place(y=535.5 / scaleFactor, x=845 / scaleFactor)

if len(LoadMessages()) > 0:
    threading.Thread(target=PlaceConv, daemon=True).start()

Window.mainloop()
