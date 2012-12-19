from django.db.models import Q
from django.views.generic import ListView, TemplateView

from basic.music.models import Band, Track


class Player(TemplateView):
    """
    Displays the player page.
    """
    template_name="player/player.html"


class ArtistList(ListView):
    template_name="player/artists.html"
    model = Band


class TrackList(ListView):
    template_name="player/tracks.html"

    def get_queryset(self):
        if 'slug' in self.kwargs and self.kwargs['slug']:
            return Track.objects.filter(
                Q(band__slug=self.kwargs['slug']) |
                Q(album__band__slug=self.kwargs['slug'])
            )
        else:
            return Track.objects.all()

    def get_paginate_by(self, queryset=None):
        if 'slug' in self.kwargs and self.kwargs['slug']:
            return 0
        else:
            return 20
