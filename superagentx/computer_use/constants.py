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

EXAMPLE_DATA = """{
            'current_state': {
                'evaluation_previous_goal': "Success - I successfully clicked on the 'Apple' link from the Google Search results page, which directed me to the 'Apple' company homepage. This is a good start toward finding the best place to buy a new iPhone as the Apple website often list iPhones for sale.",
                'memory': "I searched for 'iPhone retailers' on Google. From the Google Search results page, I used the 'click_element_by_index' tool to click on element at index [45] labeled 'Best Buy' but calling the tool did not direct me to a new page. I then used the 'click_element_by_index' tool to click on element at index [82] labeled 'Apple' which redirected me to the 'Apple' company homepage. Currently at step 3/15.",
                'next_goal': "Looking at reported structure of the current page, I can see the item '[127]<h3 iPhone/>' in the content. I think this button will lead to more information and potentially prices for iPhones. I'll click on the link at index [127] using the 'click_element_by_index' tool and hope to see prices on the next page."
            },
            'action': [{'click_element_by_index': {'index': 127}}]
        }"""

CHROME_DISABLED_COMPONENTS = [
    # Playwright defaults: https://github.com/microsoft/playwright/blob/41008eeddd020e2dee1c540f7c0cdfa337e99637/packages/playwright-core/src/server/chromium/chromiumSwitches.ts#L76
    # See https:#github.com/microsoft/playwright/pull/10380
    'AcceptCHFrame',
    # See https:#github.com/microsoft/playwright/pull/10679
    'AutoExpandDetailsElement',
    # See https:#github.com/microsoft/playwright/issues/14047
    'AvoidUnnecessaryBeforeUnloadCheckSync',
    # See https:#github.com/microsoft/playwright/pull/12992
    'CertificateTransparencyComponentUpdater',
    'DestroyProfileOnBrowserClose',
    # See https:#github.com/microsoft/playwright/pull/13854
    'DialMediaRouteProvider',
    # Chromium is disabling manifest version 2. Allow testing it as long as Chromium can actually run it.
    # Disabled in https:#chromium-review.googlesource.com/c/chromium/src/+/6265903.
    'ExtensionManifestV2Disabled',
    'GlobalMediaControls',
    # See https:#github.com/microsoft/playwright/pull/27605
    'HttpsUpgrades',
    'ImprovedCookieControls',
    'LazyFrameLoading',
    # Hides the Lens feature in the URL address bar. Its not working in unofficial builds.
    'LensOverlay',
    # See https:#github.com/microsoft/playwright/pull/8162
    'MediaRouter',
    # See https:#github.com/microsoft/playwright/issues/28023
    'PaintHolding',
    # See https:#github.com/microsoft/playwright/issues/32230
    'ThirdPartyStoragePartitioning',
    # See https://github.com/microsoft/playwright/issues/16126
    'Translate',
    'AutomationControlled',
    # Added by us:
    'OptimizationHints',
    'ProcessPerSiteUpToMainFrameThreshold',
    'InterestFeedContentSuggestions',
    'CalculateNativeWinOcclusion',
    # chrome normally stops rendering tabs if they are not visible (occluded by a foreground window or other app)
    # 'BackForwardCache',  # agent does actually use back/forward navigation, but we can disable if we ever remove that
    'HeavyAdPrivacyMitigations',
    'PrivacySandboxSettings4',
    'AutofillServerCommunication',
    'CrashReporting',
    'OverscrollHistoryNavigation',
    'InfiniteSessionRestore',
    'ExtensionDisableUnsupportedDeveloper',
]

