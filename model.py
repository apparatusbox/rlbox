import numpy as np
import tensorflow as tf
# from utils import *


class DQN:
    def __init__(self, state_shape, num_actions, learning_rate, use_huber=True):
        self.state_shape = state_shape
        self.num_actions = num_actions
        self.lr = learning_rate
        self.use_huber = use_huber

        # Model inputs
        self.actions = tf.placeholder(
            name='actions',
            shape=[None],
            dtype=tf.int32
        )
        self.rewards = tf.placeholder(
            name='rewards',
            shape=[None],
            dtype=tf.float32
        )
        self.done_mask = tf.placeholder(
            name='done_mask',
            shape=[None],
            dtype=tf.float32
        )

        # Create model
        if len(state_shape) == 3:
            self.states_t = tf.placeholder(
                name='states',
                shape=[None] + list(self.state_shape),
                dtype=tf.uint8
            )
            self.states_tp1 = tf.placeholder(
                name='states_tp1',
                shape=[None] + list(self.state_shape),
                dtype=tf.uint8
            )
            # Convert to float on GPU
            states_t_float = tf.cast(self.states_t, tf.float32) / 255.
            states_tp1_float = tf.cast(self.states_tp1, tf.float32) / 255.

            self.q_values = self._build_deepmind_model(states_t_float)
            self.q_target = self._build_deepmind_model(states_tp1_float)

        elif len(state_shape) == 1:
            print('shape1')
            self.states_t = tf.placeholder(
                name='states',
                shape=[None] + list(self.state_shape),
                dtype=tf.float32
            )
            self.states_tp1 = tf.placeholder(
                name='states_tp1',
                shape=[None] + list(self.state_shape),
                dtype=tf.float32
            )
            self.q_values = self._build_dense_model(self.states_t)
            self.q_target = self._build_dense_model(self.states_tp1)

        else:
            raise ValueError('state_shape not supported')

        # Create training operation
        # TODO: Remove hardcoded gamma
        self.training_op = self._build_optimization(learning_rate, 0.99)

    def _build_deepmind_model(self, states):
        ''' Network model from DeepMind '''
        # Model architecture
        net = states
        # Convolutional layers
        net = tf.layers.conv2d(net, 32, (8, 8), strides=(4, 4), activation=tf.nn.relu)
        net = tf.layers.conv2d(net, 64, (4, 4), strides=(2, 2), activation=tf.nn.relu)
        net = tf.layers.conv2d(net, 32, (3, 3), strides=(1, 1), activation=tf.nn.relu)
        net = tf.contrib.layers.flatten(net)

        # Dense layers
        net = tf.layers.dense(net, 512, activation=tf.nn.relu)
        output = tf.layers.dense(net, self.num_actions)

        return output

    def _build_dense_model(self, states):
        ''' Simple fully connected model '''
        # Model architecture
        net = states
        net = tf.layers.dense(net, 512, activation=tf.nn.relu)
        output = tf.layers.dense(net, self.num_actions)

        return output

    def _build_optimization(self, learning_rate, gamma):
        # Choose only the q values for selected actions
        onehot_actions = tf.one_hot(self.actions, self.num_actions)
        q_t = tf.reduce_sum(tf.multiply(self.q_values, onehot_actions), axis=1)

        # Caculate td_target
        q_tp1 = tf.reduce_max(self.q_target, axis=1)
        td_target = self.rewards + (1 - self.done_mask) * gamma * q_tp1
        # TODO: Huber loss
        errors = tf.squared_difference(q_t, td_target)
        total_error = tf.reduce_mean(errors)

        # Create training operation
        opt = tf.train.AdamOptimizer(learning_rate)
        training_op = opt.minimize(total_error)

        return training_op

    def predict(self, sess, states):
        return sess.run(self.q_values, feed_dict={self.states_t: states})

    def fit(self, sess, states_t, states_tp1, actions, rewards, dones):
        feed_dict = {
            self.states_t: states_t,
            self.states_tp1: states_tp1,
            self.actions: actions,
            self.rewards: rewards,
            self.done_mask: dones
        }
        sess.run(self.training_op, feed_dict=feed_dict)

    # def fit(self, states, actions, labels):
    #     # self.model.fit([states, actions], labels, batch_size=batch_size, epochs=epochs, verbose=verbose)
    #     loss = self.model.train_on_batch([states, actions], labels)
    #     return loss

    # def target_predict(self, states):
    #     fake_actions = np.zeros(len(states))
    #     return self.target.predict([states, fake_actions])

    # def target_update(self):
    #     self.target.set_weights(self.model.get_weights())

    # def load_weights(self, weights_file):
    #     self.model.load_weights(weights_file)
    #     self.target.load_weights(weights_file)


