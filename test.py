import os
import glob
import subprocess
import re

def run(command):
	return subprocess.Popen(
		command, 
		stdout=subprocess.PIPE, 
		stderr=subprocess.STDOUT, 
		universal_newlines=True, 
		encoding="utf8"
	).stdout.read()

def glob_remove(pattern):
	for file in glob.glob(pattern):
		os.remove(file)
		
if __name__ == "__main__":

	glob_remove("_test/*_mifs.*")

	for file in glob.glob("_test/*"):
		glob_remove("_test/*_mifs.*")
		output = run(f'py mifs.py "{file}"')
		filename, extension = os.path.splitext(os.path.basename(file))
		output_file = glob.glob(f'_test/*_mifs.*')[0]
		size_input = os.stat(file).st_size
		size_output = os.stat(output_file).st_size
		print( f'{file} {size_input}=>{size_output} ({(1 if size_input < size_output else -1)*round((size_input/size_output)*100, 2)}%)' )
		for key, value in re.findall(r"(?m)^(.*?)\: ([^\s]+)", output):
			print(f'  {key}: {value}')