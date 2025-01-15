#!/usr/bin/env python3

import os
import subprocess
import time
from musicplayer import get_audio_files as get_files
from musicplayer import print_to_file
import argparse


def my_print(*args, **kwargs):
    if verbose > 1:
        args = (time.strftime('%D - %H:%M:%S :'),) + args
    print(*args, **kwargs)


def cleanup(files):
    [os.remove(f) for f in files if os.path.isfile(f)]


def remove_empty_directory(directory):
    [os.removedirs(directory) for _ in [directory] if os.path.exists(directory) and not os.listdir(directory)]


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


def normalize_files(input_file, mode):
    return subprocess.Popen([
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
    ], stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))


def audio_fade(input_file, output_file, fade_in_sec=2, fade_out_sec=2):
    duration = get_audio_file_duration(input_file)
    return subprocess.Popen([
        'ffmpeg',
        '-i',
        input_file,
        '-af',
        'afade=in:st=0:d='+str(fade_in_sec)+',afade=out:st='+str(duration-fade_out_sec)+':d='+str(fade_out_sec),
        output_file
    ], stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))


def convert_files(input_file, output_file):
    return subprocess.Popen([
        'ffmpeg',
        '-i',
        input_file,
        output_file
    ], stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))


def select_func(input_file, output_file):
    if directory == 'output_files':
        return convert_files(input_file, output_file)
    elif directory == 'fade':
        return audio_fade(input_file, output_file, fade_in, fade_out)
    return normalize_files(input_file, normalized_mode)


def update_completed_files():
    if directory == 'output_files':
        if enable_log:
            [print_to_file(log_file, os.path.splitext(p.args[2])[0]+'.mp3') for p in process_list if p.poll() == 0]
        return [completed_files.append(p.args[3]) for p in process_list if p.poll() == 0]
    if directory == 'fade':
        if enable_log:
            [print_to_file(log_file, os.path.splitext(p.args[2])[0]+'.mp3') for p in process_list if p.poll() == 0]
        return [completed_files.append(p.args[5]) for p in process_list if p.poll() == 0]
    if enable_log:
        [print_to_file(log_file, os.path.splitext(p.args[1])[0]+'.mp3') for p in process_list if p.poll() == 0]
    return [completed_files.append(os.path.join(target_directory, os.path.splitext(p.args[1])[0]+'.mp3')) for p in process_list if p.poll() == 0]


def draw_progress_bar(status):
    bar_lenght = 40
    bar = int((status*bar_lenght)/100)
    end_ln='\r'
    if status < 0:
        my_print('{}'.format(' '*(bar_lenght+10)), end=end_ln)
        return None
    if status == 100:
        end_ln='\n'
    my_print('[{:<{}}] {:.2f}%'.format('='*bar, bar_lenght, status), end=end_ln)


def main():
    start_time = time.time()
    files = get_files(os.getcwd(), supported_files)
    file_count = len(files)
    completed_file_count = len(completed_files)
    if file_count == 0:
        remove_empty_directory(target_directory)
        raise SystemExit('No files found... Raising SystemExit')

    my_print('Converting files to .mp3 with {} option...'.format(args.output))
    files = [f for f in files if f not in completed_files]
    # completed_files[:] = [os.path.join(target_directory, f) for f in completed_files]
    if enable_log:
        [print_to_file(log_file, f) for f in completed_files]
    for f in files:
        output = os.path.join(target_directory, os.path.splitext(f)[0]+'.mp3')
        output_files.append(output)
        process_list.append(select_func(f, output))
        if len(process_list) > subprocess_limit - 1:
            for proc in process_list:
                status = (((completed_file_count+len(output_files)-(len(process_list)))/file_count)*100)
                draw_progress_bar(status)
                temp_list = [p for p in process_list if p.poll() is None]
                while (len(temp_list) > subprocess_limit - 1):
                    temp_list = [p for p in process_list if p.poll() is None]
                    time.sleep(0.01)
                if verbose > 0 and proc.poll() is not None:
                    my_print('Return code: {:3}, Output file: {}'.format(proc.returncode, proc.args[argument_index]))
            update_completed_files()
            process_list[:] = [p for p in temp_list if p.poll() is None]

    for proc in process_list:
        status = (((completed_file_count+len(output_files)-(len(process_list)-process_list.index(proc)))/file_count)*100)
        draw_progress_bar(status)
        proc.wait()
        if verbose > 0 and proc.poll() is not None:
            my_print('Return code: {:3}, Output file: {}'.format(proc.returncode, proc.args[argument_index]))
    update_completed_files()

    draw_progress_bar(100)
    my_print('Completed in {:.2f} seconds'.format(time.time() - start_time))
    if enable_log:
        print_to_file(log_file, 'Done')

    cleanup([f for f in output_files if f not in completed_files])


