let audioCtx: AudioContext | null = null;

export const initAudio = () => {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
  }
  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
};

// Listen to first user interaction to unlock audio
if (typeof window !== 'undefined') {
  const unlockAudio = () => {
    initAudio();
    window.removeEventListener('click', unlockAudio);
    window.removeEventListener('keydown', unlockAudio);
    window.removeEventListener('touchstart', unlockAudio);
  };
  window.addEventListener('click', unlockAudio);
  window.addEventListener('keydown', unlockAudio);
  window.addEventListener('touchstart', unlockAudio);
}

export const playAlertSound = (type: 'beep' | 'upload' = 'beep') => {
  try {
    initAudio();
    if (!audioCtx) return;
    
    if (audioCtx.state === 'suspended') {
       console.warn("AudioContext is suspended. User needs to interact with the page first to hear audio.");
       audioCtx.resume();
    }
    
    const oscillator = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();
    
    if (type === 'beep') {
        // Proper Security Siren Sound
        oscillator.type = 'square';
        gainNode.gain.setValueAtTime(0.2, audioCtx.currentTime); // Loud but not deafening
        gainNode.gain.linearRampToValueAtTime(0.2, audioCtx.currentTime + 1.5);
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 1.8);
        
        // Alternate frequencies rapidly for a siren effect
        for (let i = 0; i < 15; i++) { 
            const time = audioCtx.currentTime + i * 0.1;
            oscillator.frequency.setValueAtTime(800, time);
            oscillator.frequency.setValueAtTime(1000, time + 0.05);
        }

        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        oscillator.start(audioCtx.currentTime);
        oscillator.stop(audioCtx.currentTime + 1.8);
    } else {
        // Upload complete chime
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(800, audioCtx.currentTime);
        oscillator.frequency.exponentialRampToValueAtTime(1200, audioCtx.currentTime + 0.1);
        gainNode.gain.setValueAtTime(0.3, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5);
        
        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        oscillator.start();
        oscillator.stop(audioCtx.currentTime + 0.5);
    }
  } catch (e) {
    console.error("Audio playback failed", e);
  }
};
