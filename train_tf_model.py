from absl import app
from absl import flags
from absl import logging
import tensorflow.compat.v1 as tf

from open_spiel.python import policy
from open_spiel.python import rl_environment
from open_spiel.python.algorithms import exploitability
from open_spiel.python.algorithms import nfsp

# Parameters for reinforcement learning
FLAGS = flags.FLAGS

flags.DEFINE_string("game_name", "leduc_poker",
                    "Name of the game.")
flags.DEFINE_integer("num_players", 2,
                     "Number of players.")
flags.DEFINE_integer("num_train_episodes", int(1e6),
                     "Number of training episodes.")
flags.DEFINE_integer("eval_every", 10000,
                     "Episode frequency at which the agents are evaluated.")
flags.DEFINE_list("hidden_layers_sizes", [
    128,
], "Number of hidden units in the avg-net and Q-net.")
flags.DEFINE_integer("replay_buffer_capacity", int(2e4),
                     "Size of the replay buffer.")
flags.DEFINE_integer("reservoir_buffer_capacity", int(1e6),
                     "Size of the reservoir buffer.")
flags.DEFINE_integer("min_buffer_size_to_learn", 1000,
                     "Number of samples in buffer before learning begins.")
flags.DEFINE_float("anticipatory_param", 0.1,
                   "Prob of using the rl best response as episode policy.")
flags.DEFINE_integer("batch_size", 128,
                     "Number of transitions to sample at each learning step.")
flags.DEFINE_integer("learn_every", 32,
                     "Number of steps between learning updates.")
flags.DEFINE_float("rl_learning_rate", 0.01,
                   "Learning rate for inner rl agent.")
flags.DEFINE_float("sl_learning_rate", 0.01,
                   "Learning rate for avg-policy sl network.")
flags.DEFINE_string("optimizer_str", "sgd",
                    "Optimizer, choose from 'adam', 'sgd'.")
flags.DEFINE_string("loss_str", "mse",
                    "Loss function, choose from 'mse', 'huber'.")
flags.DEFINE_integer("update_target_network_every", 19200,
                     "Number of steps between DQN target network updates.")
flags.DEFINE_float("discount_factor", 1.0,
                   "Discount factor for future rewards.")
flags.DEFINE_integer("epsilon_decay_duration", int(1e6),
                     "Number of game steps over which epsilon is decayed.")
flags.DEFINE_float("epsilon_start", 0.06,
                   "Starting exploration parameter.")
flags.DEFINE_float("epsilon_end", 0.001,
                   "Final exploration parameter.")
flags.DEFINE_string("evaluation_metric", "nash_conv",
                    "Choose from 'exploitability', 'nash_conv'.")
flags.DEFINE_bool("use_checkpoints", True, "Save/load neural network weights.")
flags.DEFINE_string("checkpoint_dir", "/Users/edwintomy/PycharmProjects/ai-poker/tf_model",
                    "Directory to save/load the agent.")

# Establish Policy for Neural Fictitious Self-Play
class NFSPPolicies(policy.Policy):

    def __init__(self, env, nfsp_policies, mode):
        game = env.game
        player_ids = list(range(2))
        super(NFSPPolicies, self).__init__(game, player_ids)
        self._policies = nfsp_policies
        self._mode = mode
        self._obs = {
            "info_state": [None] * 2,
            "legal_actions": [None] * 2
        }

    # Return probabilities for choosing each action
    def action_probabilities(self, state, player_id=None):
        cur_player = state.current_player()
        legal_actions = state.legal_actions(cur_player)

        self._obs["current_player"] = cur_player
        self._obs["info_state"][cur_player] = (
            state.information_state_tensor(cur_player))
        self._obs["legal_actions"][cur_player] = legal_actions

        info_state = rl_environment.TimeStep(
            observations=self._obs, rewards=None, discounts=None, step_type=None)

        with self._policies[cur_player].temp_mode_as(self._mode):
            p = self._policies[cur_player].step(info_state, is_evaluation=True).probs
        prob_dict = {action: p[action] for action in legal_actions}
        return prob_dict


def main(unused_argv):

    # Establish the main environment for reinforcement learning
    logging.info("Loading %s", FLAGS.game_name)
    game = FLAGS.game_name
    num_players = FLAGS.num_players

    env_configs = {"players": num_players}
    env = rl_environment.Environment(game, **env_configs)
    info_state_size = env.observation_spec()["info_state"][0]
    num_actions = env.action_spec()["num_actions"]

    # Established environment for reinforcement learning
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

    # Started tensorflow session
    with tf.Session() as sess:

        # Establish NFSP agents for poker players
        agents = [
            nfsp.NFSP(sess, idx, info_state_size, num_actions, hidden_layers_sizes,
                      **kwargs) for idx in range(num_players)
        ]

        # Establish NFSP policy for poker agents
        joint_avg_policy = NFSPPolicies(env, agents, nfsp.MODE.average_policy)

        sess.run(tf.global_variables_initializer())

        if FLAGS.use_checkpoints:
            for agent in agents:
                if agent.has_checkpoint(FLAGS.checkpoint_dir):
                    agent.restore(FLAGS.checkpoint_dir)

        # Start reinforcement learning training
        for ep in range(FLAGS.num_train_episodes):
            if (ep + 1) % FLAGS.eval_every == 0:
                losses = [agent.loss for agent in agents]
                logging.info("Losses: %s", losses)

                # Average exploit-ability is implemented only for 2 players constant-sum using nash otherwise
                if FLAGS.evaluation_metric == "exploitability":
                    expl = exploitability.exploitability(env.game, joint_avg_policy)
                    logging.info("[%s] Exploitability AVG %s", ep + 1, expl)
                elif FLAGS.evaluation_metric == "nash_conv":
                    nash_conv = exploitability.nash_conv(env.game, joint_avg_policy)
                    logging.info("[%s] NashConv %s", ep + 1, nash_conv)
                else:
                    raise ValueError(" ".join(("Invalid evaluation metric, choose from",
                                               "'exploitability', 'nash_conv'.")))
                if FLAGS.use_checkpoints:
                    for agent in agents:
                        agent.save(FLAGS.checkpoint_dir)
                logging.info("_____________________________________________")

            # Step evaluation of training
            time_step = env.reset()
            while not time_step.last():
                player_id = time_step.observations["current_player"]
                agent_output = agents[player_id].step(time_step)
                action_list = [agent_output.action]
                time_step = env.step(action_list)

            # Episode is over, step all agents with final info state.
            for agent in agents:
                agent.step(time_step)


if __name__ == "__main__":
    app.run(main)
