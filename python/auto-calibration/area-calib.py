#!/usr/bin/env python3

import pandas as pd
import random
import requests
import time
import math
from io import BytesIO
import rasterio
import sys

# This script fits calibration data against CLoudRF area calculations, and uses a genetic algorithm 
# to calibrate the settings.

# The number of area calls required will be POPULATION_COUNT X (MAX_GENERATION + 1)

DATA_CSV = 'data.csv'

POPULATION_COUNT = 10 # The number of configs in a generation

MAX_GENERATION = 10 # The number of generations to run for
ELITE_COUNT = 3 # The number of configs carry over to the next generation, choosen by best fit

DISCRETE_MUTATION_RATE = 0.1
CONTINUOUS_MUTATION_VARIABILITY = 0.2

API_KEY = ''
API = ''

REQUEST_DELAY_S = 0.1

DISABLE_SSL_VERIFICATION=False

CLUTTER_PROFILE = 'AreaCalibPy'

if DISABLE_SSL_VERIFICATION:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

config_spec = {
    'network': {'kind': 'fixed', 'value': 'CALIBRATION'},

    'transmitter.lat': {'kind': 'fixed', 'value': 53.394753},
    'transmitter.lon': {'kind': 'fixed', 'value': -1.755654},
    'transmitter.alt': {'kind': 'fixed', 'value': 15},
    'transmitter.frq': {'kind': 'fixed', 'value': 700},
    'transmitter.txw': {'kind': 'fixed', 'value': 3.0},

    'antenna.txg': {'kind': 'fixed', 'value': 2.15},
    'antenna.txl': {'kind': 'fixed', 'value': 0},
    'antenna.ant': {'kind': 'fixed', 'value': 1},
    'antenna.azi': {'kind': 'fixed', 'value': 285},
    'antenna.tlt': {'kind': 'fixed', 'value': 0},
    'antenna.pol': {'kind': 'fixed', 'value': 'v'},

    'receiver.alt': {'kind': 'fixed', 'value': 1},
    'receiver.rxg': {'kind': 'fixed', 'value': 1},
    'receiver.rxs': {'kind': 'fixed', 'value': -140},

    'model.pm': {'kind': 'fixed', 'value': 10},
    'model.pe': {'kind': 'discrete', 'options': [1, 2, 3]},
    'model.ked': {'kind': 'fixed', 'value': 2},
    'model.rel': {'kind': 'continuous', 'min': 50, 'max': 99, 'cast': int},

    'environment.clt': {'kind': 'fixed', 'value': CLUTTER_PROFILE + '.clt'},
    'environment.elevation': {'kind': 'fixed', 'value': 2},
    'environment.landcover': {'kind': 'fixed', 'value': 1},
    'environment.buildings': {'kind': 'fixed', 'value': 1},

    'output.out': {'kind': 'fixed', 'value': 2},
    'output.col': {'kind': 'fixed', 'value': 9},
    'output.rad': {'kind': 'fixed', 'value': 5},
    'output.res': {'kind': 'fixed', 'value': 10},

    'clutter.building.attenuation': {'kind': 'continuous', 'min': 0.01, 'max': 10.0}, 
    'clutter.trees.attenuation': {'kind': 'continuous', 'min': 0.0, 'max': 1.5}, 
    'clutter.trees.height': {'kind': 'continuous', 'min': 0.5, 'max': 30}, 
}

status_message_depth = 0

def clear_status_message(depth=0):
    global status_message_depth
    while status_message_depth > depth:
        sys.stdout.write('\033[F\033[K')
        status_message_depth -= 1
    sys.stdout.flush()
    status_message_depth = depth


def print_status_message(message, depth=0):
    global status_message_depth
    clear_status_message(depth=depth)
    sys.stdout.write(message)
    sys.stdout.write('\n')
    sys.stdout.flush()
    status_message_depth += 1

def print_message(message):
    clear_status_message()
    sys.stdout.write(message)
    sys.stdout.write('\n')
    sys.stdout.flush()

