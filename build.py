import os 
import re 
import requests
import zipfile
import tempfile
import shutil
import exrex

DOWNLOAD_CHUNK_SIZE = 1024 * 64

def download(url, chunk_size=DOWNLOAD_CHUNK_SIZE):
	path = f'{tempfile.gettempdir()}/{exrex.getone(r"[a-z0-9]{32}")}'
	with requests.get(url, stream=True) as response:
		progress = 0
		total_size = int(response.headers.get("Content-Length"))
		with open(path, "wb") as file:
			for chunk in response.iter_content(chunk_size=chunk_size):
				progress += chunk_size
				print(round((progress / total_size) * 100, 2), "%", "   ", end="\r")
				file.write(chunk)
	return path

__version__ = re.findall(r"__version__\s*\=\s*[\"\'](.*?)[\"\']", open("mifs.py", "r").read())[0]

VERSION_FILE = f"""
VSVersionInfo(
	ffi=FixedFileInfo(
		filevers=({__version__.replace(".", ", ")}, 0, 0),
		prodvers=({__version__.replace(".", ", ")}, 0, 0),
		mask=0x3f,
		flags=0x0,
		OS=0x40004,
		fileType=0x1,
		subtype=0x0,
		date=(0, 0)
	),
	kids=[
		StringFileInfo(
			[
				StringTable(
					u'040904B0',
					[
						StringStruct(u'CompanyName', u'MIFS'),
						StringStruct(u'FileDescription', u'Make It Fucking Smaller. Encode/Compress video/audio/images/arbitrary files to the specified size'),
						StringStruct(u'FileVersion', u'{__version__}'),
						StringStruct(u'InternalName', u'MIFS'),
						StringStruct(u'LegalCopyright', u'https://github.com/nuukedo29/mifs'),
						StringStruct(u'OriginalFilename', u'mifs.exe'),
						StringStruct(u'ProductName', u'MIFS'),
						StringStruct(u'ProductVersion', u'{__version__}')
					]
				)
			]
		), 
		VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
	]
)
"""

if __name__ == "__main__":

	if not os.path.isdir("./dist"):
		os.mkdir("./dist")
	
	print("Moving 7z.exe")
	shutil.copy("7z.exe", "dist/7z.exe")

	# print("Downloading ffmpeg")
	# with zipfile.ZipFile(download("http://162.220.9.19/downloads4/2020-11-28-22-54-39-download-ffmpeg-N-100082-g81503ac58a-win64-gpl.zip"), "r") as zip_ref:
	# 	with open("dist/ffmpeg.exe", "wb") as file:
	# 		file.write(zip_ref.read("ffmpeg-N-100082-g81503ac58a-win64-gpl/bin/ffmpeg.exe"))
	print("Moving ffmpeg.exe")
	shutil.copy("ffmpeg.exe", "dist/ffmpeg.exe")
	
	print("Bundling mifs")
	with open("file_version_info.txt", "w") as file:
		file.write(VERSION_FILE)
	
	os.system(f'pyinstaller --onefile --version-file file_version_info.txt --noupx mifs.py')
	os.remove("file_version_info.txt")
