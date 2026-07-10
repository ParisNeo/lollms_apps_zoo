# 🎬 Video Studio

A Lollms web app that transforms structured HTML video-source files into narrated, animated explainer videos with synchronized audio — exportable as `.webm` with real TTS voices.

## 🚀 Quick Start

```bash
# 1. Ensure Lollms is running (TTS service must be enabled)
# 2. Start the Video Studio server
python server.py

# 3. Open in your browser
# → http://localhost:8080
```

## 📋 How It Works

### Stage 1: Build a Video Source File

Use the **video-builder** skill (v2) to create a structured `.html` file from your documentation. The skill breaks content into 8–12 slides and outputs:

- `NARRATION[]` — one narration string per slide
- `ANIMATIONS[]` — one canvas animation function per slide
- `SLIDE_META[]` — titles, subtitles, and accent colors

### Stage 2: Upload and Record

1. Open Video Studio in your browser
2. Upload the structured HTML file
3. Select a TTS voice from the dropdown
4. Adjust narration speed (0.5×–2.0×)
5. Click **Synthesize Audio** — the backend calls Lollms TTS for each slide, returning `.wav` files
6. Click **Play** to preview, or **Record** to export
7. The `.webm` file downloads automatically with **real audio**
8. Convert to seekable MP4:
   ```bash
   ffmpeg -i video-studio-*.webm -c:v libx264 -c:a aac output.mp4
   ```

## 🏗️ Architecture

```
video-studio-app/
├── server.py           ← Flask backend: TTS synthesis, audio caching, file serving
├── index.html          ← Frontend: canvas rendering, audio playback, MediaRecorder
├── description.yaml    ← Lollms app manifest (config, ports, metadata)
├── README.md           ← This file
├── LICENSE.md          ← Apache 2.0
└── icon.png            ← App icon (optional)
```

### Audio Pipeline (Why It Works)

The core innovation: **TTS audio is pre-rendered server-side as real `.wav` files**, then routed through the Web Audio graph in the browser:

```
NARRATION text → server.py → Lollms TTS API → .wav files
                                                    ↓
Browser: <audio> elements → createMediaElementSource() → createMediaStreamDestination()
                                                    ↓
Canvas: canvas.captureStream(30) → video track ─────────→ MediaStream.Merge
                                                    ↓
                                            MediaRecorder → .webm (video + audio)
```

No `SpeechSynthesis` for recording. No `getDisplayMedia`. No tab sharing. No silent failure.

## ⚙️ Configuration

Edit `description.yaml` to change:

| Setting | Default | Description |
|---|---|---|
| `server.port` | `8080` | Flask server port |
| `server.host` | `127.0.0.1` | Bind address |
| `config.default_voice` | `default` | Fallback TTS voice |
| `config.default_speed` | `1.0` | Default narration speed |
| `config.canvas_width` | `1920` | Canvas resolution width |
| `config.canvas_height` | `1080` | Canvas resolution height |
| `config.canvas_fps` | `30` | Recording frame rate |

### TTS Endpoint

The app defaults to `http://127.0.0.1:9600/tts` (standard Lollms TTS endpoint). To change it, update `lollms_host` in `description.yaml`:

```yaml
config:
  lollms_host: "http://127.0.0.1:9600"
```

## 🔍 API Endpoints

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/` | Serve the Video Studio UI |
| `POST` | `/upload` | Accept HTML video-source file, extract NARRATION |
| `POST` | `/synthesize_all` | Pre-render all TTS audio via Lollms |
| `GET` | `/list_voices` | List available TTS voices |
| `GET` | `/config` | Return app configuration |
| `GET` | `/audio_cache/<file>` | Serve cached TTS audio files |
| `GET` | `/workspace/<file>` | Serve uploaded video-source HTML |

## 🐛 Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| No audio in output | TTS endpoint unreachable | Ensure Lollms is running and TTS is enabled |
| "No NARRATION array found" | HTML file doesn't follow video-builder v2 format | Regenerate with updated video-builder skill |
| Audio status shows red | Audio files failed to load | Check server console for TTS errors |
| Video not seekable | `MediaRecorder` produces minimal WebM container | Run `ffmpeg -i input.webm -c:v libx264 -c:a aac output.mp4` |
| Canvas is blank | Animation functions not found in HTML | Verify `ANIMATIONS` array exists in the source file |

## 📄 License

Apache 2.0 — See `LICENSE.md`

## 🛠️ Author

Built by ParisNeo as part of the Lollms ecosystem.