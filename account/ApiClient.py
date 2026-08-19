# ApiClient.py

Central API Client with CSRF protection and session management
Thread-safe singleton pattern for consistent API communication


import requests
import json
import threading
from typing import Optional, Dict, Any, Union
from datetime import datetime
import os
import sys


class ApiClient
    Thread-safe API client with CSRF protection
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls)
        if cls._instance is None
            with cls._lock
                if cls._instance is None
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self)
        if self._initialized
            return
        self._initialized = True
        
        # Get API URL from config
        try
            from account_config import account_config
            self.base_url = account_config.API_BASE_URL
            self.verify_ssl = getattr(account_config, 'VERIFY_SSL', False)
        except ImportError
            # Fallback if account_config doesn't exist
            self.base_url = httpslocalhost8443
            self.verify_ssl = False
            print(⚠️  Warning account_config not found, using default URL)
        
        # Create session with cookies
        self.session = requests.Session()
        self.session.verify = self.verify_ssl
        
        # User authentication data
        self.user_id = None
        self.token = None
        self.user_data = None
        
        # Request tracking
        self._request_count = 0
        self._request_lock = threading.Lock()
        
        # Default headers
        self.default_headers = {
            Content-Type applicationjson,
            X-Requested-With XMLHttpRequest,
            Accept applicationjson,
            User-Agent Latigo-Client1.0
        }
        
        # Update session headers
        self.session.headers.update(self.default_headers)
        
        # Suppress SSL warnings if verify is False
        if not self.verify_ssl
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        print(f✅ ApiClient initialized)
        print(f   Base URL {self.base_url})
        print(f   SSL Verify {self.verify_ssl})
        print(f   Session ID {id(self.session)})
    
    def set_auth(self, user_id str, token str, user_data Dict[str, Any] = None)
        
        Set authentication data after login
        
        Args
            user_id The user's ID
            token The authentication token
            user_data Optional user data dictionary
        
        self.user_id = user_id
        self.token = token
        self.user_data = user_data
        
        # Update session headers with auth
        if token
            self.session.headers.update({
                Authorization fBearer {token},
                X-User-ID str(user_id)
            })
        
        # Also update account_config for backward compatibility
        try
            from account_config import account_config
            account_config.CURRENT_USER_ID = user_id
            account_config.CURRENT_TOKEN = token
            account_config.CURRENT_USER_DATA = user_data
        except ImportError
            pass
        
        print(f🔐 Auth set for user {user_id})
        print(f   Token {token[20]}... if token else    Token None)
    
    def clear_auth(self)
        Clear authentication data (logout)
        self.user_id = None
        self.token = None
        self.user_data = None
        
        # Remove auth headers from session
        if Authorization in self.session.headers
            del self.session.headers[Authorization]
        if X-User-ID in self.session.headers
            del self.session.headers[X-User-ID]
        
        # Clear cookies
        self.session.cookies.clear()
        
        # Clear account_config
        try
            from account_config import account_config
            account_config.CURRENT_USER_ID = None
            account_config.CURRENT_TOKEN = None
            account_config.CURRENT_USER_DATA = None
        except ImportError
            pass
        
        print(🔐 Auth cleared)
    
    def is_authenticated(self) - bool
        Check if the client is authenticated
        return self.user_id is not None and self.token is not None
    
    def get_user_id(self) - Optional[str]
        Get the current user ID
        return self.user_id
    
    def get_token(self) - Optional[str]
        Get the current token
        return self.token
    
    def get_user_data(self) - Optional[Dict[str, Any]]
        Get the current user data
        return self.user_data
    
    def _get_csrf_token(self) - Optional[str]
        Extract CSRF token from cookies
        try
            for cookie in self.session.cookies
                if cookie.name == csrf_token
                    return cookie.value
        except Exception as e
            print(f⚠️  Error getting CSRF token {e})
        return None
    
    def _prepare_headers(self, extra_headers Dict[str, str] = None) - Dict[str, str]
        Prepare headers with CSRF token if available
        headers = self.default_headers.copy()
        
        # Add auth headers if authenticated
        if self.token
            headers[Authorization] = fBearer {self.token}
        if self.user_id
            headers[X-User-ID] = str(self.user_id)
        
        # Add CSRF token if available
        csrf_token = self._get_csrf_token()
        if csrf_token
            headers[X-CSRF-Token] = csrf_token
        
        # Add custom headers
        if extra_headers
            headers.update(extra_headers)
        
        return headers
    
    def _increment_request_count(self) - int
        Increment and return the request count
        with self._request_lock
            self._request_count += 1
            return self._request_count
    
    def request(self, method str, endpoint str, 
                data Dict[str, Any] = None, 
                params Dict[str, Any] = None,
                headers Dict[str, str] = None,
                timeout int = 30,
                raw_response bool = False) - Union[requests.Response, Dict[str, Any]]
        
        Make an HTTP request with CSRF protection
        
        Args
            method HTTP method (GET, POST, PUT, DELETE, PATCH)
            endpoint API endpoint (e.g., apilogin)
            data JSON data for POSTPUTPATCH requests
            params Query parameters for GET requests
            headers Additional headers
            timeout Request timeout in seconds
            raw_response If True, return the raw Response object
        
        Returns
            requests.Response object or parsed JSON dict
        
        Raises
            requests.RequestException On network errors
            ValueError On invalid JSON response
        
        # Ensure endpoint starts with 
        if not endpoint.startswith('')
            endpoint = '' + endpoint
        
        url = f{self.base_url}{endpoint}
        prepared_headers = self._prepare_headers(headers)
        
        # Increment request counter
        request_id = self._increment_request_count()
        
        print(fn📤 [{request_id}] {method} {endpoint})
        print(f   Headers { {k v[20]+'...' if len(str(v))  20 else v for k, v in prepared_headers.items()} })
        
        # Log request data (but hide passwords)
        if data
            safe_data = data.copy() if isinstance(data, dict) else data
            if isinstance(safe_data, dict) and password in safe_data
                safe_data[password] = HIDDEN
            if isinstance(safe_data, dict) and new_password in safe_data
                safe_data[new_password] = HIDDEN
            print(f   Data {safe_data})
        
        if params
            print(f   Params {params})
        
        try
            start_time = datetime.now()
            
            # Make the request
            response = self.session.request(
                method=method.upper(),
                url=url,
                json=data,
                params=params,
                headers=prepared_headers,
                timeout=timeout
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            print(f📥 [{request_id}] Response {response.status_code} ({elapsed.2f}s))
            
            # Log response preview
            try
                response_json = response.json()
                if isinstance(response_json, dict)
                    # Remove sensitive data from logs
                    safe_response = response_json.copy()
                    if password in safe_response
                        safe_response[password] = HIDDEN
                    if token in safe_response
                        safe_response[token] = safe_response[token][20] + ... if safe_response[token] else None
                    print(f   Response {json.dumps(safe_response, indent=2)[500]}...)
            except
                print(f   Response {response.text[200]}...)
            
            if raw_response
                return response
            
            # Parse JSON response
            try
                return response.json()
            except ValueError
                # Return raw response if not JSON
                return response.text
            
        except requests.exceptions.ConnectionError as e
            print(f❌ [{request_id}] Connection error to {url} {e})
            raise requests.exceptions.ConnectionError(fCould not connect to server at {self.base_url}. Please check if the server is running.) from e
            
        except requests.exceptions.Timeout as e
            print(f❌ [{request_id}] Timeout connecting to {url} {e})
            raise requests.exceptions.Timeout(fRequest timed out after {timeout}s. Please try again.) from e
            
        except requests.exceptions.SSLError as e
            print(f❌ [{request_id}] SSL error {e})
            raise requests.exceptions.SSLError(SSL certificate verification failed. If using a self-signed certificate, set VERIFY_SSL=False in account_config.) from e
            
        except Exception as e
            print(f❌ [{request_id}] Request error {e})
            raise
    
    # ========== Convenience Methods ==========
    
    def get(self, endpoint str, params Dict[str, Any] = None, 
            headers Dict[str, str] = None, timeout int = 30,
            raw_response bool = False) - Union[requests.Response, Dict[str, Any]]
        GET request convenience method
        return self.request(GET, endpoint, params=params, 
                          headers=headers, timeout=timeout, 
                          raw_response=raw_response)
    
    def post(self, endpoint str, data Dict[str, Any] = None,
             headers Dict[str, str] = None, timeout int = 30,
             raw_response bool = False) - Union[requests.Response, Dict[str, Any]]
        POST request convenience method
        return self.request(POST, endpoint, data=data,
                          headers=headers, timeout=timeout,
                          raw_response=raw_response)
    
    def put(self, endpoint str, data Dict[str, Any] = None,
            headers Dict[str, str] = None, timeout int = 30,
            raw_response bool = False) - Union[requests.Response, Dict[str, Any]]
        PUT request convenience method
        return self.request(PUT, endpoint, data=data,
                          headers=headers, timeout=timeout,
                          raw_response=raw_response)
    
    def delete(self, endpoint str, 
               headers Dict[str, str] = None, timeout int = 30,
               raw_response bool = False) - Union[requests.Response, Dict[str, Any]]
        DELETE request convenience method
        return self.request(DELETE, endpoint,
                          headers=headers, timeout=timeout,
                          raw_response=raw_response)
    
    def patch(self, endpoint str, data Dict[str, Any] = None,
              headers Dict[str, str] = None, timeout int = 30,
              raw_response bool = False) - Union[requests.Response, Dict[str, Any]]
        PATCH request convenience method
        return self.request(PATCH, endpoint, data=data,
                          headers=headers, timeout=timeout,
                          raw_response=raw_response)
    
    # ========== File Upload Methods ==========
    
    def upload_file(self, endpoint str, file_path str, 
                    file_field str = avatar,
                    additional_data Dict[str, Any] = None,
                    timeout int = 60) - requests.Response
        
        Upload a file with multipartform-data
        
        Args
            endpoint API endpoint
            file_path Path to the file to upload
            file_field Name of the file field (default avatar)
            additional_data Additional form data
            timeout Request timeout in seconds
        
        Returns
            requests.Response object
        
        if not os.path.exists(file_path)
            raise FileNotFoundError(fFile not found {file_path})
        
        # Prepare URL
        if not endpoint.startswith('')
            endpoint = '' + endpoint
        url = f{self.base_url}{endpoint}
        
        # Prepare headers (without Content-Type, requests will set it for multipart)
        headers = self._prepare_headers({})
        
        # Remove Content-Type from headers to let requests set it
        if Content-Type in headers
            del headers[Content-Type]
        
        # Prepare files
        filename = os.path.basename(file_path)
        files = {
            file_field (filename, open(file_path, 'rb'), self._get_mime_type(file_path))
        }
        
        # Prepare data
        data = additional_data or {}
        
        request_id = self._increment_request_count()
        print(fn📤 [{request_id}] UPLOAD {endpoint})
        print(f   File {filename})
        print(f   Size {os.path.getsize(file_path)} bytes)
        
        try
            response = self.session.post(
                url,
                files=files,
                data=data,
                headers=headers,
                timeout=timeout
            )
            
            print(f📥 [{request_id}] Upload response {response.status_code})
            return response
            
        except Exception as e
            print(f❌ [{request_id}] Upload error {e})
            raise
        finally
            # Close file
            if file_field in files
                files[file_field][1].close()
    
    def _get_mime_type(self, file_path str) - str
        Get MIME type based on file extension
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.jpg' 'imagejpeg',
            '.jpeg' 'imagejpeg',
            '.png' 'imagepng',
            '.gif' 'imagegif',
            '.webp' 'imagewebp',
            '.pdf' 'applicationpdf',
            '.txt' 'textplain',
            '.json' 'applicationjson',
            '.zip' 'applicationzip',
        }
        return mime_types.get(ext, 'applicationoctet-stream')
    
    # ========== Status and Debug Methods ==========
    
    def get_status(self) - Dict[str, Any]
        Get the current status of the API client
        return {
            base_url self.base_url,
            is_authenticated self.is_authenticated(),
            user_id self.user_id,
            has_token self.token is not None,
            request_count self._request_count,
            verify_ssl self.verify_ssl,
            session_id id(self.session),
            cookies {cookie.name cookie.value for cookie in self.session.cookies},
            headers {k v[20]+'...' if len(str(v))  20 else v 
                       for k, v in self.session.headers.items()}
        }
    
    def print_status(self)
        Print the current status
        status = self.get_status()
        print(n + =50)
        print(API CLIENT STATUS)
        print(=50)
        for key, value in status.items()
            print(f  {key} {value})
        print(=50 + n)
    
    def refresh_csrf_token(self) - bool
        
        Attempt to refresh CSRF token by making a harmless GET request
        Returns True if successful, False otherwise
        
        try
            # Make a GET request to get a fresh CSRF token
            response = self.get(apihealth, raw_response=True)
            
            # Check if we got a CSRF token in cookies
            csrf_token = self._get_csrf_token()
            if csrf_token
                print(f✅ CSRF token refreshed {csrf_token[10]}...)
                return True
            else
                print(⚠️  CSRF token not received)
                return False
                
        except Exception as e
            print(f❌ Failed to refresh CSRF token {e})
            return False


# ========== Global Instance ==========

# Create a global instance for easy import
api_client = ApiClient()

# Export the instance
__all__ = ['api_client', 'ApiClient']