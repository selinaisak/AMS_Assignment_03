import sys
from pathlib import Path
# pip install ffmpeg-python
# not just 'ffmpeg' --> may not work!
import ffmpeg


### SOURCES ###
# https://stackoverflow.com/questions/3207219/how-do-i-list-all-files-of-a-directory #
# https://medium.com/@aleksej.gudkov/ffmpeg-python-example-a-guide-to-using-ffmpeg-with-python-020cdb7733e7 #
# https://trac.ffmpeg.org/wiki/Encode/AV1 #


TEST_SEQ_DIR = Path("test_sequences")
AV1_DIR = Path("av1_sequences")

###### Helpers ######

# get all files from the path --> test sequences
def get_files(path: Path):
    return [p for p in path.iterdir() if p.is_file()]

# retrieve file name without extension
def get_filename(path: Path):
    return path.stem

# encode the video with AV1 --> keep initial config
def encode_av1(video: Path):

    output = AV1_DIR / f"{get_filename(video)}.mp4"
    print(f"Encoding: {video} -> {output}")

    try:
        (
            ffmpeg
            .input(str(video))
            .output(str(output), vcodec="libsvtav1")
            .run()
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
