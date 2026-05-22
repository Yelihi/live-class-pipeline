import { useRef, useState } from "react";

const WHIP_URL = `${
  import.meta.env.VITE_MEDIAMTX_URL ?? "http://localhost:8889"
}/room1/whip`;

export function PublisherPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState("");

  async function startPublishing() {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720, frameRate: 30 },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }

      const pc = new RTCPeerConnection({ iceServers: [] });
      pcRef.current = pc;

      stream.getTracks().forEach((track) => pc.addTrack(track, stream));

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      // ICE 수집 완료 대기
      await new Promise<void>((resolve) => {
        if (pc.iceGatheringState === "complete") {
          resolve();
          return;
        }
        pc.addEventListener("icegatheringstatechange", () => {
          if (pc.iceGatheringState === "complete") resolve();
        });
      });

      const res = await fetch(WHIP_URL, {
        method: "POST",
        headers: { "Content-Type": "application/sdp" },
        body: pc.localDescription!.sdp,
      });

      if (!res.ok) throw new Error(`WHIP 오류: ${res.status} ${res.statusText}`);

      const answerSdp = await res.text();
      await pc.setRemoteDescription({ type: "answer", sdp: answerSdp });

      setPublishing(true);
    } catch (e) {
      setError(String(e));
      stopPublishing();
    }
  }

  function stopPublishing() {
    pcRef.current?.close();
    pcRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setPublishing(false);
  }

  return (
    <div className="min-h-screen bg-gray-900 p-6 space-y-4">
      <h1 className="text-white text-2xl font-bold">강의 송출</h1>
      <p className="text-gray-400 text-sm">
        WHIP: <code className="text-gray-300">{WHIP_URL}</code>
      </p>

      <video
        ref={videoRef}
        autoPlay
        muted
        playsInline
        className="w-full max-w-2xl rounded-lg bg-black"
      />

      <div className="flex gap-3">
        {!publishing ? (
          <button
            onClick={startPublishing}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
          >
            송출 시작
          </button>
        ) : (
          <button
            onClick={stopPublishing}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
          >
            송출 중지
          </button>
        )}
      </div>

      {publishing && (
        <p className="text-green-400 text-sm">● 송출 중 — room1</p>
      )}
      {error && <p className="text-red-400 text-sm">{error}</p>}
    </div>
  );
}
