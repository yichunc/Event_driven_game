import tensorflow as tf
import numpy as np
import random
import time

start_time = time.time()

class UAV_fire_extinguish(object):

  n_w = 4
  n_uav = 2
  n_fire = 3
  u_loca = (0,15)
  t_fail = (0.05,0.05)
  t_emit = (0.7,0.7)
  l_fire = (3,6,12)
  r_fire = (2.0,1.0,10.0)
  e_fire = [[0.5,0.9],[0.9,0.9],[0.05,0.9]]
  horizon = 20
  horizon = 5

##### Sampling method #####

def sampling_events(event,prob):

  n_length = len(event)

  x_rand = np.random.random()

  for i in range(n_length):

    x_rand = x_rand - prob[i]

    if x_rand <= 0:

      return event[i]


def mix_distribution(event1,prob1,event2,prob2):

  n_length_1 = len(event1)
  n_length_2 = len(event2)

  new_event = []
  new_prob = []

  for e1 in range(n_length_1):
    for e2 in range(n_length_2):
      e_new = event1[e1] + [event2[e2]]
      new_event.append(e_new)
      p_new = prob1[e1] * prob2[e2]
      new_prob.append(p_new)

  return (new_event,new_prob)

##### check boundary #####

def check_boundary(x,w):

  if x < 0:
    return 0
  elif x > w-1:
    return w-1
  else:
    return x


n_w = UAV_fire_extinguish.n_w
n_grid = n_w * n_w

##################################
##### Mapping between states #####
##################################

def two_dim_to_one(l_cor,n_w):

  x = l_cor[0]
  y = l_cor[1]

  l = n_w * y + x

  return l

def one_dim_to_two(l,n_w):

  x = l%n_w
  y = (l-x)/n_w

  return (x,y)


############################
##### TRANSITION MODEL #####
############################

### simple movement of one agent due to action

def move_location_single(l_1d,a,n_w):

  if l_1d == n_w * n_w:

    return l_1d


  l = one_dim_to_two(l_1d,n_w)

  x_next = l[0]
  y_next = l[1]

  if a == 0: # up
    y_next = y_next + 1
  elif a == 1: # down
    y_next = y_next - 1
  elif a == 2: # left
    x_next = x_next - 1
  elif a == 3:
    x_next = x_next + 1
  else:
    pass


  x_next = check_boundary(x_next,n_w)
  y_next = check_boundary(y_next,n_w)

  l_next = two_dim_to_one((x_next,y_next),n_w)

  return l_next

######################################################
##### number of uavs at the location of the fire #####
######################################################

def fire_has_uavs(lf,l1,l2):

  num = 0

  if lf == l1:

    num += 1

  if lf == l2:

    num += 1

  return num

######################################################################
##### Obtain all possible sets and the corresponding probability #####
######################################################################

