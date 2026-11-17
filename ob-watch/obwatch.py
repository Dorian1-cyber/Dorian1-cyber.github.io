# OB Watch on iPhone: saves a YouTube video's sound into iCloud Drive/OB Watch Audio, from the a-Shell app.
# Run by the "OB Watch MP3" Shortcut, after `jump obwatch` (the bookmark of that folder). One request per run:
#   save <id>    the video's sound as "<title> [<id>].mp3" (or .m4a, the same sound, if ffmpeg can't convert here)
#   delete <id>  that video's audio
#   clear        every audio file in the folder (and unfinished downloads)
#   list         the audio files
# It prints one line for OB Watch: "OBW OK <op> <json>", "OBW LIST <json>" or "OBW ERR <reason>".
# It only ever touches files in a folder named "OB Watch Audio", and only audio files and yt-dlp's leftovers.
import json
import os
import re
import sys

FOLDER_NAME = "OB Watch Audio"
ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
AUDIO = (".mp3", ".m4a")
LEFTOVER = (".part", ".ytdl", ".webm", ".m4a.part", ".temp", ".tmp")


def say(line):
    print("OBW " + line)
    sys.stdout.flush()


def video_files(folder, vid=None):
    out = []
    for name in sorted(os.listdir(folder)):
        m = re.search(r"\[([A-Za-z0-9_-]{11})\]\.[^\[\]]+$", name)
        if not m or (vid and m.group(1) != vid):
            continue
        out.append((m.group(1), name))
    return out


def audio_list(folder):
    return [{"id": v, "file": n} for v, n in video_files(folder) if n.endswith(AUDIO)]


def remove(folder, names):
    gone = 0
    for n in names:
        try:
            os.remove(os.path.join(folder, n))
            gone += 1
        except OSError:
            pass
    return gone


def save(folder, vid):
    try:
        import yt_dlp
    except ImportError:
        return say("ERR yt-dlp isn't installed in a-Shell. In a-Shell, run: pip install yt-dlp")
    url = "https://www.youtube.com/watch?v=" + vid
    base = {"outtmpl": os.path.join(folder, "%(title).100B [%(id)s].%(ext)s"), "noplaylist": True, "quiet": True,
            "no_warnings": True, "windowsfilenames": True, "noprogress": True}
    tries = [
        dict(base, format="bestaudio/best", postprocessors=[{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "0"}]),
        dict(base, format="bestaudio[ext=m4a]/bestaudio"),  # no ffmpeg here: keep YouTube's own audio (.m4a)
    ]
    last = ""
    for opts in tries:
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
        except Exception as e:  # yt-dlp's DownloadError and friends
            last = str(e)
            remove(folder, [n for v, n in video_files(folder, vid) if not n.endswith(AUDIO)])
            if not re.search(r"ffmpeg|ffprobe|postprocess", last, re.I):
                break
            continue
        done = [n for v, n in video_files(folder, vid) if n.endswith(AUDIO)]
        remove(folder, [n for v, n in video_files(folder, vid) if not n.endswith(AUDIO)])
        if done:
            return say("OK save " + json.dumps({"id": vid, "file": done[0]}))
        last = "yt-dlp finished but no audio file was made."
    reason = re.sub(r"^ERROR:\s*", "", last.strip().splitlines()[-1] if last.strip() else "yt-dlp stopped.")
    if re.search(r"Private video|Video unavailable", last):
        reason = "The video is private or unavailable."
    elif re.search(r"Sign in to confirm", last):
        reason = "YouTube wants a signed-in viewer for this video, so it can't be saved."
    elif re.search(r"HTTP Error 403|nsig|Unable to extract", last):
        reason = "YouTube refused yt-dlp; update it in a-Shell: pip install -U yt-dlp"
    say("ERR " + reason[:300])


def main(argv):
    folder = os.getcwd()
    if os.path.basename(os.path.normpath(folder)) != FOLDER_NAME:
        return say("ERR The OB Watch Audio folder isn't set up in a-Shell. In a-Shell: pickFolder (choose iCloud Drive, then OB Watch Audio), then: bookmark obwatch")
    op = argv[0] if argv else ""
    vid = argv[1] if len(argv) > 1 else ""
    if op in ("save", "delete") and not ID_RE.match(vid):
        return say("ERR That isn't a YouTube video id.")
    if op == "save":
        return save(folder, vid)
    if op == "delete":
        n = remove(folder, [n for v, n in video_files(folder, vid)])
        return say("OK delete " + json.dumps({"id": vid, "removed": n}))
    if op == "clear":
        names = [n for v, n in video_files(folder)]
        names += [n for n in os.listdir(folder) if n.endswith(AUDIO + LEFTOVER) and n not in names]
        return say("OK clear " + json.dumps({"removed": remove(folder, names)}))
    if op == "list":
        return say("LIST " + json.dumps(audio_list(folder)))
    say("ERR Unknown request: " + " ".join(argv)[:80])


if __name__ == "__main__":
    main(sys.argv[1:])
