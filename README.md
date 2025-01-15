# Musicplayer and tools

- musicplayer_extended.py : Extended functionality.
- convert2mp3.py : Convert files to .mp3 in current working directory and save new files to a new directory.
- volume_controller.py : Control system volume automatically.
- file_remover.py : Remove/Keep files in current working directory that match input directory or text file. Use with caution!
While transcoding a large amount of files with convert2mp3.py use the --enable-log flag to log what files where successfully transcoded.
In case of a crash/disconnect use "file_remover.py convert2mp3.log -k" to remove corrupted files and run convert2mp3.py again to resume
transcoding.