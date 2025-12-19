# JR Instructions: Vimeo Caption Enhancement for Tribe Extension

**Date**: 2025-12-16
**Priority**: High
**Assigned**: Jr on sasass (192.168.132.241)
**TPM**: Claude Code CLI

## Overview

Enhance the Tribe Chrome Extension to support Vimeo video control and caption extraction. This enables the Tribe to learn from web-based tutorials that use Vimeo embedded videos.

## Current State

- Extension location: `/Users/Shared/ganuda/tribe-extension/`
- Controller location: `/Users/Shared/ganuda/scripts/tribe_controller.py`
- Extension successfully connects via WebSocket on port 8765
- Can read page state, click buttons, type in fields
- Auto-navigation mode exists but stalls on video pages

## Problem

When auto mode encounters a page with a Vimeo video:
1. It detects video exists
2. Waits indefinitely for video completion
3. Never starts playing the video
4. Cannot extract captions/transcript for learning

## Required Changes

### 1. Update background.js - Add New Actions

Add these actions to the `runInPage(message)` function:

#### PLAY_VIDEO Action
```javascript
if (message.action === "PLAY_VIDEO") {
  // Try to play Vimeo video via Player.js API
  const vimeoFrame = document.querySelector("iframe[src*=vimeo]");
  if (vimeoFrame && typeof Vimeo !== "undefined") {
    try {
      const player = new Vimeo.Player(vimeoFrame);
      player.play();
      return { success: true, message: "Playing Vimeo video" };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  // Fallback: Try HTML5 video element
  const video = document.querySelector("video");
  if (video) {
    video.play();
    return { success: true, message: "Playing HTML5 video" };
  }

  // Fallback: Try clicking play button
  const playBtn = document.querySelector("[class*=play], button[aria-label*=play], .vp-play");
  if (playBtn) {
    playBtn.click();
    return { success: true, message: "Clicked play button" };
  }

  return { success: false, message: "No video found to play" };
}
```

#### GET_VIDEO_STATUS Action
```javascript
if (message.action === "GET_VIDEO_STATUS") {
  // Check Vimeo via Player.js
  const vimeoFrame = document.querySelector("iframe[src*=vimeo]");
  if (vimeoFrame && typeof Vimeo !== "undefined") {
    return new Promise((resolve) => {
      try {
        const player = new Vimeo.Player(vimeoFrame);
        Promise.all([
          player.getCurrentTime(),
          player.getDuration(),
          player.getPaused(),
          player.getEnded()
        ]).then(([time, duration, paused, ended]) => {
          resolve({
            type: "vimeo",
            currentTime: time,
            duration: duration,
            paused: paused,
            ended: ended,
            progress: duration > 0 ? Math.round((time / duration) * 100) : 0
          });
        }).catch((e) => {
          resolve({ type: "vimeo", error: e.message });
        });
      } catch (e) {
        resolve({ type: "vimeo", error: e.message });
      }
    });
  }

  // Check HTML5 video
  const video = document.querySelector("video");
  if (video) {
    return {
      type: "html5",
      currentTime: video.currentTime,
      duration: video.duration,
      paused: video.paused,
      ended: video.ended,
      progress: video.duration > 0 ? Math.round((video.currentTime / video.duration) * 100) : 0
    };
  }

  return { type: "none", message: "No video found" };
}
```

#### GET_VIMEO_CAPTIONS Action
```javascript
if (message.action === "GET_VIMEO_CAPTIONS") {
  const vimeoFrame = document.querySelector("iframe[src*=vimeo]");
  if (!vimeoFrame) {
    return { found: false, error: "No Vimeo iframe found" };
  }

  const match = vimeoFrame.src.match(/video\/(\d+)/);
  if (!match) {
    return { found: false, error: "Could not extract Vimeo video ID" };
  }

  const videoId = match[1];

  // Check if Vimeo Player API is loaded
  if (typeof Vimeo === "undefined") {
    // Load it dynamically
    return new Promise((resolve) => {
      const script = document.createElement("script");
      script.src = "https://player.vimeo.com/api/player.js";
      script.onload = () => {
        extractCaptions(vimeoFrame, videoId, resolve);
      };
      script.onerror = () => {
        resolve({ found: false, error: "Failed to load Vimeo Player API", videoId: videoId });
      };
      document.head.appendChild(script);
    });
  } else {
    return new Promise((resolve) => {
      extractCaptions(vimeoFrame, videoId, resolve);
    });
  }

  function extractCaptions(iframe, videoId, resolve) {
    try {
      const player = new Vimeo.Player(iframe);
      player.getTextTracks().then((tracks) => {
        if (tracks.length === 0) {
          resolve({
            found: false,
            videoId: videoId,
            message: "No captions available for this video",
            tracks: []
          });
          return;
        }

        Promise.all([
          player.getVideoTitle(),
          player.getDuration()
        ]).then(([title, duration]) => {
          resolve({
            found: true,
            videoId: videoId,
            title: title,
            duration: duration,
            tracks: tracks.map(t => ({
              label: t.label,
              language: t.language,
              kind: t.kind
            }))
          });
        });
      }).catch((err) => {
        resolve({ found: false, error: err.message, videoId: videoId });
      });
    } catch (e) {
      resolve({ found: false, error: e.message, videoId: videoId });
    }
  }
}
```

