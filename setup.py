import os 
import sys 
import setuptools 

setuptools.setup(
	name="mifs",
	version="",
	description="Make it fucking smaller. Encode/Compress video/audio/images/arbitrary files to the target size",
	long_description=open("./README.md", "r", encoding="utf8").read(),
	long_description_content_type="text/markdown",
	url="https://github.com/nuukedo29/mifs",
	keywords=["encode", "encoding", "audio", "video", "images", "music"],
	scripts=["mifs.py"],
	packages=setuptools.find_packages(),
	license='Unlicense',
	entry_points={
        "console_scripts": ["mifs=mifs:__main__"]
    },
	classifiers=[
        "Topic :: Utilities",
        'Environment :: Console',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
)