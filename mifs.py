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

__version__ = "0.6"

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
AUDIO_BITRATES = [8, 16, 24, 32, 40, 48, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320] # TODO: Anything below 64 kbps is a deepfried meme, should split audio if cant fit 64kbps in given size
VIDEO_BUDGET = { # How hard we need to scuff video in given bitrate
	# kbps : [height (p), fps]
	2000: [720, 60],
	1200: [720, 40],
	1000: [720, 30],
	600: [480, 30],
	200: [360, 24],
	100: [240, 20],
	50: [144, 15]
}
AUDIO_VIDEO_RATIO = 0.35 # What % of a video file we reserve for audio
# 1024x1024 color/alpha noise png (yuv420) = 1,990,732 bytes
# 1024*1024*PNG_NOISE_CONSTANT = 1990732 
# PNG_NOISE_CONSTANT = 1990732 / 1024 / 1024
# 1.8985099792480469
PNG_NOISE_CONSTANT = 1.8985099792480469 
FROZEN = getattr(sys, "frozen", False)

os.environ["PATH"] += os.pathsep + os.path.dirname(os.path.realpath(sys.executable if FROZEN else __file__))

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

def run_progress(command, parser=lambda X: 0, bar=lambda X: None):
	process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding="utf8")
	while True:
		# print(process.stdout.read())
		line = process.stdout.readline()
		if not line: break
		bar(parser(line.rstrip()))

def progress_ffmpeg(length):
	current_time = 1  
	def wrapper(line):
		nonlocal current_time
		match = re.findall(r"time\=(.*?) ", line)
		if match:
			current_time = timestamp_parse(match[0])
		return current_time / length 
	return wrapper
	
def progress_7z():
	progress = 0
	def wrapper(line):
		nonlocal progress
		match = re.findall(r"(?m)^\s*(\d+)\%", line)
		if match:
			progress = int(match[0])
		return progress / 100
	return wrapper

def progressbar(progress):
	print("[", ("="*int(progress * 40)).ljust(40), "]", f'{progress*100:0.2f}%', "   ", end="\r")

def round_bitrate_audio(bitrate):
	for bitrate_step in AUDIO_BITRATES[::-1]:
		if bitrate_step < bitrate:
			return bitrate_step
	return bitrate_step

def budget_for_bitrate(bitrate):
	for _bitrate, [height, fps] in VIDEO_BUDGET.items():
		if _bitrate < bitrate:
			return [height, fps]
	return [height, fps]

def clamp(number, min_number, max_number):
	return min(max(number, min_number), max_number)