def transition_model(cart_product,a_joint,UAV_fire_extinguish):

  s_fail = UAV_fire_extinguish.n_w * UAV_fire_extinguish.n_w

  ##### Terminal states #####

  initial_state = list((UAV_fire_extinguish.u_loca[0],UAV_fire_extinguish.u_loca[1],1,1,1))

  if cart_product[0] == s_fail and cart_product[1] == s_fail:

    return ([initial_state],[1.0])

  fire_sum = 0

  for i in range(UAV_fire_extinguish.n_fire):

    fire_sum += cart_product[UAV_fire_extinguish.n_uav + i]

  if fire_sum == 0:

    return ([initial_state],[1.0])


  ##### Transition of the first UAV #####

  if cart_product[0] == s_fail:

    event_set_0 = [[s_fail]]
    prob_set_0 = [1.0]

  else:

    l0_next = move_location_single(cart_product[0],a_joint[0],UAV_fire_extinguish.n_w)
    event_set_0 = [[l0_next],[s_fail]]
    prob_set_0 =  [1.0 - UAV_fire_extinguish.t_fail[0], UAV_fire_extinguish.t_fail[0]]

  ##### Transition of the second UAV #####

  if cart_product[1] == s_fail:

    event_set_1 = [s_fail]
    prob_set_1 = [1.0]

  else:

    l1_next = move_location_single(cart_product[1],a_joint[1],UAV_fire_extinguish.n_w)
    event_set_1 = [l1_next,s_fail]
    prob_set_1 =  [1.0 - UAV_fire_extinguish.t_fail[1], UAV_fire_extinguish.t_fail[1]]

  (event_product,prob_product) = mix_distribution(event_set_0,prob_set_0,event_set_1,prob_set_1)

  ##### Transition of the fire states #####

  for i_fire in range(UAV_fire_extinguish.n_fire):

    the_fire_state = cart_product[UAV_fire_extinguish.n_uav + i_fire]

    if the_fire_state == 0: # no fire

      (event_product,prob_product) = mix_distribution(event_product,prob_product,[0],[1.0])

    else:

      l_f = UAV_fire_extinguish.l_fire[i_fire]
      l_0 = cart_product[0]
      l_1 = cart_product[1]

      if fire_has_uavs(l_f,l_0,l_1) == 1:

        rate_put_down = UAV_fire_extinguish.e_fire[i_fire][fire_has_uavs(l_f,l_0,l_1) - 1]
        (event_product,prob_product) = mix_distribution(event_product,prob_product,[0,1],[rate_put_down,1.0-rate_put_down])

      elif fire_has_uavs(l_f,l_0,l_1) == 2:

        rate_put_down = UAV_fire_extinguish.e_fire[i_fire][fire_has_uavs(l_f,l_0,l_1) - 1]
        (event_product,prob_product) = mix_distribution(event_product,prob_product,[0,1],[rate_put_down,1.0-rate_put_down])

      else:

        (event_product,prob_product) = mix_distribution(event_product,prob_product,[1],[1.0])



  return (event_product,prob_product)



def transition_sample(current_state, # location is one-dimensional
                      a_joint,
                      last_info_0,
                      last_info_1,
                      UAV_fire_extinguish):

  n_w = UAV_fire_extinguish.n_w

  reward = 0.0

  (event,prob) = transition_model(current_state,a_joint,UAV_fire_extinguish)

  next_state = sampling_events(event,prob)

  (xp0,yp0) = one_dim_to_two(next_state[0],n_w)
  (xp1,yp1) = one_dim_to_two(next_state[1],n_w)

  next_state_coor = [xp0,yp0,xp1,yp1,next_state[2],next_state[3],next_state[4]]

  # Collect rewards

  for i_fire in range(UAV_fire_extinguish.n_fire):

    if current_state[UAV_fire_extinguish.n_uav + i_fire] == 1 and next_state[UAV_fire_extinguish.n_uav + i_fire] == 0:

      reward += UAV_fire_extinguish.r_fire[i_fire]

  # Update info

  p_info_0 = random.random()

  if p_info_0 < UAV_fire_extinguish.t_emit[0] :
    next_info_0 = next_state_coor + [1]
  else:
    next_info_0 = last_info_0[:]
    next_info_0[-1] += 1


  p_info_1 = random.random()

  if p_info_1 < UAV_fire_extinguish.t_emit[1] :
    next_info_1 = next_state_coor + [1]
  else:
    next_info_1 = last_info_1[:]
    next_info_1[-1] += 1

  return [next_state,(next_info_0,reward),(next_info_1,reward)]




