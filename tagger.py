from __future__ import print_function, division
import os
import sys
import select
import acoustid
import mutagen
from mutagen.easyid3 import EasyID3 as ID
from collections import Counter, defaultdict
import logging
import click
import time
import re

logging.basicConfig(level=logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

class Autotagger(object):

    def __init__(self, apikey, th=3):
        initlogger = logging.getLogger()
#        self._apikey = 'w7dFAF0atP'
        self._apikey = apikey
        self._th = th
        initlogger.info("Threshold {}, Apikey {}".format(
                         self._apikey, self._th))
        self._wait = 0

    def _stringformatter(self, listoftups):
        string_list = [str(x) + ' ' + str(y) for x, y in listoftups]
        string_list = '\n'.join(string_list)
        return string_list

    def _optionpicker(self, counter, best_match, art_tit, time=5):
        self._wait = True
        picklocker = logging.getLogger()
        picklocker.debug("Time is set to {}".format(time))
        possibs = zip(range(len(counter.keys())), counter.keys())
        possibs_print = self._stringformatter(possibs)
        print("please select a {} from the list: \n{}".format(art_tit, possibs_print))
        print('if no selection is made for five seconds,')
        print('the highest ranked {} will be picked'.format(art_tit))
        i, o, e = select.select([sys.stdin], [], [], 5)
        if (i):
            possibs_select = sys.stdin.readline().strip()
            return counter[possibs_select][1]
        else:
            return best_match

    def _file_iter(self, filepath):
        comp_files = defaultdict()
        for root, dirs, files in os.walk(os.path.join(filepath)):
            comp_files[root] = []
            for fil in files:
                if fil.endswith('.mp3'):
                    comp_files[root].append(fil)
        return comp_files

    def tag_and_rename(self, filepath, filename, outpath, artist, title):
        path_to_file = os.path.join(filepath, filename)
        userpath = os.path.expanduser('~')
        rel_filepath = re.sub(userpath, '', filepath)
        rel_outpath = re.sub(userpath, '', outpath)
#        outpath = os.path.join(userpath, rel_outpath, rel_filepath)
        outpath = userpath + rel_outpath + rel_filepath
        if not os.path.exists(outpath):
            os.makedirs(outpath)
        try:
            audio_file = ID(path_to_file)
        except mutagen.id3.ID3NoHeaderError:
            audio_file = mutagen.File(path_to_file, easy=True)
            audio_file.add_tags()
        audio_file.delete()
        audio_file['artist'] = 'artist'
        audio_file['title'] = 'title'
        audio_file.save()
        print("Renaming to: {} - {}.mp3".format(artist, title))
        os.rename(path_to_file, os.path.join(outpath, artist + ' - ' + title + '.mp3'))

    def recognize(self, filepath):
        if self._wait is True:
            self._wait = False
        else:
            time.sleep(0.333)
        artist_counter = Counter()
        title_counter = Counter()
        result = acoustid.match(self._apikey, filepath)
        for _, _, title, artist in result:
            artist_counter.update([artist])
            title_counter.update([title])
        try:
            artist_best_match = artist_counter.most_common(1)[0][0]
            title_best_match = title_counter.most_common(1)[0][0]
        except IndexError:
            return None, None

        if artist_best_match >= self._th and title_best_match >= self._th:
            artist = artist_best_match
            title = title_best_match

        elif artist_best_match < self._th and title_best_match >= self._th:
            artist = self._optionpicker(artist_counter, artist_best_match, 'artist')
            title = title_best_match

        elif artist_best_match >= self._th and title_best_match < self._th:
            artist = artist_best_match
            title = self._optionpicker(title_counter, title_best_match, 'title')

        elif artist_best_match < self._th and title_best_match < self._th:
            title = self._optionpicker(title_counter, title_best_match, 'title')
            artist = self._optionpicker(artist_counter, artist_best_match, 'artist')

        return artist, title


if __name__ == "__main__":
    @click.command()
    @click.option('--inpath', required=True)
    @click.option('--outpath', type=str, required=True)
    @click.option('--threshold', type=int)
    @click.option('--apikey', type=unicode, required=True)
    def cli(inpath, outpath, apikey, threshold):
        mainlogger = logging.getLogger()
        mainlogger.setLevel(logging.INFO)
        tagger = Autotagger(apikey, threshold)
        walk = tagger._file_iter(inpath)
        renamed = 0
        left_aside = 0
        for rootpath, filenames in walk.iteritems():
            for current_file in filenames:
                artist, title = tagger.recognize(os.path.join(rootpath, current_file))
                if artist is not None and title is not None:
                    tagger.tag_and_rename(rootpath, current_file, outpath, artist, title)
                    renamed += 1
                else:
                    left_aside += 1
                    mainlogger.info("Couldn't find match for {}, skipping"
                                    .format(current_file))
        mainlogger.info("Tagged {} files, left {} aside. Total files: {}".format(
                        renamed, left_aside, renamed + left_aside))
    cli()
