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
        
        self.create_widgets()
        
        self.start_button = ttk.Button(self.mainframe, text="Start Game", command=self.start_game)
        self.start_button.grid(column=3, row=self.number_of_players.get()+1, sticky=E)

        self.update_players()

    def create_widgets(self):
        tk.Label(self.mainframe, text="Number of players:").grid(row=0, column=0)
        tk.Label(self.mainframe, textvariable=self.number_of_players).grid(row=0, column=2)

        ttk.Button(self.mainframe, text="+", command=self.increment_players).grid(column=3, row=0, sticky=E)
        ttk.Button(self.mainframe, text="-", command=self.decrease_players).grid(column=1, row=0, sticky=W)
        
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

        
        # Create new player widgets
        for i in range(self.number_of_players.get()):
            label = ttk.Label(self.mainframe, text="Player Name:")
            label.grid(row=i+1, column=0)
            
            name = tk.StringVar()
            name.set("Player " + str(i+1))
            entry = ttk.Entry(self.mainframe, textvariable=name)
            entry.grid(row=i+1, column=1)

            player_type = tk.StringVar()
            type_menu = ttk.Combobox(self.mainframe, values=["Human", "AI"], textvariable=player_type)
            if i == 0:
                type_menu.set("Human")
            else:
                type_menu.set("AI")
            type_menu.grid(row=i+1, column=3)
            
            player_objects = {
                "name_label": label,
                "name_entry": entry,
                "type_combobox": type_menu
            }
            self.players.append(Player(name, player_type, player_objects))
        
        self.start_button = ttk.Button(self.mainframe, text="Start Game", command=self.start_game)
        self.start_button.grid(column=3, row=self.number_of_players.get()+1, sticky=E)

    def increment_players(self):
        if self.number_of_players.get() == 6:
            return
        self.number_of_players.set(self.number_of_players.get() + 1)
        self.update_players()
    
    def decrease_players(self):
        if self.number_of_players.get() == 2:
            return
        self.number_of_players.set(self.number_of_players.get() - 1)
        self.update_players()

    def start_game(self):
        for player in self.players:
            print('Name: ', player.name.get(), ' Type: ', player.player_type.get())
        PokerGame(self.root, self.mainframe, self.players)
        

class PokerGame:
    def __init__(self, root, mainframe, players):
        self.root = root
        self.mainframe = mainframe
        self.players = players

        self.pot = 0

        self.table_image = tk.PhotoImage(file="./resources/table.png")
        self.card_back_image = tk.PhotoImage(file="./resources/card_back.png")

        self.draw_game_table()
    
    def draw_game_table(self):
        # Remove the current widgets
        for widget in self.mainframe.winfo_children():
            widget.grid_forget()
            widget.destroy()
        
        # Display the table
        self.image_label = tk.Label(self.mainframe, image=self.table_image)
        self.image_label.image = self.table_image  # Keep a reference to the image to prevent garbage collection
        self.image_label.grid(row=1, column=1, columnspan=5, rowspan=4, padx=5, pady=5)

        # Locations of players in format:
        #   *locations[i][0][0] - Row location for player image
        #   *locations[i][0][1] - Row location for player name
        #   *locations[i][1] - Column location for player image and name
        locations = [
            ((1, 0), 2),
            ((1, 0), 3),
            ((1, 0), 4),
            ((4, 5), 2),
            ((4, 5), 3),
            ((4, 5), 4)
        ]

        bold_font = ("Arial", 10, "bold")

        for i, player in enumerate(self.players):
            player.image_label = tk.Label(self.mainframe, image=self.card_back_image)
            player.image_label.image = self.card_back_image  # Keep a reference to the image to prevent garbage collection
            player.image_label.grid(row=locations[i][0][0], column=locations[i][1], columnspan=1)
            player.name_label = tk.Label(self.mainframe, text=player.name.get(), font=bold_font)
            player.name_label.grid(row=locations[i][0][1], column=locations[i][1], columnspan=1, padx=10, pady=10)

            if player.player_type.get() == "AI":
                player.name_label.configure(foreground="red")

        self.players[0].name_label.configure(background="yellow")

        pot_label = tk.Label(self.mainframe, text=f'Current pot is: ${self.pot}')
        pot_label.grid(row=6, column=3, columnspan=1, padx=10, pady=10)


        self.call_button = ttk.Button(self.mainframe, text="Call", command=self.blank)
        self.call_button.grid(row=7,  column=2, columnspan=1)

        self.raise_button = ttk.Button(self.mainframe, text="Raise", command=self.blank)
        self.raise_button.grid(row=7, column=3, columnspan=1)

        self.fold_button = ttk.Button(self.mainframe, text="Fold", command=self.blank)
        self.fold_button.grid(row=7, column=4, columnspan=1)

        self.raise_amt = IntVar()
        self.raise_amt.set(5)
        self.raise_box = ttk.Spinbox(self.mainframe, from_=self.raise_amt.get(), to=100, increment=5, textvariable=self.raise_amt)
        self.raise_box.grid(row=8, column=3, columnspan=1)

        self.quit_button = ttk.Button(self.mainframe, text="Quit", command=self.quit)
        self.quit_button.grid(row=8, column=4, pady=5)

        self.card_1 = tk.PhotoImage(file="./resources/Kh.png")
        self.card_2 = tk.PhotoImage(file="./resources/Ks.png")

        card1_label = tk.Label(self.mainframe, image=self.card_1)
        card1_label.image = self.card_1  
        card1_label.grid(row=8, column=2, sticky=W)

        card2_label = tk.Label(self.mainframe, image=self.card_2)
        card2_label.image = self.card_2
        card2_label.grid(row=8, column=2)


    def quit(self):
        self.root.quit()
    
    def blank(self):
        pass

if __name__ == "__main__":
    root = tk.Tk()
    game = PokerGameSetup(root)
    root.mainloop()
