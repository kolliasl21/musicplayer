# Musicplayer and tools

- musicplayer_extended.py : Extended functionality.
- convert2mp3.py : Convert files to .mp3 in current working directory and save new files to a new directory.
- volume_controller.py : Control system volume automatically.
- file_remover.py : Remove/Keep files in current working directory that match input directory or text file. Use with caution!
While transcoding a large amount of files with convert2mp3.py use the --enable-log flag to log what files were successfully transcoded.
In case of a crash/disconnect use "file_remover.py /home/user/scripts/convert2mp3.log -k" to remove corrupted files and run convert2mp3.py again to resume
transcoding.
- musicplayer.sh : Modify this file to change input arguments and running parameters.

## Enable services

- Create .timer and .service files in /etc/systemd/user/
- Reload systemd daemons: $ systemctl --user daemon-reload
- Enable timer: $ systemctl --user enable musicplayerd.timer --now
- Enable services: $ systemctl --user enable volume-controller.service musicplayerd.service --now
- Start services if auto-login is disabled: loginctl enable-linger user