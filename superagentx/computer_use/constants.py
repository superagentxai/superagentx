# Define relevant resource types and content types
RELEVANT_RESOURCE_TYPES = {
    'document',
    'stylesheet',
    'image',
    'font',
    'script',
    'iframe',
}

RELEVANT_CONTENT_TYPES = {
    'text/html',
    'text/css',
    'application/javascript',
    'image/',
    'font/',
    'application/json',
}

SAFE_ATTRIBUTES = {
    'id',
    # Standard HTML attributes
    'name',
    'type',
    'placeholder',
    # Accessibility attributes
    'aria-label',
    'aria-labelledby',
    'aria-describedby',
    'role',
    # Common form attributes
    'for',
    'autocomplete',
    'required',
    'readonly',
    # Media attributes
    'alt',
    'title',
    'src',
    # Custom stable attributes (add any application-specific ones)
    'href',
    'target',
}

dynamic_attributes = {
    'data-id',
    'data-qa',
    'data-cy',
    'data-testid',
}

# Additional patterns to filter out
IGNORED_URL_PATTERNS = {
    # Analytics and tracking
    'analytics',
    'tracking',
    'telemetry',
    'beacon',
    'metrics',
    # Ad-related
    'doubleclick',
    'adsystem',
    'adserver',
    'advertising',
    # Social media widgets
    'facebook.com/plugins',
    'platform.twitter',
    'linkedin.com/embed',
    # Live chat and support
    'livechat',
    'zendesk',
    'intercom',
    'crisp.chat',
    'hotjar',
    # Push notifications
    'push-notifications',
    'onesignal',
    'pushwoosh',
    # Background sync/heartbeat
    'heartbeat',
    'ping',
    'alive',
    # WebRTC and streaming
    'webrtc',
    'rtmp://',
    'wss://',
    # Common CDNs for dynamic content
    'cloudfront.net',
    'fastly.net',
}

BROWSER_SECURITY_ARGS = [
    '--disable-web-security',
    '--disable-site-isolation-trials',
    '--disable-features=IsolateOrigins,site-per-process',
]
HEADLESS_ARGS = [
    '--no-sandbox',
    '--disable-blink-features=AutomationControlled',
    '--disable-infobars',
    '--disable-background-timer-throttling',
    '--disable-popup-blocking',
    '--disable-backgrounding-occluded-windows',
    '--disable-renderer-backgrounding',
    '--disable-window-activation',
    '--disable-focus-on-load',
    '--no-first-run',
    '--no-default-browser-check',
    '--no-startup-window',
    '--window-position=0,0',
]
