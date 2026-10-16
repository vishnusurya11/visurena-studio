"""A frame every 8 s of a master, tiled 5 wide with its time stamped: `every_8s.py <video> <out.jpg>`."""
import sys

import cv2
import numpy as np

STEP, CELL, COLS = 8.0, 320, 5


def sheet(video: str) -> np.ndarray:
    cap = cv2.VideoCapture(video)
    seconds = cap.get(cv2.CAP_PROP_FRAME_COUNT) / (cap.get(cv2.CAP_PROP_FPS) or 24)
    tiles, t = [], 0.0
    while t < seconds:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        tile = cv2.resize(frame, (CELL, CELL)) if ok else np.zeros((CELL, CELL, 3), np.uint8)
        cv2.putText(tile, f"{t:.0f}s", (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        tiles.append(tile)
        t += STEP
    tiles += [np.zeros((CELL, CELL, 3), np.uint8)] * (-len(tiles) % COLS)
    return np.vstack([np.hstack(tiles[i:i + COLS]) for i in range(0, len(tiles), COLS)])


if __name__ == "__main__":
    cv2.imwrite(sys.argv[2], sheet(sys.argv[1]), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(sys.argv[2])
