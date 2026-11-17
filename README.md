# Dorian1-cyber.github.io
## ob-watch/player.html

The phone player page for the OB Watch Obsidian plugin. Obsidian on iPhone and iPad sends YouTube no referrer, so YouTube refuses its embedded player (Error 153). This page embeds the player from an https address instead. It reads only a video id, a start time and autoplay from its address, and holds no personal data.

## ob-watch/obwatch.py

OB Watch's iPhone helper: run in the a-Shell app by the "OB Watch MP3" Shortcut, it saves a YouTube video's sound into iCloud Drive/OB Watch Audio with yt-dlp, deletes it, lists the folder, or clears it. It only touches audio files in a folder named "OB Watch Audio".
