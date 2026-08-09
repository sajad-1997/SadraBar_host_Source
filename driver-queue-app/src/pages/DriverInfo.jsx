import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueue } from '../context/QueueContext';

function DriverInfo() {
  const navigate = useNavigate();
  const { verifyDriver, setCurrentUser } = useQueue();
  
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    nationalCode: ''
  });
  
  const [error, setError] = useState('');

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
    if (!formData.firstName || !formData.lastName || !formData.nationalCode) {
      setError('لطفا تمام فیلدها را پر کنید');
      return;
    }

    // Verify driver exists in system
    const exists = verifyDriver(formData.firstName, formData.lastName, formData.nationalCode);
    
    if (exists) {
      // Driver exists, set current user and navigate to queue page
      setCurrentUser(formData);
      navigate('/queue');
    } else {
      // Driver not found, redirect to registration
      navigate('/driver-registration', { state: { driverData: formData } });
    }
  };

  return (
    <div className="page-container driver-info-page">
      <div className="form-card">
        <h2>ورود اطلاعات راننده</h2>
        <p className="subtitle">لطفا اطلاعات خود را وارد کنید</p>
        
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

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="submit-btn">
            ادامه
          </button>
        </form>
      </div>
    </div>
  );
}

export default DriverInfo;
