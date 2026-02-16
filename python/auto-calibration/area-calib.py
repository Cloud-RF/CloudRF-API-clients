#!/usr/bin/env python3

import argparse
import pandas as pd
import random
import requests
import time
import math
from io import BytesIO
import rasterio
import sys
import urllib3
import json

CLUTTER_PROFILE = 'AreaCalibPy'

config_spec = {
    'network': {'kind': 'fixed', 'value': 'CALIBRATION'},

    # Transmitter values come from the template file
    'transmitter.lat': {'kind': 'fixed'},
    'transmitter.lon': {'kind': 'fixed'},
    'transmitter.alt': {'kind': 'fixed'},
    'transmitter.frq': {'kind': 'fixed'},
    'transmitter.txw': {'kind': 'fixed'},

    # Antenna values come from the template file
    'antenna.txg': {'kind': 'fixed'},
    'antenna.txl': {'kind': 'fixed'},
    'antenna.ant': {'kind': 'fixed'},
    'antenna.azi': {'kind': 'fixed'},
    'antenna.tlt': {'kind': 'fixed'},
    'antenna.pol': {'kind': 'fixed'},

    # Receiver values come from the template file
    'receiver.alt': {'kind': 'fixed'},
    'receiver.rxg': {'kind': 'fixed'},
    'receiver.rxs': {'kind': 'fixed'},

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

class ArgparseCustomFormatter(
        # Don't do any line wrapping on descriptions
        argparse.RawDescriptionHelpFormatter, 
        # Include default values when running --help
        argparse.ArgumentDefaultsHelpFormatter
    ):
    pass

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
        'key': args.api_key,
    }

    lines = [
        f'99:3:{config['clutter.building.attenuation']}',
        '1:1:0.0',
        f'2:{config['clutter.trees.height']}:{config['clutter.trees.attenuation']}',
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

    apiUrl = args.base_url.rstrip('/') + '/API/clutter/index2.php'

    response = requests.post(f"{apiUrl}", data=data, headers=headers, verify=args.strict_ssl)
    response.raise_for_status()

    response = response.json()

    if response['status'] != 200:
        raise RuntimeError(response['message'])

def get_nested_value(data, path):
    keys = path.split('.')
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            raise ValueError(f"Missing key in template: '{path}'")
    return data

def populate_config_from_template():
    # These values come in from the template file
    global config_spec
    replaceWithTemplate = [
        'transmitter.lat',
        'transmitter.lon',
        'transmitter.alt',
        'transmitter.frq',
        'transmitter.txw',
        'antenna.txg',
        'antenna.txl',
        'antenna.ant',
        'antenna.azi',
        'antenna.tlt',
        'antenna.pol',
        'receiver.alt',
        'receiver.rxg',
        'receiver.rxs',
    ]

    with open(args.input_template, 'r') as template_file:
        template_file = json.load(template_file)

    for path in replaceWithTemplate:
        value = get_nested_value(template_file, path)
        config_spec[path]['value'] = value

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
        'key': args.api_key,
    }

    time.sleep(args.wait)

    apiUrl = args.base_url.rstrip('/') + '/area'

    try:
        response = requests.post(f"{apiUrl}", json=request, headers=headers, verify=args.strict_ssl)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")

        if e.response is not None:
            print(f"Status code: {e.response.status_code}")
            print(f"Response content: {e.response.text}")

        print(f"Request payload: {json.dumps(request, indent=4)}")
        exit(1)

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
    response = requests.get(tiff_url, verify=args.strict_ssl)
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
    count = 2 * args.population_count
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
            mutant[key] = config[key] + random.normalvariate(0, args.continuous_mutation_variability * (value_spec['max'] - value_spec['min']))
            mutant[key] = max(value_spec['min'], min(mutant[key], value_spec['max']))
        elif value_spec['kind'] == 'discrete':
            if random.uniform(0, 1) < args.discrete_mutation_rate:
                mutant[key] = random.choice(value_spec['options'])
            else:
                mutant[key] = config[key]
    return mutant

