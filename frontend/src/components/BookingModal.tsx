import React, { useState } from 'react';
import { Room, BookingCreatedResponse } from '../types';
import { createBooking } from '../services/api';
import { ReceiptCard } from './ReceiptCard';
import { 
  X, 
  Calendar, 
  User, 
  Mail, 
  Phone, 
  CreditCard, 
  KeyRound, 
  CheckCircle2, 
  Copy, 
  Check, 
  AlertCircle,
  FileText,
  Printer
} from 'lucide-react';

interface BookingModalProps {
  room: Room;
  checkIn: string;
  checkOut: string;
  onClose: () => void;
  onBookingSuccess: () => void;
}

export const BookingModal: React.FC<BookingModalProps> = ({
  room,
  checkIn,
  checkOut,
  onClose,
  onBookingSuccess,
}) => {
  // Form State
  const [formData, setFormData] = useState({
    fullName: '',
    nationality: '',
    phone: '',
    email: '',
    passportId: '',
    specialRequests: '',
  });

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [createdBooking, setCreatedBooking] = useState<BookingCreatedResponse | null>(null);
  const [showReceiptModal, setShowReceiptModal] = useState(false);
  const [copiedRef, setCopiedRef] = useState(false);
  const [copiedToken, setCopiedToken] = useState(false);

  // Compute duration and tariff
  const startDate = new Date(checkIn);
  const endDate = new Date(checkOut);
  const nights = Math.max(1, Math.round((endDate.getTime() - startDate.getTime()) / (1000 * 3600 * 24)));
  const totalTariff = nights * room.rate_per_night;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setLoading(true);

    try {
      const response = await createBooking({
        room_id: room.id,
        check_in: checkIn,
        check_out: checkOut,
        full_name: formData.fullName,
        nationality: formData.nationality,
        phone: formData.phone,
        email: formData.email,
        passport_id: formData.passportId,
        special_requests: formData.specialRequests || undefined,
      });

      setCreatedBooking(response);
      onBookingSuccess();
    } catch (err: any) {
      if (err.response?.status === 409) {
        setErrorMessage(
          err.response.data.detail ||
          'This room was just booked by another guest for the selected dates. Please choose different dates or another room.'
        );
      } else if (err.response?.status === 422) {
        const details = err.response.data?.detail;
        if (Array.isArray(details)) {
          setErrorMessage(details.map((d: any) => `${d.loc.slice(-1)}: ${d.msg}`).join('; '));
        } else {
          setErrorMessage('Please ensure all required guest fields and date formats are valid.');
        }
      } else {
        setErrorMessage(err.response?.data?.detail || 'An unexpected error occurred while placing your booking.');
      }
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string, type: 'ref' | 'token') => {
    navigator.clipboard.writeText(text);
    if (type === 'ref') {
      setCopiedRef(true);
      setTimeout(() => setCopiedRef(false), 2000);
    } else {
      setCopiedToken(true);
      setTimeout(() => setCopiedToken(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-xl w-full overflow-hidden border border-slate-200">
        {/* Header */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold">
              {createdBooking ? 'Reservation Confirmed' : `Reserve Room ${room.room_number}`}
            </h2>
            <p className="text-xs text-slate-300">
              {room.category} • ${room.rate_per_night}/night
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6">
          {createdBooking ? (
            /* Confirmation View */
            <div className="space-y-6">
              <div className="text-center">
                <div className="w-14 h-14 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-3 shadow-inner">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <h3 className="text-xl font-bold text-slate-900">Booking Confirmed!</h3>
                <p className="text-sm text-slate-500 mt-1">
                  Your reservation is secured. Please save your booking reference below.
                </p>
              </div>

              {/* Reference Box */}
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-500 font-medium block">Booking Reference</span>
                  <span className="text-lg font-mono font-bold text-brand-700 tracking-wider">
                    {createdBooking.booking_ref}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => copyToClipboard(createdBooking.booking_ref, 'ref')}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-200 hover:bg-slate-100 text-xs font-semibold text-slate-700 transition-colors shadow-sm"
                >
                  {copiedRef ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedRef ? 'Copied' : 'Copy'}</span>
                </button>
              </div>

              {/* Manage Token Box */}
              <div className="bg-amber-50/70 p-4 rounded-xl border border-amber-200/80">
                <div className="flex items-start gap-2.5">
                  <KeyRound className="w-4 h-4 text-amber-700 mt-0.5 shrink-0" />
                  <div className="text-xs text-amber-900 flex-1">
                    <p className="font-semibold text-amber-950 mb-1">Stay Management Secret Token:</p>
                    <div className="flex items-center justify-between bg-white/90 p-2 rounded-lg border border-amber-200 font-mono text-[11px] text-slate-800 break-all">
                      <span>{createdBooking.manage_token}</span>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(createdBooking.manage_token, 'token')}
                        className="ml-2 shrink-0 p-1 text-slate-600 hover:text-slate-900"
                        title="Copy Secret Token"
                      >
                        {copiedToken ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                    <p className="mt-1.5 text-[11px] text-amber-800 leading-relaxed">
                      This token has been saved to your browser's local storage for easy management. Keep it safe if accessing from another device.
                    </p>
                  </div>
                </div>
              </div>

              {/* Quick Summary */}
              <div className="grid grid-cols-2 gap-3 text-xs bg-slate-50 p-3 rounded-xl border border-slate-100">
                <div>
                  <span className="text-slate-400 block">Dates:</span>
                  <span className="font-medium text-slate-800">{checkIn} → {checkOut} ({nights} nights)</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Total Tariff:</span>
                  <span className="font-bold text-brand-700 text-sm">${totalTariff.toFixed(2)}</span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex flex-col sm:flex-row gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowReceiptModal(true)}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-medium text-sm transition-colors shadow-sm"
                >
                  <Printer className="w-4 h-4" />
                  <span>View & Print Receipt</span>
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  className="px-5 py-2.5 rounded-xl border border-slate-300 hover:bg-slate-100 text-slate-700 font-medium text-sm transition-colors"
                >
                  Close
                </button>
              </div>

              {showReceiptModal && (
                <ReceiptCard
                  booking={createdBooking}
                  isModal={true}
                  onClose={() => setShowReceiptModal(false)}
                />
              )}
            </div>
          ) : (
            /* Booking Intake Form */
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Stay Summary Strip */}
              <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-brand-600" />
                  <div>
                    <span className="text-slate-500 block">Stay Window:</span>
                    <span className="font-semibold text-slate-800">{checkIn} to {checkOut}</span>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-slate-500 block">{nights} nights × ${room.rate_per_night}</span>
                  <span className="font-bold text-slate-900 text-sm">${totalTariff.toFixed(2)}</span>
                </div>
              </div>

              {/* Error banner */}
              {errorMessage && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-start gap-2.5 text-xs text-rose-800">
                  <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold">Unable to complete reservation:</p>
                    <p>{errorMessage}</p>
                  </div>
                </div>
              )}

              {/* Full Name & Nationality */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Full Name <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <User className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                    <input
                      type="text"
                      name="fullName"
                      required
                      placeholder="e.g. Alex Mercer"
                      value={formData.fullName}
                      onChange={handleChange}
                      className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Nationality <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="nationality"
                    required
                    placeholder="e.g. Canadian"
                    value={formData.nationality}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              </div>

              {/* Email & Phone */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Email Address <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                    <input
                      type="email"
                      name="email"
                      required
                      placeholder="alex@example.com"
                      value={formData.email}
                      onChange={handleChange}
                      className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Phone Number <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <Phone className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                    <input
                      type="tel"
                      name="phone"
                      required
                      placeholder="+1-555-0199"
                      value={formData.phone}
                      onChange={handleChange}
                      className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
                </div>
              </div>

              {/* Passport / National ID */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Passport or National ID <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <CreditCard className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    name="passportId"
                    required
                    placeholder="e.g. P12345678"
                    value={formData.passportId}
                    onChange={handleChange}
                    className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-brand-500 uppercase"
                  />
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  Used to link booking history across stays without duplicate profiles.
                </p>
              </div>

              {/* Special Requests */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Special Requests (Optional)
                </label>
                <textarea
                  name="specialRequests"
                  rows={2}
                  placeholder="e.g. Quiet floor, extra pillows, late check-in"
                  value={formData.specialRequests}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
                />
              </div>

              {/* Submit Buttons */}
              <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-sm text-slate-600 hover:text-slate-900 font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-medium text-sm transition-all shadow-md shadow-brand-500/20 disabled:opacity-50"
                >
                  {loading ? (
                    <span>Confirming...</span>
                  ) : (
                    <>
                      <FileText className="w-4 h-4" />
                      <span>Confirm Reservation (${totalTariff.toFixed(2)})</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
