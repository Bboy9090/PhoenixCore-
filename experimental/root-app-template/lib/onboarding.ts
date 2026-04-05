/**
 * Onboarding and guided tour system for Bobby's PhoenixDrive
 */

export interface OnboardingTour {
  id: string;
  name: string;
  steps: OnboardingStep[];
  completed: boolean;
}

export interface OnboardingStep {
  id: string;
  screen: string;
  title: string;
  description: string;
  action: string;
  icon: string;
  position?: 'top' | 'bottom' | 'center';
  highlightElement?: string;
}

export interface Tooltip {
  id: string;
  title: string;
  description: string;
  icon: string;
  learnMoreUrl?: string;
}

/**
 * First-time user onboarding tour
 */
export const firstTimeUserTour: OnboardingTour = {
  id: 'first-time-user',
  name: 'Welcome to Bobby\'s PhoenixDrive',
  completed: false,
  steps: [
    {
      id: 'welcome',
      screen: 'home',
      title: 'Welcome to Bobby\'s PhoenixDrive',
      description: 'Your computer\'s emergency repair kit. Fix any device, any OS, any problem.',
      action: 'Next',
      icon: '🔥',
      position: 'center',
    },
    {
      id: 'how-it-works',
      screen: 'home',
      title: 'How It Works',
      description: 'Plug a USB into your computer. Bobby\'s builds a bootable USB with everything you need to fix problems.',
      action: 'Next',
      icon: '⚡',
      position: 'center',
    },
    {
      id: 'quick-actions',
      screen: 'home',
      title: 'Quick Actions',
      description: 'Choose what you want to do. "Fix Windows" is perfect for beginners!',
      action: 'Next',
      icon: '⚙️',
      position: 'top',
      highlightElement: 'quick-actions',
    },
    {
      id: 'ready',
      screen: 'home',
      title: 'Ready to Build?',
      description: 'Tap any quick action to get started. Takes just 10 minutes!',
      action: 'Get Started',
      icon: '🚀',
      position: 'center',
    },
  ],
};

/**
 * Device Wizard tour
 */
export const deviceWizardTour: OnboardingTour = {
  id: 'device-wizard',
  name: 'Understanding Your Device',
  completed: false,
  steps: [
    {
      id: 'auto-detect',
      screen: 'wizard',
      title: 'Your Device',
      description: 'Bobby\'s automatically detected your computer specs. No manual setup needed!',
      action: 'Next',
      icon: '🖥️',
      position: 'top',
      highlightElement: 'device-info',
    },
    {
      id: 'compatibility',
      screen: 'wizard',
      title: 'What Can You Install?',
      description: 'Green = works great, Yellow = might need tweaks, Red = won\'t work',
      action: 'Next',
      icon: '✓',
      position: 'top',
      highlightElement: 'compatibility-list',
    },
    {
      id: 'build-usb',
      screen: 'wizard',
      title: 'Build Your USB',
      description: 'Tap any OS to build a bootable USB for it.',
      action: 'Done',
      icon: '🚀',
      position: 'bottom',
      highlightElement: 'build-button',
    },
  ],
};

/**
 * USB Builder tour
 */
export const usbBuilderTour: OnboardingTour = {
  id: 'usb-builder',
  name: 'Building Your USB',
  completed: false,
  steps: [
    {
      id: 'choose-recipe',
      screen: 'builder',
      title: 'Choose a Recipe',
      description: 'Pick a pre-built USB recipe. "Windows Repair Kit" is recommended for first-timers.',
      action: 'Next',
      icon: '📋',
      position: 'top',
      highlightElement: 'recipe-list',
    },
    {
      id: 'recipe-details',
      screen: 'builder',
      title: 'What\'s Included?',
      description: 'Each recipe includes operating systems and repair tools. See the details before building.',
      action: 'Next',
      icon: '📦',
      position: 'top',
      highlightElement: 'recipe-details',
    },
    {
      id: 'build-warning',
      screen: 'builder',
      title: 'Important!',
      description: 'All data on the USB will be erased. Make sure you have the right USB!',
      action: 'Next',
      icon: '⚠️',
      position: 'top',
      highlightElement: 'warning',
    },
    {
      id: 'build-now',
      screen: 'builder',
      title: 'Ready to Build?',
      description: 'Tap "Yes, Build This USB" to start. Takes about 10-15 minutes.',
      action: 'Done',
      icon: '🔥',
      position: 'bottom',
      highlightElement: 'build-button',
    },
  ],
};

/**
 * Contextual tooltips throughout the app
 */
