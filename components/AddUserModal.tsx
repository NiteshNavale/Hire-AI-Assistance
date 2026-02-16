
import React, { useState } from 'react';

interface AddUserModalProps {
  onClose: () => void;
  onAdd: (u: string, p: string) => Promise<boolean>;
}

const AddUserModal: React.FC<AddUserModalProps> = ({ onClose, onAdd }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) return;
    
    setLoading(true);
    setError('');
    
    const success = await onAdd(username, password);
    setLoading(false);
    
    if (!success) {
        setError('Failed to create user. Username may already exist.');
    } else {
        onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white w-full max-w-sm rounded-3xl shadow-2xl overflow-hidden animate-slideUp">
        <div className="p-6 bg-slate-800 text-white flex justify-between items-center">
            <h3 className="font-black text-lg">Add HR Recruiter</h3>
            <button onClick={onClose} className="text-slate-400 hover:text-white">✕</button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-8 space-y-6">
            <div className="space-y-4">
                <div>
                    <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">New Username</label>
                    <input 
                        type="text" 
                        value={username}
                        onChange={e => setUsername(e.target.value)}
                        className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none"
                        required
                    />
                </div>
                <div>
                    <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">New Password</label>
                    <input 
                        type="password" 
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                        className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none"
                        required
                    />
                </div>
            </div>

            {error && <p className="text-xs text-red-500 font-bold">{error}</p>}

            <button 
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold shadow-lg shadow-blue-100 transition-all disabled:opacity-50"
            >
                {loading ? 'Adding...' : 'Create Access'}
            </button>
        </form>
      </div>
    </div>
  );
};

export default AddUserModal;
