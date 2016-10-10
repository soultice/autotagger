# autotagger
Automatically tag your mp3s with this python script

## installation

1. Clone this repository
3. Install requirements 'pip install -r requirements.txt'
2. Download [The fpcalc static file for your system](https://acoustid.org/chromaprint)
3. Add it to your $PATH
4. Get an apikey for the application at [https://acoustid.org/](https://acoustid.org/)
5. Run the script 'python tagger.py --inpath --outpath --apikey --threshold'

## Usage

Currently, all files are tagged with artist and title id3 tags as long as they are found often enough in the response from acoustid.
The value can be changed via the '--threshold' parameter. 
All items are moved to the outpath directory (this is currently bugged, it is intended that the original mp3 files remain).
If acoustid does not match with a high enough certainity, you are asked to provide either a selection of artist, title, or both.
If you do not provide a selection the tagger will pick the highest rated and move on with the process.

