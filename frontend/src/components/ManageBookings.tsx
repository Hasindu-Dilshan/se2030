import React, { useState, useEffect } from 'react';
import { Booking } from '../types';
import {
  listBookings,
  getBookingByRef,
  updateBookingDates,
  deleteBooking,
  getManageToken,
  saveManageToken,
} from '../services/api';
import { ReceiptCard } from './ReceiptCard';
import {
  Search,
  Edit2,
  Trash2,
  Printer,
  KeyRound,
  AlertTriangle,
  Info,
  Clock,
  CheckCircle,
  X,
  AlertCircle
} from 'lucide-react';

export const ManageBookings: React.FC = () => {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchRef, setSearchRef] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState<string | null>(null);

  // Modal states
  const [viewingReceipt, setViewingReceipt] = useState<Booking | null>(null);
  const [modifyingBooking, setModifyingBooking] = useState<Booking | null>(null);
  const [cancellingBooking, setCancellingBooking] = useState<Booking | null>(null);

  // Form states for Modify Dates
  const [newCheckIn, setNewCheckIn] = useState<string>('');
  const [newCheckOut, setNewCheckOut] = useState<string>('');
  const [modalToken, setModalToken] = useState<string>('');
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [modalError, setModalError] = useState<string | null>(null);

  const fetchBookingsList = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const data = await listBookings(statusFilter);
      setBookings(data);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Failed to load bookings list.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBookingsList();
  }, [statusFilter]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchRef.trim()) {
      fetchBookingsList();
      return;
    }

    setLoading(true);
    setErrorMessage(null);
    try {
      const singleBooking = await getBookingByRef(searchRef.trim().toUpperCase());
      setBookings([singleBooking]);
    } catch (err: any) {
      setBookings([]);
      setErrorMessage(
        err.response?.status === 404
          ? `No active reservation found with reference '${searchRef.trim().toUpperCase()}'. Note: Cancelled reservations are permanently removed.`
          : 'Error searching for booking.'
      );
    } finally {
      setLoading(false);
    }
  };

  const openModifyModal = (booking: Booking) => {
    setModifyingBooking(booking);
    setNewCheckIn(booking.check_in);
    setNewCheckOut(booking.check_out);
    setModalToken(getManageToken(booking.booking_ref) || '');
    setModalError(null);
  };

  const handleUpdateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!modifyingBooking) return;

    if (!modalToken.trim()) {
      setModalError('Management token is required to modify this booking.');
      return;
    }

    if (newCheckOut <= newCheckIn) {
      setModalError('Check-out date must be strictly after check-in date.');
      return;
    }

    setActionLoading(true);
    setModalError(null);
    try {
      const updated = await updateBookingDates(
        modifyingBooking.booking_ref,
        { check_in: newCheckIn, check_out: newCheckOut },
        modalToken.trim()
      );
      saveManageToken(updated.booking_ref, modalToken.trim());

      // Update state
      setBookings((prev) =>
        prev.map((b) => (b.booking_ref === updated.booking_ref ? updated : b))
      );
      setModifyingBooking(null);
      showToast(`Booking ${updated.booking_ref} dates updated successfully!`);
    } catch (err: any) {
      if (err.response?.status === 409) {
        setModalError(
          err.response.data.detail || 'The room is not available for the requested new dates.'
        );
      } else if (err.response?.status === 403) {
        setModalError('Invalid management token. Check your token and try again.');
      } else {
        setModalError(err.response?.data?.detail || 'Failed to update stay dates.');
      }
    } finally {
      setActionLoading(false);
    }
  };

  const openCancelDialog = (booking: Booking) => {
    setCancellingBooking(booking);
    setModalToken(getManageToken(booking.booking_ref) || '');
    setModalError(null);
  };

  const handleCancelConfirm = async () => {
    if (!cancellingBooking) return;

    if (!modalToken.trim()) {
      setModalError('Management token is required to cancel this reservation.');
      return;
    }

    setActionLoading(true);
    setModalError(null);
    const targetRef = cancellingBooking.booking_ref;

    try {
      await deleteBooking(targetRef, modalToken.trim());

      // Optimistic UI update: immediately remove from current list
      setBookings((prev) => prev.filter((b) => b.booking_ref !== targetRef));
      setCancellingBooking(null);
      showToast(`Reservation ${targetRef} cancelled. Room is now immediately released.`);
    } catch (err: any) {
      if (err.response?.status === 403) {
        setModalError('Invalid management token. You are not authorized to cancel this booking.');
      } else {
        setModalError(err.response?.data?.detail || 'Failed to cancel booking.');
      }
    } finally {
      setActionLoading(false);
    }
  };

  const showToast = (msg: string) => {
    setSuccessToast(msg);
    setTimeout(() => setSuccessToast(null), 4000);
  };

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {successToast && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 text-white px-5 py-3.5 rounded-2xl shadow-xl border border-slate-700 flex items-center gap-3 text-sm animate-bounce">
          <CheckCircle className="w-5 h-5 text-emerald-400" />
          <span>{successToast}</span>
        </div>
      )}

      {/* Header & Search Bar */}
      <section className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-slate-200/80">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">
              Manage Guest Bookings
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-1">
              Look up itineraries, modify reservation dates, view receipts, or manage cancellations.
            </p>
          </div>

          {/* Quick Notice about Completed vs Cancelled Stays */}
          <div className="bg-blue-50 border border-blue-200 text-blue-900 p-3 rounded-2xl text-xs flex items-start gap-2 max-w-md">
            <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <p>
              <strong>Notice:</strong> Past bookings represent completed stays (departure date has passed). Cancelled reservations are permanently removed and do not appear in stay history.
            </p>
          </div>
        </div>

        {/* Search Bar & Filters */}
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <form onSubmit={handleSearch} className="flex-1 flex items-center gap-2 w-full">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="text"
                placeholder="Search by reference (e.g. TRV-2026-X9K2L)..."
                value={searchRef}
                onChange={(e) => setSearchRef(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-mono uppercase focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
            <button
              type="submit"
              className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-sm transition-colors shadow-sm"
            >
              Search
            </button>
            {searchRef && (
              <button
                type="button"
                onClick={() => {
                  setSearchRef('');
                  fetchBookingsList();
                }}
                className="px-3 py-2.5 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-100 text-sm font-medium"
              >
                Clear
              </button>
            )}
          </form>

          {/* Status Filter */}
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full sm:w-auto px-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500 shadow-sm"
            >
              <option value="ALL">All Statuses</option>
              <option value="CONFIRMED">Active (CONFIRMED)</option>
              <option value="COMPLETED">Completed Stays</option>
            </select>
          </div>
        </div>

        {errorMessage && (
          <div className="mt-4 p-3.5 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}
      </section>

      {/* Bookings List */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div key={i} className="bg-white rounded-2xl p-6 border border-slate-200 animate-pulse h-32"></div>
          ))}
        </div>
      ) : bookings.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center border border-slate-200 shadow-sm max-w-md mx-auto">
          <Clock className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">No Reservations Found</h3>
          <p className="text-xs text-slate-500 mt-1">
            {searchRef
              ? 'No booking matches this reference. Please verify your reference code.'
              : 'There are currently no bookings matching the selected filter.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {bookings.map((booking) => {
            const hasLocalToken = !!getManageToken(booking.booking_ref);

            return (
              <div
                key={booking.id}
                className="bg-white rounded-2xl border border-slate-200 hover:border-slate-300 p-6 shadow-sm transition-all flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6"
              >
                {/* Main Details */}
                <div className="space-y-3 flex-1">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <span className="font-mono text-base font-bold text-brand-700 bg-brand-50 px-2.5 py-1 rounded-lg border border-brand-200/60">
                      {booking.booking_ref}
                    </span>
                    <span
                      className={`text-xs px-2.5 py-0.5 rounded-full font-semibold ${
                        booking.status === 'CONFIRMED'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-slate-100 text-slate-700 border border-slate-200'
                      }`}
                    >
                      {booking.status}
                    </span>
                    {hasLocalToken && (
                      <span className="text-[11px] px-2 py-0.5 rounded-md bg-amber-50 text-amber-800 border border-amber-200 flex items-center gap-1">
                        <KeyRound className="w-3 h-3 text-amber-600" />
                        <span>Token Saved</span>
                      </span>
                    )}
                  </div>

                  {/* Guest and Room Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                    <div>
                      <span className="text-slate-400 block font-medium">Guest Profile</span>
                      <span className="font-semibold text-slate-800">{booking.tourist?.full_name}</span>
                      <span className="text-slate-500 block font-mono text-[11px]">
                        ID: {booking.tourist?.passport_id}
                      </span>
                    </div>

                    <div>
                      <span className="text-slate-400 block font-medium">Room Assigned</span>
                      <span className="font-semibold text-slate-800">
                        Room {booking.room?.room_number} ({booking.room?.category})
                      </span>
                      <span className="text-slate-500 block">
                        ${booking.room?.rate_per_night}/night
                      </span>
                    </div>

                    <div>
                      <span className="text-slate-400 block font-medium">Stay Duration</span>
                      <span className="font-semibold text-slate-800">
                        {booking.check_in} → {booking.check_out}
                      </span>
                      <span className="text-brand-600 font-semibold block">
                        {booking.total_nights} nights • ${booking.total_tariff.toFixed(2)} total
                      </span>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex flex-wrap items-center gap-2 w-full lg:w-auto border-t lg:border-t-0 pt-4 lg:pt-0">
                  <button
                    type="button"
                    onClick={() => setViewingReceipt(booking)}
                    className="flex-1 lg:flex-none flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold transition-colors"
                  >
                    <Printer className="w-3.5 h-3.5" />
                    <span>Receipt</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => openModifyModal(booking)}
                    className="flex-1 lg:flex-none flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-xl bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold transition-colors shadow-sm"
                  >
                    <Edit2 className="w-3.5 h-3.5 text-brand-600" />
                    <span>Modify Dates</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => openCancelDialog(booking)}
                    className="flex-1 lg:flex-none flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-xl bg-rose-50 border border-rose-200 hover:bg-rose-100 text-rose-700 text-xs font-semibold transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5 text-rose-600" />
                    <span>Cancel Stay</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modify Dates Modal */}
      {modifyingBooking && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="relative bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden border border-slate-200">
            <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-base">Modify Stay Dates</h3>
                <p className="text-xs text-slate-300 font-mono">{modifyingBooking.booking_ref}</p>
              </div>
              <button
                onClick={() => setModifyingBooking(null)}
                className="text-slate-400 hover:text-white p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleUpdateSubmit} className="p-6 space-y-4">
              <p className="text-xs text-slate-500 leading-relaxed">
                Adjust check-in and check-out dates. Concurrency collision checking will re-evaluate availability excluding this booking.
              </p>

              {modalError && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                  <div>{modalError}</div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">New Check-In</label>
                  <input
                    type="date"
                    required
                    value={newCheckIn}
                    onChange={(e) => setNewCheckIn(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">New Check-Out</label>
                  <input
                    type="date"
                    required
                    value={newCheckOut}
                    onChange={(e) => setNewCheckOut(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center justify-between">
                  <span>Management Token</span>
                  <span className="text-[11px] text-slate-400">Required for security</span>
                </label>
                <div className="relative">
                  <KeyRound className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    required
                    placeholder="Enter booking secret token"
                    value={modalToken}
                    onChange={(e) => setModalToken(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-xs font-mono focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              </div>

              <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setModifyingBooking(null)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs transition-colors shadow-sm disabled:opacity-50"
                >
                  {actionLoading ? 'Updating...' : 'Save New Dates'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Cancel Confirmation Dialog */}
      {cancellingBooking && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="relative bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden border border-slate-200 p-6 space-y-4">
            <div className="w-12 h-12 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto">
              <AlertTriangle className="w-6 h-6" />
            </div>

            <div className="text-center">
              <h3 className="text-lg font-bold text-slate-900">Cancel Reservation?</h3>
              <p className="text-xs text-slate-500 mt-1">
                Are you sure you want to cancel booking <span className="font-mono font-bold text-slate-800">{cancellingBooking.booking_ref}</span>?
              </p>
            </div>

            <div className="bg-amber-50 border border-amber-200 p-3 rounded-xl text-xs text-amber-900">
              <p>
                <strong>Hard Delete Policy:</strong> Cancelling immediately releases the room for other guests. This record is permanently deleted from the active registry.
              </p>
            </div>

            {modalError && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800">
                {modalError}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Management Token
              </label>
              <input
                type="text"
                placeholder="Enter booking secret token"
                value={modalToken}
                onChange={(e) => setModalToken(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs font-mono focus:outline-none focus:ring-2 focus:ring-rose-500"
              />
            </div>

            <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setCancellingBooking(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900"
              >
                Keep Booking
              </button>
              <button
                type="button"
                onClick={handleCancelConfirm}
                disabled={actionLoading}
                className="px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-semibold text-xs transition-colors shadow-sm disabled:opacity-50"
              >
                {actionLoading ? 'Cancelling...' : 'Confirm Cancellation'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Printable Receipt Modal */}
      {viewingReceipt && (
        <ReceiptCard
          booking={viewingReceipt}
          isModal={true}
          onClose={() => setViewingReceipt(null)}
        />
      )}
    </div>
  );
};