def print_config(config):
    print_message(f'    Min Error : {config['min_error']:>8}')
    print_message(f'   Mean Error : {config['mean_error']:>8.2g}')
    print_message(f'    Max Error : {config['max_error']:>8}')
    print_message(f'   Prop Model : {config['model.pe']:>8}')
    print_message(f'  Reliability : {config['model.rel']:>8.2g}')
    print_message(f'Building Attn : {config['clutter.building.attenuation']:>8.6g}')
    print_message(f'    Tree Attn : {config['clutter.trees.attenuation']:>8.6g}')
    print_message(f'  Tree Height : {config['clutter.trees.height']:>8.2g}')


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

    description = [
        'CloudRF Area Calibration',
        '',
        'This script attempts to fit calibration data against CloudRF area calculations, and then uses a genetic algorithm to calibrate the settings.',
        '',
        'The number of area calls required will be POPULATION_COUNT X (MAX_GENERATION + 1)',
    ]

    parser = argparse.ArgumentParser(
        description='\n'.join(description),
        formatter_class = ArgparseCustomFormatter
    )
    parser.add_argument('-i', '--input-csv', dest = 'input_csv', default = 'data.csv', help = 'Absolute path to input CSV reference data to be used in calibration. The CSV header row must be included.')
    parser.add_argument('-t', '--input-template', dest = 'input_template', default = 'CloudRF_template.json', help = 'Absolute path to input CloudRF JSON template used as part of the calculation to calibrate against.')
    parser.add_argument('-u', '--base-url', dest = 'base_url', default = 'https://api.cloudrf.com/', help = 'The base URL for the CloudRF API service.')
    parser.add_argument('--no-strict-ssl', dest = 'strict_ssl', action="store_false", default = True, help = 'Do not verify the SSL certificate to the CloudRF API service.')
    parser.add_argument('-k', '--api-key', dest = 'api_key', required = True, help = 'Your API key to the CloudRF API service.')
    parser.add_argument('-w', '--wait', dest = 'wait', type = float, default = 0.1, help = 'Time in seconds to wait before running the next calculation.')

    parser.add_argument('--population-count', dest = 'population_count', type = int, default = 10, help = 'The number of configs in a generation.')
    parser.add_argument('--max-generation', dest = 'max_generation', type = int, default = 10, help = 'The maximum number of generations to run.')
    parser.add_argument('--elite-count', dest = 'elite_count', type = int, default = 3, help = 'The number of elite configs to retain for the next generation, chosen by best fit.')
    parser.add_argument('--discrete-mutation-rate', dest = 'discrete_mutation_rate', type = float, default = 0.1, help = 'The mutation rate for discrete parameters.')
    parser.add_argument('--continuous-mutation-variability', dest = 'continuous_mutation_variability', type = float, default = 0.2, help = 'The variability for continuous mutations.')

    args = parser.parse_args()

    if args.strict_ssl == False:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    populate_config_from_template()
    dataset = load_csv(args.input_csv)

    print_message(f"loaded dataset with {len(dataset)} rows")

    population = [generate_random_config() for _ in range(0, args.population_count)]

    for i, config in enumerate(population):
        print_status_message(f'Calculating error for config {i+1:>{len(str(args.population_count))}}/{args.population_count}')
        config['min_error'], config['mean_error'], config['max_error'] = calculate_config_error(config, dataset)
        config['fitness'] = calculate_config_fitness(config)
        print_message(f'Config {i+1:>{len(str(args.population_count))}}/{args.population_count} error:    min {config['min_error']:>4}    mean {config['mean_error']:>4.2g}    max {config['max_error']:>4}')

    for generation in range(0, args.max_generation):
        print_status_message(f'Sorting config population')
        population = sorted(population, key=lambda config: config['fitness'])
        worst = population[0]
        best = population[-1]
        print_message(f"")
        print_message(f"Generation {generation:>{len(str(args.max_generation))}}/{args.max_generation}")
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

        parent_index_pairs = [(parent_indices[2 * i], parent_indices[2 * i + 1])  for i in range(0, args.population_count)]

        print_status_message(f'Creating child configs')
        children = [crossover_configs(population[a], population[b]) for (a, b) in parent_index_pairs]
        print_status_message(f'Mutating child configs')
        children = [mutate_config(config) for config in children]

        for i, config in enumerate(children):
            print_status_message(f'Calculating error for config {i+1:>{len(str(args.population_count))}}/{args.population_count}')
            config['min_error'], config['mean_error'], config['max_error'] = calculate_config_error(config, dataset)
            config['fitness'] = calculate_config_fitness(config)
            print_message(f'Config {i+1:>{len(str(args.population_count))}}/{args.population_count} error:    min {config['min_error']:>4}    mean {config['mean_error']:>4.2g}    max {config['max_error']:>4}')

        children = sorted(children, key=lambda config: config['fitness'])

        population = population[-args.elite_count:]
        children = children[-(args.population_count - args.elite_count):]
        population.extend(children)

    population = sorted(population, key=lambda config: config['fitness'])
    worst = population[0]
    best = population[-1]
    print_message(f"")
    print_message(f"Generation {args.max_generation}/{args.max_generation}")
    print_message(f"")
    print_message(f"  Worst Config")
    print_config(worst)
    print_message(f"")
    print_message(f"  Best Config")
    print_config(best)
    print_message(f"")
