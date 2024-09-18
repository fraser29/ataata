# Ataata - Video Chapter Builder

Ataata is a Python-based desktop application that allows users to easily create and manage chapters for video files. It provides a simple interface for adding timestamps and chapter names while watching a video.

## Features

- Open and play video files
- Add, edit, and delete chapters at specific timestamps
- Adjust playback speed
- Export chapters to a text file

## Requirements

- Python 3.x
- PyQt5
- OpenCV (cv2)

## Installation

1. Clone this repository
2. Install the required packages:
   ```
   pip install PyQt5 opencv-python
   ```

## Usage

1. Run the application:
   ```
   python ataata.py [video_path]
   ```
2. Click "Open Video" to select a video file
3. Use the play/pause button and slider to navigate the video
4. Click "Add Chapter" to create a new chapter at the current timestamp
5. Double-click a chapter to edit its name
6. Right-click a chapter to delete it / seek to it
7. Use the "Export Chapters" button to save the chapters to a text file

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).