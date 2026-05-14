// Audio helpers — MediaRecorder + AnalyserNode para PTT.

export interface RecordingHandle {
  stop: () => Promise<Blob>;
  cancel: () => void;
  analyser: AnalyserNode | null;
  stream: MediaStream;
}

export async function startRecording(): Promise<RecordingHandle | null> {
  if (!navigator.mediaDevices?.getUserMedia) return null;
  let stream: MediaStream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true },
      video: false,
    });
  } catch {
    return null;
  }

  let mime = 'audio/webm;codecs=opus';
  if (!MediaRecorder.isTypeSupported(mime)) {
    mime = 'audio/webm';
    if (!MediaRecorder.isTypeSupported(mime)) {
      mime = 'audio/mp4';
    }
  }

  const recorder = new MediaRecorder(stream, { mimeType: mime });
  const chunks: Blob[] = [];
  recorder.ondataavailable = (e) => {
    if (e.data && e.data.size > 0) chunks.push(e.data);
  };
  recorder.start(250);

  let analyser: AnalyserNode | null = null;
  try {
    const AC =
      (window as any).AudioContext || (window as any).webkitAudioContext;
    const ctx = new AC();
    const src = ctx.createMediaStreamSource(stream);
    analyser = ctx.createAnalyser();
    analyser.fftSize = 256;
    src.connect(analyser);
  } catch {
    analyser = null;
  }

  let stopped = false;

  return {
    analyser,
    stream,
    stop: () =>
      new Promise<Blob>((resolve) => {
        if (stopped) return resolve(new Blob(chunks, { type: mime }));
        stopped = true;
        recorder.onstop = () => {
          stream.getTracks().forEach((t) => t.stop());
          resolve(new Blob(chunks, { type: mime }));
        };
        try {
          recorder.stop();
        } catch {
          stream.getTracks().forEach((t) => t.stop());
          resolve(new Blob(chunks, { type: mime }));
        }
      }),
    cancel: () => {
      stopped = true;
      try {
        recorder.stop();
      } catch {
        /* ignore */
      }
      stream.getTracks().forEach((t) => t.stop());
    },
  };
}

export function snapshotAmplitudes(analyser: AnalyserNode | null, bars = 28): number[] {
  if (!analyser) return new Array(bars).fill(0.1);
  const data = new Uint8Array(analyser.frequencyBinCount);
  analyser.getByteFrequencyData(data);
  const out: number[] = [];
  const step = Math.floor(data.length / bars);
  for (let i = 0; i < bars; i++) {
    let sum = 0;
    for (let j = 0; j < step; j++) sum += data[i * step + j] ?? 0;
    out.push(Math.max(0.05, sum / step / 255));
  }
  return out;
}
