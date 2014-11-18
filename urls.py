from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from player.views import Player, ArtistList, TrackList

urlpatterns = patterns(
    'player.views',
    url(r'^$',
        view=login_required(Player.as_view()),
        name='player',
    ),
    url(r'^artists$',
        view=ArtistList.as_view(),
        name='player_artists',
    ),
    url(r'^tracks/(?P<slug>[-\w]+)/$',
        view=TrackList.as_view(),
        name='player_tracks',
    ),
)
