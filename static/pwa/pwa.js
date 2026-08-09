// PWA Installation and Management Script for SadraBar

let deferredPrompt;
let installButton = null;

// Detect if app is already installed
function isAppInstalled() {
  return window.matchMedia('(display-mode: standalone)').matches ||
         window.navigator.standalone === true;
}

// Initialize PWA
document.addEventListener('DOMContentLoaded', () => {
  // Register Service Worker
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/static/pwa/sw.js')
        .then((registration) => {
          console.log('ServiceWorker registration successful:', registration.scope);
          
          // Check for updates periodically
          setInterval(() => {
            registration.update();
          }, 60 * 60 * 1000); // Check every hour
        })
        .catch((err) => {
          console.log('ServiceWorker registration failed:', err);
        });
    });
  }

  // Handle install prompt
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    showInstallButton();
  });

  // Handle app installed event
  window.addEventListener('appinstalled', () => {
    console.log('PWA was installed');
    hideInstallButton();
    deferredPrompt = null;
  });

  // Update theme color based on system preference
  updateThemeColor();
});

// Show install button
function showInstallButton() {
  // Create install button if it doesn't exist
  if (!installButton) {
    installButton = document.createElement('button');
    installButton.id = 'install-pwa';
    installButton.innerHTML = '📲 نصب اپلیکیشن';
    installButton.style.cssText = `
      position: fixed;
      bottom: 20px;
      left: 20px;
      z-index: 9999;
      padding: 12px 24px;
      background: #4CAF50;
      color: white;
      border: none;
      border-radius: 50px;
      font-family: inherit;
      font-size: 14px;
      font-weight: bold;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      transition: all 0.3s ease;
    `;
    installButton.onclick = installPWA;
    document.body.appendChild(installButton);
  }
}

// Hide install button
function hideInstallButton() {
  if (installButton) {
    installButton.style.display = 'none';
  }
}

// Install PWA
async function installPWA() {
  if (!deferredPrompt) {
    console.log('Install prompt not available');
    return;
  }

  deferredPrompt.prompt();
  const { outcome } = await deferredPrompt.userChoice;
  
  console.log(`User response to install prompt: ${outcome}`);
  
  if (outcome === 'accepted') {
    console.log('User accepted the install prompt');
    hideInstallButton();
  }
  
  deferredPrompt = null;
}

// Update theme color
function updateThemeColor() {
  const metaThemeColor = document.querySelector('meta[name="theme-color"]');
  if (metaThemeColor) {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      metaThemeColor.setAttribute('content', '#212529');
    } else {
      metaThemeColor.setAttribute('content', '#4CAF50');
    }
  }
}

// Listen for system theme changes
if (window.matchMedia) {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', updateThemeColor);
}

// Request notification permission
function requestNotificationPermission() {
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission().then(permission => {
      console.log('Notification permission:', permission);
    });
  }
}

// Send notification (for testing)
function sendNotification(title, body, icon, url) {
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification(title, {
      body: body,
      icon: icon,
      badge: '/static/pwa/icons/icon-72x72.png',
      vibrate: [200, 100, 200],
      data: url,
      tag: 'sadradar-notification',
      requireInteraction: true,
      actions: [
        { action: 'open', title: 'باز کردن' },
        { action: 'dismiss', title: 'بستن' }
      ]
    });
  }
}

// Check online/offline status
function updateOnlineStatus() {
  const status = navigator.onLine ? 'آنلاین' : 'آفلاین';
  console.log('Connection status:', status);
  
  // Show offline indicator
  const offlineIndicator = document.getElementById('offline-indicator');
  if (!navigator.onLine) {
    if (!offlineIndicator) {
      const indicator = document.createElement('div');
      indicator.id = 'offline-indicator';
      indicator.innerHTML = '⚠️ شما آفلاین هستید';
      indicator.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: #ff9800;
        color: white;
        text-align: center;
        padding: 8px;
        font-size: 12px;
        z-index: 10000;
      `;
      document.body.appendChild(indicator);
    }
  } else {
    if (offlineIndicator) {
      offlineIndicator.remove();
    }
  }
}

window.addEventListener('online', updateOnlineStatus);
window.addEventListener('offline', updateOnlineStatus);

// Add to home screen instructions modal
function showAddToHomeInstructions() {
  const modal = document.createElement('div');
  modal.id = 'ath-modal';
  modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.8);
    z-index: 10000;
    display: flex;
    align-items: center;
    justify-content: center;
  `;
  
  modal.innerHTML = `
    <div style="
      background: white;
      padding: 24px;
      border-radius: 16px;
      max-width: 400px;
      text-align: center;
      direction: rtl;
    ">
      <h3 style="margin-top: 0;">نصب اپلیکیشن</h3>
      <p>برای نصب اپلیکیشن، روی دکمه اشتراک‌گذاری کلیک کرده و گزینه "Add to Home Screen" را انتخاب کنید.</p>
      <button onclick="document.getElementById('ath-modal').remove()" style="
        background: #4CAF50;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        cursor: pointer;
        margin-top: 16px;
      ">متوجه شدم</button>
    </div>
  `;
  
  document.body.appendChild(modal);
}

// Export functions for external use
window.SadraBarPWA = {
  install: installPWA,
  requestNotificationPermission,
  sendNotification,
  showAddToHomeInstructions,
  isAppInstalled
};
