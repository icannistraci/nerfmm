import os
import cv2
import argparse
from pathlib import Path


def main():
    new_dir = Path(os.path.join(out_dir, name_out_dir))
    new_dir.mkdir(parents=True, exist_ok=True)

    video_capture = cv2.VideoCapture(file)
    success, frame = video_capture.read()
    saved_frame = 0

    while success:
        saved_frame_name = str(saved_frame) + ".JPG"
        cv2.imwrite(os.path.join(new_dir, saved_frame_name), frame)
        success, frame = video_capture.read()
        print(f'read a new frame {success}')
        saved_frame += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Video to frame extraction')
    parser.add_argument('--path_to_file', type=str, default='any_folder_demo/to_parse/template-dirt0001-0120.mp4')
    parser.add_argument('--name_out_dir', type=str, default='new')
    parser.add_argument('--out_dir', type=str, default='any_folder_demo/new')

    args = parser.parse_args()

    file = args.path_to_file
    name_out_dir = args.name_out_dir
    out_dir = args.out_dir

    main()
