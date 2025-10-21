import React, { useState, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

export default function PWAInstallPrompt() {
  const [showPrompt, setShowPrompt] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [isIOS, setIsIOS] = useState(false);
  const [isStandalone, setIsStandalone] = useState(false);

  useEffect(() => {
    // Check if running as installed PWA
    const standalone = window.matchMedia('(display-mode: standalone)').matches || 
                      window.navigator.standalone || 
                      document.referrer.includes('android-app://');
    setIsStandalone(standalone);

    // Check if iOS
    const ios = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    setIsIOS(ios);

    // Listen for beforeinstallprompt event (Chrome, Edge, etc.)
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      
      // Don't show if dismissed in last 7 days
      const dismissedDate = localStorage.getItem('pwa-prompt-dismissed');
      if (dismissedDate) {
        const daysSinceDismissed = (Date.now() - parseInt(dismissedDate)) / (1000 * 60 * 60 * 24);
        if (daysSinceDismissed < 7) {
          return;
        }
      }
      
      // Show prompt after 30 seconds
      setTimeout(() => setShowPrompt(true), 30000);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    // For iOS, show prompt if not standalone and hasn't been dismissed
    if (ios && !standalone) {
      const dismissedDate = localStorage.getItem('pwa-prompt-dismissed-ios');
      if (!dismissedDate) {
        setTimeout(() => setShowPrompt(true), 30000);
      }
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    };
  }, []);

  const handleInstallClick = async () => {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      console.log(`User response to install prompt: ${outcome}`);
      setDeferredPrompt(null);
    }
    setShowPrompt(false);
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    if (isIOS) {
      localStorage.setItem('pwa-prompt-dismissed-ios', Date.now().toString());
    } else {
      localStorage.setItem('pwa-prompt-dismissed', Date.now().toString());
    }
  };

  // Don't show if already installed
  if (isStandalone || !showPrompt) {
    return null;
  }

  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:max-w-md z-50 animate-slide-up">
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg shadow-2xl p-4 text-white">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <h3 className="font-bold text-lg mb-1">Install Misty Manufacturing</h3>
            <p className="text-sm text-blue-100">
              {isIOS 
                ? 'Add to your home screen for quick access and offline use.'
                : 'Install this app on your device for a better experience!'}
            </p>
          </div>
          <button
            onClick={handleDismiss}
            className="ml-2 p-1 hover:bg-white/10 rounded-full transition-colors"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        {isIOS ? (
          <div className="mt-3 space-y-2 text-sm bg-white/10 rounded p-3">
            <p className="font-semibold">Installation steps:</p>
            <ol className="list-decimal list-inside space-y-1 text-blue-50">
              <li>Tap the Share button <span className="inline-block px-2 py-0.5 bg-white/20 rounded">⎆</span></li>
              <li>Scroll down and tap "Add to Home Screen"</li>
              <li>Tap "Add" in the top-right corner</li>
            </ol>
          </div>
        ) : (
          <div className="mt-3 flex gap-2">
            <button
              onClick={handleInstallClick}
              className="flex-1 bg-white text-blue-600 hover:bg-blue-50 font-semibold py-2 px-4 rounded-lg transition-colors"
            >
              Install App
            </button>
            <button
              onClick={handleDismiss}
              className="px-4 py-2 hover:bg-white/10 rounded-lg transition-colors"
            >
              Not now
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
