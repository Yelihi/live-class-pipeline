import Hls from "hls.js";
import { useEffect, useRef } from "react";

interface Props {
  src: string;
}

export function HlsPlayer({ src }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    if (Hls.isSupported()) {
      const hls = new Hls({ lowLatencyMode: false });
      hls.loadSource(src);
      hls.attachMedia(video);
      return () => hls.destroy();
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      // Safari: 네이티브 HLS 지원
      video.src = src;
    }
  }, [src]);

  return (
    <div className="rounded-lg bg-gray-800 p-4">
      <h3 className="text-white font-medium mb-3">HLS Preview</h3>
      <video
        ref={videoRef}
        controls
        autoPlay
        muted
        className="w-full rounded bg-black"
      />
      <p className="text-gray-500 text-xs mt-2">{src}</p>
    </div>
  );
}
