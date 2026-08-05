import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueue } from '../context/QueueContext';

function QueuePage() {
  const navigate = useNavigate();
  const { 
    currentUser, 
    queueList, 
    userPosition, 
    isQueueActive, 
    showNotification, 
    handleNotificationResponse,
    joinQueue
  } = useQueue();
  
  const [hasJoinedQueue, setHasJoinedQueue] = useState(false);

  const handleJoinQueue = () => {
    if (currentUser) {
      joinQueue(currentUser);
      setHasJoinedQueue(true);
    }
  };

  // Get current time status
  const getCurrentTimeStatus = () => {
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes();
    
    if (hours < 8) {
      return 'نوبت‌دهی از ساعت ۸ صبح شروع می‌شود';
    } else if (hours === 8 || hours === 9 || hours === 10) {
      return 'زمان دریافت نوبت';
    } else if (hours === 11 && minutes <= 30) {
      return 'زمان اعلام حضور';
    } else if (hours === 11 && minutes > 30) {
      return 'نوبت‌دهی به پایان رسیده است';
    } else {
      return 'نوبت‌دهی غیرفعال است';
    }
  };

  // Render notification modal
  if (showNotification && hasJoinedQueue) {
    return (
      <div className="page-container queue-page">
        <div className="notification-modal">
          <h2>اعلام حضور</h2>
          <p>آیا بار گرفته‌اید؟</p>
          <div className="notification-buttons">
            <button 
              className="btn-cargo-taken"
              onClick={() => handleNotificationResponse(true)}
            >
              بار گرفته‌ام
            </button>
            <button 
              className="btn-still-waiting"
              onClick={() => handleNotificationResponse(false)}
            >
              هنوز در نوبت هستم
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container queue-page">
      <div className="queue-header">
        <h2>صفحه نوبت‌دهی</h2>
        <div className="time-status">{getCurrentTimeStatus()}</div>
      </div>

      {!isQueueActive ? (
        <div className="queue-inactive">
          <p>نوبت‌دهی در حال حاضر غیرفعال است.</p>
          <p>ساعات کاری: شنبه تا چهارشنبه، ۸ صبح تا ۱۱:۳۰</p>
        </div>
      ) : (
        <>
          <div className="queue-info">
            <div className="queue-count">
              <span className="count-label">تعداد افراد در صف:</span>
              <span className="count-value">{queueList.length}</span>
            </div>
            
            {currentUser && hasJoinedQueue && userPosition && (
              <div className="user-position">
                <span className="position-label">موقعیت شما در صف:</span>
                <span className="position-value">{userPosition}</span>
              </div>
            )}
          </div>

          <div className="queue-actions">
            {!hasJoinedQueue ? (
              <button 
                className="join-queue-btn"
                onClick={handleJoinQueue}
                disabled={!currentUser}
              >
                دریافت نوبت
              </button>
            ) : (
              <div className="in-queue-info">
                <p>شما در صف قرار دارید</p>
                <p>تعداد نفرات جلوتر از شما: {userPosition ? userPosition - 1 : 0}</p>
              </div>
            )}
          </div>

          {queueList.length > 0 && (
            <div className="queue-list">
              <h3>اعضای در صف روزانه</h3>
              <ul>
                {queueList.map((driver, index) => (
                  <li key={driver.userId} className={`queue-item ${currentUser?.nationalCode === driver.userId ? 'current-user' : ''}`}>
                    <span className="queue-number">{index + 1}</span>
                    <span className="driver-name">{driver.firstName} {driver.lastName}</span>
                    {currentUser?.nationalCode === driver.userId && (
                      <span className="you-badge">شما</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}

      <button className="back-btn" onClick={() => navigate('/')}>
        بازگشت به صفحه اصلی
      </button>
    </div>
  );
}

export default QueuePage;
