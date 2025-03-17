import matplotlib.pyplot as plt
import numpy as np
import math
import json


class SimpleCity:
    def __init__(self, workable_tiles, center=(2,1)):
        self.workable_tiles = workable_tiles
        self.center = center

        self.pop = 1
        self.total_production = 0
        self.turn = 0
        self.basket = 0
        self.init_growth_reqs()

        self.worked_tiles = [False] * len(workable_tiles)
        self.worked_tiles[np.random.randint(len(workable_tiles))] = True


    def end_turn(self, worked_tiles):
        tot_yields = np.sum(self.available_tiles[worked_tiles], axis=0)
        food = tot_yields[0]
        prod = tot_yields[1]

        # food
        self.basket += food
        greq = self.growth_requirement[self.pop]
        if self.basket > greq:
            basket -= greq
            self.pop += 1
        # prod
        self.total_production += prod

        self.turn += 1


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





class City:
    def __init__(self, tiles=None, pop=1, housing=5, amenities=0, capital=True, center=None,
                 build_order=['scout', 'scout', 'settler', 'settler']):
        if center is None:
            self.center = (2, 1)
        if tiles is None:
            tiles = [
                (3, 1),
                (2, 2),
                (1, 3),
            ]
        self.pop = pop
        self.pophist = [pop]
        self.housing = housing
        self.amenities = amenities
        self.capital = capital
        self.tiles = tiles
        self.build_order = build_order
        self.cumprod = [0]
        self.basket = 0
        self.update_production()
        self.update_foodprod()
        self.init_prod_legend()
        self.init_settler_timing()
        self.remaining_settlers = self.settler_timing.copy()
        self.init_growth_reqs()


    def update_production(self):
        worked_tiles = self.tiles[:self.pop]
        self.ppt = np.sum(worked_tiles, axis=0)[1] + self.center[1]


    def update_foodprod(self):
        worked_tiles = self.tiles[:self.pop]
        self.fpt = np.sum(worked_tiles, axis=0)[0] + self.center[0]


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


    def init_prod_legend(self):
        with open('prod_legend.json') as file:
            legend = json.load(file)

        self.prod_legend = legend


    def init_settler_timing(self):
        bo = self.build_order

        if 'settler' not in bo:
            return None
        else:
            bo_costs = [self.prod_legend[item] for item in self.build_order]
            cum_cost = np.cumsum(bo_costs)
            settler_thresholds = cum_cost[np.where(np.array(bo)=='settler')]
        
        self.settler_timing = settler_thresholds


    def get_production(self, pop):
        worked_tiles = self.tiles[:pop]
        return np.sum(worked_tiles, axis=0)[1] + self.center[1]
        

    def get_foodprod(self, pop):
        worked_tiles = self.tiles[:pop]
        return np.sum(worked_tiles, axis=0)[0] + self.center[0]


    def get_growth_from_housing(self):
        excess_housing = self.housing - self.pop

        if excess_housing >= 2:
            return 1
        elif excess_housing == 1:
            return 0.5
        elif excess_housing <= 5:
            return 0
        else:
            return 0.25


    def get_amenity_requirement(self):
        requirement = math.ceil(self.pop / 2)
        if self.capital:
            requirement -= 1

        return requirement


    def get_satisfaction_level(self):
        amenity_excess = self.amenities - self.get_amenity_requirement()

        if amenity_excess >= 5:
            return 'ecstatic'
        elif amenity_excess >= 3:
            return 'happy'
        elif amenity_excess >= 0:
            return 'content'
        elif amenity_excess <= -7:
            return 'revolt'
        elif amenity_excess <= -5:
            return 'unrest'
        elif amenity_excess <= -3:
            return 'unhappy'
        elif amenity_excess <= -1:
            return 'displeased'
        else:
            return 'error'


    def get_satisfaction_growth(self):
        satisfaction = self.get_satisfaction_level()

        match satisfaction:
            case 'ecstatic' | 'happy' | 'content':
                return 1
            case 'displeased':
                return 0.85
            case 'unhappy' | 'unrest' | 'revolt':
                return 0.7


    def get_satisfaction_multiplier(self):
        satisfaction = self.get_satisfation_level()

        match satisfaction:
            case 'ecstatic':
                return 1.2
            case 'happy':
                return 1.1
            case 'content':
                return 1
            case 'displeased':
                return 0.9
            case 'unhappy':
                return 0.8
            case 'unrest':
                return 0.7
            case 'revolt':
                return 0.6


    def get_growth(self):
        excess_food = self.fpt - self.pop * 2
        housing_mult = self.get_growth_from_housing()
        amenities_mult = self.get_satisfaction_growth()

        growth = excess_food * (housing_mult + amenities_mult - 1)

        return growth


    def get_turns_to_growth(self):
        return (self.growth_requirement[self.pop] - self.basket) / self.get_growth()


    def end_turn(self, noprint=True):
        self.update_foodprod()
        self.update_production()
        
        # prod tracking
        self.cumprod.append(self.ppt) 
        if (self.cumprod[-1] > self.remaining_settlers[0]):
            self.pop -= 1
            del self.remaining_settlers[0]

        # growth calc
        self.pophist.append(self.pop)
        self.basket += self.get_growth() 
        greq = self.growth_requirement[self.pop]
        if self.basket >= greq:
            self.basket -= greq
            self.pop += 1

        if not noprint:
            self.update_foodprod()
            print(self)


    def get_prod_path(self):
        return np.cumsum(self.cumprod)


    def __str__(self, turn=None):
        if turn is None:
            return (
                f'Pop: {self.pop}\n'
                f'Worked tiles: {self.tiles[:self.pop]}\n'
                f'Yields: {self.fpt} food; {self.ppt} prod\n'
                f'Excess food: {self.fpt - self.pop * 2}\n'
                f'Growth: {self.get_growth()}\n'
                f'Multipliers: Amenities: {self.get_satisfaction_growth()} '
                f'Housing: {self.get_growth_from_housing()}\n'
                f'Basket: {self.basket}\n'
                f'Turns to growth: {self.get_turns_to_growth()}'
                f'Total prod: {self.get_prod_path()}'
            )

        else:
            pop = self.pophist[turn]
            return (
                f'T{turn} status:'
                f'Pop: {pop}\n'
                f'Yields: {self.get_foodprod(pop)} food; {self.get_production(pop)} prod\n'
                f'Worked tiles: {self.tiles[:pop]}'
            )


    def print_timeline(self):
        for i, era in enumerate(np.unique(self.pophist)):
            where = np.where(np.array(self.pophist)==era)[0]
            cprod = np.cumsum(self.cumprod)

            if i == 0:
                segment = cprod[where[0]: where[-1]+1]
                xaxis = list(range(len(cprod)))[where[0]: where[-1]+1]
            else:
                segment = cprod[where[0]-1: where[-1]+1]
                xaxis = list(range(len(cprod)))[where[0]-1: where[-1]+1]

            plt.plot(xaxis, segment)

            



    def turn_report(self):
        print(f'Yields: {self.ppt} prod & {self.fpt} food\n')
