# ReelSaver — Instagram public-media downloader

A responsive black/pink frontend with a Flask + yt-dlp backend. It accepts public Instagram reel/post URLs. Instagram frequently changes access rules, so downloads are not guaranteed. Private/login-protected posts are not supported.

## Run locally
1. Install Python 3.11+ and FFmpeg.
2. In this folder run:
   ```bash
   pip install -r requirements.txt
   python app.py
   ```
3. Open `http://localhost:5000`.

## Free deployment with Render (Android-friendly)
1. Create a GitHub account and a new public repository named `reelsaver`.
2. Upload all files/folders from this project ZIP to the repository (GitHub mobile site → repository → Add file → Upload files).
3. Sign in to Render and choose **New → Web Service**.
4. Connect the GitHub repository. Render detects `render.yaml` / Dockerfile. Choose the free plan and deploy.
5. Wait for the build to finish, then open the `*.onrender.com` URL.
6. Test `/health`, then paste a public Instagram link.

Free hosting may sleep when idle and has limited CPU, memory and temporary storage. Files are temporary and automatically cleaned after about 30 minutes. Do not use this as a high-volume public service.

## Android steps
You can do the upload and deployment in Chrome on your phone. Download and extract this ZIP first. On GitHub, upload the extracted project files (including the `static` folder and its HTML files), not the ZIP itself.

## Important limitations
- Instagram may block automated requests or change its page/API format. Update yt-dlp when needed.
- Only public content is attempted. No login cookies, private account access, or bypassing access controls.
- Audio conversion requires FFmpeg (included in the Docker image).
- Photo extraction depends on what yt-dlp can expose for that post; some photo posts will return an unavailable message.
- Respect copyright, privacy, Instagram's terms and local law. Only save content you own or have permission to download.
- The Render free service uses ephemeral storage. Downloads are not permanent.