def samples_by_random_action(n_init_pool,s_init,UAV_fire_extinguish):

  s0_pool = np.zeros((n_init_pool,8),float)
  a0_pool = np.zeros((n_init_pool,5),float)
  r0_pool = np.zeros((n_init_pool,1),float)
  s0p_pool = np.zeros((n_init_pool,8),float)

  s1_pool = np.zeros((n_init_pool,8),float)
  a1_pool = np.zeros((n_init_pool,5),float)
  r1_pool = np.zeros((n_init_pool,1),float)
  s1p_pool = np.zeros((n_init_pool,8),float)

  s_current = s_init
  (x0_init ,y0_init) = one_dim_to_two(s_init[0],UAV_fire_extinguish.n_w)
  (x1_init ,y1_init) = one_dim_to_two(s_init[1],UAV_fire_extinguish.n_w)
  s_current_coor = [x0_init,y0_init,x1_init,y1_init,s_init[2],s_init[3],s_init[4]]

  last_info_0 = s_current_coor + [1]
  last_info_1 = s_current_coor + [1]

  for i_event in range(n_init_pool):
    a0 = random.randint(0,4)
    a1 = random.randint(0,4)
    outcome = transition_sample(s_current,(a0,a1),last_info_0,last_info_1,UAV_fire_extinguish)

    next_state = outcome[0]
    (next_info_0,reward) = outcome[1]
    (next_info_1,reward) = outcome[2]

    #print("s_current = ", s_current)
    #print("a_joint = ", (a0,a1))
    #print("next_state = ", next_state)
    #print("last_info_0 = ",last_info_0)
    #print("next_info_0 = ",next_info_0)
    #print("last_info_1 = ",last_info_1)
    #print("next_info_1 = ",next_info_1)

    s0_pool[i_event,:] = last_info_0
    s0p_pool[i_event,:] = next_info_0
    a0_pool[i_event,a0] = 1.0
    r0_pool[i_event,0] = reward

    s1_pool[i_event,:] = last_info_1
    s1p_pool[i_event,:] = next_info_1
    a1_pool[i_event,a1] = 1.0
    r1_pool[i_event,0] = reward

    last_info_0 = next_info_0
    last_info_1 = next_info_1
    s_current = next_state


  return ((s0_pool,a0_pool,r0_pool,s0p_pool),(s1_pool,a1_pool,r1_pool,s1p_pool))

def truncate_dataset(data_array,n_keep_size):

  n_size = len(data_array)

  if n_size <= n_keep_size:
    return data_array
  else:
    return data_array[(n_size-n_keep_size):,:]


##########################################
############ Neural Network ##############
##########################################

##### functions for nerual network #####


def add_layer(inputs, in_size, out_size, activation_function=None):
    # add one more layer and return the output of this layer
    Weights = tf.Variable(tf.random_normal([in_size, out_size]))
    biases = tf.Variable(tf.zeros([1, out_size]) + 0.1)
    inputs = tf.to_float(inputs)
    Wx_plus_b = tf.matmul(inputs, Weights) + biases
    if activation_function is None:
        outputs = Wx_plus_b
    else:
        outputs = activation_function(Wx_plus_b)
    return (outputs,Weights,biases)

def copy_layer(inputs,Weights,biases,activation_function = None):
    inputs = tf.to_float(inputs)
    Wx_plus_b = tf.matmul(inputs, Weights) + biases
    if activation_function is None:
        outputs = Wx_plus_b
    else:
        outputs = activation_function(Wx_plus_b)
    return outputs

def es_greedy(inputs,epsi):

  x_rand = np.random.random()

  if x_rand < epsi:
    return np.random.randint(0,4)
  else:
    return np.argmax(inputs)

def batch_select(inputs,n_total,n_batch,seeds):

  batch_set = np.zeros((n_batch,len(inputs[0])))
  for i in range(n_batch):
    batch_set[i,:] = inputs[seeds[i],:]

  return batch_set

##### Sequential test #####

def visualize_scenario_indp(initial_state,h_print,r_explore,UAV_fire_extinguish):

  (x0,y0) = one_dim_to_two(initial_state[0],UAV_fire_extinguish.n_w)
  (x1,y1) = one_dim_to_two(initial_state[1],UAV_fire_extinguish.n_w)

  last_info_0 = [x0,y0,x1,y1,1,1,1,1]
  last_info_1 = [x0,y0,x1,y1,1,1,1,1]

  current_state = initial_state

  print("state  = ",current_state)

  for h in range(h_print):
    action_chosen_1 = es_greedy(sess.run(Q_a1, feed_dict={last_info_a1: [last_info_1]}),r_explore)
    action_chosen_0 = es_greedy(sess.run(Q_a0, feed_dict={last_info_a0: [last_info_0]}),r_explore)

    outcome_transition = transition_sample(current_state,
                                           (action_chosen_0,action_chosen_1),
                                           last_info_0,
                                           last_info_1,
                                           UAV_fire_extinguish)

    next_state = outcome_transition[0]
    (next_info_0,reward_immed) = outcome_transition[1]
    (next_info_1,reward_immed) = outcome_transition[2]
    print("action = ",(action_chosen_0,action_chosen_1))

    current_state = next_state
    last_info_0 = next_info_0
    last_info_1 = next_info_1

    print("state  = ",current_state)
    print("delay  = ",(last_info_0[-1],last_info_1[-1]))

