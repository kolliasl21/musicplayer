#!/usr/bin/env python3

import os
import subprocess
import time
from musicplayer import get_audio_files as get_files
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed


def cleanup(files):
    [os.remove(f) for f in files if os.path.isfile(f)]


def remove_empty_directories(*directories):
    [os.removedirs(directory) for directory in directories
     if os.path.exists(directory) and not os.listdir(directory)]


def get_bitrate_or_samplerate_int(stream_opt, audio_file):
    result = subprocess.run([
        'ffprobe',
        '-v',
        'error',
        '-select_streams',
        'a:0',
        '-show_entries',
        'stream='+str(stream_opt),
        '-of',
        'default=noprint_wrappers=1:nokey=1',
        audio_file
    ], capture_output=True, text=True)
    return int(result.stdout)


def get_bitrate_and_samplerate_raw(audio_file):
    result = subprocess.run([
        'ffprobe',
        '-v',
        'error',
        '-select_streams',
        'a:0',
        '-show_entries',
        'stream=bit_rate',
        '-show_entries',
        'stream=sample_rate',
        '-of',
        'default=noprint_wrappers=1:nokey=1',
        audio_file
    ], capture_output=True, text=True)
    return result.stdout


def print_bitrate_info(audio_file):
    output = get_bitrate_and_samplerate_raw(audio_file)
    print(output.replace('\n', ' '), audio_file)


def get_audio_file_duration(audio_file):
    result = subprocess.run([
        'ffprobe',
        '-v',
        'error',
        '-show_entries',
        'format=duration',
        '-of',
        'default=noprint_wrappers=1:nokey=1',
        audio_file
    ], capture_output=True, text=True)
    duration = float(result.stdout)
    return duration


def normalize_files(input_file, output_file, mode):
    result = subprocess.run([
        'ffmpeg-normalize',
        input_file,
        '-nt',
        mode,
        '-c:a',
        'libmp3lame',
        '-b:a',
        '128k',
        '-ext',
        'mp3',
        '-o',
        output_file
    ], stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))
    return result.returncode


def audio_fade(input_file, output_file, fade_in_sec=2, fade_out_sec=2):
    duration = get_audio_file_duration(input_file)
    result = subprocess.run([
        'ffmpeg',
        '-i',
        input_file,
        '-af',
        'afade=in:st=0:d='+str(fade_in_sec)+''
        ',afade=out:st='+str(duration-fade_out_sec)+':d='+str(fade_out_sec),
        output_file,
        '-n'
    ], stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))
    return result.returncode


def convert_files(input_file, output_file):
    result = subprocess.run([
        'ffmpeg',
        '-i',
        input_file,
        output_file,
        '-n'
    ], stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))
    return result.returncode


def scan_audio_files(audio_files):
    with ThreadPoolExecutor(max_workers=subprocess_limit) as e:
        e.map(print_bitrate_info, files, chunksize=subprocess_limit)


def select_func(input_file, output_file):
    returncode = -1
    if directory == 'output_files':
        returncode = convert_files(input_file, output_file)
    elif directory == 'fade':
        returncode = audio_fade(input_file, output_file, fade_in, fade_out)
    else:
        returncode = normalize_files(input_file, output_file, normalized_mode)
    if verbose == 1:
        print('Return code: {:3}, Processed file: {}'.format(
            returncode, input_file))
    elif verbose > 1 and returncode == 0:
        print(os.path.splitext(input_file)[0]+'.mp3')


def draw_progress_bar(status):
    bar_lenght = 40
    bar = int((status*bar_lenght)/100)
    end_ln = '\r'
    if status < 0:
        print('{}'.format(' '*(bar_lenght+10)), end=end_ln)
        return None
    if status == 100:
        end_ln = '\n'
    print('[{:<{}}] {:.2f}%'.format('='*bar, bar_lenght, status), end=end_ln)


def main():
    start_time = time.time()
    file_count = len(files)
    output_files = []

    if file_count == 0:
        remove_empty_directories(target_directory)
        raise SystemExit('No files found... Raising SystemExit')

    print('Converting files to .mp3 with {} option...'.format(args.output))

    for f in files:
        output = os.path.join(target_directory, os.path.splitext(f)[0]+'.mp3')
        output_files.append(output)

    with ThreadPoolExecutor(max_workers=subprocess_limit) as e:
        futures = []
        for file, output_file in zip(files, output_files):
            futures.append(e.submit(select_func, file, output_file))

        # queue_size = e._work_queue.qsize()

        if verbose <= 1:
            draw_progress_bar(0)
            for future in as_completed(futures):
                completed_count = len([f for f in futures if f.done()])
                draw_progress_bar((completed_count/file_count)*100)

    print('Completed in {:.2f} seconds'.format(time.time() - start_time))


if __name__ == '__main__':

    cpu_count = os.cpu_count()
    max_subprocess_limit = cpu_count * 2

    parser = argparse.ArgumentParser(
            prog='convert2mp3',
            description='Convert audio files to .mp3 files', epilog='')
    parser.add_argument('-o', '--output', choices=['default', 'normalized',
                                                   'fade', 'scan'],
                        default='default', help='normalized option: Normalizes'
                        ' volume on all audio files')
    parser.add_argument('-m', '--mode', choices=['ebu', 'rms', 'peak'],
                        default='ebu', help='Normalized modes, default=ebu')
    parser.add_argument('-l', '--limit', type=int, default=cpu_count,
                        help='limit subprocesses spawned')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='Increase verbosity level')
    parser.add_argument('--fade-in', type=float, default=2.00,
                        help='Fade-in (seconds). \"default = 2.00\"')
    parser.add_argument('--fade-out', type=float, default=2.00,
                        help='Fade-out (seconds). \"default = 2.00\"')
    args = parser.parse_args()

    verbose = args.verbose
    subprocess_limit = abs(args.limit)
    if subprocess_limit > max_subprocess_limit:
        print('Maximum subprocess limit is {}'.format(max_subprocess_limit))
        subprocess_limit = max_subprocess_limit
    supported_files = [".mp3", ".wma", ".m4a", ".webm", ".wav", ".mp4"]
    directory = 'normalized'
    normalized_mode = args.mode
    fade_in = abs(args.fade_in)
    fade_out = abs(args.fade_out)

    files = get_files(os.getcwd(), supported_files)

    if args.output == 'default':
        directory = 'output_files'
    elif args.output == 'fade':
        directory = 'fade'
    elif args.output == 'scan':
        scan_audio_files(files)
        raise SystemExit(0)

    target_directory = os.path.join(os.getcwd(), directory)

    if not os.path.isdir(target_directory):
        os.mkdir(target_directory)

    main()