### 2. Update tribe_controller.py - Add New Commands

Add these commands to the `command_interface()` function:

```python
elif act in ("play", "p"):
    await send_command(ws, {"action": "PLAY_VIDEO"})

elif act in ("status", "st"):
    await send_command(ws, {"action": "GET_VIDEO_STATUS"})

elif act in ("captions", "cap"):
    await send_command(ws, {"action": "GET_VIMEO_CAPTIONS"})
```

Update the help text:
```python
print("\nCommands: state | text <t> | auto | play | status | captions | transcript | video | pagetext | scroll | quit\n")
```

Add response handlers in `process_message()`:
```python
elif action == "GET_VIDEO_STATUS":
    vtype = result.get("type", "unknown")
    if vtype != "none":
        print(f"\n[VIDEO STATUS] Type: {vtype}")
        print(f"  Progress: {result.get('progress', 0)}%")
        print(f"  Time: {result.get('currentTime', 0):.1f}s / {result.get('duration', 0):.1f}s")
        print(f"  Paused: {result.get('paused', '?')}, Ended: {result.get('ended', '?')}")
    else:
        print(f"[VIDEO STATUS] {result.get('message', 'No video')}")

elif action == "GET_VIMEO_CAPTIONS":
    print(f"\n[VIMEO CAPTIONS]")
    if result.get("found"):
        print(f"  Video ID: {result.get('videoId')}")
        print(f"  Title: {result.get('title', 'Unknown')}")
        print(f"  Duration: {result.get('duration', 0):.1f}s")
        print(f"  Tracks: {len(result.get('tracks', []))}")
        for t in result.get("tracks", []):
            print(f"    - {t.get('label')} ({t.get('language')})")
    else:
        print(f"  Not found: {result.get('error', result.get('message', 'Unknown'))}")

elif action == "PLAY_VIDEO":
    if result.get("success"):
        print(f"[PLAY] {result.get('message', 'Playing')}")
    else:
        print(f"[PLAY] Failed: {result.get('error', result.get('message', 'Unknown'))}")
```

### 3. Update Auto-Navigation Logic

Modify the auto_navigate() function to handle videos smarter:

```python
elif videos and any("vimeo" in str(v.get("src", "")) or "video" in str(v.get("type", "")) for v in videos):
    # First check if there's a "Watch Tutorial" button
    if any("watch" in b.lower() for b in btn_texts):
        print("[AUTO] Found 'Watch' button - clicking to start video...")
        await send_command(ws, {"action": "CLICK_TEXT", "text": "watch"})
        await asyncio.sleep(2)
        continue

    # Try to play the video if it exists but isn't playing
    print("[AUTO] Video on page - attempting to play...")
    await send_command(ws, {"action": "PLAY_VIDEO"})
    await asyncio.sleep(3)

    # Then wait and check status periodically
    print("[AUTO] Waiting for video completion...")
    await asyncio.sleep(10)
    continue
```

## Testing Steps

1. Reload extension in Chrome (chrome://extensions > Tribe > Reload)
2. Restart controller: `python3 /Users/Shared/ganuda/scripts/tribe_controller.py`
3. Navigate to a page with Vimeo video
4. Test commands:
   - `video` - Should show video info with ID
   - `play` - Should start video playback
   - `status` - Should show progress percentage
   - `captions` - Should list available caption tracks
5. Test auto mode on tutorial pages

## Reference Files

- Updated background.js template: See code blocks above
- Vimeo Player.js docs: https://github.com/vimeo/player.js
- Current extension manifest requires no changes (permissions sufficient)

## Success Criteria

- [ ] `play` command starts Vimeo video playback
- [ ] `status` command shows video progress
- [ ] `captions` command lists available caption tracks
- [ ] Auto mode can start videos and wait for completion
- [ ] Auto mode clicks "Watch Tutorial" buttons when present

## For Seven Generations

---
TPM Note: This enhancement enables the Tribe to autonomously learn from web-based video tutorials, a key capability for Aether certification training.
