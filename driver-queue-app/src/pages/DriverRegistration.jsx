import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useQueue } from '../context/QueueContext';

function DriverRegistration() {
  const navigate = useNavigate();
  const location = useLocation();
  const { registerDriver, setCurrentUser } = useQueue();
  
  const initialData = location.state?.driverData || {};
  
  const [formData, setFormData] = useState({
    firstName: initialData.firstName || '',
    lastName: initialData.lastName || '',
    nationalCode: initialData.nationalCode || '',
    phone: ''
  });
  
  const [error, setError] = useState('');
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validate inputs
    if (!formData.firstName || !formData.lastName || !formData.nationalCode || !formData.phone) {
      setError('لطفا تمام فیلدها را پر کنید');
      return;
    }

    // Validate phone number (Iranian mobile format)
    const phoneRegex = /^09[0-9]{9}$/;
    if (!phoneRegex.test(formData.phone)) {
      setError('شماره تماس معتبر نیست. فرمت صحیح: 09123456789');
      return;
    }

    // Register driver
    const success = registerDriver(formData);
    
    if (success) {
      // Show success message
      setShowSuccessMessage(true);
      
      // Set current user
      setCurrentUser(formData);
      
      // After user confirms, navigate to queue page
      setTimeout(() => {
        navigate('/queue');
      }, 3000); // Auto navigate after 3 seconds
    }
  };

  const handleConfirmAndContinue = () => {
    navigate('/queue');
  };

  if (showSuccessMessage) {
    return (
      <div className="page-container registration-page">
        <div className="success-card">
          <div className="success-icon">✓</div>
          <h2>ثبت نام با موفقیت انجام شد</h2>
          <p className="message">
            جهت دریافت بار باید اطلاعات تکمیلی خود را به دفتر باربری ارائه دهید 
            و پس از تایید پیام توسط کاربر به صفحه نوبت دهی هدایت شوید.
          </p>
          <button 
            className="confirm-btn"
            onClick={handleConfirmAndContinue}
          >
            تایید و ادامه
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container registration-page">
      <div className="form-card">
        <h2>ثبت نام راننده</h2>
        <p className="subtitle">لطفا اطلاعات خود را کامل کنید</p>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="firstName">نام:</label>
            <input
              type="text"
              id="firstName"
              name="firstName"
              value={formData.firstName}
              onChange={handleChange}
              placeholder="نام خود را وارد کنید"
              dir="rtl"
            />
          </div>

          <div className="form-group">
            <label htmlFor="lastName">نام خانوادگی:</label>
            <input
              type="text"
              id="lastName"
              name="lastName"
              value={formData.lastName}
              onChange={handleChange}
              placeholder="نام خانوادگی خود را وارد کنید"
              dir="rtl"
            />
          </div>

          <div className="form-group">
            <label htmlFor="nationalCode">کد ملی:</label>
            <input
              type="text"
              id="nationalCode"
              name="nationalCode"
              value={formData.nationalCode}
              onChange={handleChange}
              placeholder="کد ملی ۱۰ رقمی"
              maxLength="10"
              dir="ltr"
            />
          </div>

          <div className="form-group">
            <label htmlFor="phone">شماره تماس فعال:</label>
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              placeholder="09123456789"
              maxLength="11"
              dir="ltr"
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="submit-btn">
            ثبت نام
          </button>
        </form>
      </div>
    </div>
  );
}

export default DriverRegistration;
