import fnmatch
import logging
from optparse import make_option
import os
import re

from mutagen.id3 import TCON, ID3, TIT1

from django.core.management.base import BaseCommand
from django.db.models import get_model
from django.db.utils import IntegrityError
from django.template.defaultfilters import slugify

from base.utils import configure_logging

Track = get_model('music', 'track')
Album = get_model('music', 'album')
Band = get_model('music', 'band')
Label = get_model('music', 'label')
Genre = get_model('music', 'genre')


class Command(BaseCommand):
    '''Indexes tracks
    '''
    help = __doc__
    args = 'directory'

    def get_id3(self, filename):
        fp = open(filename, 'r') 
        fp.seek(-128, 2)
        fp.read(3)
        title   = re.sub('\0.*', '', fp.read(30))
        artist  = re.sub('\0.*', '', fp.read(30))
        album   = re.sub('\0.*', '', fp.read(30))
        year = re.sub('\0.*', '', fp.read(4))
        fp.read(28)
        b = fp.read(1)
        if ord(b):
            track = ord(fp.read(1))
        else:
            track = 0
            fp.read(1)
        genre = ord(fp.read(1))
        fp.close()
        return {
            'title':title,
            'artist':artist,
            'album':album,
            'track': track,
            'genre': genre,
            'year': year,
        }

    def handle(self, *args, **options):
        '''Do the stuff.
        '''
        configure_logging(**options)
        for root, dirnames, filenames in os.walk(args[0]):
            for filename in fnmatch.filter(filenames, '*.mp3'):
                abspath = os.path.join(root, filename)
                logging.info('%s', abspath)
                if Track.objects.filter(mp3=abspath).exists():
                    continue
                #id3 = self.get_id3(abspath)
                try:
                    id3 = ID3(abspath)
                except Exception as e:
                    logging.warning(e)
                    continue

                album_band = track_band = album = title = genre = None
                num = 0
                if 'TRCK' in id3:
                    logging.info('Track:    %s', id3['TRCK'])
                    try:
                        num = int(id3['TRCK'].text[0])
                    except:
                        pass
                if 'TCON' in id3:
                    logging.info('Genre:    %s', id3['TCON'])
                    try:
                        genre, _created = Genre.objects.get_or_create(
                            title=id3['TCON'],
                            slug=slugify(id3['TCON']))
                    except IntegrityError:
                        genre = Genre.objects.get(slug=slugify(id3['TCON']))
                if 'TPE1' in id3:
                    logging.info('Artist 1: %s', id3['TPE1'])
                    try:
                        band, _created = Band.objects.get_or_create(
                            title=id3['TPE1'],
                            slug=slugify(id3['TPE1']))
                    except IntegrityError:
                        band = Band.objects.get(slug=slugify(id3['TPE1']))
                    track_band = album_band = band
                if 'TPE2' in id3:
                    logging.info('Artist 2: %s', id3['TPE2'])
                    try:
                        band, _created = Band.objects.get_or_create(
                            title=id3['TPE2'],
                            slug=slugify(id3['TPE2']))
                    except IntegrityError:
                        band = Band.objects.get(slug=slugify(id3['TPE2']))
                    album_band = band
                if 'TALB' in id3 and album_band:
                    logging.info('Album:    %s', id3['TALB'])
                    band_slug = '' if not album_band else album_band.slug
                    album, _created = Album.objects.get_or_create(
                        title=id3['TALB'],
                        band=album_band,
                        slug=slugify('%s %s' % (band_slug, id3['TALB']))
                    )
                    if genre:
                        album.genre.add(genre)
                if 'TIT1' in id3:
                    logging.info('Title:    %s', id3['TIT1'])
                    title = id3['TIT1']
                if 'TIT2' in id3:
                    logging.info('Title:    %s', id3['TIT2'])
                    title = id3['TIT2']
                if not title:
                    title = filename

                track, _created = Track.objects.get_or_create(
                    title=title,
                    band=track_band,
                    album=album,
                    mp3=abspath,
                    number=num
                )
        for track in Track.objects.all():
            if not os.path.exists(track.mp3):
                logging.info('Deleting %s', track.mp3)
                track.delete()
