#!/usr/bin/env python3

import os
import random
import time
import argparse
import pathlib
import textwrap
import datetime
from math import log10


def my_print(*args, **kwargs):
    if verbose > 1:
        args = (time.strftime('%D - %H:%M:%S :'),) + args
    print(*args, **kwargs)
    if enable_log:
        print_to_file(log_file, *args, **kwargs)
        if not disable_log_limit:
            trim_log_file(log_file, 400, 2000)


def print_to_file(log_file, *args, **kwargs):
    with open(log_file, 'a', encoding='utf-8') as fp:
        print(*args, file=fp, **kwargs)


def write_list_to_file(file, input_list):
    if not os.path.exists(file):
        return None
    with open(file, 'w', encoding='utf-8') as fp:
        fp.writelines(str('{}\n'.format(entry)) for entry in input_list)


def trim_log_file(log_file, minimum_lines, maximum_lines):
    if not os.path.exists(log_file):
        return None
    with open(log_file, 'r', encoding='utf-8') as fp:
        _lines = [_line.rstrip() for _line in fp]
    if len(_lines) > maximum_lines:
        _list = [_line.rstrip() for _line in _lines[-minimum_lines:]]
        write_list_to_file(log_file, _list)


def create_link():
    if not create_log_file_link or not enable_log or not os.path.exists(log_file):
        return None
    try:
        if not os.path.exists(link_file):
            os.link(log_file, link_file)
    except Exception as e:
        my_print(e)


def get_audio_files(filepath, input_list):
    audio_files = [f for f in os.listdir(filepath) if any(f.endswith(ext) for ext in input_list)]
    audio_files.sort()
    return audio_files


def get_file_list(file, file_extensions):
    audio_files = []
    if os.path.isfile(file):
        with open(file, 'r', encoding='utf-8') as fp:
            audio_files = [line.rstrip() for line in fp if any(line.rstrip().endswith(ext) for ext in file_extensions)]
            audio_files.sort()
    return audio_files


def sort_file_lists(filepath):
    if sort_files is None:
        return None
    genre_files = get_audio_files(filepath, supported_txt_files)
    genre_files.append('favorites.txt')
    if genre_files:
        for file in genre_files:
            write_list_to_file(os.path.join(filepath, str(file)), get_file_list(os.path.join(filepath, str(file)), supported_audio_files))
        if sort_files == 'exit':
            raise SystemExit(0)


def format_str_time(input_string):
    if input_string is None:
        return None
    hours, minutes = map(int, input_string.split(':'))
    output_time = datetime.time(hour=hours, minute=minutes)
    return output_time


def sleep_func(timer_start, timer_stop):
    if timer_start is None:
        return None
    while get_sleep_condition(timer_start, timer_stop):
        time.sleep(3)


def get_sleep_status(timer_start, timer_stop):
    if timer_start is None:
        return False
    return get_sleep_condition(timer_start, timer_stop)


def get_sleep_condition(timer_start, timer_stop):
    current_time = format_str_time(time.strftime('%H:%M'))
    if timer_start < timer_stop:
        return not (timer_start <= current_time < timer_stop)
    return timer_stop <= current_time < timer_start