##### Create initial population of samples #####

n_hidd = 50
n_init_pool = 100000#50000

outcome = samples_by_random_action(n_init_pool,[0,15,1,1,1],UAV_fire_extinguish)

s0_array = outcome[0][0]
a0_array = outcome[0][1]
r0_array = outcome[0][2]
sp0_array = outcome[0][3]

s1_array = outcome[1][0]
a1_array = outcome[1][1]
r1_array = outcome[1][2]
sp1_array = outcome[1][3]


##### Value holders #####

last_info_a0 = tf.placeholder(tf.int32,[None,8])
next_info_a0 = tf.placeholder(tf.int32,[None,8])
actions_a0 = tf.placeholder(tf.float32,[None,5])
rewards_a0 = tf.placeholder(tf.float32,[None,1])

W1_train_a0 = tf.placeholder(tf.float32,[8,n_hidd])
b1_train_a0 = tf.placeholder(tf.float32,[1,n_hidd])
W2_train_a0 = tf.placeholder(tf.float32,[n_hidd,5])
b2_train_a0 = tf.placeholder(tf.float32,[1,5])

last_info_a1 = tf.placeholder(tf.int32,[None,8])
next_info_a1 = tf.placeholder(tf.int32,[None,8])
actions_a1 = tf.placeholder(tf.float32,[None,5])
rewards_a1 = tf.placeholder(tf.float32,[None,1])

W1_train_a1 = tf.placeholder(tf.float32,[8,n_hidd])
b1_train_a1 = tf.placeholder(tf.float32,[1,n_hidd])
W2_train_a1 = tf.placeholder(tf.float32,[n_hidd,5])
b2_train_a1 = tf.placeholder(tf.float32,[1,5])


##################
##### Layers #####
##################

##### Agent 0's NN #####
layer_1_a0 = add_layer(last_info_a0, 8, n_hidd, activation_function = tf.nn.relu)
layer_out_a0 = add_layer(layer_1_a0[0], n_hidd, 5, activation_function = None)
Q_a0 = layer_out_a0[0]

layer_c1_a0 = copy_layer(next_info_a0, W1_train_a0, b1_train_a0, activation_function = tf.nn.relu)
Q_next_a0 = copy_layer(layer_c1_a0, W2_train_a0, b2_train_a0, activation_function = None)

##### Agent 1's NN #####
layer_1_a1 = add_layer(last_info_a1, 8, n_hidd, activation_function = tf.nn.relu)
layer_out_a1 = add_layer(layer_1_a1[0], n_hidd, 5, activation_function = None)
Q_a1 = layer_out_a1[0]

layer_c1_a1 = copy_layer(next_info_a1, W1_train_a1, b1_train_a1, activation_function = tf.nn.relu)
Q_next_a1 = copy_layer(layer_c1_a1, W2_train_a1, b2_train_a1, activation_function = None)


### Loss function for Agent 0 ###
best_next_state_action_a0 = tf.reduce_max(Q_next_a0,reduction_indices=[1],keep_dims=True)
current_state_action_a0 = tf.reduce_sum(tf.mul(Q_a0,actions_a0),reduction_indices=[1],keep_dims=True)
loss_a0 = tf.reduce_mean(tf.square(rewards_a0 + 0.95 * best_next_state_action_a0 - current_state_action_a0))

### train for the loss function of Agent0 ###
train_step_a0 = tf.train.AdamOptimizer(0.001).minimize(loss_a0)

