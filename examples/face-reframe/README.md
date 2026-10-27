# Example: face-tracked reframe of a stream webcam

Source: a 1920x1080 live-stream recording (screen share on the left, webcam box on the right). Only the webcam box is used.

```
python -I skills/2bft-video-editor/scripts/reframe.py stream.mp4 compare.mp4 \
  --region 1476,154,384,768 --zoom 1.7 --size 540x960 --start 575 --dur 20 --compare --no-audio
```

Measured on our PC (Windows 11, OpenCV 5.0, ffmpeg 9.0.2, CPU only):

| What | Result |
|---|---|
| Face found | 100 % of 200 samples (10 fps over 20 s), with two posters of faces on the wall behind |
| 20 s side-by-side render (2 x 540x960) | 8.1 s |
| 5 s full-frame 1080p to 1080x1920 with audio | 5.7 s |

Output: [`media/demo.mp4`](../../media/demo.mp4). Left: a fixed centre crop loses the face when the speaker stands and leans. Right: the tracked crop keeps the face in frame.
