import { memo, useEffect, useRef, useState } from "react";

type ConnectionState = "connecting" | "connected" | "failed" | "stopped";

interface Props {
  src: string;
}

const MAX_RETRIES = 10;
const RETRY_DELAY_MS = 2000;
const ICE_GATHER_TIMEOUT_MS = 5000;

export const WhepPlayer = memo(function WhepPlayer({ src }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retryCountRef = useRef(0);
  const [status, setStatus] = useState<ConnectionState>("connecting");
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    let cancelled = false;

    function cleanup() {
      if (retryTimerRef.current !== null) {
        clearTimeout(retryTimerRef.current);
        retryTimerRef.current = null;
      }
      if (pcRef.current) {
        pcRef.current.close();
        pcRef.current = null;
      }
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
    }

    function scheduleRetry() {
      if (cancelled) return;
      if (retryCountRef.current >= MAX_RETRIES) {
        setStatus("failed");
        return;
      }
      retryCountRef.current += 1;
      retryTimerRef.current = setTimeout(() => {
        if (!cancelled) connect();
      }, RETRY_DELAY_MS);
    }

    async function connect() {
      cleanup();
      if (cancelled) return;
      setStatus("connecting");

      try {
        const pc = new RTCPeerConnection({ iceServers: [] });
        pcRef.current = pc;

        pc.addTransceiver("video", { direction: "recvonly" });

        pc.ontrack = (event) => {
          if (videoRef.current && event.streams[0]) {
            videoRef.current.srcObject = event.streams[0];
          }
        };

        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        await Promise.race([
          new Promise<void>((resolve) => {
            if (pc.iceGatheringState === "complete") {
              resolve();
              return;
            }
            const handler = () => {
              if (pc.iceGatheringState === "complete") {
                pc.removeEventListener("icegatheringstatechange", handler);
                resolve();
              }
            };
            pc.addEventListener("icegatheringstatechange", handler);
          }),
          new Promise<void>((resolve) => setTimeout(resolve, ICE_GATHER_TIMEOUT_MS)),
        ]);

        if (cancelled) {
          pc.close();
          return;
        }

        const res = await fetch(src, {
          method: "POST",
          headers: { "Content-Type": "application/sdp" },
          body: pc.localDescription!.sdp,
        });

        if (!res.ok) throw new Error(`WHEP ${res.status}`);

        const answerSdp = await res.text();
        await pc.setRemoteDescription({ type: "answer", sdp: answerSdp });

        // setRemoteDescription 완료 직후에 이미 connected인 경우를 커버
        if (!cancelled && pc.connectionState === "connected") {
          retryCountRef.current = 0;
          setStatus("connected");
        }

        pc.addEventListener("connectionstatechange", () => {
          if (cancelled) return;
          if (pc.connectionState === "connected") {
            retryCountRef.current = 0;
            setStatus("connected");
          } else if (pc.connectionState === "failed") {
            scheduleRetry();
          }
        });
      } catch {
        if (!cancelled) scheduleRetry();
      }
    }

    retryCountRef.current = 0;
    connect();

    return () => {
      cancelled = true;
      cleanup();
      setStatus("stopped");
    };
  }, [src, retryKey]);

  function handleManualRetry() {
    retryCountRef.current = 0;
    setRetryKey((k) => k + 1);
  }

  const statusDot =
    status === "connected"
      ? "bg-green-500"
      : status === "failed"
        ? "bg-red-500"
        : "bg-yellow-400 animate-pulse";

  const statusLabel =
    status === "connected"
      ? "연결됨"
      : status === "failed"
        ? "연결 실패"
        : status === "stopped"
          ? "중지됨"
          : `연결 중... (${retryCountRef.current}/${MAX_RETRIES})`;

  return (
    <div className="rounded-lg bg-gray-800 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-white font-medium">실시간 Preview (WebRTC)</h3>
        <span className="flex items-center gap-1.5 text-xs text-gray-400">
          <span className={`inline-block w-2 h-2 rounded-full ${statusDot}`} />
          {statusLabel}
        </span>
      </div>
      <video
        ref={videoRef}
        autoPlay
        muted
        playsInline
        className="w-full rounded bg-black"
      />
      {status === "failed" && (
        <button
          onClick={handleManualRetry}
          className="mt-2 px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          재시도
        </button>
      )}
      <p className="text-gray-500 text-xs mt-2">{src}</p>
    </div>
  );
});
