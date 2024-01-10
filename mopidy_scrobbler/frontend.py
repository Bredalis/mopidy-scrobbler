import logging  # Importing Python's logging module for handling logs
import time  # Importing Python's time module for time-related functionality

import pykka  # Importing Pykka for concurrency
import pylast  # Importing pylast, a Last.fm API wrapper

from mopidy.core import CoreListener  # Importing CoreListener from Mopidy library

# Configuring logger to track application events and messages
logger = logging.getLogger(__name__)

# Defining Last.fm API credentials
API_KEY = "2236babefa8ebb3d93ea467560d00d04"
API_SECRET = "94d9a09c0cd5be955c4afaeaffcaefcd"

# Tuple containing specific Last.fm errors
PYLAST_ERRORS = tuple(
    getattr(pylast, exc_name)
    for exc_name in (
        "ScrobblingError",
        "NetworkError",
        "MalformedResponseError",
        "WSError",
    )
    if hasattr(pylast, exc_name)
)

# Class representing the ScrobblerFrontend, acting as a Pykka actor and CoreListener
class ScrobblerFrontend(pykka.ThreadingActor, CoreListener):
    def __init__(self, config, core):
        super().__init__()
        self.config = config
        self.lastfm = None  # Initializing Last.fm instance
        self.last_start_time = None  # Initializing the start time of the last track

    # Method called when the actor starts
    def on_start(self):
        try:
            # Initializing the Last.fm network with provided credentials
            self.lastfm = pylast.LastFMNetwork(
                api_key=API_KEY,
                api_secret=API_SECRET,
                username=self.config["scrobbler"]["username"],
                password_hash=pylast.md5(self.config["scrobbler"]["password"]),
            )
            logger.info("Scrobbler connected to Last.fm")  # Logging successful connection
        except PYLAST_ERRORS as exc:
            logger.error(f"Error during Last.fm setup: {exc}")
            self.stop()

    # Method called when a track starts playing
    def track_playback_started(self, tl_track):
        track = tl_track.track
        artists = ", ".join(sorted([a.name for a in track.artists]))  # Extracting artist names
        duration = track.length and track.length // 1000 or 0  # Calculating track duration
        self.last_start_time = int(time.time())  # Storing current time as start time
        logger.debug(f"Now playing track: {artists} - {track.name}")  # Logging track details
        try:
            # Updating track details on Last.fm as currently playing
            self.lastfm.update_now_playing(
                artists,
                (track.name or ""),
                album=(track.album and track.album.name or ""),
                duration=str(duration),
                track_number=str(track.track_no or 0),
                mbid=(track.musicbrainz_id or ""),
            )
        except PYLAST_ERRORS as exc:
            logger.warning(f"Error submitting playing track to Last.fm: {exc}")

    # Method called when a track playback ends
    def track_playback_ended(self, tl_track, time_position):
        track = tl_track.track
        artists = ", ".join(sorted([a.name for a in track.artists]))  # Extracting artist names
        duration = track.length and track.length // 1000 or 0  # Calculating track duration
        time_position = time_position // 1000  # Converting time position to seconds
        # Checking conditions for scrobbling the track
        if duration < 30:
            logger.debug("Track too short to scrobble. (30s)")
            return
        if time_position < duration // 2 and time_position < 240:
            logger.debug(
                "Track not played long enough to scrobble. (50% or 240s)"
            )
            return
        if self.last_start_time is None:
            self.last_start_time = int(time.time()) - duration
        logger.debug(f"Scrobbling track: {artists} - {track.name}")  # Logging scrobbling details
        try:
            # Scrobbling the track details to Last.fm
            self.lastfm.scrobble(
                artists,
                (track.name or ""),
                str(self.last_start_time),
                album=(track.album and track.album.name or ""),
                track_number=str(track.track_no or 0),
                duration=str(duration),
                mbid=(track.musicbrainz_id or ""),
            )
        except PYLAST_ERRORS as exc:
            logger.warning(f"Error submitting played track to Last.fm: {exc}")
