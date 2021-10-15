import json

import numpy as np
import sumo_rl
import supersuit as ss
from array2gif import write_gif
from custom.utils import load_cfg
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.vec_env import VecMonitor

# NOTE: Don't forget to execute this script from 1 directory above experiments/

if __name__ == '__main__':
    # TODO: store stuff in json maybe
    cfg = load_cfg("custom/config.json")

    n_evaluations = 20
    n_agents = 1
    n_envs = 1  # You can not use LIBSUMO if using more than one env
    train_timesteps = int(1e3)
    eval_timesteps = int(1e3)

    env = sumo_rl.parallel_env(net_file='nets/4x4-Lucas/4x4.net.xml',
                route_file='nets/4x4-Lucas/4x4c1c2c1c2.rou.xml',
                out_csv_name='outputs/4x4grid/test',
                use_gui=True,
                num_seconds=train_timesteps)

    #env = ss.frame_stack_v1(env, 3)
    env = ss.pettingzoo_env_to_vec_env_v0(env)
    env = ss.concat_vec_envs_v0(env, n_envs, num_cpus=1, base_class='stable_baselines3')
    env = VecMonitor(env)

    eval_env = sumo_rl.parallel_env(net_file='nets/4x4-Lucas/4x4.net.xml',
                        route_file='nets/4x4-Lucas/4x4c1c2c1c2.rou.xml',
                        out_csv_name='outputs/4x4grid/test',
                        use_gui=False,
                        num_seconds=eval_timesteps)

    #eval_env = ss.frame_stack_v1(eval_env, 3)
    eval_env = ss.pettingzoo_env_to_vec_env_v0(eval_env)
    eval_env = ss.concat_vec_envs_v0(eval_env, 1, num_cpus=1, base_class='stable_baselines3')
    eval_env = VecMonitor(eval_env)

    eval_freq = int(train_timesteps / n_evaluations)
    eval_freq = 1000 # max(eval_freq // (n_envs*n_agents), 1)

    # TODO: replace with custom policy
    model = PPO("MlpPolicy", env, verbose=3, gamma=0.95, n_steps=256, ent_coef=0.0905168, learning_rate=0.00062211, vf_coef=0.042202, max_grad_norm=0.9, gae_lambda=0.99, n_epochs=5, clip_range=0.3, batch_size=256)
    eval_callback = EvalCallback(eval_env, best_model_save_path='./logs/', log_path='./logs/', eval_freq=eval_freq, deterministic=True, render=False)
    model.learn(total_timesteps=train_timesteps, callback=eval_callback)
    # save a learned model
    save_path = "outputs/" + cfg.get("model_name")
    model.save(save_path)


    print("Finished training model, evaluating..............................")

    del model

    model = PPO.load(save_path)

    mean_reward, std_reward = evaluate_policy(model, eval_env, n_eval_episodes=10)

    print(f"Reward Mean = {mean_reward:.3f}")
    print(f"Reward Std Dev = {std_reward:.3f}")

    """ render_env = sumo_rl.env(net_file='nets/4x4-Lucas/4x4.net.xml',
                        route_file='nets/4x4-Lucas/4x4c1c2c1c2.rou.xml',
                        out_csv_name='outputs/4x4grid/test',
                        use_gui=False,
                        num_seconds=80000)

    render_env = render_env.parallel_env()
    render_env = ss.color_reduction_v0(render_env, mode='B')
    render_env = ss.resize_v0(render_env, x_size=84, y_size=84)
    render_env = ss.frame_stack_v1(render_env, 3)

    obs_list = []
    i = 0
    render_env.reset()


    while True:
        for agent in render_env.agent_iter():
            observation, _, done, _ = render_env.last()
            action = model.predict(observation, deterministic=True)[0] if not done else None

            render_env.step(action)
            i += 1
            if i % (len(render_env.possible_agents)) == 0:
                obs_list.append(np.transpose(render_env.render(mode='rgb_array'), axes=(1, 0, 2)))
        render_env.close()
        break

    print('Writing gif')
    write_gif(obs_list, 'kaz.gif', fps=15) """