def create_clutter_profile(config):    
    headers = {
        'key': API_KEY
    }

    lines = [
        f"99:3:{config['clutter.building.attenuation']}",
        '1:1:0.0',
        f"2:{config['clutter.trees.height']}:{config['clutter.trees.attenuation']}",
        '3:1:0.0',
        '4:1:0.0',
        '5:1:0.0',
        '6:3:0.0',
        '7:1:0.0',
        '8:1:0',
        '9:1:0',
        '10:0:0',
        '11:6:0.1:Obstacle+1:#ea580c',
        '12:8:0.2:Obstacle+2:#f43f5e',
        '13:3:0.25:Obstacle+3:#a3e635',
        '14:4:0.3:Obstacle+4:#67e8f9',
        '15:5:0.4:Obstacle+5:#14b8a6',
        '16:6:0.5:Obstacle+6:#16a34a',
        '17:7:0.6:Obstacle+7:#a78bfa',
        '18:8:0.7:Obstacle+8:#4338ca',
        '19:3:0.8:Obstacle+9:#075985',
    ]

    data = {
        'save': CLUTTER_PROFILE,
        'values': '\n'.join(lines)
    }

    response = requests.post(f"{API}/API/clutter/index2.php", data=data, headers=headers, verify=not DISABLE_SSL_VERIFICATION)
    response.raise_for_status()

    response = response.json()

    if response['status'] != 200:
        raise RuntimeError(response['message'])

def build_area_request(config):
    request = {}

    for key, value_spec in config_spec.items():
        value = None

        if value_spec['kind'] == 'continuous' or value_spec['kind'] == 'discrete':
            value = config[key]
        elif value_spec['kind'] == 'fixed':
            value = value_spec['value']
        
        if 'cast' in value_spec:
            value = value_spec['cast'](value)

        keys = key.split('.')

        if (keys[0] == 'clutter'):
            continue

        dict = request
        for key in keys[:-1]:
            if key not in dict:
                dict[key] = {}
            dict = dict[key]
        dict[keys[-1]] = value

    return request

def send_area_request(request):
    headers = {
        'key': API_KEY
    }

    time.sleep(REQUEST_DELAY_S)

    response = requests.post(f"{API}/area", json=request, headers=headers, verify=not DISABLE_SSL_VERIFICATION)
    response.raise_for_status()

    return response.json()

def calculate_config_error(config, batch):

    total_error = 0
    min_error = None
    max_error = None

    print_status_message('Creating clutter profile', depth=1)
    create_clutter_profile(config)

    request = build_area_request(config)

    print_status_message('Performing area calculation', depth=1)
    response = send_area_request(request)

    tiff_url = response['kmz'][:-3] + 'tiff'

    print_status_message('Downloading area output tiff', depth=1)
    response = requests.get(tiff_url, verify=not DISABLE_SSL_VERIFICATION)
    response.raise_for_status()

    with rasterio.open(BytesIO(response.content)) as tiff:
        for i, row in batch.iterrows():
            print_status_message(f'Calculating error for data {i:>{len(str(len(batch)))}}/{len(batch)}', depth=1)
            lat = row['latitude']
            lon = row['longitude']

            expected = row['received_power']

            y, x = tiff.index(lon, lat)

            actual = None

            if 0 <= x < tiff.width and 0 <= y < tiff.height:
                red = int(tiff.read()[0, y, x])
                if red != 0:
                    actual = -red

            if actual == None:
                actual = request['receiver']['rxs']

            error = actual - expected
            total_error += abs(error)

            min_error = error if min_error == None else min(error, min_error)
            max_error = error if max_error == None else max(error, max_error)

    return min_error, total_error / len(batch), max_error

def calculate_config_fitness(config):
    return math.exp(-config['mean_error'])

def select_parent_configs(population):
    count = 2 * POPULATION_COUNT
    total_fitness = sum([config['fitness'] for config in population])
    step = total_fitness / count
    start_point = random.uniform(0, step)

    selected_indices = []

    cumulative_fitness = 0.0
    parent_index = 0
    for i in range(0, count):
        while cumulative_fitness < start_point + step * i:
            cumulative_fitness += population[parent_index]['fitness']
            parent_index += 1
        
        selected_indices.append(parent_index - 1)
    
    return selected_indices

def generate_random_config():
    config = {}
    for key, value_spec in config_spec.items():
        if value_spec['kind'] == 'continuous':
            config[key] = random.uniform(value_spec['min'], value_spec['max'])
        elif value_spec['kind'] == 'discrete':
            config[key] = random.choice(value_spec['options'])
    return config


def crossover_configs(a, b):
    config = {}
    for key, value_spec in config_spec.items():
        if value_spec['kind'] == 'continuous':
            config[key] = random.uniform(a[key], b[key])
        elif value_spec['kind'] == 'discrete':
            config[key] = random.choice([a[key], b[key]])
    return config

