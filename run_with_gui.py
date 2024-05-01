import tkinter as tk
from tkinter import *
from tkinter import ttk
import random

from train_tf_model import *
from run_with_terminal import *


class Player:
    def __init__(self, name, player_type, objects, bank=100):
        self.name = name
        self.player_type = player_type
        self.tk_objects = objects
        self.bank = bank
        self.hand1 = None
        self.curr_bet = 0

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
        if self.number_of_players.get() == 2: #Limiting the players to 2 because of 
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
        [self.player1, self.player2] = players

        self.pot = 0

        self.table_image = tk.PhotoImage(file="./resources/table.png")
        self.card_back_image = tk.PhotoImage(file="./resources/card_back.png")

        self.start_game()
    
    def start_game(self):
        # Remove the current widgets
        for widget in self.mainframe.winfo_children():
            widget.grid_forget()
            widget.destroy()
        
        # Display the table
        self.image_label = tk.Label(self.mainframe, image=self.table_image)
        self.image_label.image = self.table_image  # Keep a reference to the image to prevent garbage collection
        self.image_label.grid(row=1, column=1, columnspan=5, rowspan=4, padx=5, pady=5)

        self.call_button_var = tk.StringVar(value="Check")
        self.call_button = ttk.Button(self.mainframe, textvariable=self.call_button_var, command=self.check)
        self.call_button.grid(row=7,  column=2, columnspan=1)

        self.raise_button = ttk.Button(self.mainframe, text="Raise", command=self.raise_bet)
        self.raise_button.grid(row=7, column=3, columnspan=1)

        self.raise_amt = IntVar()
        self.raise_amt.set(5)
        self.raise_box = ttk.Spinbox(self.mainframe, from_=self.raise_amt.get(), to=100, increment=5, textvariable=self.raise_amt)
        self.raise_box.grid(row=8, column=3, columnspan=1)

        self.fold_button = ttk.Button(self.mainframe, text="Fold", command=self.fold)
        self.fold_button.grid(row=7, column=4, columnspan=1)

        
        bold_font = ("Arial", 10, "bold")

        self.player1_name_label_var = tk.StringVar()
        self.player1_bet_label_var = tk.StringVar()
        self.player2_name_label_var = tk.StringVar()
        self.player2_bet_label_var = tk.StringVar()
        self.pot_var = tk.StringVar()

        #Entry bets
        self.player1_bet(5)
        self.player2_bet(5)

        self.player1.image_label = tk.Label(self.mainframe, image=self.card_back_image)
        self.player1.image_label.image = self.card_back_image  # Keep a reference to the image to prevent garbage collection
        self.player1.image_label.grid(row=4, column=3, columnspan=1)
        
        self.player1.name_label = tk.Label(self.mainframe, textvariable=self.player1_name_label_var, font=bold_font)
        self.player1.name_label.grid(row=5, column=3, columnspan=1, padx=10, pady=10)
        
        if self.player1.player_type.get() == "AI":
            self.player1.name_label.configure(foreground="red")
            
        self.player2.image_label = tk.Label(self.mainframe, image=self.card_back_image)
        self.player2.image_label.image = self.card_back_image  
        self.player2.image_label.grid(row=1, column=3, columnspan=1)
    
        self.player2.name_label = tk.Label(self.mainframe, textvariable=self.player2_name_label_var, font=bold_font)
        self.player2.name_label.grid(row=0, column=3, columnspan=1, padx=10, pady=10)

        if self.player2.player_type.get() == "AI":
            self.player2.name_label.configure(foreground="red")
                
        pot_label = tk.Label(self.mainframe, textvariable=self.pot_var)
        pot_label.grid(row=6, column=3, columnspan=1, padx=10, pady=10)
        
        player1_bet_label = tk.Label(self.mainframe, textvariable=self.player1_bet_label_var)
        player1_bet_label.grid(row=4, column=2, columnspan=1, padx=10, pady=10, sticky=E)

        player2_bet_label = tk.Label(self.mainframe, textvariable=self.player2_bet_label_var)
        player2_bet_label.grid(row=1, column=4, columnspan=1, padx=10, pady=10, sticky=W)

        self.quit_button = ttk.Button(self.mainframe, text="Quit", command=self.quit)
        self.quit_button.grid(row=8, column=4, pady=5)

        self.deal_cards()
        
        self.card_1 = tk.PhotoImage(file=f"./resources/deck/{self.player1.hand1}.png")

        self.card1_label = tk.Label(self.mainframe, image=self.card_1)
        self.card1_label.image = self.card_1  
        self.card1_label.grid(row=8, column=2, sticky=W)

        self.community_card_label = tk.Label(self.mainframe, image=self.card_back_image)
        self.community_card_label.image = self.card_back_image
        self.community_card_label.grid(row=3, column=3, columnspan=1, sticky=(N))

        self.round = 1
        self.sub_round = 1
        self.update_round()

    def update_round(self):
        #Player 1's turn
        if self.sub_round % 2 == 1:
            self.player1.name_label.configure(background="yellow")
            self.player2.name_label.configure(background=self.player2.name_label.master["bg"])

            self.card1 = tk.PhotoImage(file=f"./resources/deck/{self.player1.hand1}.png")
            self.card1_label.configure(image=self.card1)
            #self.card1_label.image = self.card1
            if self.player1.curr_bet < self.player2.curr_bet:
                self.call_button_var.set(f"Call ${abs(self.player2.curr_bet - self.player1.curr_bet)}")
                self.call_button.configure(command=self.call)
            else:
                self.call_button_var.set("Check")
                self.call_button.configure(command=self.check)

        #Player 2's turn
        else:
            self.player1.name_label.configure(background=self.player1.name_label.master["bg"])
            self.player2.name_label.configure(background="yellow")

            self.card1 = tk.PhotoImage(file=f"./resources/deck/{self.player2.hand1}.png")
            self.card1_label.configure(image=self.card1)
            #self.card1_label.image = self.card1
            if self.player2.curr_bet < self.player1.curr_bet:
                self.call_button_var.set(f"Call ${abs(self.player2.curr_bet - self.player1.curr_bet)}")
                self.call_button.configure(command=self.call)
            else:
                self.call_button_var.set("Check")
                self.call_button.configure(command=self.call)


        
        if self.sub_round > 4:
            self.round += 1
            self.sub_round = 1
        
        if self.round == 2:
            #Show community card
            self.community_card_label.configure(image=self.community_card_front)
            pass
        
        if self.round == 3:
            #End game, collect profits
            self.end_game()
            pass
        
        if self.sub_round % 2 == 1:
            player_type = self.player1.player_type.get()
            #Check if player 1 is AI
            if player_type == "AI":
                # Define the choices and their corresponding probabilities
                choices = [0, 1, 2]
                probabilities = [0.47, 0.47, 0.05]

                # Use random.choices() to make the random selection
                choice = random.choices(choices, probabilities)[0]
                if choice == 0:
                    #Call
                    if self.player1.curr_bet < self.player2.curr_bet:
                        self.call()
                    #Check
                    else:
                        self.check()

                if choice == 1:
                    #Raise
                    self.raise_amt.set(5)
                    self.raise_bet()
                    
                if choice == 2:
                    #Fold  
                    self.fold()
                    pass
        else:
            #Check if player 2 is AI
            player_type = self.player2.player_type.get()
            if player_type == "AI":
                # Define the choices and their corresponding probabilities
                choices = [0, 1, 2]
                probabilities = [0.47, 0.47, 0.05]

                # Use random.choices() to make the random selection
                choice = random.choices(choices, probabilities)[0]
                if choice == 0:
                    #Call
                    if self.player2.curr_bet < self.player1.curr_bet:
                        self.call()
                    #Check
                    else:
                        self.check()

                if choice == 1:
                    #Raise
                    self.raise_amt.set(5)
                    self.raise_bet()
                    
                if choice == 2:
                    #Fold  
                    self.fold()

    def end_game(self):
        print(self.player1.hand1)
        print(self.player2.hand1)
        if self.player1.hand1[:1] == self.community_card[:1]:
            #Player 1 wins
            print('player 1 wins')
            self.player1.bank += self.pot
        
        if self.player2.hand1[:1] == self.community_card[:1]:
            #Player 2 wins
            print('player 2 wins')
            self.player2.bank += self.pot
        
        #Determine higher ranking card
        symbols = ['J', 'Q', 'K', 'A']
        player1_rank = symbols.index(self.player1.hand1[:1])
        player2_rank = symbols.index(self.player2.hand1[:1])
        if player1_rank > player2_rank:
            print('player 1 wins')
            self.player1.bank += self.pot
        if player2_rank > player1_rank:
            print('player 2 wins')
            self.player2.bank += self.pot
        else:
            print('TIE!')
            self.player1.bank += self.pot//2
            self.player2.bank += self.pot//2

        self.player1.curr_bet = 0
        self.player2.curr_bet = 0
        self.pot = 0
        self.start_game()

    def player1_bet(self, amt):
        self.player1.bank -= amt
        self.pot += amt
        self.player1.curr_bet += amt

        self.player1_name_label_var.set(f'{self.player1.name.get()}\n${self.player1.bank}')
        self.player1_bet_label_var.set(f'{self.player1.name.get()} bet: ${self.player1.curr_bet}')
        self.pot_var.set(f'Current pot is: ${self.pot}')

    def player2_bet(self, amt):
        self.player2.bank -= amt
        self.pot += amt
        self.player2.curr_bet += amt

        self.player2_name_label_var.set(f'{self.player2.name.get()}\n${self.player2.bank}')
        self.player2_bet_label_var.set(f'{self.player2.name.get()} bet: ${self.player2.curr_bet}')
        self.pot_var.set(f'Current pot is: ${self.pot}')

    def deal_cards(self):
        #suits = ['c', 'd', 'h', 's']
        #symbols = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']

        #Limiting to only 4 cards of 2 suits because of leduc poker
        suits = ['h', 's']
        symbols = ['J', 'Q', 'K', 'A']

        deck = []
        for symbol in symbols:
            for suit in suits:
                deck.append(symbol + suit)
        
        random.shuffle(deck)

        self.player1.hand1 = deck.pop()
        self.player2.hand1 = deck.pop()
        
        self.community_card = deck.pop()
        self.community_card_front = tk.PhotoImage(file=f"./resources/deck/{self.community_card}.png")
        
    def quit(self):
        self.root.quit()
    
    def raise_bet(self):
        if self.sub_round % 2 == 1:
            #Player 1 raised
            self.player1_bet(self.raise_amt.get())
        else:
            #Player 2 raised
            self.player2_bet(self.raise_amt.get())
        self.sub_round += 1
        self.update_round()

    def check(self):
        self.sub_round+=1
        self.update_round()
    
    def call(self):
        if self.sub_round % 2 == 1:
            #Player 1 called
            self.player1_bet(abs(self.player2.curr_bet - self.player1.curr_bet))
        else:
            #Player 2 called
            self.player2_bet(abs(self.player2.curr_bet - self.player1.curr_bet))
        self.sub_round += 1
        self.update_round()

    def fold(self):
        if self.sub_round % 2 == 1:
            #Player 1 folded
            self.player1.curr_bet = 0
            print('player 2 wins')
            self.player2.bank += self.pot
        else:
            #Player 2 folded
            self.player2.curr_bet = 0
            print('player 1 wins')
            self.player1.bank += self.pot
        
        self.player1.curr_bet = 0
        self.player2.curr_bet = 0
        self.pot = 0
        self.start_game()
        
    def blank(self):
        self.sub_round+=1
        self.update_round()
        

if __name__ == "__main__":
    root = tk.Tk()
    game = PokerGameSetup(root)
    root.mainloop()
