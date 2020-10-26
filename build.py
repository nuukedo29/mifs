import os 
import re 
import requests
import zipfile
import tempfile
import shutil
import exrex

def download(url):
	path = f'{tempfile.gettempdir()}/{exrex.getone(r"[a-z0-9]{32}")}'
	with requests.get(url, stream=True) as response:
		with open(path, "wb") as file:
			for chunk in response.iter_content(chunk_size=8192):
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

	print("Downloading ffmpeg")
	with zipfile.ZipFile(download("https://github.com/GyanD/codexffmpeg/releases/download/2020-10-21-git-289e964873/ffmpeg-2020-10-21-git-289e964873-essentials_build.zip"), "r") as zip_ref:
		with open("dist/ffmpeg.exe", "wb") as file:
			file.write(zip_ref.read("ffmpeg-2020-10-21-git-289e964873-essentials_build/bin/ffmpeg.exe"))
	
	print("Bundling mifs")
	with open("file_version_info.txt", "w") as file:
		file.write(VERSION_FILE)
	
	os.system(f'pyinstaller --onefile --version-file file_version_info.txt mifs.py')
	os.remove("file_version_info.txt")
