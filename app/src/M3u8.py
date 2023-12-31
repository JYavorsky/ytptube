import math
import os
from urllib.parse import quote
from src.Utils import calcDownloadPath
from src.ffprobe import FFProbe
from src.Config import Config


class M3u8:
    ok_vcodecs: tuple = ('h264', 'x264', 'avc',)
    ok_acodecs: tuple = ('aac', 'mp3',)

    segment_duration: float = 10.000000
    config: Config = None
    download_path: str = None

    def __init__(self, config: Config, segment_duration: float = 6.000000):
        self.config = config
        self.download_path = self.config.download_path
        self.segment_duration = float(segment_duration)

    def make_stream(self, file: str):
        realFile: str = calcDownloadPath(
            basePath=self.download_path,
            folder=file,
            createPath=False
        )

        if not os.path.exists(realFile):
            raise Exception(f"File {realFile} does not exist.")

        try:
            ffprobe = FFProbe(realFile)
        except UnicodeDecodeError as e:
            pass

        if not 'duration' in ffprobe.metadata:
            raise Exception(f"Unable to get {realFile} duration.")

        duration: float = float(ffprobe.metadata.get('duration'))

        m3u8 = "#EXTM3U\n"
        m3u8 += "#EXT-X-VERSION:3\n"
        m3u8 += f"#EXT-X-TARGETDURATION:{int(self.segment_duration)}\n"
        m3u8 += "#EXT-X-MEDIA-SEQUENCE:0\n"
        m3u8 += "#EXT-X-PLAYLIST-TYPE:VOD\n"

        segmentSize: float = '{:.6f}'.format(self.segment_duration)
        splits: int = math.ceil(duration / self.segment_duration)

        segmentParams = {
        }

        for stream in ffprobe.streams:
            if stream.is_video():
                if stream.codec_name not in self.ok_vcodecs:
                    segmentParams['vc'] = 1
            if stream.is_audio():
                if stream.codec_name not in self.ok_acodecs:
                    segmentParams['ac'] = 1

        for i in range(splits):
            if (i + 1) == splits:
                segmentParams.update({
                    'sd': '{:.6f}'.format(duration - (i * self.segment_duration))
                })
                m3u8 += f"#EXTINF:{segmentParams['sd']}, nodesc\n"
            else:
                m3u8 += f"#EXTINF:{segmentSize}, nodesc\n"

            m3u8 += f"{self.config.url_host}{self.config.url_prefix}segments/{i}/{quote(file)}"
            if len(segmentParams) > 0:
                m3u8 += '?'+'&'.join([f"{key}={value}" for key,
                                      value in segmentParams.items()])
            m3u8 += "\n"

        m3u8 += "#EXT-X-ENDLIST\n"

        return m3u8

    def parseDuration(self, duration: str):
        if duration.find(':') > -1:
            duration = duration.split(':')
            duration.reverse()
            duration = sum([float(duration[i]) * (60 ** i)
                           for i in range(len(duration))])
        else:
            duration = float(duration)

        return duration
