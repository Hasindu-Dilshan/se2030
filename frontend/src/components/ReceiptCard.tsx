import React from 'react';
import { Booking } from '../types';
import { Printer, X, CheckCircle2, ShieldCheck, MapPin, Calendar, User, CreditCard } from 'lucide-react';

interface ReceiptCardProps {
  booking: Booking;
  onClose?: () => void;
  isModal?: boolean;
}

export const ReceiptCard: React.FC<ReceiptCardProps> = ({ booking, onClose, isModal = false }) => {
  const handlePrint = () => {
    window.print();
  };

  const content = (
    <div className="receipt-card bg-white rounded-2xl border border-slate-200 shadow-xl overflow-hidden max-w-2xl w-full mx-auto text-slate-800">
      {/* Receipt Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-brand-900 text-white p-6 sm:p-8 flex justify-between items-start">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs uppercase tracking-widest bg-brand-500/30 text-sky-200 px-2.5 py-0.5 rounded-full font-semibold border border-brand-400/30">
              Official Guest Itinerary
            </span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">Tourstay Portal</h2>
          <p className="text-slate-300 text-sm mt-1 flex items-center gap-1.5">
            <MapPin className="w-3.5 h-3.5 text-brand-400" /> Grand Coastal Haven & Resort
          </p>
        </div>
        <div className="text-right">
          <div className="text-xs text-slate-400 uppercase tracking-wider font-medium">Booking Ref</div>
          <div className="text-xl sm:text-2xl font-mono font-bold text-white tracking-wider bg-white/10 px-3 py-1 rounded-lg mt-1 border border-white/10">
            {booking.booking_ref}
          </div>
        </div>
      </div>

      {/* Confirmation Seal Bar */}
      <div className="bg-emerald-50 border-y border-emerald-100 px-6 sm:px-8 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-emerald-800 font-semibold text-sm">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>Status: {booking.status}</span>
        </div>
        <div className="text-xs text-emerald-700 flex items-center gap-1">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Verified & Guaranteed</span>
        </div>
      </div>

      {/* Receipt Body */}
      <div className="p-6 sm:p-8 space-y-6">
        {/* Guest Credentials */}
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
            <User className="w-3.5 h-3.5 text-brand-500" /> Guest Information
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-slate-50 p-4 rounded-xl border border-slate-100 text-sm">
            <div>
              <span className="text-slate-500 text-xs block">Full Name</span>
              <span className="font-semibold text-slate-900">{booking.tourist?.full_name}</span>
            </div>
            <div>
              <span className="text-slate-500 text-xs block">Passport / National ID</span>
              <span className="font-mono font-medium text-slate-900">{booking.tourist?.passport_id}</span>
            </div>
            <div>
              <span className="text-slate-500 text-xs block">Nationality</span>
              <span className="text-slate-800">{booking.tourist?.nationality}</span>
            </div>
            <div>
              <span className="text-slate-500 text-xs block">Email & Phone</span>
              <span className="text-slate-800 text-xs">{booking.tourist?.email} • {booking.tourist?.phone}</span>
            </div>
          </div>
        </div>

        {/* Accommodation Details */}
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-brand-500" /> Reservation Schedule
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 bg-slate-50 p-4 rounded-xl border border-slate-100 text-sm">
            <div>
              <span className="text-slate-500 text-xs block">Room Assigned</span>
              <span className="font-semibold text-slate-900">Room {booking.room?.room_number}</span>
              <span className="text-xs text-brand-600 block">{booking.room?.category}</span>
            </div>
            <div>
              <span className="text-slate-500 text-xs block">Check-In Date</span>
              <span className="font-semibold text-slate-900">{booking.check_in}</span>
              <span className="text-xs text-slate-500 block">From 14:00</span>
            </div>
            <div>
              <span className="text-slate-500 text-xs block">Check-Out Date</span>
              <span className="font-semibold text-slate-900">{booking.check_out}</span>
              <span className="text-xs text-slate-500 block">Until 11:00</span>
            </div>
          </div>
        </div>

        {/* Financial Breakdown */}
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
            <CreditCard className="w-3.5 h-3.5 text-brand-500" /> Tariff Breakdown
          </h3>
          <div className="border border-slate-200 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-100 text-slate-600 text-xs uppercase">
                <tr>
                  <th className="py-2.5 px-4 text-left font-medium">Description</th>
                  <th className="py-2.5 px-4 text-center font-medium">Rate / Night</th>
                  <th className="py-2.5 px-4 text-center font-medium">Nights</th>
                  <th className="py-2.5 px-4 text-right font-medium">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                <tr>
                  <td className="py-3 px-4 text-slate-800">
                    {booking.room?.category} (Room {booking.room?.room_number})
                  </td>
                  <td className="py-3 px-4 text-center text-slate-600">
                    ${booking.room?.rate_per_night?.toFixed(2)}
                  </td>
                  <td className="py-3 px-4 text-center font-semibold text-slate-800">
                    {booking.total_nights}
                  </td>
                  <td className="py-3 px-4 text-right font-semibold text-slate-900">
                    ${booking.total_tariff?.toFixed(2)}
                  </td>
                </tr>
              </tbody>
              <tfoot className="bg-slate-50/80 border-t border-slate-200 font-bold">
                <tr>
                  <td colSpan={3} className="py-3 px-4 text-right text-slate-700">Total Tariff:</td>
                  <td className="py-3 px-4 text-right text-base text-brand-700 font-mono">
                    ${booking.total_tariff?.toFixed(2)}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        {/* Special Requests */}
        {booking.special_requests && (
          <div className="bg-amber-50/70 border border-amber-200/70 p-3 rounded-lg text-xs text-amber-900">
            <span className="font-semibold block mb-0.5">Special Requests:</span>
            {booking.special_requests}
          </div>
        )}

        {/* Footer Note */}
        <div className="text-center pt-2 border-t border-slate-100 text-xs text-slate-400">
          <p>Thank you for choosing Tourstay Portal. Present this confirmation code at hotel reception.</p>
          <p className="mt-0.5 text-[11px]">System Generated: {new Date(booking.created_at).toLocaleString()}</p>
        </div>
      </div>

      {/* Action Buttons (Excluded from print) */}
      <div className="no-print bg-slate-50 px-6 sm:px-8 py-4 border-t border-slate-200 flex items-center justify-between">
        <button
          type="button"
          onClick={handlePrint}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-medium text-sm shadow-sm transition-colors"
        >
          <Printer className="w-4 h-4" />
          <span>Print Receipt Card</span>
        </button>

        {isModal && onClose && (
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2.5 rounded-xl border border-slate-300 hover:bg-slate-100 text-slate-700 font-medium text-sm transition-colors"
          >
            Close Itinerary
          </button>
        )}
      </div>
    </div>
  );

  if (isModal) {
    return (
      <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 no-print-bg">
        <div className="relative w-full max-w-2xl my-8">
          <button
            type="button"
            onClick={onClose}
            className="no-print absolute -top-3 -right-3 w-8 h-8 rounded-full bg-white text-slate-600 hover:text-slate-900 shadow-md flex items-center justify-center z-10 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
          {content}
        </div>
      </div>
    );
  }

  return content;
};
