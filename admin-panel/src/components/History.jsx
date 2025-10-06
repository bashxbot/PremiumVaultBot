import { useState, useEffect } from 'react';
import './History.css';
import { FiUser, FiClock, FiKey, FiMail } from 'react-icons/fi';
import { SiNetflix, SiCrunchyroll } from 'react-icons/si';
import { GiWrestling } from 'react-icons/gi';
import { MdLocalMovies } from 'react-icons/md';

function History() {
  const [redemptionHistory, setRedemptionHistory] = useState([]);
  const [claimHistory, setClaimHistory] = useState([]);
  const [activeTab, setActiveTab] = useState('redemptions');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const [redemptionRes, claimRes] = await Promise.all([
        fetch('/api/redemption-history', { credentials: 'include' }),
        fetch('/api/claim-history', { credentials: 'include' })
      ]);

      if (redemptionRes.ok) {
        const redemptionData = await redemptionRes.json();
        setRedemptionHistory(redemptionData.history || []);
      }

      if (claimRes.ok) {
        const claimData = await claimRes.json();
        setClaimHistory(claimData.history || []);
      }
    } catch (error) {
      console.error('Error fetching history:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPlatformIcon = (platform) => {
    const iconMap = {
      'Netflix': <SiNetflix className="platform-icon" />,
      'Crunchyroll': <SiCrunchyroll className="platform-icon" />,
      'WWE': <GiWrestling className="platform-icon" />,
      'DisneyPlus': <MdLocalMovies className="platform-icon" />,
      'ParamountPlus': <MdLocalMovies className="platform-icon" />,
      'Dazn': <MdLocalMovies className="platform-icon" />,
      'MolotovTV': <MdLocalMovies className="platform-icon" />,
      'PSNFA': <MdLocalMovies className="platform-icon" />,
      'Xbox': <MdLocalMovies className="platform-icon" />
    };
    return iconMap[platform] || <MdLocalMovies className="platform-icon" />;
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

  return (
    <div className="history-container">
      <div className="history-header">
        <h1 className="history-title">Activity History</h1>
        <div className="tab-buttons">
          <button
            className={`tab-button ${activeTab === 'redemptions' ? 'active' : ''}`}
            onClick={() => setActiveTab('redemptions')}
          >
            <FiKey /> Key Redemptions ({redemptionHistory.length})
          </button>
          <button
            className={`tab-button ${activeTab === 'claims' ? 'active' : ''}`}
            onClick={() => setActiveTab('claims')}
          >
            <FiMail /> Credential Claims ({claimHistory.length})
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading">Loading history...</div>
      ) : (
        <>
          {activeTab === 'redemptions' && (
            <div className="history-section">
              <h2 className="section-title">Key Redemption History</h2>
              {redemptionHistory.length === 0 ? (
                <div className="no-data">No redemption history available</div>
              ) : (
                <div className="history-table-container">
                  <table className="history-table">
                    <thead>
                      <tr>
                        <th>Platform</th>
                        <th>Key Code</th>
                        <th>User Name</th>
                        <th>Username</th>
                        <th>User ID</th>
                        <th>Redeemed At</th>
                      </tr>
                    </thead>
                    <tbody>
                      {redemptionHistory.map((item, index) => (
                        <tr key={index} style={{ animationDelay: `${index * 0.05}s` }}>
                          <td>
                            <div className="platform-cell">
                              {getPlatformIcon(item.platform)}
                              <span>{item.platform}</span>
                            </div>
                          </td>
                          <td><code className="key-code">{item.key_code}</code></td>
                          <td><FiUser className="inline-icon" /> {item.full_name}</td>
                          <td>@{item.username}</td>
                          <td><code>{item.user_id}</code></td>
                          <td><FiClock className="inline-icon" /> {formatDate(item.redeemed_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === 'claims' && (
            <div className="history-section">
              <h2 className="section-title">Credential Claim History</h2>
              {claimHistory.length === 0 ? (
                <div className="no-data">No claim history available</div>
              ) : (
                <div className="history-table-container">
                  <table className="history-table">
                    <thead>
                      <tr>
                        <th>Platform</th>
                        <th>Email</th>
                        <th>User Name</th>
                        <th>Username</th>
                        <th>User ID</th>
                        <th>Claimed At</th>
                      </tr>
                    </thead>
                    <tbody>
                      {claimHistory.map((item, index) => (
                        <tr key={index} style={{ animationDelay: `${index * 0.05}s` }}>
                          <td>
                            <div className="platform-cell">
                              {getPlatformIcon(item.platform)}
                              <span>{item.platform}</span>
                            </div>
                          </td>
                          <td><code className="email-code">{item.email}</code></td>
                          <td><FiUser className="inline-icon" /> {item.full_name}</td>
                          <td>@{item.username}</td>
                          <td><code>{item.user_id}</code></td>
                          <td><FiClock className="inline-icon" /> {formatDate(item.claimed_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default History;
