from enum import Enum
import sys
from pathlib import Path
import os
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
ENCODED_DIR = Path("av1_sequences")
REPRESENTATIONS = {
    Quality.LOW:  Representation([640, 360], 15.0),
    Quality.MEDIUM:  Representation([1280, 720], 30.0),
    Quality.HIGH:  Representation([3840, 2160], 60.0)
}

QUALITY_IDS = {
    Quality.LOW: "0",
    Quality.MEDIUM: "1",
    Quality.HIGH: "2"
}

###### Helpers ######

# get all files from the path --> test sequences
def get_files(path: Path):
    return [p for p in path.iterdir() if p.is_file()]

# retrieve file name without extension
def get_filename(path: Path):
    return path.stem

# encode representations separately first into fragmented MP4s
def encode_representation(
    input_video: Path,
    output_mp4: Path,
    width: int,
    height: int,
    fps: float,
):
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    try: (
            ffmpeg
            .input(str(input_video.resolve()))
            .output(
                str(output_mp4),
                vcodec="libsvtav1",
                preset=8,
                vf=f"scale={width}:{height},fps={fps}",
                # adjust GOP size to segment size
                #g=round(fps * 5),
                movflags="+frag_keyframe+empty_moov+default_base_moof",
                an=None,   # no audio
            )
            .run(overwrite_output=True)
    )
    except ffmpeg.Error as e:
        print(f"An error occurred: {e}")

# multiplex representations --> create 1 MPD for all representations
def dash_mux(
    encoded_mp4s: list[Path],
    out_dir: Path,
    mpd_name: str,
):
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Create rep directories
    for q in REPRESENTATIONS.keys():
        # make the directory for each quality level where segments are saved
        (out_dir / QUALITY_IDS.get(q)).mkdir(parents=True, exist_ok=True)

    # grab the paths of the fragmented MP4s
    inputs = [ffmpeg.input(str(p.resolve())).video for p in encoded_mp4s]

    # save current working directory so we can return later
    original_cwd = os.getcwd()
    
    # switch cwd to the output directory (otherwise ffmpeg cannot find the correct files?)
    os.chdir(out_dir)
    print(f"Current CWD: {os.getcwd()}")
    #stream_indices = ",".join(QUALITY_IDS.values())
    #print("INDICES: " + stream_indices)
    
    out = ffmpeg.output(
            *inputs,
            str((out_dir / mpd_name).resolve()),
            format="dash",
            vcodec="copy",  
            #use_template=1,
            #use_timeline=1,
            an=None, 
            sn=None,
            seg_duration=5,
            adaptation_sets= "id=0,streams=v",
            init_seg_name="$RepresentationID$/init.mp4",
            media_seg_name="$RepresentationID$/chunk_$Number%05d$.m4s",
        )
    #for i in range(len(inputs)):
    #    out = out.global_args("-map", f"{i}:v")
    
    out.run(overwrite_output=True)
    
    os.chdir(original_cwd)

# dashify the passed video
def dashify(video: Path):
    encoded_mp4s = []
    video_name = get_filename(video)

    # build directories for the fragmented MP4s per video per representation
    (ENCODED_DIR / video_name).mkdir(parents=True, exist_ok=True)

    for q, rep in REPRESENTATIONS.items():
        # name the files after their quality 'name'
        out_mp4 = ENCODED_DIR / video_name / f"{q.name}.mp4"

        # only change resolution and framerate per representation
        encode_representation(
            input_video=video,
            output_mp4=out_mp4,
            width=rep.resolution[0],
            height=rep.resolution[1],
            fps=rep.framerate
        )

        encoded_mp4s.append(out_mp4)

    # pass fragmented MP4s to muxer
    dash_mux(
    encoded_mp4s=encoded_mp4s,
    out_dir=DASH_DIR / video_name,
    mpd_name=f"{video_name}.mpd"
)

# dashify all videos
def dashify_all(videos):
    for video in videos:
        dashify(video)

# encode the video with AV1 for DASH
def encode_av1(video: Path):

    # save current working directory so we can return later
    original_cwd = os.getcwd()

    video_name = get_filename(video)
    out_dir = DASH_DIR / video_name
    out_dir.mkdir(parents=True, exist_ok=True)

    # use 'resolve' to get absolute path
    output_mpd = (out_dir / f"{video_name}.mpd").resolve()

    # use 'resolve' to get absolute path
    input_stream = ffmpeg.input(str(video.resolve()))

    video_streams = []

    # iterate over both quality levels and there representations (via 'items')
    for q, rep in REPRESENTATIONS.items():
        w, h = rep.resolution
        fps = rep.framerate

        # make the directory for each quality level where segments are saved
        (out_dir / QUALITY_IDS.get(q)).mkdir(parents=True, exist_ok=True)

        # for each quality level only change resolution and framerate
        v = (
            input_stream
            .video
            .filter("scale", w, h)
            .filter("fps", fps=fps)
        )
        
        # save all video streams to pass to ffmpeg
        video_streams.append(v)

    print(f"Encoding: {video} -> {output_mpd}")

    try:
        # switch cwd to the output directory (otherwise ffmpeg cannot find the correct files?)
        os.chdir(out_dir)
        (
            # encode all video streams (= different versions) and save segments to the directory
            # of the current quality level
            # remove audio for now
            ffmpeg
            .output(
                *video_streams,
                str(output_mpd), 
                format="dash", 
                vcodec="libsvtav1", 
                preset=8,
                seg_duration=5,
                adaptation_sets="id=0,streams=v",
                an=None,
                init_seg_name=  "$RepresentationID$/init.mp4",
                media_seg_name= "$RepresentationID$/chunk_$Number%05d$.m4s")
            .run(overwrite_output=True)
        )
    except ffmpeg.Error as e:
        print(f"An error occurred: {e}")
    finally:
        #return to original working directory when done
        os.chdir(original_cwd)

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
        dashify(video_path)

    elif len(sys.argv) > 2:
        print(
            f"Too many arguments.\n"
            f"Usage: python {Path(sys.argv[0]).name} <video name>\n"
            f"If omitted, all videos will be encoded."
        )

    else:
        # Encode all videos
        videos = get_files(TEST_SEQ_DIR)
        dashify_all(videos)