### Loss function for Agent 1 ###
best_next_state_action_a1 = tf.reduce_max(Q_next_a1,reduction_indices=[1],keep_dims=True)
current_state_action_a1 = tf.reduce_sum(tf.mul(Q_a1,actions_a1),reduction_indices=[1],keep_dims=True)
loss_a1 = tf.reduce_mean(tf.square(rewards_a1 + 0.95 * best_next_state_action_a1 - current_state_action_a1))

### train for the loss function of Agent1 ###
train_step_a1 = tf.train.AdamOptimizer(0.001).minimize(loss_a1)

### session ###
init = tf.initialize_all_variables()
sess = tf.Session()
sess.run(init)

### initialize all information ###
current_state = [0,15,1,1,1]
next_state = 0
last_info_0 = [0,0,3,3,1,1,1,1]
last_info_1 = [0,0,3,3,1,1,1,1]

W1_for_feed_train_a0 = np.ones((8,n_hidd),float)
b1_for_feed_train_a0 = np.ones((1,n_hidd),float)
W2_for_feed_train_a0 = np.ones((n_hidd,5),float)
b2_for_feed_train_a0 = np.ones((1,5),float)

W1_for_feed_train_a1 = np.ones((8,n_hidd),float)
b1_for_feed_train_a1 = np.ones((1,n_hidd),float)
W2_for_feed_train_a1 = np.ones((n_hidd,5),float)
b2_for_feed_train_a1 = np.ones((1,5),float)


### batch ###

n_batch_size = 5000

seeds = random.sample(xrange(1,n_init_pool),n_batch_size)

s0_batch = batch_select(s0_array,n_init_pool,n_batch_size,seeds)
r0_batch = batch_select(r0_array,n_init_pool,n_batch_size,seeds)
a0_batch = batch_select(a0_array,n_init_pool,n_batch_size,seeds)
sp0_batch = batch_select(sp0_array,n_init_pool,n_batch_size,seeds)

s1_batch = batch_select(s1_array,n_init_pool,n_batch_size,seeds)
r1_batch = batch_select(r1_array,n_init_pool,n_batch_size,seeds)
a1_batch = batch_select(a1_array,n_init_pool,n_batch_size,seeds)
sp1_batch = batch_select(sp1_array,n_init_pool,n_batch_size,seeds)


h_train_step = 1000
h_grad = 100
r_explore = 0.4

