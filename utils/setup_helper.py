import torch
import random
import numpy as np
import psutil
import os

# Check array/tensor size
mem_size_of = lambda a: a.element_size() * a.nelement()
gb = lambda bs: bs / 2. ** 30


def get_sys_mem():
    """ Function to estimate memory usage."""
    p = psutil.Process()
    pmem = p.memory_info()

    # only for linux!
    # possibly not giving us accurate values though
    total_memory, used_memory, free_memory = map(int, os.popen('free -t -m').readlines()[-1].split()[1:])
    cpu_mem_percent_os = round((used_memory/total_memory) * 100, 2)
    cpu_av_mem_os = round((free_memory/total_memory) * 100, 2)

    # not os specific
    # seems to be more reliable
    cpu_mem_percent = round(psutil.virtual_memory().percent, 2)
    cpu_available_mem_percent = round(psutil.virtual_memory().available * 100 / psutil.virtual_memory().total, 2)

    return gb(pmem.rss), gb(pmem.vms), cpu_mem_percent_os, cpu_av_mem_os, cpu_mem_percent, cpu_available_mem_percent


def load_weights(weights_dir, device, key='state_dict'):
    map_location = lambda storage, loc: storage.cuda(device.index) if torch.cuda.is_available() else storage
    weights_dict = None
    if weights_dir is not None:
        weights_dict = torch.load(weights_dir, map_location=map_location)
    return weights_dict


def lprint(ms, log=None):
    '''Print message on console and in a log file'''
    print(ms)
    if log:
        log.write(ms + '\n')
        log.flush()


def make_deterministic(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False  # Important also


def config2str(config):
    """ Function to help with printing of configuration."""
    print_ignore = ['weights_dict', 'optimizer_dict']
    args = vars(config)
    separator = '\n'
    confstr = ''
    confstr += '------------ Configuration -------------{}'.format(separator)
    for k, v in sorted(args.items()):
        if k in print_ignore:
            if v is not None:
                confstr += '{}:{}{}'.format(k, len(v), separator)
            continue
        confstr += '{}:{}{}'.format(k, str(v), separator)
    confstr += '----------------------------------------{}'.format(separator)
    return confstr