class Musicplayer:

    import subprocess


    def __init__(self, audio_gain: float = 1.0, supported_files: list = None):
        self.audio_gain = audio_gain
        self.args_list = [None]
        self.kwargs = {'stdout': open(os.devnull, 'w'), 'stderr': open(os.devnull, 'w')}
        self.audio_file = 'audio_file'
        self.duration = 0
        self.__audio_file_index = 0
        self.__duration_index = 0
        self._p = None

        if supported_files is None:
            self._supported_files = ['.mp3', '.wma', '.m4a', '.webm', '.mkv'] 
        else:
            self._supported_files = supported_files

    def set_media(self, audio_file):
        self.args_list[self.__audio_file_index] = audio_file
        self.audio_file = audio_file
        if any(audio_file.endswith(ext) for ext in self._supported_files):
            self.__set_duration(audio_file)
        if self.__duration_index > 0:
            self.args_list[self.__duration_index] = str(self.duration)


    def set_vlc(self, **kwargs):
        self.loop = '--no-loop'
        self.repeat = '--no-repeat'
        self.random = '--no-random'
        self.enable_video = False
        self.no_controls = False

        if kwargs.get('loop', False) is True:
            self.loop = '--loop'

        if kwargs.get('repeat', False) is True:
            self.repeat = '--repeat'

        if kwargs.get('random', False) is True:
            self.random = '--random'

        if kwargs.get('enable_video', False) is True:
            self.enable_video = True

        if kwargs.get('no_controls', False) is True:
            self.no_controls = True

        if self.enable_video:
            self.args_list = [
                'vlc',
                '--quiet',
                '--play-and-exit',
                self.random,
                self.loop,
                self.repeat,
                '--gain=' + str(self.audio_gain),
                self.audio_file
            ]
            self.__audio_file_index = self.args_list.index(self.audio_file)
            self.__duration_index = 0
            self.kwargs = {}
            return None
        self.args_list = [
            'vlc',
            '-I',
            'dummy',
            '--quiet',
            '--play-and-exit',
            '--no-video',
            self.random,
            self.loop,
            self.repeat,
            '--gain=' + str(self.audio_gain),
            self.audio_file
        ]
        self.__audio_file_index = self.args_list.index(self.audio_file)
        self.__duration_index = 0
        if not self.no_controls:
            self.args_list.extend([
                '--global-key-play-pause',
                'ctrl+shift+p',
                '--global-key-stop',
                'ctrl+shift+x',
                '--global-key-jump-short',
                'ctrl+shift+b',
                '--global-key-jump+short',
                'ctrl+shift+f',
                '--global-key-next',
                'ctrl+shift+v',
                '--global-key-prev',
                'ctrl+shift+w'
            ])


    def set_ffplay(self, **kwargs):
        self.loop = False
        self.enable_video = False

        if kwargs.get('loop', False) is True:
            self.loop = True

        if kwargs.get('enable_video', False) is True:
            self.enable_video = True

        self.args_list = [
            'ffplay',
            self.audio_file,
            '-autoexit',
            '-af',
            'volume=' + str(self.audio_gain)
        ]
        self.__audio_file_index = self.args_list.index(self.audio_file)
        self.__duration_index = 0
        if not self.enable_video:
            self.args_list.extend(['-nodisp'])
        if self.loop:
            self.args_list.extend([
                '-loop',
                '0'  # 0 infinite loop
            ])


    def __set_duration(self, audio_file):
        result = self.subprocess.run([
            'ffprobe',
            '-v',
            'error',
            '-show_entries',
            'format=duration',
            '-of',
            'default=noprint_wrappers=1:nokey=1',
            audio_file
        ], capture_output=True, text=True)
        self.duration = float(result.stdout)


    def set_ffmpeg(self, **kwargs):
        self.loop = '-1'  # infinite loop
        self.args_list = ['ffmpeg']
        self.__duration_index = 0
        self.output_device = kwargs.get('output_device', 'default')
        loop = False

        if kwargs.get('loop', False) is True:
            loop = True

        if not loop:
            self.loop = '0'  # no loop
            self.args_list.extend([
                '-t',
                str(self.duration)
            ])
            self.__duration_index = 2
        self.args_list.extend([
            '-stream_loop',
            self.loop,
            '-i',
            self.audio_file,
            '-af',
            'volume=' + str(self.audio_gain),
            '-f',
            'alsa',
            self.output_device
        ])
        self.__audio_file_index = self.args_list.index(self.audio_file)


    def set_omxplayer(self, **kwargs):
        loop = False
        self.output = kwargs.get('output', 'alsa')

        if kwargs.get('loop', False) is True:
            loop = True

        clamp = lambda n: max(min(2, n), 0.001)
        millibels = 2000*log10(clamp(self.audio_gain))
        self.args_list = [
            'omxplayer',
            '-o',
            self.output,
            self.audio_file,
            '--vol',
            str(millibels)
        ]
        self.__audio_file_index = self.args_list.index(self.audio_file)
        self.__duration_index = 0
        if loop:
            self.args_list.extend(['--loop'])


    def play(self):
        self._p = self.subprocess.Popen(self.args_list, **self.kwargs)


    def stop(self):
        if self._p is not None:
            self._p.kill()


    def wait(self):
        if self._p is not None:
            self._p.wait()


    def poll(self):
        if self._p is not None:
            return self._p.poll()


