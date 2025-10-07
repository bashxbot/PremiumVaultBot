
import { useState, useEffect } from 'react';
import './ClaimedCredentials.css';
import { FiUser, FiClock, FiMail } from 'react-icons/fi';
import { SiNetflix, SiCrunchyroll } from 'react-icons/si';
import { GiBoxingGlove } from 'react-icons/gi';
import { FaStar, FaTv, FaGamepad, FaXbox } from 'react-icons/fa';
import { MdSportsKabaddi } from 'react-icons/md';

function ClaimedCredentials({ platform }) {
  const [claimedCreds, setClaimedCreds] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClaimedCredentials();
  }, [platform]);

  const fetchClaimedCredentials = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/credentials/${platform}/claimed`, {
        credentials: 'include'
      });
      const data = await response.json();
      if (data.success) {
        setClaimedCreds(data.claimed || []);
      }
    } catch (error) {
      console.error('Error fetching claimed credentials:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const platformIcons = {
    netflix: SiNetflix,
    crunchyroll: SiCrunchyroll,
    wwe: GiBoxingGlove,
    paramountplus: FaStar,
    dazn: MdSportsKabaddi,
    molotovtv: FaTv,
    disneyplus: FaStar,
    psnfa: FaGamepad,
    xbox: FaXbox
  };

  const PlatformIcon = platformIcons[platform];

  return (
    <div className="claimed-credentials">
      <div className="claimed-header">
        <h2>
          <PlatformIcon className="platform-icon" />
          Claimed {platform.charAt(0).toUpperCase() + platform.slice(1)} Credentials
        </h2>
      </div>

      {loading ? (
        <div className="loading">Loading claimed credentials...</div>
      ) : claimedCreds.length === 0 ? (
        <div className="no-data">No claimed credentials found</div>
      ) : (
        <div className="claimed-table-container">
          <table className="claimed-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Email</th>
                <th>User Name</th>
                <th>Username</th>
                <th>Chat ID</th>
                <th>Claimed At</th>
              </tr>
            </thead>
            <tbody>
              {claimedCreds.map((cred, index) => (
                <tr key={cred.id} style={{ animationDelay: `${index * 0.05}s` }}>
                  <td>{index + 1}</td>
                  <td>
                    <FiMail className="inline-icon" />
                    <code>{cred.email}</code>
                  </td>
                  <td>
                    <FiUser className="inline-icon" />
                    {cred.claimed_by_name || 'N/A'}
                  </td>
                  <td>@{cred.claimed_by_username || 'N/A'}</td>
                  <td><code>{cred.claimed_by}</code></td>
                  <td>
                    <FiClock className="inline-icon" />
                    {formatDate(cred.claimed_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default ClaimedCredentials;
