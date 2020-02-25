import sys
import os 
import os.path
import shutil 
import time
import traceback

try:
	import unidecode
except ImportError:
	unidecode = False

EXTENSIONS_AUDIO = ["mp3", "wav", "flac", "m4a"]
EXTENSIONS_VIDEO = ["h264", "mp4", "mov", "avi", "webm", "mkv"]
EXTENSIONS_IMAGE = ["jpg", "jpeg", "png", "webp", "gif"]
MAX_SIZE_DISCORD = 1024*1024*8

def number_to_string(number):
	string = "{:.40f}".format(size).rstrip("0")
	return string[:-1] if string[-1] == "." else string

if __name__ == "__main__":

	try:	

		file = sys.argv[1]

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

		# TODO: Extract length and calculate best bitrate/resolution possible within target size
		# TODO: Properly escape windows paths

		if extension in EXTENSIONS_AUDIO:
			output = f'{output_without_extension}.mp3'
			if os.path.exists(output): os._exit(0)
			os.system(f'ffmpeg -loglevel error -i \"{file}\" -ab 128k \"{output}\"')

		elif extension in EXTENSIONS_VIDEO:
			output = f'{output_without_extension}.mp4'
			if os.path.exists(output): os._exit(0)
			os.system(f'ffmpeg -loglevel error -i \"{file}\" -ab 128k -maxrate 2M -bufsize 1M -vf "scale=480:-2" \"{output}\"')

		elif extension in EXTENSIONS_IMAGE:
			output = f'{output_without_extension}.png'
			if os.path.exists(output): os._exit(0)
			os.system(f'ffmpeg -loglevel error -i \"{file}\" -vf "scale=480:-2" \"{output}\"')

		else:
			output = f'{output_without_extension}.7z'
			if os.path.exists(output) or os.path.exists(f'{output}.001'): os._exit(0)
			os.system(f'7z a -v{MAX_SIZE_DISCORD-1024} \"{output_without_extension}.7z\" \"{file}\"')

	except:
		print(":(\nOOPSIE WOOPSIE!!\n\nOOPSIE WOOPSIE!! Uwu We make a fucky wucky!! A wittle fucko boingo! The code monkeys at our headquarters are working VEWY HAWD to fix this!\n")
		traceback.print_exc()
		time.sleep(3)