def load_musicplayer(pq, filepath, current_audio_file, timer_start, timer_stop):
    current_path = os.path.join(filepath, current_audio_file)

    pq.set_media(current_path)
    pq.play()

    time_start = time.time()
    my_print(current_audio_file)
    try:
        while (((time.time() - time_start) < (p.duration-fade)) \
                or disable_fade) and pq.poll() is None:
            if get_sleep_status(timer_start, timer_stop) \
                and force_kill_subprocess:
                pq.stop()
            time.sleep(0.1)  # poll every 100ms
    except KeyboardInterrupt:
        pq.stop()
        if not skip_tracks:
            raise SystemExit(0)


def get_tracklist(filepath, audio_files, genre_files):

    track_list = audio_files

    if random_mode:
        weight_list = get_file_list(os.path.join(filepath, 'favorites.txt'), supported_audio_files)
        track_list.extend(item for item in weight_list for _ in range(weight))
        random.shuffle(track_list)
        if not genre_files:
            return track_list
        for file in genre_files:
            genre_list = get_file_list(os.path.join(filepath, str(file)), supported_audio_files)
            track_list = [item for item in track_list if item not in genre_list]
            random.shuffle(genre_list)
            track_list.extend(genre_list)
    elif genre_files:
        temp_list = []
        for file in genre_files:
            genre_list = get_file_list(os.path.join(filepath, str(file)), supported_audio_files)
            track_list = list(set(track_list) - set(genre_list))
            genre_list = list(set(genre_list))
            genre_list.sort()
            temp_list.extend(genre_list)
        track_list.sort()
        track_list.extend(temp_list)

    return track_list