CHROME_ARGS = [
    # provided by playwright by default: https://github.com/microsoft/playwright/blob/41008eeddd020e2dee1c540f7c0cdfa337e99637/packages/playwright-core/src/server/chromium/chromiumSwitches.ts#L76
    # we don't need to include them twice in our own config, but it's harmless
    '--disable-field-trial-config',
    # https://source.chromium.org/chromium/chromium/src/+/main:testing/variations/README.md
    '--disable-background-networking',
    '--disable-background-timer-throttling',
    '--disable-backgrounding-occluded-windows',
    '--disable-back-forward-cache',  # Avoids surprises like main request not being intercepted during page.goBack().
    '--disable-breakpad',
    '--disable-client-side-phishing-detection',
    '--disable-component-extensions-with-background-pages',
    '--disable-component-update',  # Avoids unneeded network activity after startup.
    '--no-default-browser-check',
    # '--disable-default-apps',
    '--disable-dev-shm-usage',
    # '--disable-extensions',
    # '--disable-features=' + disabledFeatures(assistantMode).join(','),
    '--allow-pre-commit-input',  # let page JS run a little early before GPU rendering finishes
    '--disable-hang-monitor',
    '--disable-ipc-flooding-protection',
    '--disable-popup-blocking',
    '--disable-prompt-on-repost',
    '--disable-renderer-backgrounding',
    # '--force-color-profile=srgb',  # moved to CHROME_DETERMINISTIC_RENDERING_ARGS
    '--metrics-recording-only',
    '--no-first-run',
    '--password-store=basic',
    '--use-mock-keychain',
    # // See https://chromium-review.googlesource.com/c/chromium/src/+/2436773
    '--no-service-autorun',
    '--export-tagged-pdf',
    # // https://chromium-review.googlesource.com/c/chromium/src/+/4853540
    '--disable-search-engine-choice-screen',
    # // https://issues.chromium.org/41491762
    '--unsafely-disable-devtools-self-xss-warnings',
    '--enable-features=NetworkService,NetworkServiceInProcess',
    '--enable-network-information-downlink-max',
    # added by us:
    '--test-type=gpu',
    '--disable-sync',
    '--allow-legacy-extension-manifests',
    '--allow-pre-commit-input',
    '--disable-blink-features=AutomationControlled',
    '--install-autogenerated-theme=0,0,0',
    '--hide-scrollbars',
    '--log-level=2',
    # '--enable-logging=stderr',
    '--disable-focus-on-load',
    '--disable-window-activation',
    '--generate-pdf-document-outline',
    '--no-pings',
    '--ash-no-nudges',
    '--disable-infobars',
    '--simulate-outdated-no-au="Tue, 31 Dec 2099 23:59:59 GMT"',
    '--hide-crash-restore-bubble',
    '--suppress-message-center-popups',
    '--disable-domain-reliability',
    '--disable-datasaver-prompt',
    '--disable-speech-synthesis-api',
    '--disable-speech-api',
    '--disable-print-preview',
    '--safebrowsing-disable-auto-update',
    '--disable-external-intent-requests',
    '--disable-desktop-notifications',
    '--noerrdialogs',
    '--silent-debugger-extension-api',
    f'--disable-features={",".join(CHROME_DISABLED_COMPONENTS)}',
]

CHROME_HEADLESS_ARGS = [
    '--no-sandbox',
    '--disable-gpu-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',
    '--no-xshm',
    '--no-zygote',
    '--single-process',
]

CHROME_DOCKER_ARGS = [
    # Docker-specific options
    # https://github.com/GoogleChrome/lighthouse-ci/tree/main/docs/recipes/docker-client#--no-sandbox-issues-explained
    '--no-sandbox',  # rely on docker sandboxing in docker, otherwise we need cap_add: SYS_ADM to use host sandboxing
    '--disable-gpu-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',  # docker 75mb default shm size is not big enough, disabling just uses /tmp instead
    '--no-xshm',
    # dont try to disable (or install) dbus in docker, its not needed, chrome can work without dbus despite the errors
]

CHROME_DISABLE_SECURITY_ARGS = [
    '--disable-web-security',
    '--disable-site-isolation-trials',
    '--disable-features=IsolateOrigins,site-per-process',
    '--allow-running-insecure-content',
    '--ignore-certificate-errors',
    '--ignore-ssl-errors',
    '--ignore-certificate-errors-spki-list',
]

# flags to make chrome behave more deterministically across different OS's
CHROME_DETERMINISTIC_RENDERING_ARGS = [
    '--deterministic-mode',
    '--js-flags=--random-seed=1157259159',
    '--force-device-scale-factor=2',
    '--enable-webgl',
    # '--disable-skia-runtime-opts',
    # '--disable-2d-canvas-clip-aa',
    '--font-render-hinting=none',
    '--force-color-profile=srgb',
]
CHROME_DEBUG_PORT = 9222
