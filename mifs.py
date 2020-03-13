#!/usr/bin/env python

import sys
import os 
import os.path
import shutil 
import time
import traceback
import subprocess
import re
import io

__version__ = "0.2"

try:
	import unidecode
except ImportError:
	unidecode = False

# TODO: Implement animated images, APNG, WEBP, GIF
EXTENSIONS_AUDIO = ["mp3", "wav", "flac", "m4a"]
EXTENSIONS_VIDEO = ["h264", "h265", "h266", "mp4", "mov", "avi", "webm", "mkv"]
EXTENSIONS_IMAGE = ["heic", "jfif", "jpe", "jpg", "jpeg", "png", "webp", "tif", "tiff", "bmp", "gif"]
EXTENSIONS_MEDIA = [*EXTENSIONS_AUDIO, *EXTENSIONS_VIDEO, *EXTENSIONS_IMAGE]
MAX_SIZE_DISCORD = 1024*1024*8
AUDIO_BITRATES = [8, 16, 24, 32, 40, 48, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]

os.environ["PATH"] += os.pathsep + os.path.dirname(os.path.realpath(sys.executable if getattr(sys, "frozen", False) else __file__))

def number_to_string(number):
	string = "{:.40f}".format(size).rstrip("0")
	return string[:-1] if string[-1] == "." else string

def timestamp_parse(timestamp):
	hours, minutes, seconds, milliseconds = re.split(r"\:|\.", timestamp)
	return (
		int(milliseconds) + 
		int(seconds) * 1000 +
		int(minutes) * 1000 * 60 +
		int(hours) * 1000 * 60 * 60
	)

def timestamp_create(length):
	return f"{int(length/1000/60/60)%24:02}:{int(length/1000/60)%60:02}:{int(length/1000)%60:02}.{int(length)%1000:03}"

def run(command):
	return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding="utf8").stdout.read()

def round_bitrate_audio(bitrate):
	for bitrate_step in AUDIO_BITRATES[::-1]:
		if bitrate_step < bitrate:
			return bitrate_step
	return bitrate_step

if __name__ == "__main__":

	try:	
		file = sys.argv[1]

		# TODO: Maybe add magic byte detection for extracting true extension?

		filename, extension = os.path.splitext(os.path.basename(file))
		extension = extension.replace(".", "")
		folder = os.path.dirname(file) or "."
		size = os.stat(file).st_size

		if unidecode:
			filename = unidecode.unidecode(filename)

		output_without_extension = f'{folder}/{filename}_{number_to_string(size)}_mifs'
		output = f'{output_without_extension}.{extension}'

		if size < MAX_SIZE_DISCORD:
			shutil.copy(file, output)
			os._exit(0)
		
		# Stage 1: Gather meta info
		# ___________________________________________

		duration = None
		bitrate = None
		video = None 
		audio = None

		if extension in EXTENSIONS_MEDIA:
			# TODO: Maybe use ffprobe instead?
			stdout = run(f'ffmpeg -i \"{file}\"')

			if not extension in EXTENSIONS_IMAGE:
				duration, bitrate = re.findall(r"Duration\: ([\d\:\.]+)\,.*?([\d\.]+) kb\/s", stdout)[0]
				duration = timestamp_parse(duration)
				bitrate = int(bitrate)
				
			for stream in re.finditer(r"(?m)Stream \#(?P<stream>\d+\:\d+).*?(?P<type>Audio|Video|Subtitle)\:.*?(?:.*?(?P<samplerate>[\d\.]+) Hz.*?)?(?:.*?(?P<resolution>(?P<width>\d+)x(?P<height>\d+))(?:,| \[).*?)?.*?(?:.*?(?P<bitrate>\d+) kb\/s.*?)?.*?(?:.*?(?P<fps>[\d\.]+) fps.*?)?$", stdout):
				stream = stream.groupdict()
				stream = {
					**stream,
					**({"samplerate": int(stream["samplerate"])} if stream["samplerate"] else {}),
					**({"width": int(stream["width"])} if stream["width"] else {}),
					**({"height": int(stream["height"])} if stream["height"] else {}),
					**({"bitrate": int(stream["bitrate"])} if stream["bitrate"] else {}),
					**({"fps": float(stream["fps"])} if stream["fps"] else {}) 
				}
				if not video and stream["type"] == "Video":
					video = stream
				if not audio and stream["type"] == "Audio":
					audio = stream

		# Stage 2: Calculate best bitrate, resolution, fps, etc..
		# ___________________________________________
		
		height = None
		width = None
		fps = None
		samplerate = None
		bitrate_audio = None
		bitrate_video = None
		channels = 2

		# TODO: Change resolution dynamically
		# TODO: Calculate best maximum bitrate for video

		if video:
			height = min(video["height"], 480)
			width = int(video["width"] / abs(max(video["height"],height) / min(video["height"],height)))
			width = width - width % 2 # Make even
			fps = min(video["fps"] or 0, 24)

		if audio:
			bitrate_audio = round_bitrate_audio(min(320, int(8*(MAX_SIZE_DISCORD-1024) / duration)))
			samplerate = min(audio["samplerate"], 44100)

		# Stage 3: Encode
		# ___________________________________________

		if extension in EXTENSIONS_AUDIO:
			output = f'{output_without_extension}.mp3'
			if os.path.exists(output): os._exit(0)
			os.system(" ".join([
				f'ffmpeg -loglevel error -i \"{file}\"',
				f'-map {audio["stream"]} -b:a {bitrate_audio}k -ac {channels}', 
				f'\"{output}\"'
			]))

		elif extension in EXTENSIONS_VIDEO:
			output = f'{output_without_extension}.mp4'
			if os.path.exists(output): os._exit(0)
			os.system(" ".join([
				f'ffmpeg -loglevel error -i \"{file}\"', 
				f'{"-map "+video["stream"] if video else ""} -c:v libx264 -pix_fmt yuv420p -maxrate 2M -bufsize 1M -vf "scale={width}x{height}"',
				f'{"-map "+audio["stream"] if audio else ""} -ab 128k -ac 2',
				f'\"{output}\"'		
			]))

		elif extension in EXTENSIONS_IMAGE:
			output = f'{output_without_extension}.png'
			if os.path.exists(output): os._exit(0)
			os.system(" ".join([
				f'ffmpeg -loglevel error -i \"{file}\"'
				f'-map {video["stream"]} -vf "scale={width}x{height}"',
				f'\"{output}\"'
			]))

		else:
			output = f'{output_without_extension}.7z'
			if os.path.exists(output) or os.path.exists(f'{output}.001'): os._exit(0)
			os.system(f'7z a -v{MAX_SIZE_DISCORD-1024} \"{output_without_extension}.7z\" \"{file}\"')

	except:
		print(":(\nOOPSIE WOOPSIE!!\n\nOOPSIE WOOPSIE!! Uwu We make a fucky wucky!! A wittle fucko boingo! The code monkeys at our headquarters are working VEWY HAWD to fix this!\n")
		traceback.print_exc()
		time.sleep(3)