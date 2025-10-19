#!/usr/bin/env python3

import os
import argparse
import pathlib
from musicplayer import get_file_list
from musicplayer import get_audio_files


def main():

    original_files = os.path.abspath(args.path)
    supported_audio_files = [".mp3", ".wma", ".m4a"]

    if original_files.endswith((".txt", ".log")):
        file_list = get_file_list(original_files, supported_audio_files)
    else:
        file_list = get_audio_files(original_files, supported_audio_files)

    if not args.keep:
        [os.remove(f) for f in file_list if os.path.isfile(f)]
    else:
        [os.remove(f) for f in get_audio_files(os.getcwd(), supported_audio_files) if f not in file_list]


if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog='file remover', description='compares audio files between two directories and'
                                     ' removes or keeps matching audio files', epilog='')
    parser.add_argument('path', type=pathlib.Path, help='audio files directory')
    parser.add_argument('-k', '--keep', action='store_true',
                        help='keep option: Keeps matching audio files and removes the rest')
    args = parser.parse_args()

    try:
        main()
    except KeyboardInterrupt:
        print('Program interrupted')
        raise SystemExit(0)
    except Exception as e:
        print('Exception encountered:', e)
        raise SystemExit(1)
