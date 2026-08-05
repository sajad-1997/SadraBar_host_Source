import { createContext, useContext, useState, useEffect } from 'react';

const QueueContext = createContext();

export const useQueue = () => {
  const context = useContext(QueueContext);
  if (!context) {
    throw new Error('useQueue must be used within a QueueProvider');
  }
  return context;
};

// Mock data for existing drivers in the system
const mockExistingDrivers = [
  { firstName: 'علی', lastName: 'محمدی', nationalCode: '1234567890', phone: '09123456789' },
  { firstName: 'رضا', lastName: 'احمدی', nationalCode: '0987654321', phone: '09129876543' },
];

export const QueueProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [queueList, setQueueList] = useState([]);
  const [userPosition, setUserPosition] = useState(null);
  const [isQueueActive, setIsQueueActive] = useState(false);
  const [showNotification, setShowNotification] = useState(false);
  const [notificationResponse, setNotificationResponse] = useState(null);

  // Check if queue is active (8:00 - 11:00 for registration, 11:00-11:30 for notifications)
  useEffect(() => {
    const checkQueueTime = () => {
      const now = new Date();
      const hours = now.getHours();
      const minutes = now.getMinutes();
      const dayOfWeek = now.getDay(); // 0 = Sunday, 6 = Saturday in Iran

      // Check if it's a working day (Saturday to Thursday in Iran: 6, 0, 1, 2, 3, 4)
      const isWorkingDay = dayOfWeek !== 5; // Not Friday

      if (isWorkingDay) {
        // Queue active from 8:00 to 11:30
        if ((hours === 8 || hours === 9 || hours === 10) || (hours === 11 && minutes <= 30)) {
          setIsQueueActive(true);
          
          // Show notification between 11:00 and 11:30
          if (hours === 11 && minutes >= 0 && minutes <= 30) {
            setShowNotification(true);
          } else {
            setShowNotification(false);
          }
        } else {
          setIsQueueActive(false);
          setShowNotification(false);
        }
      } else {
        setIsQueueActive(false);
        setShowNotification(false);
      }
    };

    checkQueueTime();
    const interval = setInterval(checkQueueTime, 60000); // Check every minute

    return () => clearInterval(interval);
  }, []);

  // Verify driver exists in system
  const verifyDriver = (firstName, lastName, nationalCode) => {
    const driver = mockExistingDrivers.find(
      d => d.firstName === firstName && d.lastName === lastName && d.nationalCode === nationalCode
    );
    return !!driver;
  };

  // Register new driver
  const registerDriver = (driverData) => {
    // In real app, this would save to backend
    console.log('Driver registered:', driverData);
    return true;
  };

  // Get queue position
  const getQueuePosition = (userId) => {
    const index = queueList.findIndex(q => q.userId === userId);
    return index !== -1 ? index + 1 : null;
  };

  // Join queue
  const joinQueue = (user) => {
    const newEntry = {
      userId: user.nationalCode,
      firstName: user.firstName,
      lastName: user.lastName,
      joinedAt: new Date(),
      hasCargo: false,
      location: { lat: 35.6892, lng: 51.3890 } // Tehran office location mock
    };
    
    setQueueList(prev => [...prev, newEntry]);
    setCurrentUser(user);
    setUserPosition(queueList.length + 1);
  };

  // Handle notification response
  const handleNotificationResponse = (hasCargo) => {
    if (hasCargo) {
      // Remove user from queue
      setQueueList(prev => prev.filter(q => q.userId !== currentUser?.nationalCode));
      setNotificationResponse('cargo-taken');
    } else {
      // Keep user in queue
      setNotificationResponse('still-waiting');
    }
    setShowNotification(false);
    
    // Update positions after response
    updateQueuePositions();
  };

  // Update queue positions
  const updateQueuePositions = () => {
    if (currentUser) {
      setUserPosition(getQueuePosition(currentUser.nationalCode));
    }
  };

  // Auto-remove users who didn't respond after 15 minutes
  useEffect(() => {
    if (showNotification) {
      const checkTimeout = setTimeout(() => {
        // This would check for non-responders and remove them
        console.log('Checking for non-responders...');
      }, 15 * 60 * 1000); // 15 minutes

      return () => clearTimeout(checkTimeout);
    }
  }, [showNotification]);

  // Check distance from office (mock function)
  const checkDistanceFromOffice = (userLocation) => {
    const officeLocation = { lat: 35.6892, lng: 51.3890 }; // Tehran
    const distance = calculateDistance(userLocation, officeLocation);
    return distance <= 5; // Within 5km
  };

  // Calculate distance between two points (Haversine formula)
  const calculateDistance = (coord1, coord2) => {
    const R = 6371; // Earth radius in km
    const dLat = (coord2.lat - coord1.lat) * Math.PI / 180;
    const dLng = (coord2.lng - coord1.lng) * Math.PI / 180;
    const a = 
      Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(coord1.lat * Math.PI / 180) * Math.cos(coord2.lat * Math.PI / 180) *
      Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  };

  // Auto-remove users outside 5km range during update time
  const removeUsersOutsideRange = () => {
    setQueueList(prev => prev.filter(q => {
      if (q.location) {
        return checkDistanceFromOffice(q.location);
      }
      return true;
    }));
  };

  const value = {
    currentUser,
    setCurrentUser,
    queueList,
    userPosition,
    isQueueActive,
    showNotification,
    notificationResponse,
    verifyDriver,
    registerDriver,
    joinQueue,
    handleNotificationResponse,
    getQueuePosition,
    removeUsersOutsideRange,
  };

  return (
    <QueueContext.Provider value={value}>
      {children}
    </QueueContext.Provider>
  );
};
