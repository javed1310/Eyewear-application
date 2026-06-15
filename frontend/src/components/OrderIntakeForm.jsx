import { useState, useRef } from 'react'
import { Plus, X, UploadCloud, Sparkles, CheckCircle, AlertCircle } from 'lucide-react'
import api from '../api/client'
import toast from 'react-hot-toast'

export function OrderIntakeForm({ onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    customer_id: 1, // hardcoded for demo
    store_location: 'Downtown Flagship',
    source_channel: 'in_store',
    prescription: {
      od_sph: -1.0, od_cyl: -0.5, od_axis: 90, od_pd: 31.5,
      os_sph: -1.0, os_cyl: -0.5, os_axis: 180, os_pd: 31.5,
      prescribed_by: 'Dr. Smith'
    },
    lens_spec: {
      lens_type: 'single_vision', lens_index: 1.61, coatings: ['AR']
    },
    frame: {
      sku: 'FR-123', model_name: 'Wayfarer Classic', color: 'Black'
    }
  })
  
  const [isUploading, setIsUploading] = useState(false)
  const [aiConfidence, setAiConfidence] = useState(null)
  const fileInputRef = useRef(null)

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(formData)
  }

  const updateRx = (eye, field, value) => {
    setFormData(prev => ({
      ...prev,
      prescription: {
        ...prev.prescription,
        [`${eye}_${field}`]: parseFloat(value) || value
      }
    }))
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      setIsUploading(true)
      const res = await api.post('/api/v1/prescriptions/parse-image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      const { parsed_data, confidence } = res.data
      
      setFormData(prev => ({
        ...prev,
        prescription: {
          od_sph: parsed_data.od_sph, od_cyl: parsed_data.od_cyl, od_axis: parsed_data.od_axis, od_pd: parsed_data.od_pd,
          os_sph: parsed_data.os_sph, os_cyl: parsed_data.os_cyl, os_axis: parsed_data.os_axis, os_pd: parsed_data.os_pd,
          prescribed_by: parsed_data.prescribed_by || prev.prescription.prescribed_by
        }
      }))
      
      setAiConfidence(confidence)
      toast.success('AI successfully extracted prescription data')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to parse image')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[100] p-4">
      <div className="glass-card w-full max-w-3xl bg-surface-900 overflow-hidden flex flex-col max-h-[90vh]">
        <div className="p-4 border-b border-surface-700 flex justify-between items-center bg-surface-800">
          <h2 className="text-lg font-bold text-surface-100">New Order Intake</h2>
          <button onClick={onClose} className="text-surface-400 hover:text-white"><X className="w-5 h-5"/></button>
        </div>

        <div className="p-6 overflow-y-auto flex-1">
          <form id="intake-form" onSubmit={handleSubmit} className="space-y-6">
            
            {/* Meta */}
            <div className="grid grid-cols-2 gap-4">
               <div>
                  <label className="block text-xs text-surface-400 mb-1">Store Location</label>
                  <input type="text" className="input-field text-sm" value={formData.store_location} onChange={e => setFormData({...formData, store_location: e.target.value})} required />
               </div>
               <div>
                  <label className="block text-xs text-surface-400 mb-1">Source Channel</label>
                  <select className="input-field text-sm bg-surface-900" value={formData.source_channel} onChange={e => setFormData({...formData, source_channel: e.target.value})}>
                     <option value="in_store">In-Store</option>
                     <option value="online">Online</option>
                     <option value="phone">Phone</option>
                  </select>
               </div>
            </div>

            {/* AI Upload Zone */}
            <div className="border-2 border-dashed border-primary-500/30 rounded-xl p-6 bg-primary-500/5 text-center cursor-pointer hover:bg-primary-500/10 transition-colors" onClick={() => fileInputRef.current?.click()}>
              <input type="file" ref={fileInputRef} className="hidden" accept="image/*" onChange={handleFileUpload} />
              {isUploading ? (
                <div className="flex flex-col items-center gap-2">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500" />
                  <p className="text-sm text-primary-400 font-medium">Analyzing Prescription with xAI Vision...</p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <div className="p-3 bg-primary-500/20 rounded-full text-primary-400">
                    <UploadCloud className="w-6 h-6" />
                  </div>
                  <h3 className="text-sm font-semibold text-primary-400 flex items-center gap-2">
                    <Sparkles className="w-4 h-4" /> Autofill with AI
                  </h3>
                  <p className="text-xs text-surface-400">Upload an image of the physical prescription card</p>
                </div>
              )}
            </div>

            {/* Prescription */}
            <div className={`border rounded-xl p-4 transition-colors ${aiConfidence ? 'border-emerald-500/50 bg-emerald-500/5' : 'border-surface-700 bg-surface-800/30'}`}>
               <div className="flex justify-between items-center mb-4">
                 <h3 className="text-sm font-semibold text-primary-400 flex items-center gap-2">
                   Prescription (Rx) 
                   {aiConfidence && <CheckCircle className="w-4 h-4 text-emerald-400" />}
                 </h3>
                 {aiConfidence && (
                   <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full font-medium">
                     AI Confidence: {(aiConfidence.overall * 100).toFixed(0)}%
                   </span>
                 )}
               </div>
               <div className="grid grid-cols-5 gap-4 mb-2 text-xs text-surface-400 font-medium">
                  <div>Eye</div><div>SPH</div><div>CYL</div><div>AXIS</div><div>PD</div>
               </div>
               
               {['od', 'os'].map(eye => (
                  <div key={eye} className="grid grid-cols-5 gap-4 mb-3 items-center relative">
                     <div className="text-sm font-bold uppercase text-surface-300">{eye === 'od' ? 'Right (OD)' : 'Left (OS)'}</div>
                     {['sph', 'cyl', 'axis', 'pd'].map(field => {
                       const conf = aiConfidence?.fields[`${eye}_${field}`]
                       const isLowConf = conf && conf < 0.90
                       return (
                         <div key={field} className="relative">
                           <input type="number" step="any" className={`input-field text-sm w-full ${isLowConf ? 'border-amber-500/50 bg-amber-500/10 focus:ring-amber-500' : ''}`} value={formData.prescription[`${eye}_${field}`]} onChange={e => updateRx(eye, field, e.target.value)} required />
                           {isLowConf && <AlertCircle className="w-3 h-3 text-amber-500 absolute top-2 right-2" title={`Low Confidence: ${(conf*100).toFixed(0)}%`} />}
                         </div>
                       )
                     })}
                  </div>
               ))}
            </div>

            {/* Lens Spec */}
            <div className="border border-surface-700 rounded-xl p-4 bg-surface-800/30">
               <h3 className="text-sm font-semibold text-accent-400 mb-4">Lens Specification</h3>
               <div className="grid grid-cols-2 gap-4">
                  <div>
                     <label className="block text-xs text-surface-400 mb-1">Lens Type</label>
                     <select className="input-field text-sm bg-surface-900" value={formData.lens_spec.lens_type} onChange={e => setFormData({...formData, lens_spec: {...formData.lens_spec, lens_type: e.target.value}})}>
                        <option value="single_vision">Single Vision</option>
                        <option value="bifocal">Bifocal</option>
                        <option value="progressive">Progressive</option>
                     </select>
                  </div>
                  <div>
                     <label className="block text-xs text-surface-400 mb-1">Lens Index</label>
                     <select className="input-field text-sm bg-surface-900" value={formData.lens_spec.lens_index} onChange={e => setFormData({...formData, lens_spec: {...formData.lens_spec, lens_index: parseFloat(e.target.value)}})}>
                        <option value={1.56}>1.56</option>
                        <option value={1.61}>1.61</option>
                        <option value={1.67}>1.67</option>
                        <option value={1.74}>1.74</option>
                     </select>
                  </div>
               </div>
            </div>

            {/* Frame */}
            <div className="border border-surface-700 rounded-xl p-4 bg-surface-800/30">
               <h3 className="text-sm font-semibold text-surface-300 mb-4">Frame Information</h3>
               <div className="grid grid-cols-3 gap-4">
                  <div>
                     <label className="block text-xs text-surface-400 mb-1">SKU</label>
                     <input type="text" className="input-field text-sm" value={formData.frame.sku} onChange={e => setFormData({...formData, frame: {...formData.frame, sku: e.target.value}})} />
                  </div>
                  <div>
                     <label className="block text-xs text-surface-400 mb-1">Model</label>
                     <input type="text" className="input-field text-sm" value={formData.frame.model_name} onChange={e => setFormData({...formData, frame: {...formData.frame, model_name: e.target.value}})} />
                  </div>
                  <div>
                     <label className="block text-xs text-surface-400 mb-1">Color</label>
                     <input type="text" className="input-field text-sm" value={formData.frame.color} onChange={e => setFormData({...formData, frame: {...formData.frame, color: e.target.value}})} />
                  </div>
               </div>
            </div>
            
          </form>
        </div>

        <div className="p-4 border-t border-surface-700 bg-surface-800 flex justify-end gap-3">
          <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" form="intake-form" className="btn-primary">Create Order</button>
        </div>
      </div>
    </div>
  )
}
