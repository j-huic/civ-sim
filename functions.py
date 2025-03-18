from classes import City
import pandas as pd
import numpy as np
import copy
from tqdm import tqdm
import random
import matplotlib.pyplot as plt
import gymenv

def sim_to_npop(n, tiles):
    a = City(tiles=tiles)
    cont = True
    while cont:
        a.end_turn()
        if a.pop == n:
            cont = False
    
    return np.cumsum(a.cumprod)


def sim_n_turns(n, tilepath):
    city = City(tiles=tilepath)
    for i in range(n):
        city.end_turn()
    
    return copy.deepcopy(city)


def get_random_tilepath(tilespace, n):
    tilepath = []
    for i in range(n):
        tilepath.append(random.choice(tilespace))

    return tilepath


def plot_trajectories(prodpaths, n, maxturns=None, buildorder=None):
    if maxturns is None:
        maxturns = len(prodpaths[0] - 1)

    plt.figure(figsize=(15,15))
    for path in prodpaths[:n]:
        plt.plot(path[:maxturns])
    
    if buildorder is not None:
        for level in np.cumsum(buildorder):
            plt.axhline(y=level, color='red', linestyle='--')

    plt.grid(True, alpha=0.3)
    plt.show()


def first_to_xprod(df, x):
    for col in df.columns:
        good_paths = df[col] >= x
        if sum(good_paths) > 0:
            good_indexes = df.index[good_paths]
            return good_indexes
        

def sim_n_cities(n, tiles, turns):
    cities = []
    for i in tqdm(range(n)):
        tilepath = get_random_tilepath(tiles, 10)
        city = sim_n_turns(turns, tilepath)
        cities.append(copy.deepcopy(city))

    return cities


def get_possible_paths(tiles, n, paths=None):
    if n == 0: return paths 

    if paths is None:
        paths = []
        for tile in tiles:
            paths.append([tile])
        return get_possible_paths(tiles, n - 1, paths)
    else:
        newpaths = []
        for path in paths:
            for tile in tiles:
                newpaths.append(path + [tile])
        return get_possible_paths(tiles, n - 1, newpaths)
    

def sim_episode(model, env=None, deterministic=True):
    if env is None:
        env = model.get_env()
    else:
        env = gymenv.SB3Wrap(env)
        
    obs = env.reset()

    while True:
        action, _ = model.predict(obs, deterministic=deterministic)
        obs, _, done, info = env.step(action)

        if done:
            env.reset()
            return info
        

def tilehist_print(episode, tiles):
    tilehist = episode['tilehist']
    tiles = np.array(tiles)

    for index, wt in enumerate(tilehist):
        if index == 0:
            print(f'Turn {index}: ')
            print(list((int(a),int(b)) for a,b in tiles[wt]))
            continue
        
        l = len(tilehist[0])
        if sum(wt == tilehist[index - 1]) == l:
            continue
        else:
            print(f'Turn {index}: ')
            print(list((int(a),int(b)) for a,b in tiles[wt]))