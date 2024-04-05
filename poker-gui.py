import tkinter as tk
from tkinter import *
from tkinter import ttk
import random


class Player:
    def __init__(self, name, player_type, objects):
        self.name = name
        self.player_type = player_type
        self.tk_objects = objects


class PokerGameSetup:
    def __init__(self, root):
        self.root = root
        self.root.title("Poker Game")
        
        self.mainframe = tk.Frame(self.root)
        self.mainframe.grid(row=0, column=0, sticky=(N, W, E, S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.number_of_players = tk.IntVar()
        self.number_of_players.set(2)
        
        self.players = []
        self.player_entries = []
        self.player_actions = []
        self.player_name_labels = []
        
        self.create_widgets()
        
        self.start_button = ttk.Button(self.mainframe, text="Start Game", command=self.start_game)
        self.start_button.grid(column=3, row=self.number_of_players.get()+1, sticky=E)

        self.update_players()

        
    def create_widgets(self):
        tk.Label(self.mainframe, text="Number of players:").grid(row=0, column=0)
        tk.Label(self.mainframe, textvariable=self.number_of_players).grid(row=0, column=2)

        ttk.Button(self.mainframe, text="+", command=self.IncrementPlayers).grid(column=3, row=0, sticky=E)
        ttk.Button(self.mainframe, text="-", command=self.DecrementPlayers).grid(column=1, row=0, sticky=W)
        
        for child in self.mainframe.winfo_children():
            child.grid_configure(padx=5, pady=5)
    
    def update_players(self):

        # Remove previous player widgets
        for player in self.players:
            for name, object in player.tk_objects.items():
                object.grid_forget()
                object.destroy()
        self.start_button.grid_forget()
        self.start_button.destroy()

        self.players = []
        self.player_entries = []
        self.player_actions = []
        self.player_name_labels = []
        
        # Create new player widgets
        for i in range(self.number_of_players.get()):
            label = ttk.Label(self.mainframe, text="Player Name:")
            label.grid(row=i+1, column=0)
            self.player_name_labels.append(label)

            name = tk.StringVar()
            name.set("Player " + str(i+1))
            entry = ttk.Entry(self.mainframe, textvariable=name)
            entry.grid(row=i+1, column=1)
            self.player_entries.append(entry)
            
            player_type = tk.StringVar()
            type_menu = ttk.Combobox(self.mainframe, values=["Human", "AI"], textvariable=player_type)
            if i == 0:
                type_menu.set("Human")
            else:
                type_menu.set("AI")
            type_menu.grid(row=i+1, column=3)
            self.player_actions.append(type_menu)
            
            player_objects = {
                "name_label": label,
                "name_entry": entry,
                "type_combobox": type_menu
            }
            self.players.append(Player(name, player_type, player_objects))
        
        self.start_button = ttk.Button(self.mainframe, text="Start Game", command=self.start_game)
        self.start_button.grid(column=3, row=self.number_of_players.get()+1, sticky=E)

    def IncrementPlayers(self):
        if self.number_of_players.get() == 6:
            return
        self.number_of_players.set(self.number_of_players.get() + 1)
        self.update_players()
    
    def DecrementPlayers(self):
        if self.number_of_players.get() == 2:
            return
        self.number_of_players.set(self.number_of_players.get() - 1)
        self.update_players()

    def start_game(self):
        for player in self.players:
            print('Name: ', player.name.get(), ' Type: ', player.player_type.get())

if __name__ == "__main__":
    root = tk.Tk()
    game = PokerGameSetup(root)
    root.mainloop()
