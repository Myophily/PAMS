// Empty service worker to prevent 404 errors
// This file exists to stop browsers from requesting /sw.js and getting 404 errors
// It registers but performs no caching or offline functionality

self.addEventListener('install', () => {
  // Skip waiting to activate immediately
  self.skipWaiting();
});

self.addEventListener('activate', () => {
  // Claim all clients immediately
  self.clients.claim();
});

// No fetch event listener - this worker doesn't intercept any requests
