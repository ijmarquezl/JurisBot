import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_URL, // API_URL from env already contains /api
});

// Request interceptor to add the auth token header to requests
apiClient.interceptors.request.use(
  (config) => {
    const accessToken = localStorage.getItem('accessToken');
    if (accessToken) {
      config.headers['Authorization'] = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem('refreshToken');
        // Use apiClient to automatically handle the base URL and prefixes
        const response = await apiClient.post('/refresh', { refresh_token: refreshToken });
        
        const { access_token } = response.data;
        localStorage.setItem('accessToken', access_token);
        
        // Update the authorization header of the original request
        originalRequest.headers['Authorization'] = `Bearer ${access_token}`;
        
        // Retry the original request
        return apiClient(originalRequest);
      } catch (refreshError) {
        // If refresh fails, logout the user
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        // Redirect to login or handle as needed
        window.location.href = '/'; // Or some other logout logic
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

export const createUser = async (email, password, fullName, role) => {
    try {
        const response = await apiClient.post('/admin/users', {
            email: email,
            password: password,
            full_name: fullName,
            role: role
        });
        return response.data;
    } catch (error) {
        throw error;
    }
};

export default apiClient;
