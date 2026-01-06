from enum import Enum
import sys
from pathlib import Path
# pip install ffmpeg-python
# not just 'ffmpeg' --> may not work!
import ffmpeg


### SOURCES ###
# https://stackoverflow.com/questions/3207219/how-do-i-list-all-files-of-a-directory #
# https://medium.com/@aleksej.gudkov/ffmpeg-python-example-a-guide-to-using-ffmpeg-with-python-020cdb7733e7 #
# https://trac.ffmpeg.org/wiki/Encode/AV1 #

class Quality(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Representation:
    def __init__(self, resolution: tuple[int, int], framerate: float):
        self.resolution = resolution
        self.framerate = framerate

TEST_SEQ_DIR = Path("test_sequences")
DASH_DIR = Path("av1_dash")
REPRESENTATIONS = {
    #Quality.HIGH:  Representation([3840, 2160], 60.0),
    Quality.MEDIUM:  Representation([1280, 720], 30.0),
    Quality.LOW:  Representation([640, 360], 15.0)
}

###### Helpers ######

# get all files from the path --> test sequences
def get_files(path: Path):
    return [p for p in path.iterdir() if p.is_file()]

# retrieve file name without extension
def get_filename(path: Path):
    return path.stem

# encode the video with AV1 --> keep initial config
def encode_av1(video: Path):

    video_name = get_filename(video)
    out_dir = DASH_DIR / video_name
    out_dir.mkdir(parents=True, exist_ok=True)
    output_mpd = out_dir / f"{video_name}.mpd"

    input_stream = ffmpeg.input(str(video))

    video_streams = []

    for rep in REPRESENTATIONS.values():
        w, h = rep.resolution
        fps = rep.framerate

        v = (
            input_stream
            .video
            .filter("scale", w, h)
            .filter("fps", fps=fps)
        )

        video_streams.append(v)

    print(f"Encoding: {video} -> {output_mpd}")

    try:
        (
            ffmpeg
            .output(
                *video_streams,
                str(output_mpd), 
                format="dash", 
                vcodec="libsvtav1", 
                seg_duration=5,
                adaptation_sets="id=0,streams=v",
                an=None)
            .run(overwrite_output=True)
        )
    except ffmpeg.Error as e:
        print(f"An error occurred: {e}")

# encode all videos with AV1
def encode_av1_all(videos):
    for video in videos:
        encode_av1(video)




###### Main ######

if __name__ == "__main__":

    #sys.argv[0] is the program name
    #sys.argv[1] is the 1st argument --> here: video name (in case we want to encode single video)
    
    if len(sys.argv) == 2:
        # Encode a single video
        video_path = TEST_SEQ_DIR / sys.argv[1]
        if not video_path.exists():
            print(f"File not found: {video_path}")
            sys.exit(1)
        encode_av1(video_path)

    elif len(sys.argv) > 2:
        print(
            f"Too many arguments.\n"
            f"Usage: python {Path(sys.argv[0]).name} <video name>\n"
            f"If omitted, all videos will be encoded."
        )

    else:
        # Encode all videos
        videos = get_files(TEST_SEQ_DIR)
        encode_av1_all(videos)
