import React, { useState, useEffect } from 'react';
import { Room } from '../types';
import { getAvailableRooms } from '../services/api';
import { BookingModal } from './BookingModal';
import { 
  Calendar, 
  Users, 
  Search, 
  Sparkles, 
  Check, 
  AlertCircle,
  BedDouble
} from 'lucide-react';

export const RoomCatalog: React.FC = () => {
  // Date range defaults: tomorrow to 4 days from tomorrow
  const getFormattedDate = (daysFromNow: number) => {
    const d = new Date();
    d.setDate(d.getDate() + daysFromNow);
    return d.toISOString().split('T')[0];
  };

  const [checkIn, setCheckIn] = useState<string>(getFormattedDate(1));
  const [checkOut, setCheckOut] = useState<string>(getFormattedDate(4));
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Filters
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [minCapacity, setMinCapacity] = useState<number>(1);

  // Selected room for booking modal
  const [bookingRoom, setBookingRoom] = useState<Room | null>(null);

  // Calculate nights
  const computeNights = () => {
    if (!checkIn || !checkOut) return 1;
    const start = new Date(checkIn);
    const end = new Date(checkOut);
    const diffDays = Math.round((end.getTime() - start.getTime()) / (1000 * 3600 * 24));
    return diffDays > 0 ? diffDays : 0;
  };

  const nights = computeNights();

  const fetchRooms = async () => {
    if (nights <= 0) {
      setErrorMessage('Check-out date must be strictly after check-in date.');
      setRooms([]);
      return;
    }

    setErrorMessage(null);
    setLoading(true);
    try {
      const data = await getAvailableRooms(checkIn, checkOut);
      setRooms(data);
    } catch (err: any) {
      setErrorMessage(
        err.response?.data?.detail || 'Failed to fetch room availability. Please verify dates and try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchRooms();
  }, []);

  // Filtered rooms
  const filteredRooms = rooms.filter((r) => {
    const matchesCategory = selectedCategory === 'ALL' || r.category.toLowerCase().includes(selectedCategory.toLowerCase());
    const matchesCapacity = r.max_capacity >= minCapacity;
    return matchesCategory && matchesCapacity;
  });

  return (
    <div className="space-y-8">
      {/* Hero / Date Search Bar */}
      <section className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-slate-200/80">
        <div className="max-w-3xl mb-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-50 border border-brand-200 text-brand-700 text-xs font-semibold mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Guaranteed Direct Reservation</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900">
            Find Your Ideal Stay
          </h1>
          <p className="text-slate-500 mt-2 text-sm sm:text-base leading-relaxed">
            Real-time room availability powered by atomic concurrency protection. Select your check-in and check-out dates to browse available rooms.
          </p>
        </div>

        {/* Search Controls */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end bg-slate-50 p-4 rounded-2xl border border-slate-200">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-brand-600" /> Check-In
            </label>
            <input
              type="date"
              value={checkIn}
              onChange={(e) => setCheckIn(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500 shadow-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-brand-600" /> Check-Out
            </label>
            <input
              type="date"
              value={checkOut}
              onChange={(e) => setCheckOut(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500 shadow-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <Users className="w-3.5 h-3.5 text-brand-600" /> Min Guests
            </label>
            <select
              value={minCapacity}
              onChange={(e) => setMinCapacity(Number(e.target.value))}
              className="w-full px-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500 shadow-sm"
            >
              <option value={1}>1+ Guest</option>
              <option value={2}>2+ Guests</option>
              <option value={3}>3+ Guests</option>
              <option value={4}>4+ Guests</option>
            </select>
          </div>

          <div>
            <button
              type="button"
              onClick={fetchRooms}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-sm shadow-md shadow-brand-500/20 transition-all disabled:opacity-50 h-[42px]"
            >
              <Search className="w-4 h-4" />
              <span>{loading ? 'Checking...' : 'Check Availability'}</span>
            </button>
          </div>
        </div>

        {/* Validation Error Banner */}
        {errorMessage && (
          <div className="mt-4 p-3.5 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-2.5 text-xs text-rose-800">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}
      </section>

      {/* Room Listing Header & Category Filters */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">
            Available Rooms ({filteredRooms.length})
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Showing accommodations with no conflicting reservations between <span className="font-semibold">{checkIn}</span> and <span className="font-semibold">{checkOut}</span> ({nights} {nights === 1 ? 'night' : 'nights'}).
          </p>
        </div>

        {/* Category Pills */}
        <div className="flex flex-wrap gap-2 text-xs">
          {['ALL', 'Single', 'Double', 'Suite', 'Penthouse'].map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                selectedCategory === cat
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100'
              }`}
            >
              {cat === 'ALL' ? 'All Types' : cat}
            </button>
          ))}
        </div>
      </div>

      {/* Room Cards Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((n) => (
            <div key={n} className="bg-white rounded-2xl p-6 border border-slate-200 animate-pulse space-y-4">
              <div className="h-6 bg-slate-200 rounded w-1/2"></div>
              <div className="h-4 bg-slate-100 rounded w-3/4"></div>
              <div className="h-10 bg-slate-200 rounded"></div>
            </div>
          ))}
        </div>
      ) : filteredRooms.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center border border-slate-200 shadow-sm max-w-lg mx-auto">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-slate-400">
            <BedDouble className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">No Rooms Available</h3>
          <p className="text-sm text-slate-500 mt-1">
            All rooms matching your criteria are booked for these dates. Try adjusting your check-in/out range or guest filter.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredRooms.map((room) => {
            const estimatedTotal = nights * room.rate_per_night;

            return (
              <div
                key={room.id}
                className="bg-white rounded-2xl border border-slate-200 hover:border-brand-300 shadow-sm hover:shadow-md transition-all flex flex-col justify-between overflow-hidden group"
              >
                {/* Card Header */}
                <div className="p-6">
                  <div className="flex justify-between items-start mb-3">
                    <span className="text-xs uppercase tracking-wider font-bold px-2.5 py-1 rounded-md bg-brand-50 text-brand-700 border border-brand-200/60">
                      {room.category}
                    </span>
                    <span className="font-mono text-xs font-semibold text-slate-400">
                      Room #{room.room_number}
                    </span>
                  </div>

                  <h3 className="text-xl font-bold text-slate-900 group-hover:text-brand-600 transition-colors">
                    {room.category}
                  </h3>

                  <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
                    <div className="flex items-center gap-1">
                      <Users className="w-4 h-4 text-slate-400" />
                      <span>Up to {room.max_capacity} {room.max_capacity === 1 ? 'Guest' : 'Guests'}</span>
                    </div>
                    <div className="flex items-center gap-1 text-emerald-600 font-medium">
                      <Check className="w-3.5 h-3.5" />
                      <span>Available Now</span>
                    </div>
                  </div>
                </div>

                {/* Card Footer */}
                <div className="bg-slate-50/80 p-6 border-t border-slate-100 flex items-center justify-between">
                  <div>
                    <div className="flex items-baseline gap-1">
                      <span className="text-2xl font-black text-slate-900">${room.rate_per_night}</span>
                      <span className="text-xs text-slate-500">/ night</span>
                    </div>
                    {nights > 0 && (
                      <span className="text-[11px] text-slate-400 font-medium block">
                        Est. ${estimatedTotal.toFixed(2)} for {nights} {nights === 1 ? 'night' : 'nights'}
                      </span>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={() => setBookingRoom(room)}
                    className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-brand-600 text-white font-semibold text-xs transition-colors shadow-sm"
                  >
                    Book Room
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Booking Modal */}
      {bookingRoom && (
        <BookingModal
          room={bookingRoom}
          checkIn={checkIn}
          checkOut={checkOut}
          onClose={() => setBookingRoom(null)}
          onBookingSuccess={() => {
            fetchRooms();
          }}
        />
      )}
    </div>
  );
};