if __name__ == "__main__":

	try:	
		file = sys.argv[1]

		filename, extension = os.path.splitext(os.path.basename(file))
		extension = extension.replace(".", "")
		folder = os.path.dirname(file) or "."
		size = os.stat(file).st_size

		if unidecode:
			filename = unidecode.unidecode(filename)

		filename = re.subn(r"[\/\\\?\%\*\:\|\"\<\>\.]", "", filename)[0]

		output_without_extension = f'{folder}/{filename}_{number_to_string(size)}_mifs'
		output = f'{output_without_extension}.{extension}'

		# Stage 1: Gather meta info
		# ___________________________________________

		duration = None
		bitrate = None
		video = None 
		audio = None
		alpha = False
		pixel_formats = {}

		if extension in EXTENSIONS_MEDIA:
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

		if not extension in EXTENSIONS_AUDIO:
			for pixel_format in re.finditer( r'(?m)^(?P<flags>[IOHPB\.]{5})\s+(?P<name>.*?)\s+(?P<components>\d+)\s+(?P<bits>\d+)\s*$', run(f'ffmpeg -pix_fmts')):
				pixel_format = pixel_format.groupdict()
				pixel_formats[pixel_format["name"]] = {
					"components": int(pixel_format["components"]),
					"bits": int(pixel_format["bits"])
				}

		# Stage 2: Calculate best bitrate, resolution, fps, etc..
		# ___________________________________________
		
		# TODO: Implement video/audio cutting 

		height = None
		width = None
		fps = None
		samplerate = None
		bitrate_audio = 0
		bitrate_video = 0
		channels = 2
		estimated_size = 0

		if audio and not audio["bitrate"]:
			audio["bitrate"] = 320

		if video and not video["bitrate"] and not extension in EXTENSIONS_IMAGE:
			video["bitrate"] = int(bitrate - (audio["bitrate"] if audio else 0))

		if audio:
			bitrate_audio = round_bitrate_audio(min(int(8*(MAX_SIZE_DISCORD-1024) * (1-AUDIO_VIDEO_RATIO if extension in EXTENSIONS_VIDEO else 1) / duration), audio["bitrate"]))
			samplerate = min(audio["samplerate"], 44100)

			estimated_size += (bitrate_audio * duration)/8

		if video:
			if extension in EXTENSIONS_IMAGE:
				# TODO: Implement optimization function based on research/entropy_to_filesize_corelation.md

				# WIDTH*HEIGHT*PNG_NOISE_CONSTANT = SIZE
				# WIDTH*HEIGHT = SIZE / PNG_NOISE_CONSTANT
				# PIXELS = SIZE / PNG_NOISE_CONSTANT

				ratio = video["height"] / video["width"]
				pixels = MAX_SIZE_DISCORD / PNG_NOISE_CONSTANT 

				height = int(min(pixels * ratio / video["width"], video["height"]))
				width = int(min(pixels * ratio / video["height"], video["width"]))

			else:				
				bitrate_video = min(int(8*((MAX_SIZE_DISCORD-1024)-estimated_size) / duration), video["bitrate"])
				budget_height, budget_fps = budget_for_bitrate(bitrate_video) 
				fps = min(video["fps"] or 0, budget_fps)
				height = min(video["height"], budget_height)
				width = int(video["width"] / abs(max(video["height"],height) / min(video["height"],height)))
				width = width - width % 2 # Make even

				if not extension in EXTENSIONS_AUDIO: 
					estimated_size += (bitrate_video * duration)/8

		# Stage 3: Encode
		# ___________________________________________

		if extension in EXTENSIONS_AUDIO:
			output = f'{output_without_extension}.mp3'
			print(f'''\
Encoding audio
bitrate: {bitrate_audio}kbps
estimated: ~{estimated_size/1024/1042:0.2f}MB 
			''')
			run_progress(
				" ".join([
					f'ffmpeg -y -i \"{file}\"',
					f'-map {audio["stream"]} -b:a {bitrate_audio}k -ac {channels}', 
					f'\"{output}\"'
				]),
				progress_ffmpeg(duration),
				progressbar
			)

		elif extension in EXTENSIONS_VIDEO:
			output = f'{output_without_extension}.mp4'
			print(f'''\
Encoding video
bitrate/audio: {bitrate_audio}kbps
bitrate/video: {bitrate_video}kbps
fps: {fps}
resolution: {width}x{height}
estimated: ~{estimated_size/1024/1042:0.2f}MB
			''')
			run_progress(
				" ".join([
					f'ffmpeg -y -i \"{file}\"', 
					f'{"-map "+video["stream"] if video else ""} -c:v libx264 -r {fps} -pix_fmt yuv420p -b:v {bitrate_video}k -vf "scale={width}x{height}"',
					f'{"-map "+audio["stream"] if audio else ""} -ab {bitrate_audio}k -ac {channels}',
					f'\"{output}\"'		
				]),
				progress_ffmpeg(duration),
				progressbar
			)

		elif extension in EXTENSIONS_IMAGE:
			output = f'{output_without_extension}.png'
			print(f'''\
Encoding image
resolution: {width}x{height}\
			''')
			run_progress(
				" ".join([
					f'ffmpeg -y -i \"{file}\"',
					f'-map {video["stream"]} -vf "scale={width}x{height}" -compression_level 100',
					f'\"{output}\"'
				]), 
			)

		else:
			output = f'{output_without_extension}.7z'
			if os.path.exists(output) or os.path.exists(f'{output}.001'): os._exit(0)
			run_progress(
				f'7z a -v{MAX_SIZE_DISCORD-1024} \"{output_without_extension}.7z\" \"{file}\"',
				progress_7z(),
				progressbar
			)

	except:
		print(":(\nOOPSIE WOOPSIE!!\n\nOOPSIE WOOPSIE!! Uwu We make a fucky wucky!! A wittle fucko boingo! The code monkeys at our headquarters are working VEWY HAWD to fix this!\n")
		traceback.print_exc()
		time.sleep(20)