for iteration_times in range(0):
  print("iteration times = ", iteration_times)
  print("--- %s seconds ---" % (time.time() - start_time))
  ##############################
  ###### Only for agent 1 ######
  ##############################

  for h in range(h_train_step):

    numeric_loss_a0 = 0.0

    ##### training the NN #####
    for i in range(h_grad):

      numeric_loss_a0, _ = sess.run([loss_a0,train_step_a0],feed_dict={last_info_a0: s0_batch,
                                                                       rewards_a0: r0_batch,
                                                                       next_info_a0:sp0_batch,
                                                                       actions_a0: a0_batch,
                                                                       W1_train_a0: W1_for_feed_train_a0,
                                                                       b1_train_a0: b1_for_feed_train_a0,
                                                                       W2_train_a0: W2_for_feed_train_a0,
                                                                       b2_train_a0: b2_for_feed_train_a0})
    #print(numeric_loss_a0)


    ##### Choose action #####

    # action for agent 0 is chosen from the current NN
    # action for agent 1 is chosen randomly in the first iteration,
    # otherwise it is learned from previous network

    action_chosen_0 = es_greedy(sess.run(Q_a0, feed_dict={last_info_a0: [last_info_0]}),r_explore)
    if iteration_times == 0:
      action_chosen_1 = random.randint(0,4)
    else:
      action_chosen_1 = es_greedy(sess.run(Q_a1, feed_dict={last_info_a1: [last_info_1]}),0.0)

    ##### sample the transition #####
    outcome_transition = transition_sample(current_state,
                                           (action_chosen_0,action_chosen_1),
                                           last_info_0,
                                           last_info_1,
                                           UAV_fire_extinguish)

    next_state = outcome_transition[0]
    (next_info_0,reward_immed) = outcome_transition[1]
    (next_info_1,reward_immed) = outcome_transition[2]
    if h%50 == 0: print(numeric_loss_a0)
    #print('(current_state)= ',current_state)
    #print('(joint action )= ',(action_chosen_0,action_chosen_1))
    #print('(next state   )= ',next_state)

    ##### increase sample dataset #####

    s0_array = np.vstack([s0_array, last_info_0])
    sp0_array = np.vstack([sp0_array, next_info_0])
    r0_array = np.vstack([r0_array, reward_immed])

    s1_array = np.vstack([s1_array, last_info_1])
    sp1_array = np.vstack([sp1_array, next_info_1])
    r1_array = np.vstack([r1_array, reward_immed])

    action_new_0 = np.zeros((1,5),float)
    action_new_0[0,action_chosen_0] = 1.0
    a0_array = np.vstack([a0_array, action_new_0])

    action_new_1 = np.zeros((1,5),float)
    action_new_1[0,action_chosen_1] = 1.0
    a1_array = np.vstack([a1_array, action_new_1])

    ##### update the train network #####

    if h%100 == 0:
      W1_for_feed_train_a0 = sess.run(layer_1_a0[1], feed_dict={last_info_a0: [last_info_0]})
      b1_for_feed_train_a0 = sess.run(layer_1_a0[2], feed_dict={last_info_a0: [last_info_0]})
      W2_for_feed_train_a0 = sess.run(layer_out_a0[1], feed_dict={last_info_a0: [last_info_0]})
      b2_for_feed_train_a0 = sess.run(layer_out_a0[2], feed_dict={last_info_a0: [last_info_0]})

    current_state = next_state
    last_info_0 = next_info_0
    last_info_1 = next_info_1

    # truncate the size of data samples
    s0_array = truncate_dataset(s0_array,n_init_pool)
    r0_array = truncate_dataset(r0_array,n_init_pool)
    a0_array = truncate_dataset(a0_array,n_init_pool)
    sp0_array = truncate_dataset(sp0_array,n_init_pool)

    s1_array = truncate_dataset(s1_array,n_init_pool)
    r1_array = truncate_dataset(r1_array,n_init_pool)
    a1_array = truncate_dataset(a1_array,n_init_pool)
    sp1_array = truncate_dataset(sp1_array,n_init_pool)


    # re-sample the batch set

    seeds = random.sample(xrange(1,n_init_pool),n_batch_size)

    s0_batch = batch_select(s0_array,n_init_pool,n_batch_size,seeds)
    r0_batch = batch_select(r0_array,n_init_pool,n_batch_size,seeds)
    a0_batch = batch_select(a0_array,n_init_pool,n_batch_size,seeds)
    sp0_batch = batch_select(sp0_array,n_init_pool,n_batch_size,seeds)

    s1_batch = batch_select(s1_array,n_init_pool,n_batch_size,seeds)
    r1_batch = batch_select(r1_array,n_init_pool,n_batch_size,seeds)
    a1_batch = batch_select(a1_array,n_init_pool,n_batch_size,seeds)
    sp1_batch = batch_select(sp1_array,n_init_pool,n_batch_size,seeds)


  #############################################
  ##### Done the training for the agent 0 #####
  #############################################


  #####################################
  ##### Training only for agent 1 #####
  #####################################

  for h in range(h_train_step):

    numeric_loss_a1 = 0.0

    ##### training the NN #####
    for i in range(h_grad):

      numeric_loss_a1, _ = sess.run([loss_a1,train_step_a1],feed_dict={last_info_a1: s1_batch,
                                                                       rewards_a1: r1_batch,
                                                                       next_info_a1: sp1_batch,
                                                                       actions_a1: a1_batch,
                                                                       W1_train_a1: W1_for_feed_train_a1,
                                                                       b1_train_a1: b1_for_feed_train_a1,
                                                                       W2_train_a1: W2_for_feed_train_a1,
                                                                       b2_train_a1: b2_for_feed_train_a1})

    ##### Choose action #####

    # action for agent 1 is chosen from the current NN
    # action for agent 0 is chosen from the previous network

    action_chosen_1 = es_greedy(sess.run(Q_a1, feed_dict={last_info_a1: [last_info_1]}),r_explore)
    action_chosen_0 = es_greedy(sess.run(Q_a0, feed_dict={last_info_a0: [last_info_0]}),0.0)


    ##### sample the transition #####
    outcome_transition = transition_sample(current_state,
                                           (action_chosen_0,action_chosen_1),
                                           last_info_0,
                                           last_info_1,
                                           UAV_fire_extinguish)

    next_state = outcome_transition[0]
    (next_info_0,reward_immed) = outcome_transition[1]
    (next_info_1,reward_immed) = outcome_transition[2]

    if h%50 == 0: print(numeric_loss_a1)
    #print('(current_state)= ',current_state)
    #print('(joint action )= ',(action_chosen_0,action_chosen_1))
    #print('(next state   )= ',next_state)

    ##### increase sample dataset #####

    s0_array = np.vstack([s0_array, last_info_0])
    sp0_array = np.vstack([sp0_array, next_info_0])
    r0_array = np.vstack([r0_array, reward_immed])

    s1_array = np.vstack([s1_array, last_info_1])
    sp1_array = np.vstack([sp1_array, next_info_1])
    r1_array = np.vstack([r1_array, reward_immed])

    action_new_0 = np.zeros((1,5),float)
    action_new_0[0,action_chosen_0] = 1.0
    a0_array = np.vstack([a0_array, action_new_0])

    action_new_1 = np.zeros((1,5),float)
    action_new_1[0,action_chosen_1] = 1.0
    a1_array = np.vstack([a1_array, action_new_1])

    ##### update the train network #####

    if h%100 == 0:
      W1_for_feed_train_a1 = sess.run(layer_1_a1[1], feed_dict={last_info_a1: [last_info_1]})
      b1_for_feed_train_a1 = sess.run(layer_1_a1[2], feed_dict={last_info_a1: [last_info_1]})
      W2_for_feed_train_a1 = sess.run(layer_out_a1[1], feed_dict={last_info_a1: [last_info_1]})
      b2_for_feed_train_a1 = sess.run(layer_out_a1[2], feed_dict={last_info_a1: [last_info_1]})

    current_state = next_state
    last_info_0 = next_info_0
    last_info_1 = next_info_1

    # truncate the size of data samples
    s0_array = truncate_dataset(s0_array,n_init_pool)
    r0_array = truncate_dataset(r0_array,n_init_pool)
    a0_array = truncate_dataset(a0_array,n_init_pool)
    sp0_array = truncate_dataset(sp0_array,n_init_pool)

    s1_array = truncate_dataset(s1_array,n_init_pool)
    r1_array = truncate_dataset(r1_array,n_init_pool)
    a1_array = truncate_dataset(a1_array,n_init_pool)
    sp1_array = truncate_dataset(sp1_array,n_init_pool)


    # re-sample the batch set
    seeds = random.sample(xrange(1,n_init_pool),n_batch_size)

    s0_batch = batch_select(s0_array,n_init_pool,n_batch_size,seeds)
    r0_batch = batch_select(r0_array,n_init_pool,n_batch_size,seeds)
    a0_batch = batch_select(a0_array,n_init_pool,n_batch_size,seeds)
    sp0_batch = batch_select(sp0_array,n_init_pool,n_batch_size,seeds)

    s1_batch = batch_select(s1_array,n_init_pool,n_batch_size,seeds)
    r1_batch = batch_select(r1_array,n_init_pool,n_batch_size,seeds)
    a1_batch = batch_select(a1_array,n_init_pool,n_batch_size,seeds)
    sp1_batch = batch_select(sp1_array,n_init_pool,n_batch_size,seeds)


print("--- %s seconds ---" % (time.time() - start_time))
#visualize_scenario([0,15,1,1,1],100,UAV_fire_extinguish)