def mutate_config(config):

    mutant = {}
    for key, value_spec in config_spec.items():
        if value_spec['kind'] == 'continuous':
            mutant[key] = config[key] + random.normalvariate(0, CONTINUOUS_MUTATION_VARIABILITY * (value_spec['max'] - value_spec['min']))
            mutant[key] = max(value_spec['min'], min(mutant[key], value_spec['max']))
        elif value_spec['kind'] == 'discrete':
            if random.uniform(0, 1) < DISCRETE_MUTATION_RATE:
                mutant[key] = random.choice(value_spec['options'])
            else:
                mutant[key] = config[key]
    return mutant

def print_config(config):
    print_message(f"    Min Error : {config['min_error']:>8}")
    print_message(f"   Mean Error : {config['mean_error']:>8.2g}")
    print_message(f"    Max Error : {config['max_error']:>8}")
    print_message(f"   Prop Model : {config['model.pe']:>8}")
    print_message(f"  Reliability : {config['model.rel']:>8.2g}")
    print_message(f"Building Attn : {config['clutter.building.attenuation']:>8.6g}")
    print_message(f"    Tree Attn : {config['clutter.trees.attenuation']:>8.6g}")
    print_message(f"  Tree Height : {config['clutter.trees.height']:>8.2g}")


def load_csv(path):
    required_columns = {'latitude', 'longitude', 'received_power'}

    df = pd.read_csv(path)

    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f'Missing expected columns: {missing_columns}')
    
    df = df [[col for col in df.columns if col in required_columns]]

    try:
        df = df.apply(pd.to_numeric, errors='raise')
    except Exception as e:
        raise ValueError(f'Non-numeric data found: {e}')
    
    return df

if __name__ == '__main__':
    dataset = load_csv(DATA_CSV)

    print_message(f"loaded dataset with {len(dataset)} rows")

    population = [generate_random_config() for _ in range(0, POPULATION_COUNT)]

    for i, config in enumerate(population):
        print_status_message(f'Calculating error for config {i+1:>{len(str(POPULATION_COUNT))}}/{POPULATION_COUNT}')
        config['min_error'], config['mean_error'], config['max_error'] = calculate_config_error(config, dataset)
        config['fitness'] = calculate_config_fitness(config)
        print_message(f"Config {i+1:>{len(str(POPULATION_COUNT))}}/{POPULATION_COUNT} error:    min {config['min_error']:>4}    mean {config['mean_error']:>4.2g}    max {config['max_error']:>4}")

    for generation in range(0, MAX_GENERATION):

        print_status_message(f'Sorting config population')
        population = sorted(population, key=lambda config: config['fitness'])
        worst = population[0]
        best = population[-1]
        print_message(f"")
        print_message(f"Generation {generation:>{len(str(MAX_GENERATION))}}/{MAX_GENERATION}")
        print_message(f"")
        print_message(f"  Worst Config")
        print_config(worst)
        print_message(f"")
        print_message(f"  Best Config")
        print_config(best)
        print_message(f"")

        print_status_message(f'Selecting parent configs')
        parent_indices = select_parent_configs(population)
        random.shuffle(parent_indices)

        parent_index_pairs = [(parent_indices[2 * i], parent_indices[2 * i + 1])  for i in range(0, POPULATION_COUNT)]

        print_status_message(f'Creating child configs')
        children = [crossover_configs(population[a], population[b]) for (a, b) in parent_index_pairs]
        print_status_message(f'Mutating child configs')
        children = [mutate_config(config) for config in children]

        for i, config in enumerate(children):
            print_status_message(f'Calculating error for config {i+1:>{len(str(POPULATION_COUNT))}}/{POPULATION_COUNT}')
            config['min_error'], config['mean_error'], config['max_error'] = calculate_config_error(config, dataset)
            config['fitness'] = calculate_config_fitness(config)
            print_message(f"Config {i+1:>{len(str(POPULATION_COUNT))}}/{POPULATION_COUNT} error:    min {config['min_error']:>4}    mean {config['mean_error']:>4.2g}    max {config['max_error']:>4}")

        children = sorted(children, key=lambda config: config['fitness'])

        population = population[-ELITE_COUNT:]
        children = children[-(POPULATION_COUNT-ELITE_COUNT):]
        population.extend(children)

    population = sorted(population, key=lambda config: config['fitness'])
    worst = population[0]
    best = population[-1]
    print_message(f"")
    print_message(f"Generation {MAX_GENERATION}/{MAX_GENERATION}")
    print_message(f"")
    print_message(f"  Worst Config")
    print_config(worst)
    print_message(f"")
    print_message(f"  Best Config")
    print_config(best)
    print_message(f"")
