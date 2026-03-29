import { computed, onUnmounted, ref, watch } from "vue";

import { usePlaybackState } from "./usePlaybackState";

const LOCAL_VOLUME_STORAGE_KEY = "airwave:settings:local-volume";
const DEFAULT_LOCAL_VOLUME = 0.8;

function clampVolume(value) {
  if (!Number.isFinite(value)) return DEFAULT_LOCAL_VOLUME;
  return Math.max(0, Math.min(1, value));
}

function readStoredLocalVolume() {
  if (typeof window === "undefined") return null;
  try {
    const stored = window.localStorage.getItem(LOCAL_VOLUME_STORAGE_KEY);
    if (stored == null) return null;
    const parsed = Number.parseFloat(stored);
    if (!Number.isFinite(parsed) || parsed < 0 || parsed > 1) return null;
    return parsed;
  } catch {
    return null;
  }
}

function writeStoredLocalVolume(volume) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(LOCAL_VOLUME_STORAGE_KEY, String(clampVolume(volume)));
  } catch {
    // Ignore localStorage write errors and keep in-memory state.
  }
}

/**
 * Shared local playback over a single audio element. Call from the component that owns the element (e.g. App.vue).
 * @param {import('vue').Ref<HTMLAudioElement | null>} audioRef
 */
export function useLocalPlayback(audioRef) {
  const { playbackState } = usePlaybackState();
  const wantsLocalPlayback = ref(false);
  /** Mirrors the audio element's paused/ended state so Vue updates when OS / Media Session controls the element. */
  const localAudioPaused = ref(true);
  const storedVolume = readStoredLocalVolume();
  const localVolume = ref(storedVolume ?? DEFAULT_LOCAL_VOLUME);
  const isMuted = ref(localVolume.value <= 0);
  const previousVolumeBeforeMute = ref(localVolume.value > 0 ? localVolume.value : DEFAULT_LOCAL_VOLUME);

  function syncLocalAudioPausedFromElement() {
    const audio = audioRef.value;
    if (!audio) {
      localAudioPaused.value = true;
      return;
    }
    localAudioPaused.value = audio.paused || audio.ended;
  }

  const isLocalPlaybackActive = computed(() => {
    const local = localPlaybackStatus();
    return local.isLocalPlaybackActive && !local.isLocalPlaybackPaused;
  });

  const localPlaybackSessionDeps = computed(() => ({
    wantsLocal: wantsLocalPlayback.value,
    audioPaused: localAudioPaused.value,
  }));

  function applyAudioVolume() {
    if (!audioRef.value) return;
    audioRef.value.volume = clampVolume(localVolume.value);
    audioRef.value.muted = isMuted.value || localVolume.value <= 0;
  }

  function setLocalVolume(volume) {
    const nextVolume = clampVolume(volume);
    localVolume.value = nextVolume;
    if (nextVolume > 0) {
      previousVolumeBeforeMute.value = nextVolume;
      isMuted.value = false;
    } else {
      isMuted.value = true;
    }
    applyAudioVolume();
    writeStoredLocalVolume(nextVolume);
  }

  function toggleMuted() {
    if (isMuted.value || localVolume.value <= 0) {
      const restoredVolume = previousVolumeBeforeMute.value > 0 ? previousVolumeBeforeMute.value : DEFAULT_LOCAL_VOLUME;
      localVolume.value = clampVolume(restoredVolume);
      isMuted.value = false;
      applyAudioVolume();
      writeStoredLocalVolume(localVolume.value);
      return;
    }

    previousVolumeBeforeMute.value = localVolume.value;
    localVolume.value = 0;
    isMuted.value = true;
    applyAudioVolume();
    writeStoredLocalVolume(0);
  }

  async function startLocalPlayback() {
    if (!audioRef.value || !playbackState.value.stream_url) return;

    wantsLocalPlayback.value = true;
    audioRef.value.src = playbackState.value.stream_url;
    applyAudioVolume();

    try {
      await audioRef.value.play();
    } catch {
      stopLocalPlayback();
    }
    syncLocalAudioPausedFromElement();
  }

  function stopLocalPlayback() {
    if (!audioRef.value) return;

    wantsLocalPlayback.value = false;

    audioRef.value.pause();
    audioRef.value.removeAttribute("src");
    audioRef.value.load();
    syncLocalAudioPausedFromElement();
  }

  function pauseLocalPlayback() {
    if (!wantsLocalPlayback.value || !audioRef.value) return;
    audioRef.value.pause();
    syncLocalAudioPausedFromElement();
  }

  function localPlaybackStatus() {
    const audio = audioRef.value;
    const active = wantsLocalPlayback.value;
    const paused = !audio || localAudioPaused.value;
    const playing = Boolean(audio && active && !paused);
    return {
      isLocalPlaybackActive: active,
      isLocalPlaybackPaused: paused,
      isLocalPlaybackPlaying: playing,
      isLocalPlaybackStopped: !active || !audio?.src,
    };
  }

  async function resumeLocalPlayback() {
    if (!wantsLocalPlayback.value || !audioRef.value || !playbackState.value.stream_url) return;

    const oldValue = playbackState.value.stream_url;
    // Reset the audio element to its initial state.
    audioRef.value.removeAttribute("src");
    audioRef.value.load();
    audioRef.value.src = oldValue;
    applyAudioVolume();
    try {
      await audioRef.value.play();
    } catch {
      stopLocalPlayback();
    }
    syncLocalAudioPausedFromElement();
  }

  watch(
    () => playbackState.value.stream_url,
    async (newUrl) => {
      if (!newUrl) {
        stopLocalPlayback();
        return;
      }

      if (!wantsLocalPlayback.value || !audioRef.value) return;

      audioRef.value.src = newUrl;
      applyAudioVolume();

      try {
        await audioRef.value.play();
      } catch {
        stopLocalPlayback();
      }
      syncLocalAudioPausedFromElement();
    }
  );

  let detachAudioStateListeners = () => {};

  watch(
    audioRef,
    (audio) => {
      detachAudioStateListeners();
      detachAudioStateListeners = () => {};
      if (!audio) {
        localAudioPaused.value = true;
        return;
      }
      applyAudioVolume();
      const onAudioStateEvent = () => syncLocalAudioPausedFromElement();
      syncLocalAudioPausedFromElement();
      audio.addEventListener("play", onAudioStateEvent);
      audio.addEventListener("pause", onAudioStateEvent);
      audio.addEventListener("ended", onAudioStateEvent);
      detachAudioStateListeners = () => {
        audio.removeEventListener("play", onAudioStateEvent);
        audio.removeEventListener("pause", onAudioStateEvent);
        audio.removeEventListener("ended", onAudioStateEvent);
      };
    },
    { immediate: true }
  );

  if (storedVolume == null) {
    writeStoredLocalVolume(localVolume.value);
  }

  onUnmounted(() => {
    detachAudioStateListeners();
    stopLocalPlayback();
  });

  return {
    startLocalPlayback,
    stopLocalPlayback,
    pauseLocalPlayback,
    resumeLocalPlayback,
    localPlaybackStatus,
    localPlaybackSessionDeps,
    isLocalPlaybackActive,
    localVolume,
    isMuted,
    setLocalVolume,
    toggleMuted,
  };
}
