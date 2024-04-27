import tensorflow.compat.v1 as tf
from train_nfsp import *

import random
import numpy as np
import pyspiel


def main():
    # Parameters to load NFSP agents
    param_dict = {"game_name": "leduc_poker", "num_players": 2, "num_train_episodes": int(1e6), "eval_every": 10000,
                  "hidden_layers_sizes": [
                      128,
                  ], "replay_buffer_capacity": int(2e4), "reservoir_buffer_capacity": int(1e6),
                  "min_buffer_size_to_learn": 1000, "anticipatory_param": 0.1, "batch_size": 128, "learn_every": 32,
                  "rl_learning_rate": 0.01, "sl_learning_rate": 0.01, "optimizer_str": "sgd", "loss_str": "mse",
                  "update_target_network_every": 19200, "discount_factor": 1.0, "epsilon_decay_duration": int(1e6),
                  "epsilon_start": 0.06, "epsilon_end": 0.001, "evaluation_metric": "nash_conv",
                  "use_checkpoints": True, "checkpoint_dir": "/Users/edwintomy/PycharmProjects/ai-poker/tf_model"}

    logging.info("Loading %s", param_dict["game_name"])
    game = param_dict["game_name"]
    num_players = param_dict["num_players"]

    # Parameters to load environment
    env_configs = {"players": num_players}
    env = rl_environment.Environment(game, **env_configs)
    info_state_size = env.observation_spec()["info_state"][0]
    num_actions = env.action_spec()["num_actions"]

    # Parameters to load reinforcement learning model
    hidden_layers_sizes = [int(l) for l in param_dict["hidden_layers_sizes"]]
    kwargs = {
        "replay_buffer_capacity": param_dict["replay_buffer_capacity"],
        "reservoir_buffer_capacity": param_dict["reservoir_buffer_capacity"],
        "min_buffer_size_to_learn": param_dict["min_buffer_size_to_learn"],
        "anticipatory_param": param_dict["anticipatory_param"],
        "batch_size": param_dict["batch_size"],
        "learn_every": param_dict["learn_every"],
        "rl_learning_rate": param_dict["rl_learning_rate"],
        "sl_learning_rate": param_dict["sl_learning_rate"],
        "optimizer_str": param_dict["optimizer_str"],
        "loss_str": param_dict["loss_str"],
        "update_target_network_every": param_dict["update_target_network_every"],
        "discount_factor": param_dict["discount_factor"],
        "epsilon_decay_duration": param_dict["epsilon_decay_duration"],
        "epsilon_start": param_dict["epsilon_start"],
        "epsilon_end": param_dict["epsilon_end"]
    }

    # Starting Tensorflow session
    with tf.Session() as sess:

        # Load NFSP agents
        agents = [
            nfsp.NFSP(sess, idx, info_state_size, num_actions, hidden_layers_sizes,
                      **kwargs) for idx in range(num_players)
        ]

        for agent in agents:
            if agent.has_checkpoint(param_dict["checkpoint_dir"]):
                agent.restore(param_dict["checkpoint_dir"])

        # Loaf Leduc Poker game with associated NFSP policies
        joint_avg_policy = NFSPPolicies(env, agents, nfsp.MODE.average_policy)
        games_list = pyspiel.registered_games()
        print("Creating game: " + param_dict["game_name"])
        game = pyspiel.load_game(param_dict["game_name"])

        player_type = {0: int(input("Select 0 for AI or 1 for human")), 1: int(input("Select 0 for AI or 1 for human"))}

        # Create the initial state
        state = game.new_initial_state()
        print(str(state))

        # Actions -> 0 (Fold), 1 (Call), 2 (Raise)
        # Cards -> 0, 1, 2, 3, 4, 5, 6 (Queen of Hearts, Queen of Spades,
        # King of Hearts, King of Spades, Ace of Hearts, Ace of Spades)
        while not state.is_terminal():
            # The state can be three different types: chance node,
            # simultaneous node, or decision node
            if state.is_chance_node():
                # Chance node: sample an outcome
                outcomes = state.chance_outcomes()
                num_actions = len(outcomes)
                print("Chance node, got " + str(num_actions) + " outcomes")
                print("outcomes", outcomes)
                action_list, prob_list = zip(*outcomes)
                action = np.random.choice(action_list, p=prob_list)
                print("Sampled outcome: ",
                      state.action_to_string(state.current_player(), action))
                state.apply_action(action)

            elif state.is_simultaneous_node():
                # Simultaneous node: sample actions for all players.
                random_choice = lambda a: np.random.choice(a) if a else [0]
                chosen_actions = [
                    random_choice(state.legal_actions(pid))
                    for pid in range(game.num_players())
                ]

                print("Chosen actions: ", [
                    state.action_to_string(pid, action)
                    for pid, action in enumerate(chosen_actions)
                ])

                state.apply_actions(chosen_actions)
            else:
                # Human Player
                if player_type[state.current_player()] == 1:
                    print("Current legal actions for player {}:".format(state.current_player()))
                    print(state.legal_actions(state.current_player()))
                    ans = int(input())
                    state.apply_action(ans)

                else:
                    # Decision node: sample action for the single current player
                    action = random.choice(state.legal_actions(state.current_player()))
                    action_string = state.action_to_string(state.current_player(), action)
                    print("Player ", state.current_player(), ", action: ",
                          action_string)

                    action = np.random.choice(list(joint_avg_policy.action_probabilities(state).keys()),
                                              p=list(joint_avg_policy.action_probabilities(state).values()))
                    state.apply_action(action)

            print(str(state))

        # Game is now done. Print utilities for each player
        returns = state.returns()
        for pid in range(game.num_players()):
            print("Utility for player {} is {}".format(pid, returns[pid]))


if __name__ == "__main__":
    main()
