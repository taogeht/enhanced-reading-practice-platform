/**
 * Frontend security utilities
 */

// Input sanitization utilities
export class SecurityUtils {
  /**
   * Sanitize user input to prevent XSS
   */
  static sanitizeInput(input: string): string {
    if (!input) return input;
    
    // Create a temporary div element to leverage browser's built-in HTML encoding
    const div = document.createElement('div');
    div.textContent = input;
    return div.innerHTML;
  }

  /**
   * Validate email format
   */
  static isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  /**
   * Validate password strength
   */
  static validatePassword(password: string): {
    isValid: boolean;
    errors: string[];
  } {
    const errors: string[] = [];
    
    if (password.length < 8) {
      errors.push('Password must be at least 8 characters long');
    }
    
    if (!/[A-Z]/.test(password)) {
      errors.push('Password must contain at least one uppercase letter');
    }
    
    if (!/[a-z]/.test(password)) {
      errors.push('Password must contain at least one lowercase letter');
    }
    
    if (!/\d/.test(password)) {
      errors.push('Password must contain at least one number');
    }
    
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      errors.push('Password must contain at least one special character');
    }
    
    // Check for common patterns
    const commonPatterns = ['123456', 'password', 'qwerty', 'abc123'];
    if (commonPatterns.some(pattern => password.toLowerCase().includes(pattern))) {
      errors.push('Password contains common patterns');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Validate file upload
   */
  static validateFileUpload(file: File, options: {
    maxSize?: number; // in MB
    allowedTypes?: string[];
  } = {}): {
    isValid: boolean;
    errors: string[];
  } {
    const errors: string[] = [];
    const maxSize = options.maxSize || 10; // Default 10MB
    const allowedTypes = options.allowedTypes || [];
    
    // Check file size
    if (file.size > maxSize * 1024 * 1024) {
      errors.push(`File size must be less than ${maxSize}MB`);
    }
    
    // Check file type
    if (allowedTypes.length > 0) {
      const fileExtension = file.name.split('.').pop()?.toLowerCase();
      if (!fileExtension || !allowedTypes.includes(fileExtension)) {
        errors.push(`File type must be one of: ${allowedTypes.join(', ')}`);
      }
    }
    
    // Check for suspicious file names
    const dangerousPatterns = /\.(exe|bat|cmd|com|scr|php|asp|jsp|py|pl)$/i;
    if (dangerousPatterns.test(file.name)) {
      errors.push('File type not allowed for security reasons');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Check if URL is safe (same origin or whitelisted)
   */
  static isSafeUrl(url: string): boolean {
    try {
      const urlObj = new URL(url, window.location.origin);
      
      // Check if same origin
      if (urlObj.origin === window.location.origin) {
        return true;
      }
      
      // Whitelist of allowed external domains
      const allowedDomains = [
        'https://api.example.com',
        // Add other trusted domains here
      ];
      
      return allowedDomains.some(domain => urlObj.origin === domain);
    } catch {
      return false;
    }
  }

  /**
   * Content Security Policy helper
   */
  static createCSPNonce(): string {
    const array = new Uint8Array(16);
    crypto.getRandomValues(array);
    return btoa(String.fromCharCode.apply(null, Array.from(array)));
  }
}

// API Security utilities
export class APISecurityUtils {
  /**
   * Add security headers to API requests
   */
  static addSecurityHeaders(headers: Record<string, string> = {}): Record<string, string> {
    const csrfToken = this.getCSRFToken();
    
    return {
      ...headers,
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
      ...(csrfToken && { 'X-CSRFToken': csrfToken }),
    };
  }

  /**
   * Get CSRF token from cookie or meta tag
   */
  static getCSRFToken(): string | null {
    // Try to get from cookie first
    const cookieValue = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrftoken='))
      ?.split('=')[1];
    
    if (cookieValue) {
      return cookieValue;
    }
    
    // Fallback to meta tag
    const metaElement = document.querySelector('meta[name="csrf-token"]') as HTMLMetaElement;
    return metaElement?.content || null;
  }

  /**
   * Validate API response to prevent prototype pollution
   */
  static validateAPIResponse(response: any): boolean {
    if (typeof response !== 'object' || response === null) {
      return true; // Primitive values are safe
    }
    
    // Check for dangerous keys
    const dangerousKeys = ['__proto__', 'constructor', 'prototype'];
    
    const checkObject = (obj: any): boolean => {
      if (typeof obj !== 'object' || obj === null) {
        return true;
      }
      
      for (const key in obj) {
        if (dangerousKeys.includes(key)) {
          return false;
        }
        
        if (!checkObject(obj[key])) {
          return false;
        }
      }
      
      return true;
    };
    
    return checkObject(response);
  }

  /**
   * Rate limiting helper for frontend
   */
  static createRateLimiter(maxRequests: number, timeWindow: number) {
    const requests: number[] = [];
    
    return () => {
      const now = Date.now();
      
      // Remove old requests outside the time window
      while (requests.length > 0 && now - requests[0] > timeWindow) {
        requests.shift();
      }
      
      // Check if we can make another request
      if (requests.length >= maxRequests) {
        return false;
      }
      
      requests.push(now);
      return true;
    };
  }
}

// Local Storage security utilities
export class StorageSecurityUtils {
  /**
   * Secure localStorage wrapper with encryption
   */
  static setSecureItem(key: string, value: any, encrypt = false): void {
    try {
      let dataToStore = JSON.stringify(value);
      
      if (encrypt) {
        // Simple obfuscation (in production, use proper encryption)
        dataToStore = btoa(dataToStore);
      }
      
      localStorage.setItem(key, dataToStore);
    } catch (error) {
      console.error('Failed to store secure item:', error);
    }
  }

  /**
   * Secure localStorage getter with decryption
   */
  static getSecureItem(key: string, encrypted = false): any {
    try {
      let data = localStorage.getItem(key);
      
      if (!data) return null;
      
      if (encrypted) {
        // Simple deobfuscation
        data = atob(data);
      }
      
      return JSON.parse(data);
    } catch (error) {
      console.error('Failed to retrieve secure item:', error);
      return null;
    }
  }

  /**
   * Clear sensitive data from storage
   */
  static clearSensitiveData(): void {
    const sensitiveKeys = ['auth_token', 'user_data', 'session_data'];
    
    sensitiveKeys.forEach(key => {
      localStorage.removeItem(key);
      sessionStorage.removeItem(key);
    });
  }

  /**
   * Check if storage is available and secure
   */
  static isStorageSecure(): boolean {
    try {
      // Check if localStorage is available
      const test = 'security_test';
      localStorage.setItem(test, test);
      localStorage.removeItem(test);
      
      // Check if we're on HTTPS (in production)
      if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost') {
        console.warn('Storage may not be secure over HTTP');
        return false;
      }
      
      return true;
    } catch {
      return false;
    }
  }
}

// Form security utilities
export class FormSecurityUtils {
  /**
   * Add honeypot field to form for bot detection
   */
  static createHoneypot(): HTMLInputElement {
    const honeypot = document.createElement('input');
    honeypot.type = 'text';
    honeypot.name = 'website'; // Common honeypot name
    honeypot.style.display = 'none';
    honeypot.setAttribute('tabindex', '-1');
    honeypot.setAttribute('autocomplete', 'off');
    
    return honeypot;
  }

  /**
   * Check if honeypot field was filled (indicates bot)
   */
  static isHoneypotFilled(formData: FormData): boolean {
    return !!formData.get('website');
  }

  /**
   * Add CSRF protection to form
   */
  static addCSRFProtection(form: HTMLFormElement): void {
    const csrfToken = APISecurityUtils.getCSRFToken();
    
    if (csrfToken) {
      const csrfInput = document.createElement('input');
      csrfInput.type = 'hidden';
      csrfInput.name = 'csrfmiddlewaretoken';
      csrfInput.value = csrfToken;
      form.appendChild(csrfInput);
    }
  }

  /**
   * Validate form submission timing (prevents rapid-fire submissions)
   */
  static createSubmissionLimiter(minInterval = 1000) {
    let lastSubmission = 0;
    
    return (): boolean => {
      const now = Date.now();
      if (now - lastSubmission < minInterval) {
        return false;
      }
      lastSubmission = now;
      return true;
    };
  }
}