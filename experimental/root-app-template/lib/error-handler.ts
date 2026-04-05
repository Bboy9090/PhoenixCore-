/**
 * Comprehensive error handling and recovery system for Bobby's PhoenixDrive
 */

export enum ErrorSeverity {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical',
}

export interface PhoenixError {
  code: string;
  message: string;
  severity: ErrorSeverity;
  context?: Record<string, any>;
  recoverySteps?: string[];
  retryable: boolean;
  timestamp: string;
}

export class ErrorHandler {
  private static errors: PhoenixError[] = [];
  private static maxErrors = 50;

  /**
   * Create a new error with context
   */
  static create(
    code: string,
    message: string,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    context?: Record<string, any>,
    retryable: boolean = false,
    recoverySteps?: string[]
  ): PhoenixError {
    const error: PhoenixError = {
      code,
      message,
      severity,
      context,
      recoverySteps,
      retryable,
      timestamp: new Date().toISOString(),
    };

    this.log(error);
    return error;
  }

  /**
   * Log error to internal store
   */
  private static log(error: PhoenixError): void {
    this.errors.push(error);
    if (this.errors.length > this.maxErrors) {
      this.errors.shift();
    }

    // Log to console in development
    if (__DEV__) {
      console.error(`[${error.severity.toUpperCase()}] ${error.code}: ${error.message}`, error.context);
    }
  }

  /**
   * Get user-friendly error message
   */
  static getUserMessage(error: PhoenixError): string {
    const messages: Record<string, string> = {
      HARDWARE_DETECT_FAILED: 'Could not detect device hardware. Please try again.',
      USB_ENUM_FAILED: 'Could not find USB devices. Please connect a USB drive and try again.',
      RECIPE_BUILD_FAILED: 'Failed to create recipe. Please check your selections and try again.',
      USB_BUILD_FAILED: 'Failed to build USB. Please ensure the USB drive is connected and try again.',
      NETWORK_ERROR: 'Network connection lost. Please check your connection and try again.',
      STORAGE_ERROR: 'Could not save data locally. Please check storage space.',
      INVALID_RECIPE: 'Recipe is invalid. Please rebuild it.',
      DEVICE_DISCONNECTED: 'USB device was disconnected. Please reconnect and try again.',
      INSUFFICIENT_SPACE: 'USB device does not have enough space for this recipe.',
      PERMISSION_DENIED: 'Permission denied. Please check device permissions.',
    };

    return messages[error.code] || error.message;
  }

  /**
   * Handle specific error types
   */
  static handle(error: unknown): PhoenixError {
    if (error && typeof error === 'object' && 'code' in error && 'message' in error) {
      return error as PhoenixError;
    }

    if (error instanceof Error) {
      const code = this.inferErrorCode(error.message);
      return this.create(code, error.message, ErrorSeverity.ERROR, { originalError: error }, true);
    }

    if (typeof error === 'string') {
      return this.create('UNKNOWN_ERROR', error, ErrorSeverity.ERROR, {}, true);
    }

    return this.create('UNKNOWN_ERROR', 'An unknown error occurred', ErrorSeverity.ERROR, { error }, true);
  }

  /**
   * Infer error code from error message
   */
  private static inferErrorCode(message: string): string {
    if (message.includes('network') || message.includes('fetch') || message.includes('connection')) {
      return 'NETWORK_ERROR';
    }
    if (message.includes('storage') || message.includes('storage')) {
      return 'STORAGE_ERROR';
    }
    if (message.includes('permission') || message.includes('denied')) {
      return 'PERMISSION_DENIED';
    }
    if (message.includes('device') || message.includes('disconnect')) {
      return 'DEVICE_DISCONNECTED';
    }
    if (message.includes('space') || message.includes('size')) {
      return 'INSUFFICIENT_SPACE';
    }
    return 'UNKNOWN_ERROR';
  }

  /**
   * Get all logged errors
   */
  static getErrors(): PhoenixError[] {
    return [...this.errors];
  }

  /**
   * Clear error log
   */
  static clearErrors(): void {
    this.errors = [];
  }

  /**
   * Get last error
   */
  static getLastError(): PhoenixError | null {
    return this.errors[this.errors.length - 1] || null;
  }

  /**
   * Get errors by severity
   */
  static getErrorsBySeverity(severity: ErrorSeverity): PhoenixError[] {
    return this.errors.filter((e) => e.severity === severity);
  }

  /**
   * Check if there are critical errors
   */
  static hasCriticalErrors(): boolean {
    return this.errors.some((e) => e.severity === ErrorSeverity.CRITICAL);
  }
}

/**
 * Retry logic with exponential backoff
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxAttempts: number = 3,
  initialDelayMs: number = 1000
): Promise<T> {
  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));

      if (attempt < maxAttempts) {
        const delayMs = initialDelayMs * Math.pow(2, attempt - 1);
        await new Promise((resolve) => setTimeout(resolve, delayMs));
      }
    }
  }

  throw lastError || new Error('Retry failed');
}

/**
 * Timeout wrapper for promises
 */
export function withTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
  return Promise.race([
    promise,
    new Promise<T>((_, reject) =>
      setTimeout(() => reject(new Error('Operation timed out')), timeoutMs)
    ),
  ]);
}

/**
 * Safe async operation wrapper
 */
export async function safeAsync<T>(
  fn: () => Promise<T>,
  errorCode: string = 'OPERATION_FAILED'
): Promise<{ success: boolean; data?: T; error?: PhoenixError }> {
  try {
    const data = await fn();
    return { success: true, data };
  } catch (error) {
    const phoenixError = ErrorHandler.create(
      errorCode,
      error instanceof Error ? error.message : String(error),
      ErrorSeverity.ERROR,
      { originalError: error },
      true
    );
    return { success: false, error: phoenixError };
  }
}

/**
 * Validate required fields
 */
export function validateRequired(data: Record<string, any>, requiredFields: string[]): PhoenixError | null {
  const missing = requiredFields.filter((field) => !data[field]);

  if (missing.length > 0) {
    return ErrorHandler.create(
      'VALIDATION_ERROR',
      `Missing required fields: ${missing.join(', ')}`,
      ErrorSeverity.WARNING,
      { missingFields: missing },
      false
    );
  }

  return null;
}

/**
 * Validate recipe structure
 */
export function validateRecipe(recipe: any): PhoenixError | null {
  const requiredFields = ['recipe_id', 'name', 'deployment_type', 'os_images', 'tools', 'metadata'];
  return validateRequired(recipe, requiredFields);
}

/**
 * Validate USB device
 */
export function validateUSBDevice(device: any): PhoenixError | null {
  const requiredFields = ['device_id', 'device_path', 'size_gb', 'vendor', 'model'];
  return validateRequired(device, requiredFields);
}

/**
 * Check if error is retryable
 */
export function isRetryable(error: PhoenixError): boolean {
  const retryableCodes = [
    'NETWORK_ERROR',
    'DEVICE_DISCONNECTED',
    'TIMEOUT',
    'HARDWARE_DETECT_FAILED',
    'USB_ENUM_FAILED',
  ];

  return error.retryable && retryableCodes.includes(error.code);
}
