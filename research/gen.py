import math
import os
import os.path
import io
import random
import PIL
import PIL.Image
import glob
import numba



def entropy_bytes(file):
	if type(file) == str:
		file = open(file, "rb")
		
	entropy = 0
	for byte in file:
		if byte == 0: continue
		probability = (1.0 * count / total)
		entropy -= probability * math.log(probability, 256)

	return entropy


@numba.jit(nopython=True)
def fast_noise(width, height, pallet, min, max):
	data = []
	for x in range(width):
		for y in range(height):
			data.append([random.randint(min, max) for n in range(pallet)])
	return data

def generate_noise(width, height, pallet=3, min=0, max=255):
	return [ tuple(value) for value in fast_noise(width, height, pallet, min, max) ]

SIZES = [
	[1280, 720],
	[128, 128],
]
PALLETS = [ "RGB", "RGBA" ]
FORMATS = [ "jpeg", "jpg", "png", "webp" ]
NOISES = [
	[0, 255],
	[0, 1],
	[1, 1],
	[20, 50],
	[70, 128]
]
FOLDERS = ["memes_reddit"]

if __name__ == "__main__":

	output = open("./data/data.csv", "w")

	# for pallet in PALLETS:
	# 	for width, height in SIZES:
	# 		image = PIL.Image.new(pallet, (width, height))
			
	# 		for noise in NOISES:
	# 			image.putdata(generate_noise(
	# 				width, 
	# 				height, 
	# 				pallet=3 if pallet == "RGB" else 4,
	# 				min=noise[0],
	# 				max=noise[1]
	# 			))
	# 			for format in FORMATS:
	# 				if pallet == "RGBA" and format == "jpeg": continue

	# 				file = io.BytesIO()
	# 				image.save(file, format=format)
	# 				# image.save("test.png")

	# 				file.seek(0, os.SEEK_END)
	# 				file_size = file.tell()
	# 				file.seek(0)

	# 				entropy = entropy_bytes(file)

	# 				file_name = f'noise_{pallet}_{width}x{height}_{noise[0]}x{noise[0]}.{format}'

	# 				print(file_name, entropy, file_size)

	# 				output.write(f'{file_name},{format.replace("jpeg", "jpg")},{entropy},{file_size}\n')
	# 				output.flush()


	# https://www.kaggle.com/sayangoswami/reddit-memes-dataset
	# Normie memes
	for folder in FOLDERS:
		for format in FORMATS:
			for image in glob.glob(f'./data/{folder}/*.{format}'):

				file_name = os.path.basename(image) 

				image = PIL.Image.open(image)							

				file = io.BytesIO()
				image.resize([512, 512]).convert("RGB").save(file, format=format.replace("jpg", "jpeg"))

				# file = open(image, "rb")

				file.seek(0, os.SEEK_END)
				file_size = file.tell()
				file.seek(0)

				entropy = entropy_bytes(file)			

				print(file_name, file_size, entropy)

				output.write(f'{file_name},{format.replace("jpeg", "jpg")},{entropy},{file_size}\n')
				output.flush()