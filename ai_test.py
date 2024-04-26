from absl import flags
from absl import logging
import tensorflow.compat.v1 as tf

from open_spiel.python import policy
from open_spiel.python import rl_environment
from open_spiel.python.algorithms import exploitability
from open_spiel.python.algorithms import nfsp

import random
from absl import app
from absl import flags
import numpy as np

from open_spiel.python import games  # pylint: disable=unused-import
import pyspiel

from ai_agent_train import *

def main(unused_argv):
    logging.info("Loading %s", FLAGS.game_name)
    game = FLAGS.game_name
    num_players = FLAGS.num_players

    env_configs = {"players": num_players}
    env = rl_environment.Environment(game, **env_configs)
    info_state_size = env.observation_spec()["info_state"][0]
    num_actions = env.action_spec()["num_actions"]

    hidden_layers_sizes = [int(l) for l in FLAGS.hidden_layers_sizes]
    kwargs = {
      "replay_buffer_capacity": FLAGS.replay_buffer_capacity,
      "reservoir_buffer_capacity": FLAGS.reservoir_buffer_capacity,
      "min_buffer_size_to_learn": FLAGS.min_buffer_size_to_learn,
      "anticipatory_param": FLAGS.anticipatory_param,
      "batch_size": FLAGS.batch_size,
      "learn_every": FLAGS.learn_every,
      "rl_learning_rate": FLAGS.rl_learning_rate,
      "sl_learning_rate": FLAGS.sl_learning_rate,
      "optimizer_str": FLAGS.optimizer_str,
      "loss_str": FLAGS.loss_str,
      "update_target_network_every": FLAGS.update_target_network_every,
      "discount_factor": FLAGS.discount_factor,
      "epsilon_decay_duration": FLAGS.epsilon_decay_duration,
      "epsilon_start": FLAGS.epsilon_start,
      "epsilon_end": FLAGS.epsilon_end,
    }

    with tf.Session() as sess:
        agents = [
            nfsp.NFSP(sess, idx, info_state_size, num_actions, hidden_layers_sizes,
                      **kwargs) for idx in range(num_players)
        ]

        for agent in agents:
            print("hello", agent)
            if agent.has_checkpoint(FLAGS.checkpoint_dir):
                agent.restore(FLAGS.checkpoint_dir)

        joint_avg_policy = NFSPPolicies(env, agents, nfsp.MODE.average_policy)

        games_list = pyspiel.registered_games()
        print("Registered games:")
        print(games_list)

        action_string = None

        # Game strings can just contain the name or the name followed by parameters
        # and arguments, e.g. "breakthrough(rows=6,columns=6)"

        print("Creating game: " + FLAGS.game_name)
        game = pyspiel.load_game(FLAGS.game_name)

        guy0, guy1 = [], []
        for i in range(10000):
            # Create the initial state
            state = game.new_initial_state()

            # Print the initial state
            print(str(state))

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
                    print("action", action)
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
                    # Decision node: sample action for the single current player
                    action = random.choice(state.legal_actions(state.current_player()))
                    action_string = state.action_to_string(state.current_player(), action)
                    print("Player ", state.current_player(), ", randomly sampled action: ",
                          action_string)
                    print("NSPE", joint_avg_policy.action_probabilities(state), sum(list(joint_avg_policy.action_probabilities(state).keys())))

                    if state.current_player() == 0:
                        action = np.random.choice(list(joint_avg_policy.action_probabilities(state).keys()), p=list(joint_avg_policy.action_probabilities(state).values()))
                    state.apply_action(action)
                print(str(state))

            # Game is now done. Print utilities for each player
            returns = state.returns()
            for pid in range(game.num_players()):
                print("Utility for player {} is {}".format(pid, returns[pid]))

            guy0.append(returns[0])
            guy1.append(returns[1])

        print(sum(guy0), sum(guy1))



if __name__ == "__main__":
  app.run(main)