def main(p):

    timer_start = format_str_time(start_time)
    timer_stop = format_str_time(stop_time)

    audio_files = get_audio_files(path, supported_audio_files)
    genre_files = get_audio_files(path, supported_txt_files)
    track_list = get_tracklist(path, audio_files, genre_files)
    m3u_list = []
    create_link()

    for track in track_list:

        target = os.path.join(path, track)

        if get_sleep_status(timer_start, timer_stop):
            if terminate:
                my_print('Playback terminated. Exit with code 0')
                raise SystemExit(0)
            if verbose > 0:
                my_print('------Sleep------')
            sleep_func(timer_start, timer_stop)
            if verbose > 0:
                my_print('------Resume------')

        if track in previous_tracks and len(audio_files) > list_len:
            if verbose > 0:
                my_print('Skipping "{}" in previously played tracks list...'.format(track))
            if force_reload_list:
                break

        elif track in previous_tracks[-3:] and len(audio_files) > 9:  # fallback to checking last 3 played songs
            if verbose > 0:
                my_print('Skipping "{}" in last 3 previously played tracks list...'.format(track))
            if force_reload_list:
                break

        elif track in previous_tracks[-1] and len(audio_files) > 1:  # fallback to checking last played song
            if verbose > 0:
                my_print('Skipping "{}" previously played track...'.format(track))
            if force_reload_list:
                break

        elif os.path.isfile(target):

            if playlist_mode:
                my_print(track)
                m3u_list.append(os.path.join(path, track))
            elif test_mode:
                my_print(track)
                time.sleep(0.1)
            else:
                load_musicplayer(p, path, track, timer_start, timer_stop)

            if list_len < 1:
                pass
            elif len(previous_tracks) < list_len:
                previous_tracks.insert(list_len - 1, track)
            else:
                previous_tracks.append(track)
                previous_tracks.pop(0)

        elif verbose > 0:
            my_print('File "{}" Not Found. Skipping...'.format(track))

    if playlist_mode and musicplayer == 'vlc':
        open(os.path.join(path, 'playlist.m3u'), 'w').close()
        write_list_to_file(os.path.join(path, 'playlist.m3u'), m3u_list)
        if not test_mode:
            load_musicplayer(p, path, 'playlist.m3u', timer_start, timer_stop)
        else:
            my_print('playlist.m3u')
            time.sleep(2)
    elif playlist_mode:
        my_print('Error: --playlist mode only available for VLC. Raising SystemExit')
        raise SystemExit(1)

    if no_reload:
        my_print('Playlist done...')
        raise SystemExit(0)

    if verbose > 0:
        my_print('------Reload list------')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog='musicplayer', formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=textwrap.dedent('''\

            Custom cli musicplayer

            ------------------------------------

            Controls (cli):
                Exit................Ctrl+C
                Pause/Suspend.......Ctrl+Z
                Skip tracks on cli..Ctrl+C (--ctrl-c)

            Controls (desktop vlc):
                Stop/Next track.....Ctrl+Shift+X
                Pause/Resume........Ctrl+Shift+P
                Jump forwards.......Ctrl+Shift+F
                Jump backwards......Ctrl+Shift+B
                Next track..........Ctrl+Shift+V (--playlist)
                Previous track......Ctrl+Shift+W (--playlist)

            Notes:
                - Add your favorite tracks to \"favorites.txt\" if
                  you want them to be included more than once per cycle.

                - Use \"*.genre.txt\" files to organize playlists
                  according to music genres. Files not included in
                  \"*.genre.txt\" will be sorted at the top of the
                  playlist.

            '''), epilog='')
    parser.add_argument('path', type=pathlib.Path, help='Audio files directory')
    parser.add_argument('-r', '--random', action='store_true', help='Random playback')
    parser.add_argument('-p', '--player', choices=['vlc', 'ffplay', 'ffmpeg', 'omxplayer'], default='vlc',
                        help='Default = vlc')
    parser.add_argument('-o', '--output', choices=['alsa', 'local', 'hdmi', 'both'], default='alsa',
                        help='Select omxplayer device output \"default omxplayer output = alsa\"')
    parser.add_argument('-d', '--device', default='default', help='Select ffmpeg device output (hw:0,0, hdmi:0,0)')
    parser.add_argument('-l', '--list-len', type=int, default=20,
                        help='Keep track of previously played audio files \"default size = 20\"')
    parser.add_argument('-g', '--gain', type=float, default=1.00, help='Audio gain \"default GAIN = 1.00\"')
    parser.add_argument('-f', '--fade', type=float, default=0.00, help='Crossfade (sedonds). Requires --no-controls \"default = 0.00\"')
    parser.add_argument('-c', '--ctrl-c', action='store_true', help='Skip tracks with ctrl+c on cli')
    parser.add_argument('-w', '--weight', type=int, default=1, help='WEIGHT*favorites.txt \"default WEIGHT = 1\"')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity level')
    parser.add_argument('-t', '--timer', metavar=('\"HH:MM\"', '\"HH:MM\"'), nargs=2, default=[None, None],
                        help='Pause playback outside the specified time window')
    parser.add_argument('--wait', action='store_false', help='Wait for track/playlist to finish before'
                        ' entering sleep mode')
    parser.add_argument('--loop', action='store_true', help='Loop track or playlist.m3u')
    parser.add_argument('--repeat', action='store_true', help='Repeat track')
    parser.add_argument('--shuffle', action='store_true', help='Shuffle VLC playlist')
    parser.add_argument('--sort-files', choices=['startup', 'exit'], default=None,
                        help='Sort *.txt files associated with this script \"at startup/and exit\"')
    parser.add_argument('--playlist', action='store_true', help='Generate playlist.m3u and load vlc')
    parser.add_argument('--no-reload', action='store_true', help='Play the tracklist once and exit')
    parser.add_argument('--no-controls', action='store_true',
                        help='Disable controls when running this script as a background service')
    parser.add_argument('--dry-run', action='store_true', help='Print program output without playing music')
    parser.add_argument('--enable-log', action='store_true', help='Log program output to musicplayer.log')
    parser.add_argument('--rename-log', type=str, default='musicplayer.log', help='Rename log file')
    parser.add_argument('--create-link', action='store_true', help='Create a link to log file in audio files directory')
    parser.add_argument('--enable-video', action='store_true', help='Enable video playback')
    parser.add_argument('--terminate', action='store_true', help='Terminate musicplayer when sleep mode activates')
    args = parser.parse_args()

    path = os.path.abspath(args.path)
    musicplayer = args.player
    omx_output = args.output
    ffmpeg_output_device = args.device
    previous_tracks = ['a']  # skip previously played tracks
    list_len = abs(args.list_len)
    force_reload_list = False  # force a list reload when a track is skipped
    gain = max(min(2, args.gain), 0)
    fade = max(min(7, args.fade), 0)
    random_mode = args.random
    skip_tracks = args.ctrl_c
    weight = abs(args.weight)
    verbose = args.verbose
    sort_files = args.sort_files
    test_mode = args.dry_run
    no_reload = args.no_reload
    no_controls = args.no_controls
    playlist_mode = args.playlist
    enable_log = args.enable_log
    log_file_name = args.rename_log
    supported_audio_files = ['.mp3', '.wma', '.m4a', '.webm', '.mkv']
    supported_txt_files = ['.genre.txt']
    start_time, stop_time = args.timer
    force_kill_subprocess = args.wait
    loop_playback = args.loop
    repeat_track = args.repeat
    shuffle_playback = args.shuffle
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), log_file_name)
    link_file = os.path.join(path, log_file_name)
    disable_log_limit = False
    reset_log_at_startup = False
    create_log_file_link = args.create_link
    enable_video = args.enable_video
    terminate = args.terminate
    disable_fade = ((enable_video or not no_controls or playlist_mode) or (loop_playback or repeat_track))

    p = Musicplayer(gain, supported_audio_files)

    if musicplayer == 'vlc':
        p.set_vlc(loop=loop_playback, repeat=repeat_track, random=shuffle_playback, enable_video=enable_video, no_controls=no_controls)
    elif musicplayer == 'ffplay':
        p.set_ffplay(loop=(loop_playback or repeat_track), enable_video=enable_video)
    elif musicplayer == 'ffmpeg':
        p.set_ffmpeg(loop=(loop_playback or repeat_track), output_device=str(ffmpeg_output_device))
    else:
        p.set_omxplayer(loop=(loop_playback or repeat_track), output=str(omx_output))

    flag = False
    sort_file_lists(path)

    if enable_log and not os.path.exists(log_file):
        open(log_file, 'w').close()

    if reset_log_at_startup and os.path.exists(log_file):
        open(log_file, 'w').close()

    if verbose > 0:
        my_print('------Start------')

    if fade > 0 and not no_controls:
        my_print('Crossfade requires --no-controls!')

    try:
        while True:
            if get_audio_files(path, supported_audio_files):
                main(p)
                flag = False
            elif not flag:
                my_print('Playlist is empty. Waiting for files')
                flag = True
            else:
                time.sleep(1)
    except KeyboardInterrupt:
        my_print('Program interrupted')
        raise SystemExit(0)
    except Exception as e:
        my_print('Exception encountered:', e)
        raise SystemExit(1)
