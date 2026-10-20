import axios from 'axios';
import {
  Room,
  Booking,
  BookingCreatePayload,
  BookingUpdatePayload,
  BookingCreatedResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BxASE_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================================================
// Security Token LocalStorage Management
// ============================================================================
const TOKEN_STORAGE_PREFIX = 'tourstay_token_';

export const saveManageToken = (bookingRef: string, token: string): void => {
  try {
    localStorage.setItem(`${TOKEN_STORAGE_PREFIX}${bookingRef}`, token);
  } catch (err) {
    console.error('Failed to save manage token to localStorage:', err);
  }
};

export const getManageToken = (bookingRef: string): string | null => {
  try {
    return localStorage.getItem(`${TOKEN_STORAGE_PREFIX}${bookingRef}`);
  } catch (err) {
    console.error('Failed to read manage token from localStorage:', err);
    return null;
  }
};

export const removeManageToken = (bookingRef: string): void => {
  try {
    localStorage.removeItem(`${TOKEN_STORAGE_PREFIX}${bookingRef}`);
  } catch (err) {
    console.error('Failed to remove manage token from localStorage:', err);
  }
};

// ============================================================================
// API Methods
// ============================================================================

export const getRooms = async (): Promise<Room[]> => {
  const response = await apiClient.get<Room[]>('/rooms');
  return response.data;
};

export const getAvailableRooms = async (checkIn: string, checkOut: string): Promise<Room[]> => {
  const response = await apiClient.get<Room[]>('/rooms/available', {
    params: {
      check_in: checkIn,
      check_out: checkOut,
    },
  });
  return response.data;
};

export const createBooking = async (
  payload: BookingCreatePayload
): Promise<BookingCreatedResponse> => {
  const response = await apiClient.post<BookingCreatedResponse>('/bookings', payload);
  const data = response.data;
  if (data.booking_ref && data.manage_token) {
    saveManageToken(data.booking_ref, data.manage_token);
  }
  return data;
};

export const getBookingByRef = async (ref: string): Promise<Booking> => {
  const response = await apiClient.get<Booking>(`/bookings/${encodeURIComponent(ref)}`);
  return response.data;
};

export const listBookings = async (
  status?: string,
  limit: number = 50,
  offset: number = 0
): Promise<Booking[]> => {
  const params: Record<string, string | number> = { limit, offset };
  if (status && status !== 'ALL') {
    params.status = status;
  }
  const response = await apiClient.get<Booking[]>('/bookings', { params });
  return response.data;
};

export const updateBookingDates = async (
  ref: string,
  payload: BookingUpdatePayload,
  token: string
): Promise<Booking> => {
  const response = await apiClient.patch<Booking>(
    `/bookings/${encodeURIComponent(ref)}`,
    payload,
    {
      headers: {
        'X-Manage-Token': token,
      },
    }
  );
  return response.data;
};

export const deleteBooking = async (ref: string, token: string): Promise<void> => {
  await apiClient.delete(`/bookings/${encodeURIComponent(ref)}`, {
    headers: {
      'X-Manage-Token': token,
    },
  });
  removeManageToken(ref);
};
