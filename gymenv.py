import numpy as np
import gymnasium as gym

class SB3Wrap(gym.Wrapper):
    def __init__(self, gym_env):
        super().__init__(gym_env)
        # self.env = gym_env
        # self.action_space = gym_env.action_space
        # self.observation_space = gym_env.observation_space

    def reset(self, **kwargs):
        obs, _ = self.env.reset(**kwargs)

        return obs, {}
    
    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        done = terminated or truncated
        
        return obs, reward, done, info

class City(gym.Env):

    def __init__(self, workable_tiles, center=(2,1)):
        self.workable_tiles = np.array(workable_tiles, dtype=np.int32).reshape(-1,2)
        self.max_tiles = len(workable_tiles)
        self.center = np.array(center)

        self.population = 1
        self.total_production = 0
        self.turn = 0
        self.episode_count = 0
        self.basket = 0
        self.init_growth_reqs()

        self.pophist = [1]
        self.prodhist = [0]

        self.observation_space = gym.spaces.Dict({
            "population": gym.spaces.Discrete(20),
            "turn": gym.spaces.Discrete(141),
            "workable_tiles": gym.spaces.Box(
                low=np.zeros((self.max_tiles, 2)),
                high=np.ones((self.max_tiles, 2)) * 5,
                dtype=np.int32
            ),
            "worked_tiles": gym.spaces.MultiBinary(self.max_tiles),
            "yields": gym.spaces.Box(
                low=np.ones(2), 
                high=np.sum(self.workable_tiles, axis=0),
                dtype=np.int32
            ),
            "basket": gym.spaces.Box(low=0, high=100, shape=(1,), dtype=np.float32)
        })

        self.action_space = gym.spaces.Box(
            low=np.ones(self.max_tiles, dtype=np.float32)*-1,
            high=np.ones(self.max_tiles, dtype=np.float32)
        )

        self.worked_tiles = np.array([False] * self.max_tiles)
        self.worked_tiles[np.random.randint(self.max_tiles)] = True
        self.worked_hist = [self.worked_tiles]


    def _process_action(self, action):
        try:
            n = self.population
            indices = np.argsort(action)[-n:]

            worked_tiles = np.zeros_like(action, dtype=bool)
            worked_tiles[indices] = True
            self.worked_hist.append(worked_tiles)
        except Exception as e:
            raise ValueError(e)

        return worked_tiles


    def _get_obs(self):
        yields = np.sum(self.workable_tiles[self.worked_tiles], axis=0) + self.center
        return {"population": self.population,
                "turn": self.turn,
                "workable_tiles": np.array(self.workable_tiles, dtype=np.int32),
                "worked_tiles": np.array(self.worked_tiles, dtype=np.int8),
                "yields": np.array(yields, dtype=np.int32),
                "basket": np.array([self.basket], dtype=np.float32)
                }


    def step(self, action):
        self.worked_tiles = self._process_action(action)
        tot_yields = np.sum(self.workable_tiles[self.worked_tiles], axis=0)
        food = tot_yields[0]
        prod = tot_yields[1]

        # food
        self.basket += food
        greq = self.growth_requirement[self.population]
        if self.basket > greq:
            self.basket -= greq
            self.population += 1
        self.pophist.append(self.population)
        # prod
        self.total_production+= prod
        self.prodhist.append(prod)
        self.turn += 1

        terminated = True if self.total_production >= 140 else False
        observation = self._get_obs()
        reward = -self.turn if terminated else 0
        truncated = False
        
        if terminated:
            self.episode_count += 1
            info = {
                "pophist": self.pophist, 
                "prodhist": self.prodhist,
                "tilehist": self.worked_hist
                } 
        else:
            info = {}

        return observation, reward, terminated, truncated, info


    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.population = 1
        self.pophist = [1]
        self.total_production = 0
        self.prodhist = [0]
        self.basket = 0
        self.turn = 0

        self.worked_tiles = np.array([False] * self.max_tiles)
        self.worked_tiles[np.random.randint(self.max_tiles)] = True
        self.worked_hist = [self.worked_tiles]

        return self._get_obs(), {}


    def init_growth_reqs(self):
            self.growth_requirement = {
                1: 15,
                2: 24,
                3: 33,
                4: 44,
                5: 55,
                6: 66, 
                7: 77
            }

