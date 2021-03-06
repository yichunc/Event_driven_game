h_step_for_gradient = 50
h_train_step = 500 * h_step_for_gradient
h_grad = 100
r_explore = 0.4
n_upper_size = 20000


rate = UAV_fire_extinguish.e_fire[2][0]
task_parameter = [0.2, 0.0, 0.0]

for task in range(3):

  print("task = ", task)

  ##### Add initial samples for each task

  rate_task = task_parameter[task]
  UAV_fire_extinguish.e_fire[2][0] = rate_task
  rate = UAV_fire_extinguish.e_fire[2][0]

  current_state = [0,n_w**2-1,1,1,1]
  next_state = 0
  last_info_0 = [0,0,3,3,1,1,1,1]
  last_info_1 = [0,0,3,3,1,1,1,1]

  print("Start to self play for task ", task)

  it_time = 2


  for iteration_times in range(it_time):
    print("iteration times = ", iteration_times)
    print("--- %s seconds ---" % (time.time() - start_time))
    ##############################
    ###### Only for agent 1 ######
    ##############################


    for h in range(h_train_step):

      numeric_loss_a0 = 0.0

      ##### training the NN for every 50 steps of self-playing #####
      if h % h_step_for_gradient == 0:

        for i in range(h_grad):

          numeric_loss_a0, _ = sess.run([loss_a0,train_step_a0],feed_dict={last_info_a0: s0_batch_0,
                                                                           rewards_a0: r0_batch_0,
                                                                           next_info_a0: sp0_batch_0,
                                                                           actions_a0: a0_batch_0,
                                                                           W1_train_a0: W1_for_feed_train_a0,
                                                                           b1_train_a0: b1_for_feed_train_a0,
                                                                           W2_train_a0: W2_for_feed_train_a0,
                                                                           b2_train_a0: b2_for_feed_train_a0})


      ##### Choose action #####

      # action for agent 0 is chosen from the current NN
      # action for agent 1 is chosen randomly in the first iteration,
      # otherwise it is learned from previous network

      action_chosen_0 = es_greedy(sess.run(Q_a0, feed_dict={last_info_a0: [[rate] +last_info_0]}),r_explore)
      if iteration_times + task == 0:
        action_chosen_1 = random.randint(0,4)
      else:
        action_chosen_1 = es_greedy(sess.run(Q_a1, feed_dict={last_info_a1: [[rate] +last_info_1]}),0.0)

      ##### sample the transition #####
      outcome_transition = transition_sample(current_state,
                                             (action_chosen_0,action_chosen_1),
                                             last_info_0,
                                             last_info_1,
                                             UAV_fire_extinguish)

      next_state = outcome_transition[0]
      (next_info_0,reward_immed) = outcome_transition[1]
      (next_info_1,reward_immed) = outcome_transition[2]
      if h%(20*h_step_for_gradient) == 0: print(h,numeric_loss_a0)


      ##### increase sample dataset #####

      s0_array_0 = np.vstack([s0_array_0, [rate] + last_info_0])
      sp0_array_0 = np.vstack([sp0_array_0, [rate] + next_info_0])
      r0_array_0 = np.vstack([r0_array_0, reward_immed])

      s1_array_0 = np.vstack([s1_array_0, [rate] + last_info_1])
      sp1_array_0 = np.vstack([sp1_array_0, [rate] + next_info_1])
      r1_array_0 = np.vstack([r1_array_0, reward_immed])

      action_new_0 = np.zeros((1,5),float)
      action_new_0[0,action_chosen_0] = 1.0
      a0_array_0 = np.vstack([a0_array_0, action_new_0])

      action_new_1 = np.zeros((1,5),float)
      action_new_1[0,action_chosen_1] = 1.0
      a1_array_0 = np.vstack([a1_array_0, action_new_1])

      current_state = next_state
      last_info_0 = next_info_0
      last_info_1 = next_info_1

      ##### update the target network #####

      if h% (h_step_for_gradient * 50) == 0:
        W1_for_feed_train_a0 = sess.run(layer_1_a0[1], feed_dict={last_info_a0: [[rate] +last_info_0]})
        b1_for_feed_train_a0 = sess.run(layer_1_a0[2], feed_dict={last_info_a0: [[rate] +last_info_0]})
        W2_for_feed_train_a0 = sess.run(layer_out_a0[1], feed_dict={last_info_a0: [[rate] +last_info_0]})
        b2_for_feed_train_a0 = sess.run(layer_out_a0[2], feed_dict={last_info_a0: [[rate] +last_info_0]})


      ##### update the dataset #####
      if h % h_step_for_gradient == 0:

        # truncate the size of data samples
        s0_array_0 = truncate_dataset(s0_array_0,n_upper_size)
        r0_array_0 = truncate_dataset(r0_array_0,n_upper_size)
        a0_array_0 = truncate_dataset(a0_array_0,n_upper_size)
        sp0_array_0 = truncate_dataset(sp0_array_0,n_upper_size)

        s1_array_0 = truncate_dataset(s1_array_0,n_upper_size)
        r1_array_0 = truncate_dataset(r1_array_0,n_upper_size)
        a1_array_0 = truncate_dataset(a1_array_0,n_upper_size)
        sp1_array_0 = truncate_dataset(sp1_array_0,n_upper_size)


        # re-sample the batch set
        seeds = random.sample(xrange(1,len(s0_array_0)),n_batch_size)

        s0_batch_0 = batch_select(s0_array_0,n_batch_size,seeds)
        r0_batch_0 = batch_select(r0_array_0,n_batch_size,seeds)
        a0_batch_0 = batch_select(a0_array_0,n_batch_size,seeds)
        sp0_batch_0 = batch_select(sp0_array_0,n_batch_size,seeds)

        s1_batch_0 = batch_select(s1_array_0,n_batch_size,seeds)
        r1_batch_0 = batch_select(r1_array_0,n_batch_size,seeds)
        a1_batch_0 = batch_select(a1_array_0,n_batch_size,seeds)
        sp1_batch_0 = batch_select(sp1_array_0,n_batch_size,seeds)


    #############################################
    ##### Done the training for the agent 0 #####
    #############################################


    #####################################
    ##### Training only for agent 1 #####
    #####################################

    for h in range(h_train_step):

      numeric_loss_a1 = 0.0

      ##### training the NN #####

      if h % h_step_for_gradient == 0:
        for i in range(h_grad):

          numeric_loss_a1, _ = sess.run([loss_a1,train_step_a1],feed_dict={last_info_a1: s1_batch_1,
                                                                           rewards_a1: r1_batch_1,
                                                                           next_info_a1: sp1_batch_1,
                                                                           actions_a1: a1_batch_1,
                                                                           W1_train_a1: W1_for_feed_train_a1,
                                                                           b1_train_a1: b1_for_feed_train_a1,
                                                                           W2_train_a1: W2_for_feed_train_a1,
                                                                           b2_train_a1: b2_for_feed_train_a1})

      ##### Choose action #####

      # action for agent 1 is chosen from the current NN
      # action for agent 0 is chosen from the previous network

      action_chosen_1 = es_greedy(sess.run(Q_a1, feed_dict={last_info_a1: [[rate] +last_info_1]}),r_explore)
      action_chosen_0 = es_greedy(sess.run(Q_a0, feed_dict={last_info_a0: [[rate] +last_info_0]}),0.0)


      ##### sample the transition #####
      outcome_transition = transition_sample(current_state,
                                             (action_chosen_0,action_chosen_1),
                                             last_info_0,
                                             last_info_1,
                                             UAV_fire_extinguish)

      next_state = outcome_transition[0]
      (next_info_0,reward_immed) = outcome_transition[1]
      (next_info_1,reward_immed) = outcome_transition[2]
      if h%(20*h_step_for_gradient) == 0: print(h,numeric_loss_a1)


      ##### increase sample dataset #####

      s0_array_1 = np.vstack([s0_array_1, [rate] + last_info_0])
      sp0_array_1 = np.vstack([sp0_array_1, [rate] + next_info_0])
      r0_array_1 = np.vstack([r0_array_1, reward_immed])

      s1_array_1 = np.vstack([s1_array_1, [rate] + last_info_1])
      sp1_array_1 = np.vstack([sp1_array_1, [rate] + next_info_1])
      r1_array_1 = np.vstack([r1_array_1, reward_immed])

      action_new_0 = np.zeros((1,5),float)
      action_new_0[0,action_chosen_0] = 1.0
      a0_array_1 = np.vstack([a0_array_1, action_new_0])

      action_new_1 = np.zeros((1,5),float)
      action_new_1[0,action_chosen_1] = 1.0
      a1_array_1 = np.vstack([a1_array_1, action_new_1])

      current_state = next_state
      last_info_0 = next_info_0
      last_info_1 = next_info_1

      ##### update the train network #####

      if h% (h_step_for_gradient * 50) == 0:
        W1_for_feed_train_a1 = sess.run(layer_1_a1[1], feed_dict={last_info_a1: [[rate] + last_info_1]})
        b1_for_feed_train_a1 = sess.run(layer_1_a1[2], feed_dict={last_info_a1: [[rate] + last_info_1]})
        W2_for_feed_train_a1 = sess.run(layer_out_a1[1], feed_dict={last_info_a1: [[rate] + last_info_1]})
        b2_for_feed_train_a1 = sess.run(layer_out_a1[2], feed_dict={last_info_a1: [[rate] + last_info_1]})


      ##### update the dataset #####
      if h % h_step_for_gradient == 0:

        # truncate the size of data samples
        s0_array_1 = truncate_dataset(s0_array_1,n_upper_size)
        r0_array_1 = truncate_dataset(r0_array_1,n_upper_size)
        a0_array_1 = truncate_dataset(a0_array_1,n_upper_size)
        sp0_array_1 = truncate_dataset(sp0_array_1,n_upper_size)

        s1_array_1 = truncate_dataset(s1_array_1,n_upper_size)
        r1_array_1 = truncate_dataset(r1_array_1,n_upper_size)
        a1_array_1 = truncate_dataset(a1_array_1,n_upper_size)
        sp1_array_1 = truncate_dataset(sp1_array_1,n_upper_size)


        # re-sample the batch set
        seeds = random.sample(xrange(1,len(s0_array_1)),n_batch_size)

        s0_batch_1 = batch_select(s0_array_1,n_batch_size,seeds)
        r0_batch_1 = batch_select(r0_array_1,n_batch_size,seeds)
        a0_batch_1 = batch_select(a0_array_1,n_batch_size,seeds)
        sp0_batch_1 = batch_select(sp0_array_1,n_batch_size,seeds)

        s1_batch_1 = batch_select(s1_array_1,n_batch_size,seeds)
        r1_batch_1 = batch_select(r1_array_1,n_batch_size,seeds)
        a1_batch_1 = batch_select(a1_array_1,n_batch_size,seeds)
        sp1_batch_1 = batch_select(sp1_array_1,n_batch_size,seeds)