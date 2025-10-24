#!/usr/bin/env python3

import os
import argparse
import time
import subprocess
from musicplayer import get_sleep_condition
from musicplayer import format_str_time


def call_amixer_subprocess(current_volume):
    p = subprocess.Popen([
        'amixer',
        '-D',
        'pulse',
        'set',
        'Master',
        str(current_volume)+'%'
    ], stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))
    p.wait()
    return p.returncode


def exit_func(exit_flag, current_volume, limit):
    if exit_flag is None:
        return None
    if current_volume == limit:
        raise SystemExit(0)


def set_volume(target_volume, current_volume, limit):
    return_code = 1
    if current_volume != limit:
        return_code = call_amixer_subprocess(target_volume)
    if return_code == 0:
        return target_volume
    return current_volume


def main():
    current_volume = int(subprocess.check_output(
        command, shell=True, text=True))

    if not get_sleep_condition(
            format_str_time(start_time), format_str_time(ramp_down_time)):
        current_volume = set_volume(min(
            current_volume+step_up, maximum_volume),
                                    current_volume, maximum_volume)
    else:
        current_volume = set_volume(max(
            current_volume-step_down, minimum_volume), current_volume,
                                    minimum_volume)

    exit_func(exit_flag, current_volume, vol_dict.get(exit_flag))
    time.sleep(interval)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
            prog='volume controller',
            description='Automatic system volume controller', epilog='')
    parser.add_argument('time_window', nargs=2, help='\"HH:MM\" \"HH:MM\"')
    parser.add_argument('minimum_volume', type=int, help='Minimum volume')
    parser.add_argument('maximum_volume', type=int, help='Maximum volume')
    parser.add_argument('step_up', type=int, help='Volume step increase')
    parser.add_argument('step_down', type=int, help='Volume step decrease')
    parser.add_argument('interval', type=int, help='Interval in seconds')
    parser.add_argument('--exit', choices=['volmax', 'volmin'], default=None,
                        help='Exit when maximum or minimum volume is set')
    args = parser.parse_args()

    command = 'amixer -D pulse sget Master | grep \'Right:\' | \
            awk -F\'[][]\' \'{ print $2 }\' | cut -d% -f1'
    start_time, ramp_down_time = args.time_window
    minimum_volume = args.minimum_volume
    maximum_volume = args.maximum_volume
    step_up = args.step_up
    step_down = args.step_down
    interval = args.interval
    exit_flag = args.exit
    vol_dict = {'volmin': minimum_volume, 'volmax': maximum_volume}

    try:
        while True:
            main()
    except KeyboardInterrupt:
        print('Program interrupted')
        raise SystemExit(0)
    except Exception as e:
        print('Exception encountered:', e)
        raise SystemExit(1)
