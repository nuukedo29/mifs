# MIFS - Make it fucking smaller 
When you cant be fucked to run ffmpeg and 7zip every time you want to share something on the internet.

This script automatically calculates the best possible parameters (bitrate, resolution, fps, etc...) and encodes video/audio/image files to stay under the specified target size (currently a constant `MAX_SIZE_DISCORD=1024*1024*8`). For arbitrary files and unknown filetypes it compresses them in 7z archives and splits them in multiple archives if required.

![preview](./doc/preview.png)

### Planned features
- Normie MSI installer 
- pypi package/script
- Better support for videos (right now its not guaranteed that video will stay under the target size)

## Installation
### Requirements 
- 75 iq points
- Python 3.7+
- Optionally `py -3.7 -m pip install -r requirements.txt`

### A. Use it like a retard
`py mifs.py ./path/to/file.ext`

### B. Install it in the context menu

Cant be fucked to write .reg files, so just use [Ultimate Windows Context Menu Customizer](http://www.door2windows.com/ultimate-windows-context-menu-customizer-customize-context-menu-in-windows-xp-vista-7/)

`py G:\_sync\mifs\mifs.py "%1"`

![howto_1](./doc/howto_1.png)


#### P.S.

Don't pay furries $4.99/$9.99 a month.