if __name__ == '__main__':

    cpu_count = os.cpu_count()
    max_subprocess_limit = cpu_count * 2

    parser = argparse.ArgumentParser(prog='convert2mp3', description='Convert audio files to .mp3 files',
                                     epilog='')
    parser.add_argument('-o', '--output', choices=['default', 'normalized', 'fade'], default='default',
                        help='normalized option: Normalizes volume on all audio files')
    parser.add_argument('-m', '--mode', choices=['ebu', 'rms', 'peak'], default='ebu', help='Normalized modes, default=ebu')
    parser.add_argument('-l', '--limit', type=int, default=cpu_count,
                        help='limit subprocesses spawned')
    parser.add_argument('-c', '--clean', action='store_true',
                        help='Clean target directory when manually interrupting the program')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity level')
    parser.add_argument('--fade-in', type=float, default=2.00, help='Fade-in (seconds). \"default = 2.00\"')
    parser.add_argument('--fade-out', type=float, default=2.00, help='Fade-out (seconds). \"default = 2.00\"')
    parser.add_argument('--enable-log', action='store_true', help='Log program output to convert2mp3.log')
    parser.add_argument('--rename-log', type=str, default='convert2mp3.log', help='Rename log file')
    args = parser.parse_args()

    verbose = args.verbose
    subprocess_limit = abs(args.limit)
    if subprocess_limit > max_subprocess_limit:
        my_print('Maximum subprocess limit is {}'.format(max_subprocess_limit))
        subprocess_limit = max_subprocess_limit
    output_files = []
    process_list = []
    supported_files = [".mp3", ".wma", ".m4a", ".webm", ".wav"]
    directory = 'normalized'
    normalized_mode = args.mode
    argument_index = 1
    fade_in = abs(args.fade_in)
    fade_out = abs(args.fade_out)
    enable_log = args.enable_log
    log_file_name = args.rename_log
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), log_file_name)
    reset_log_at_startup = True

    if args.output == 'default':
        directory = 'output_files'
        argument_index = 2
    elif args.output == 'fade':
        directory = 'fade'
        argument_index = 2

    if enable_log and not os.path.exists(log_file):
        open(log_file, 'w').close()

    if reset_log_at_startup and os.path.exists(log_file):
        open(log_file, 'w').close()

    target_directory = os.path.join(os.getcwd(), directory)
    if enable_log:
        open(log_file, 'a', encoding='utf-8').writelines('Completed files in {}\n'.format(target_directory))

    if not os.path.isdir(target_directory):
        os.mkdir(target_directory)

    completed_files = get_files(target_directory, supported_files)

    try:
        main()
    except KeyboardInterrupt:
        draw_progress_bar(-1)
        my_print('Program interrupted')
        for p in process_list:
            if args.clean:
                p.terminate()
            p.wait()
        update_completed_files()
        if enable_log:
            print_to_file(log_file, 'Program interrupted')
        if verbose > 0:
            [my_print('Return code: {:3}, Output file: {}'.format(p.returncode, p.args[argument_index])) for p in process_list if p.poll() is not None]
        if not args.clean:
            output_files = [f for f in output_files if f not in completed_files]
        my_print('cleaning up...')
        cleanup(output_files)
        remove_empty_directory(target_directory)
        raise SystemExit(0)
    except Exception as e:
        my_print('Exception encountered:', e)
        raise SystemExit(1)