export const tooltips: Record<string, Tooltip> = {
  'multi-boot': {
    id: 'multi-boot',
    title: 'Multi-Boot USB',
    description: 'One USB that can boot Windows, Linux, ChromeOS, and repair tools. Choose which one when you boot!',
    icon: '⚡',
    learnMoreUrl: '/knowledge/multi-boot-usb',
  },
  'compatible-os': {
    id: 'compatible-os',
    title: 'Compatible',
    description: 'This operating system works great on your device. No issues expected!',
    icon: '✓',
  },
  'partial-os': {
    id: 'partial-os',
    title: 'Partial Support',
    description: 'This OS might work, but there could be some issues. See details for more info.',
    icon: '⚠️',
  },
  'incompatible-os': {
    id: 'incompatible-os',
    title: 'Not Compatible',
    description: 'Your device can\'t run this OS. Try one of the compatible ones instead.',
    icon: '✗',
  },
  'quick-actions': {
    id: 'quick-actions',
    title: 'Quick Actions',
    description: 'These are the most common things people do. Pick one to get started!',
    icon: '⚡',
  },
  'custom-usb': {
    id: 'custom-usb',
    title: 'Custom USB',
    description: 'Build your own USB by choosing specific operating systems and tools.',
    icon: '⚙️',
  },
  'device-wizard': {
    id: 'device-wizard',
    title: 'Device Wizard',
    description: 'Automatically detects your computer and shows which operating systems you can install.',
    icon: '🖥️',
  },
  'usb-builder': {
    id: 'usb-builder',
    title: 'USB Builder',
    description: 'Choose which operating systems and tools to include on your USB.',
    icon: '🔨',
  },
  'knowledge-base': {
    id: 'knowledge-base',
    title: 'Knowledge Base',
    description: 'Guides, tutorials, and troubleshooting for everything Bobby\'s PhoenixDrive.',
    icon: '📖',
  },
  'recipe-size': {
    id: 'recipe-size',
    title: 'USB Size Needed',
    description: 'The minimum USB size required for this recipe. Use a larger USB if you have one.',
    icon: '💾',
  },
  'recipe-time': {
    id: 'recipe-time',
    title: 'Build Time',
    description: 'How long it takes to create this USB. Depends on your internet speed and USB speed.',
    icon: '⏱️',
  },
  'progress-bar': {
    id: 'progress-bar',
    title: 'Build Progress',
    description: 'Shows how far along the USB build is. Don\'t disconnect the USB during this process!',
    icon: '📊',
  },
  'bookmark': {
    id: 'bookmark',
    title: 'Save for Later',
    description: 'Bookmark this article to find it quickly later.',
    icon: '🔖',
  },
};

/**
 * Help content for common questions
 */
export const helpContent: Record<string, string> = {
  'what-is-bootable-usb': `A bootable USB is a USB drive that your computer can start from. Instead of using Windows or Mac that's already on your computer, it uses the operating system on the USB. This is useful for fixing problems or trying a new OS.`,

  'why-multi-boot': `A multi-boot USB lets you choose which operating system to use when you start your computer. This saves space and time because you only need one USB instead of several.`,

  'how-to-boot-from-usb': `1. Plug the USB into your computer
2. Restart your computer
3. Press F12, F2, DEL, or ESC during startup (depends on your computer)
4. Select the USB from the boot menu
5. Choose which OS to boot`,

  'usb-too-small': `The USB is too small for the recipe you chose. You need at least the size shown. Try a different recipe or use a larger USB.`,

  'build-failed': `The build failed. This could be because:
- USB was disconnected during build
- USB is damaged or faulty
- Not enough space on USB
Try again with a different USB or recipe.`,

  'how-long-does-build-take': `Building a USB usually takes 10-15 minutes, depending on:
- Your internet speed (downloading files)
- Your USB speed (writing files)
- The size of the recipe

You can see the estimated time before building.`,

  'can-i-use-same-usb': `Yes! You can erase and rebuild the same USB many times. Each time you build, all the old data is erased.`,

  'is-it-safe': `Yes, it's completely safe. Bobby's PhoenixDrive:
- Only writes to the USB you select
- Never touches your computer's hard drive
- Validates everything before building
- Includes safety checks at every step`,
};

/**
 * Get onboarding tour by ID
 */
export function getTour(id: string): OnboardingTour | null {
  const tours = [firstTimeUserTour, deviceWizardTour, usbBuilderTour];
  return tours.find((tour) => tour.id === id) || null;
}

/**
 * Get tooltip by ID
 */
export function getTooltip(id: string): Tooltip | null {
  return tooltips[id] || null;
}

/**
 * Get help content by ID
 */
export function getHelp(id: string): string | null {
  return helpContent[id] || null;
}

/**
 * Mark tour as completed
 */
export function completeTour(id: string): void {
  const tour = getTour(id);
  if (tour) {
    tour.completed = true;
  }
}

/**
 * Check if tour should be shown
 */
export function shouldShowTour(id: string): boolean {
  const tour = getTour(id);
  return tour ? !tour.completed : false;
}
