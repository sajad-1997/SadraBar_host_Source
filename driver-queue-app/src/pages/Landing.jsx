import { useNavigate } from 'react-router-dom';

function Landing() {
  const navigate = useNavigate();

  const handleGetQueue = () => {
    navigate('/driver-info');
  };

  const handleBookCargo = () => {
    // This would navigate to the cargo booking page
    alert('انتقال به صفحه رزرو آنلاین بار');
  };

  return (
    <div className="landing-page">
      <header className="landing-header">
        <h1>سامانه نوبت‌دهی رانندگان</h1>
        <p>به سامانه مدیریت نوبت رانندگان خوش آمدید</p>
      </header>

      <main className="landing-main">
        <div className="action-buttons">
          <button 
            className="action-btn queue-btn"
            onClick={handleGetQueue}
          >
            دریافت نوبت
          </button>
          
          <button 
            className="action-btn cargo-btn"
            onClick={handleBookCargo}
          >
            رزرو آنلاین بار
          </button>
        </div>

        <div className="info-section">
          <h2>ساعات کاری نوبت‌دهی</h2>
          <ul>
            <li>شروع نوبت‌دهی: ۸ صبح</li>
            <li>پایان نوبت‌دهی: ۱۱ صبح</li>
            <li>اعلام حضور: ۱۱ تا ۱۱:۳۰</li>
          </ul>
        </div>
      </main>
    </div>
  );
}

export default Landing;
