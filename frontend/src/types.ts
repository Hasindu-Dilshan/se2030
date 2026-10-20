export interface Room {
  id: number;
  room_number: string;
  category: string;
  rate_per_night: number;
  max_capacity: number;
}

export interface Tourist {
  id: number;
  full_name: string;
  nationality: string;
  phone: string;
  email: string;
  passport_id: string;
}

export interface Booking {
  id: number;
  booking_ref: string;
  room_id: number;
  tourist_id: number;
  check_in: string;
  check_out: string;
  total_nights: number;
  total_tariff: number;
  status: 'CONFIRMED' | 'COMPLETED';
  special_requests?: string | null;
  created_at: string;
  room: Room;
  tourist: Tourist;
}

export interface BookingCreatePayload {
  room_id: number;
  check_in: string;
  check_out: string;
  full_name: string;
  nationality: string;
  phone: string;
  email: string;
  passport_id: string;
  special_requests?: string;
}

export interface BookingUpdatePayload {
  check_in: string;
  check_out: string;
}

export interface BookingCreatedResponse extends Booking {
  manage_token: string;
}
