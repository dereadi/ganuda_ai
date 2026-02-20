async function processFrame(framePath, cameraId) {
    const response = await fetch("/api/optic/process", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({frame_path: framePath, camera_id: cameraId})
    });
    return await response.json();
}
